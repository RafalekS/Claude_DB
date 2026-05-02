"""
Project Conversations SubTab — sessions for the currently selected project only.
Filtered view of Memory > Conversations; the global view remains in memory_tab.py.
"""

from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSplitter, QTextEdit, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QLineEdit, QApplication,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor

from utils import theme
from utils.project_scanner import get_project_sessions
from utils.ui_state_manager import UIStateManager
from tabs.memory_tab import _parse_conversation, _extract_text, _get_snippet, _highlight_in_viewer


class ProjectConversationsSubTab(QWidget):
    """Sessions viewer filtered to the current project."""

    def __init__(self, project_context, config_manager=None):
        super().__init__()
        self.project_context = project_context
        self.config_manager = config_manager
        self._init_ui()
        self.project_context.project_changed.connect(self._on_project_changed)
        if self.project_context.has_project():
            self._refresh()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        self._active_search = ""

        # Toolbar
        bar = QHBoxLayout()
        self._project_label = QLabel("No project selected")
        self._project_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh)
        bar.addWidget(self._project_label)
        bar.addStretch()
        bar.addWidget(refresh_btn)
        layout.addLayout(bar)

        # Search bar
        search_row = QHBoxLayout()
        search_row.setSpacing(4)
        self._search_bar = QLineEdit()
        self._search_bar.setPlaceholderText("Search sessions for this project…")
        self._search_bar.returnPressed.connect(self._search_sessions)
        search_btn = QPushButton("🔍 Search")
        search_btn.clicked.connect(self._search_sessions)
        clear_btn = QPushButton("✕ Clear")
        clear_btn.clicked.connect(self._clear_search)
        self._search_status = QLabel("")
        self._search_status.setStyleSheet(
            f"color: {theme.FG_DIM}; font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        search_row.addWidget(self._search_bar, 1)
        search_row.addWidget(search_btn)
        search_row.addWidget(clear_btn)
        search_row.addWidget(self._search_status)
        layout.addLayout(search_row)

        # Splitter: session tree | conversation viewer
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(5)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabel("Sessions (newest first)")
        self._tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tree.itemClicked.connect(self._load_conversation)

        self._viewer = QTextEdit()
        self._viewer.setReadOnly(True)
        self._viewer.setFont(QFont(theme.FONT_MONOSPACE, theme.FONT_SIZE_SMALL))
        self._viewer.setPlaceholderText("Click a session to view its conversation.")

        splitter.addWidget(self._tree)
        splitter.addWidget(self._viewer)
        splitter.setSizes([360, 640])

        mgr = UIStateManager.instance()
        mgr.restore_splitter_state("proj_config.conv_splitter", splitter)
        mgr.connect_splitter("proj_config.conv_splitter", splitter)

        layout.addWidget(splitter, 1)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_project_changed(self, new_project):
        self._active_search = ""
        self._search_bar.clear()
        self._search_status.setText("")
        self._refresh()

    def _refresh(self):
        if self._active_search:
            return  # keep search results; user clears with ✕ Clear
        self._tree.clear()
        self._viewer.clear()

        if not self.project_context.has_project():
            self._project_label.setText("No project selected")
            self._tree.addTopLevelItem(QTreeWidgetItem(["Select a project to see its sessions."]))
            return

        project_path = self.project_context.get_project()
        self._project_label.setText(str(project_path))

        fs, projects_dir = self._get_fs_and_projects_dir()
        sessions = get_project_sessions(project_path, projects_dir, fs)
        if not sessions:
            self._tree.addTopLevelItem(QTreeWidgetItem(["No sessions found for this project."]))
            return

        for s in sessions:
            mod = datetime.fromtimestamp(s["mtime"]).strftime("%Y-%m-%d %H:%M")
            item = QTreeWidgetItem([f"{mod}   {s['uuid'][:24]}…"])
            item.setData(0, Qt.ItemDataRole.UserRole, str(s["path"]))
            item.setForeground(0, QColor(theme.FG_SECONDARY))
            self._tree.addTopLevelItem(item)

        self._tree.setCurrentItem(self._tree.topLevelItem(0))
        self._load_conversation(self._tree.topLevelItem(0))

    def _get_fs_and_projects_dir(self):
        """Return (fs, projects_dir) — None/None for local, remote fs + dir for remote."""
        if self.config_manager is None:
            return None, None
        fs = self.config_manager.fs
        projects_dir = self.config_manager.claude_dir / "projects"
        return fs, projects_dir

    def _load_conversation(self, item: QTreeWidgetItem, _col: int = 0):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path:
            return
        fs, _ = self._get_fs_and_projects_dir()
        exists = fs.exists(path) if fs else Path(path).exists()
        if not exists:
            self._viewer.setPlainText("File not found.")
            return

        messages = _parse_conversation(path, fs)
        if not messages:
            self._viewer.setPlainText(
                f"No readable messages in:\n{path}\n\n"
                "(All entries are progress / tool / snapshot records.)"
            )
            return

        stem = Path(str(path)).stem
        lines = [f"Session: {stem}\nMessages: {len(messages)}\n{'─'*60}\n"]
        for m in messages:
            role_label = "You" if m["role"] == "user" else "Claude"
            ts = f"  [{m['time']}]" if m["time"] else ""
            lines.append(f"\n{'─'*40}\n{role_label}{ts}\n{'─'*40}\n{m['text']}\n")

        self._viewer.setPlainText("".join(lines))
        if self._active_search:
            _highlight_in_viewer(self._viewer, self._active_search)

    # ── Session search ────────────────────────────────────────────────────────

    def _search_sessions(self):
        term = self._search_bar.text().strip()
        if not term:
            self._clear_search()
            return

        if not self.project_context.has_project():
            self._search_status.setText("No project selected")
            return

        self._active_search = term
        self._search_status.setText("Searching…")
        QApplication.processEvents()

        self._tree.clear()
        self._viewer.clear()
        self._viewer.setExtraSelections([])

        project_path = self.project_context.get_project()
        fs, projects_dir = self._get_fs_and_projects_dir()
        sessions = get_project_sessions(project_path, projects_dir, fs)
        if not sessions:
            self._search_status.setText("No sessions found")
            return

        term_lower = term.lower()
        matches = []
        for s in sessions:
            messages = _parse_conversation(s["path"], fs)
            snippet = ""
            for m in messages:
                if term_lower in m["text"].lower():
                    snippet = _get_snippet(m["text"], term)
                    break
            if snippet:
                matches.append({**s, "snippet": snippet})

        if not matches:
            self._search_status.setText("No matches found")
            self._tree.addTopLevelItem(QTreeWidgetItem([f"No sessions contain '{term}'"]))
            return

        total = len(sessions)
        self._search_status.setText(f"{len(matches)} of {total} session(s) match")

        for s in matches:
            mod = datetime.fromtimestamp(s["mtime"]).strftime("%Y-%m-%d %H:%M")
            sess_item = QTreeWidgetItem([f"{mod}   {s['uuid'][:24]}…"])
            sess_item.setData(0, Qt.ItemDataRole.UserRole, str(s["path"]))
            sess_item.setForeground(0, QColor(theme.FG_SECONDARY))

            snip_item = QTreeWidgetItem(sess_item, [f"  ↳ {s['snippet']}"])
            snip_item.setForeground(0, QColor(theme.FG_DIM))

            self._tree.addTopLevelItem(sess_item)

        self._tree.expandAll()
        self._tree.setCurrentItem(self._tree.topLevelItem(0))
        self._load_conversation(self._tree.topLevelItem(0))

    def _clear_search(self):
        self._active_search = ""
        self._search_bar.clear()
        self._search_status.setText("")
        self._viewer.clear()
        self._viewer.setExtraSelections([])
        self._refresh()
