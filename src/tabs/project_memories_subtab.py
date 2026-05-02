"""
Project Memories SubTab — per-project memory .md files.

Memory files live at:
  ~/.claude/projects/<encoded-project-path>/memory/*.md
"""

from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSplitter, QTextEdit, QListWidget, QListWidgetItem,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from utils import theme
from utils.project_scanner import find_project_encoded_dir
from utils.ui_state_manager import UIStateManager


class ProjectMemoriesSubTab(QWidget):
    """Memory .md viewer filtered to the current project."""

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

        bar = QHBoxLayout()
        self._project_label = QLabel("No project selected")
        self._project_label.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh)
        bar.addWidget(self._project_label)
        bar.addStretch()
        bar.addWidget(refresh_btn)
        layout.addLayout(bar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(5)

        self._list = QListWidget()
        self._list.currentItemChanged.connect(self._load_file)

        self._viewer = QTextEdit()
        self._viewer.setReadOnly(True)
        self._viewer.setFont(QFont(theme.FONT_MONOSPACE, theme.FONT_SIZE_SMALL))
        self._viewer.setPlaceholderText("Click a memory file to view its contents.")

        splitter.addWidget(self._list)
        splitter.addWidget(self._viewer)
        splitter.setSizes([300, 700])

        mgr = UIStateManager.instance()
        mgr.restore_splitter_state("proj_config.memories_splitter", splitter)
        mgr.connect_splitter("proj_config.memories_splitter", splitter)

        layout.addWidget(splitter, 1)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_fs_and_projects_dir(self):
        """Return (fs, projects_dir). None/None for local."""
        if self.config_manager is None:
            return None, None
        fs = self.config_manager.fs
        projects_dir = self.config_manager.claude_dir / "projects"
        return fs, projects_dir

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_project_changed(self, _):
        self._refresh()

    def _refresh(self):
        self._list.clear()
        self._viewer.clear()

        if not self.project_context.has_project():
            self._project_label.setText("No project selected")
            self._list.addItem("Select a project to see its memory files.")
            return

        project_path = self.project_context.get_project()
        self._project_label.setText(str(project_path))

        fs, projects_dir = self._get_fs_and_projects_dir()
        encoded_dir = find_project_encoded_dir(project_path, projects_dir, fs)
        if not encoded_dir:
            self._list.addItem("No Claude project directory found for this path.")
            return

        memory_dir = encoded_dir / "memory"

        if fs is not None:
            # ── Remote ────────────────────────────────────────────────────────
            if not fs.exists(memory_dir):
                self._list.addItem("No memory/ directory found for this project.")
                return
            try:
                md_files_all = fs.glob(memory_dir, "*.md")
            except Exception:
                md_files_all = []
            if not md_files_all:
                self._list.addItem("No memory files found.")
                return
            try:
                md_files = sorted(md_files_all, key=lambda f: fs.stat(f).st_mtime, reverse=True)
            except Exception:
                md_files = md_files_all
            for f in md_files:
                fname = f.name if hasattr(f, "name") else str(f).rsplit("/", 1)[-1]
                item = QListWidgetItem(fname)
                item.setData(Qt.ItemDataRole.UserRole, str(f))
                self._list.addItem(item)
        else:
            # ── Local ──────────────────────────────────────────────────────────
            if not memory_dir.exists():
                self._list.addItem("No memory/ directory found for this project.")
                return
            md_files = sorted(memory_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
            if not md_files:
                self._list.addItem("No memory files found.")
                return
            for f in md_files:
                item = QListWidgetItem(f.name)
                item.setData(Qt.ItemDataRole.UserRole, str(f))
                self._list.addItem(item)

        if self._list.count():
            self._list.setCurrentRow(0)

    def _load_file(self, current: QListWidgetItem | None, _prev=None):
        if not current:
            return
        path = current.data(Qt.ItemDataRole.UserRole)
        if not path:
            return

        fs, _ = self._get_fs_and_projects_dir()
        if fs is not None:
            if not fs.exists(path):
                self._viewer.setPlainText("File not found.")
                return
            try:
                self._viewer.setPlainText(fs.read_text(path))
            except Exception as e:
                self._viewer.setPlainText(f"Error reading file: {e}")
        else:
            fp = Path(path)
            if not fp.exists():
                self._viewer.setPlainText("File not found.")
                return
            try:
                self._viewer.setPlainText(fp.read_text(encoding="utf-8", errors="replace"))
            except Exception as e:
                self._viewer.setPlainText(f"Error reading file: {e}")
