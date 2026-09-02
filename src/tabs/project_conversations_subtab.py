"""
Project Conversations SubTab — sessions for the currently selected project.

Session search finds sessions containing a term; opening one then runs an
in-conversation find (Prev / Next / count, Ctrl+F) so you never scroll a
50-70 MB transcript looking for a highlight. In remote mode session text is
cached on local disk for ~15 min (utils.session_cache) so repeated searches
don't re-download over SFTP.
"""

import re
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSplitter, QPlainTextEdit, QTextEdit, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QLineEdit, QCheckBox, QApplication,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QColor, QFont, QTextCharFormat, QTextCursor, QShortcut,
    QKeySequence,
)

from utils import theme
from utils import session_cache
from utils.project_scanner import get_project_sessions
from utils.ui_state_manager import UIStateManager
from tabs.memory_tab import _parse_conversation, _get_snippet


def _build_regex(term: str, whole_word: bool, match_case: bool) -> "re.Pattern | None":
    if not term:
        return None
    pat = re.escape(term)
    if whole_word:
        pat = rf"(?<!\w){pat}(?!\w)"
    return re.compile(pat, 0 if match_case else re.IGNORECASE)


class ProjectConversationsSubTab(QWidget):
    """Sessions viewer filtered to the current project."""

    def __init__(self, project_context, config_manager=None):
        super().__init__()
        self.project_context = project_context
        self.config_manager = config_manager
        self._active_search = ""
        self._match_spans: list[tuple[int, int]] = []
        self._match_idx = -1
        self._init_ui()
        self.project_context.project_changed.connect(self._on_project_changed)
        if self.project_context.has_project():
            self._refresh()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(theme.MARGIN_MD, theme.MARGIN_MD, theme.MARGIN_MD, theme.MARGIN_MD)
        layout.setSpacing(theme.MARGIN_SM)

        # Toolbar
        bar = QHBoxLayout()
        self._project_label = QLabel("No project selected")
        self._project_label.setStyleSheet(theme.get_label_style("small", "secondary"))
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh)
        redl_btn = QPushButton("Refresh (re-download)")
        redl_btn.setToolTip("Clear the local session cache for this server, then refresh")
        redl_btn.clicked.connect(self._force_refresh)
        bar.addWidget(self._project_label)
        bar.addStretch()
        bar.addWidget(redl_btn)
        bar.addWidget(refresh_btn)
        layout.addLayout(bar)

        # Session-search row
        srow = QHBoxLayout()
        srow.setSpacing(theme.MARGIN_SM)
        self._search_bar = QLineEdit()
        self._search_bar.setPlaceholderText("Find sessions containing…")
        self._search_bar.returnPressed.connect(self._search_sessions)
        self._cb_word = QCheckBox("Whole word")
        self._cb_case = QCheckBox("Match case")
        self._cb_word.toggled.connect(self._reapply_options)
        self._cb_case.toggled.connect(self._reapply_options)
        search_btn = QPushButton("Search sessions")
        search_btn.clicked.connect(self._search_sessions)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_search)
        self._search_status = QLabel("")
        self._search_status.setStyleSheet(theme.get_label_style("small", "dim"))
        srow.addWidget(self._search_bar, 1)
        srow.addWidget(self._cb_word)
        srow.addWidget(self._cb_case)
        srow.addWidget(search_btn)
        srow.addWidget(clear_btn)
        srow.addWidget(self._search_status)
        layout.addLayout(srow)

        # Splitter: session tree | conversation viewer + find bar
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(5)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabel("Sessions (newest first)")
        self._tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._tree.itemClicked.connect(self._load_conversation)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(theme.MARGIN_SM)
        self._viewer = QPlainTextEdit()
        self._viewer.setReadOnly(True)
        self._viewer.setFont(QFont(theme.FONT_MONOSPACE, theme.FONT_SIZE_SMALL))
        self._viewer.setPlaceholderText("Click a session to view its conversation.")
        rl.addWidget(self._viewer, 1)

        # In-conversation find bar
        frow = QHBoxLayout()
        frow.setSpacing(theme.MARGIN_SM)
        frow.addWidget(QLabel("Find:"))
        self._find_bar = QLineEdit()
        self._find_bar.setPlaceholderText("find in this conversation  (Ctrl+F)")
        self._find_bar.textChanged.connect(self._recompute_matches)
        self._find_bar.returnPressed.connect(self._find_next)
        self._prev_btn = QPushButton("◀ Prev")
        self._next_btn = QPushButton("Next ▶")
        self._prev_btn.clicked.connect(self._find_prev)
        self._next_btn.clicked.connect(self._find_next)
        self._match_lbl = QLabel("")
        self._match_lbl.setStyleSheet(theme.get_label_style("small", "dim"))
        frow.addWidget(self._find_bar, 1)
        frow.addWidget(self._prev_btn)
        frow.addWidget(self._next_btn)
        frow.addWidget(self._match_lbl)
        rl.addLayout(frow)

        splitter.addWidget(self._tree)
        splitter.addWidget(right)
        splitter.setSizes([360, 640])

        mgr = UIStateManager.instance()
        mgr.restore_splitter_state("proj_config.conv_splitter", splitter)
        mgr.connect_splitter("proj_config.conv_splitter", splitter)
        layout.addWidget(splitter, 1)

        QShortcut(QKeySequence.StandardKey.Find, self, activated=self._focus_find)
        QShortcut(QKeySequence(Qt.Key.Key_F3), self, activated=self._find_next)
        QShortcut(QKeySequence("Shift+F3"), self, activated=self._find_prev)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_project_changed(self, _new_project):
        self._active_search = ""
        self._search_bar.clear()
        self._search_status.setText("")
        self._refresh()

    def _force_refresh(self):
        fs, _ = self._get_fs_and_projects_dir()
        n = session_cache.clear(session_cache.identity_for(fs)) if fs is not None else session_cache.clear()
        self._search_status.setText(f"cleared {n // 2} cached session(s)")
        self._active_search = ""
        self._refresh()

    def _refresh(self):
        if self._active_search:
            return
        self._tree.clear()
        self._viewer.clear()
        self._set_matches([])

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
            self._tree.addTopLevelItem(self._session_item(s))
        self._tree.setCurrentItem(self._tree.topLevelItem(0))
        self._load_conversation(self._tree.topLevelItem(0))

    def _session_item(self, s: dict) -> QTreeWidgetItem:
        mod = datetime.fromtimestamp(s["mtime"]).strftime("%Y-%m-%d %H:%M")
        cached = " ⇩" if session_cache.is_cached_fresh(s["path"], self._get_fs_and_projects_dir()[0]) else ""
        item = QTreeWidgetItem([f"{mod}   {s['uuid'][:24]}…{cached}"])
        item.setData(0, Qt.ItemDataRole.UserRole, str(s["path"]))
        item.setForeground(0, QColor(theme.FG_SECONDARY))
        return item

    def _get_fs_and_projects_dir(self):
        if self.config_manager is None:
            return None, None
        fs = self.config_manager.fs
        projects_dir = self.config_manager.claude_dir / "projects"
        return fs, projects_dir

    # ── Load + render a conversation ─────────────────────────────────────────

    @staticmethod
    def _render_body(path, fs, text: str) -> str:
        """Build the display transcript from raw session text.

        Used by both the viewer and the session-search hit count so the count
        shown in the tree matches the count the find bar reports.
        """
        messages = _parse_conversation(path, fs, text=text, full=True)
        if not messages:
            return ""
        stem = Path(str(path)).stem
        parts = [f"Session: {stem}\nMessages: {len(messages)}   ({len(text)//1024} KB)\n{'─'*60}\n"]
        for m in messages:
            role = "You" if m["role"] == "user" else "Claude"
            ts = f"  [{m['time']}]" if m["time"] else ""
            parts.append(f"\n{'─'*40}\n{role}{ts}\n{'─'*40}\n{m['text']}\n")
        return "".join(parts)

    def _load_conversation(self, item: QTreeWidgetItem, _col: int = 0):
        if item is None:
            return
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path:
            return
        fs, _ = self._get_fs_and_projects_dir()

        self._viewer.setPlainText("Loading…")
        QApplication.processEvents()
        try:
            text = session_cache.get_text(path, fs)
        except Exception as e:
            self._viewer.setPlainText(f"Could not read session:\n{path}\n\n{e}")
            self._set_matches([])
            return

        body = self._render_body(path, fs, text)
        if not body:
            self._viewer.setPlainText(
                f"No readable messages in:\n{path}\n\n"
                "(All entries are progress / tool / snapshot records.)"
            )
            self._set_matches([])
            return
        self._viewer.setPlainText(body)

        # carry the session-search term into the find bar
        if self._active_search and not self._find_bar.text():
            self._find_bar.blockSignals(True)
            self._find_bar.setText(self._active_search)
            self._find_bar.blockSignals(False)
        self._recompute_matches()

    # ── In-conversation find ────────────────────────────────────────────────

    def _focus_find(self):
        self._find_bar.setFocus()
        self._find_bar.selectAll()

    def _reapply_options(self):
        self._recompute_matches()

    def _recompute_matches(self):
        term = self._find_bar.text()
        rx = _build_regex(term, self._cb_word.isChecked(), self._cb_case.isChecked())
        spans: list[tuple[int, int]] = []
        if rx:
            body = self._viewer.toPlainText()
            spans = [(m.start(), m.end()) for m in rx.finditer(body)]
        self._set_matches(spans)
        if spans:
            self._goto_match(0)

    def _set_matches(self, spans: list[tuple[int, int]]):
        self._match_spans = spans
        self._match_idx = -1
        self._highlight_all(spans)
        self._update_match_label()
        enabled = bool(spans)
        self._prev_btn.setEnabled(enabled)
        self._next_btn.setEnabled(enabled)

    def _update_match_label(self):
        n = len(self._match_spans)
        if n == 0:
            self._match_lbl.setText("no matches" if self._find_bar.text() else "")
        else:
            cur = self._match_idx + 1 if self._match_idx >= 0 else 0
            self._match_lbl.setText(f"{cur} / {n}")

    def _highlight_all(self, spans):
        sels = []
        if spans:
            fmt = QTextCharFormat()
            fmt.setBackground(QColor(theme.WARNING_COLOR))
            fmt.setForeground(QColor(theme.BG_DARK))
            doc = self._viewer.document()
            for a, b in spans:
                cur = QTextCursor(doc)
                cur.setPosition(a)
                cur.setPosition(b, QTextCursor.MoveMode.KeepAnchor)
                sel = QTextEdit.ExtraSelection()
                sel.cursor = cur
                sel.format = fmt
                sels.append(sel)
        self._viewer.setExtraSelections(sels)

    def _goto_match(self, idx: int):
        if not self._match_spans:
            return
        self._match_idx = idx % len(self._match_spans)
        a, b = self._match_spans[self._match_idx]
        cur = self._viewer.textCursor()
        cur.setPosition(a)
        cur.setPosition(b, QTextCursor.MoveMode.KeepAnchor)
        self._viewer.setTextCursor(cur)
        self._viewer.centerCursor()
        self._update_match_label()

    def _find_next(self):
        if self._match_spans:
            self._goto_match(self._match_idx + 1)

    def _find_prev(self):
        if self._match_spans:
            self._goto_match(self._match_idx - 1)

    # ── Session search ──────────────────────────────────────────────────────

    def _search_sessions(self):
        term = self._search_bar.text().strip()
        if not term:
            self._clear_search()
            return
        if not self.project_context.has_project():
            self._search_status.setText("No project selected")
            return

        self._active_search = term
        rx = _build_regex(term, self._cb_word.isChecked(), self._cb_case.isChecked())
        self._search_status.setText("Searching…")
        QApplication.processEvents()

        self._tree.clear()
        self._viewer.clear()
        self._set_matches([])

        project_path = self.project_context.get_project()
        fs, projects_dir = self._get_fs_and_projects_dir()
        sessions = get_project_sessions(project_path, projects_dir, fs)
        if not sessions:
            self._search_status.setText("No sessions found")
            return

        matches = []
        for i, s in enumerate(sessions):
            self._search_status.setText(f"Searching… {i + 1}/{len(sessions)}")
            QApplication.processEvents()
            try:
                text = session_cache.get_text(s["path"], fs)
            except Exception:
                continue
            body = self._render_body(s["path"], fs, text)
            hits = len(rx.findall(body))
            if not hits:
                continue
            m = rx.search(body)
            snippet = _get_snippet(body[max(0, m.start() - 200):m.start() + 200], term) if m else ""
            matches.append({**s, "snippet": snippet, "hits": hits})

        if not matches:
            self._search_status.setText(f"No session matches '{term}'")
            self._tree.addTopLevelItem(QTreeWidgetItem([f"No sessions contain '{term}'"]))
            return

        self._search_status.setText(
            f"{len(matches)} of {len(sessions)} session(s) match "
            f"({sum(x['hits'] for x in matches)} hits)"
        )
        for s in matches:
            sess_item = self._session_item(s)
            sess_item.setText(0, sess_item.text(0) + f"   ({s['hits']} hits)")
            QTreeWidgetItem(sess_item, [f"  ↳ {s['snippet']}"]).setForeground(0, QColor(theme.FG_DIM))
            self._tree.addTopLevelItem(sess_item)

        self._tree.expandAll()
        self._tree.setCurrentItem(self._tree.topLevelItem(0))
        self._load_conversation(self._tree.topLevelItem(0))

    def _clear_search(self):
        self._active_search = ""
        self._search_bar.clear()
        self._search_status.setText("")
        self._find_bar.clear()
        self._viewer.clear()
        self._set_matches([])
        self._refresh()
