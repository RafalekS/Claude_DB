"""
Project File History SubTab — pre-edit snapshots for the current project.

How it works:
  ~/.claude/projects/<encoded>/<uuid>.jsonl  → session conversation
  ~/.claude/file-history/<uuid>/             → snapshot files for that session

Inside each JSONL, 'file-history-snapshot' entries have:
  snapshot.trackedFileBackups:
    "<actual/file/path>": {"backupFileName": "<hash>@v<n>", "version": n, "backupTime": "..."}

The backupFileName matches a file inside ~/.claude/file-history/<uuid>/.
That file contains the raw pre-edit content of the source file.
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSplitter, QTextEdit, QTreeWidget, QTreeWidgetItem, QHeaderView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from utils import theme
from utils.project_scanner import get_project_sessions, CLAUDE_PROJECTS_DIR
from utils.ui_state_manager import UIStateManager


def _parse_file_history(session_uuid: str, jsonl_path: Path, fh_base: Path) -> list[dict]:
    """
    Parse a session JSONL and return snapshot records for files that exist in file-history.

    Returns list of:
        {"file_path": str, "backup_name": str, "version": int, "backup_time": str,
         "backup_file": Path, "session_uuid": str}
    """
    fh_dir = fh_base / session_uuid
    if not fh_dir.exists():
        return []

    # Build set of available backup filenames for quick lookup
    available = {f.name: f for f in fh_dir.iterdir() if f.is_file()}
    if not available:
        return []

    records = []
    seen_backups: set[str] = set()

    try:
        with open(jsonl_path, encoding="utf-8", errors="replace") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    entry = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") != "file-history-snapshot":
                    continue
                backups = entry.get("snapshot", {}).get("trackedFileBackups", {})
                for file_path, info in backups.items():
                    backup_name = info.get("backupFileName", "")
                    if not backup_name or backup_name in seen_backups:
                        continue
                    if backup_name not in available:
                        continue
                    seen_backups.add(backup_name)
                    try:
                        bt = datetime.fromisoformat(
                            info.get("backupTime", "").replace("Z", "+00:00")
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        bt = info.get("backupTime", "")
                    records.append({
                        "file_path": file_path,
                        "backup_name": backup_name,
                        "version": info.get("version", 0),
                        "backup_time": bt,
                        "backup_file": available[backup_name],
                        "session_uuid": session_uuid,
                    })
    except Exception:
        pass

    return records


class ProjectFileHistorySubTab(QWidget):
    """File-history snapshot viewer filtered to the current project."""

    def __init__(self, project_context):
        super().__init__()
        self.project_context = project_context
        self._fh_base = Path.home() / ".claude" / "file-history"
        self._init_ui()
        self.project_context.project_changed.connect(self._on_project_changed)
        if self.project_context.has_project():
            self._refresh()

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        # Toolbar
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

        # Splitter: file tree | content viewer
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(5)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["File / Snapshot", "Time"])
        self._tree.setColumnCount(2)
        self._tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._tree.itemClicked.connect(self._load_snapshot)

        self._viewer = QTextEdit()
        self._viewer.setReadOnly(True)
        self._viewer.setFont(QFont(theme.FONT_MONOSPACE, theme.FONT_SIZE_SMALL))
        self._viewer.setPlaceholderText("Click a snapshot to view the pre-edit file content.")

        splitter.addWidget(self._tree)
        splitter.addWidget(self._viewer)
        splitter.setSizes([400, 600])

        mgr = UIStateManager.instance()
        mgr.restore_splitter_state("proj_config.file_history_splitter", splitter)
        mgr.connect_splitter("proj_config.file_history_splitter", splitter)

        layout.addWidget(splitter, 1)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_project_changed(self, _):
        self._refresh()

    def _refresh(self):
        self._tree.clear()
        self._viewer.clear()

        if not self.project_context.has_project():
            self._project_label.setText("No project selected")
            QTreeWidgetItem(self._tree, ["Select a project to see its file history.", ""])
            return

        project_path = self.project_context.get_project()
        self._project_label.setText(str(project_path))

        sessions = get_project_sessions(project_path)
        if not sessions:
            QTreeWidgetItem(self._tree, ["No sessions found for this project.", ""])
            return

        # Collect all snapshot records across all sessions
        by_file: dict[str, list[dict]] = defaultdict(list)
        for s in sessions:
            for rec in _parse_file_history(s["uuid"], s["path"], self._fh_base):
                by_file[rec["file_path"]].append(rec)

        if not by_file:
            QTreeWidgetItem(self._tree, ["No file history snapshots found.", ""])
            return

        # Sort files by most recent snapshot time (desc)
        def _latest(recs):
            return max(r["backup_time"] for r in recs)

        for file_path in sorted(by_file, key=lambda fp: _latest(by_file[fp]), reverse=True):
            recs = sorted(by_file[file_path], key=lambda r: (r["backup_time"], r["version"]))
            file_item = QTreeWidgetItem([file_path, f"{len(recs)} snapshot{'s' if len(recs) != 1 else ''}"])
            file_item.setForeground(0, QColor(theme.ACCENT_PRIMARY))
            file_item.setFont(0, QFont(self._tree.font().family(), -1, QFont.Weight.Bold))
            self._tree.addTopLevelItem(file_item)

            for rec in reversed(recs):  # newest first under each file
                label = f"v{rec['version']}  ({rec['backup_name']})"
                child = QTreeWidgetItem([label, rec["backup_time"]])
                child.setData(0, Qt.ItemDataRole.UserRole, str(rec["backup_file"]))
                child.setForeground(0, QColor(theme.FG_SECONDARY))
                child.setToolTip(0, f"Session: {rec['session_uuid']}")
                file_item.addChild(child)

            file_item.setExpanded(True)

    def _load_snapshot(self, item: QTreeWidgetItem, _col: int = 0):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path:
            return  # clicked a file-level header row
        fp = Path(path)
        if not fp.exists():
            self._viewer.setPlainText("Snapshot file not found.")
            return
        try:
            content = fp.read_text(encoding="utf-8", errors="replace")
            self._viewer.setPlainText(
                f"Backup: {fp.name}\nFull path: {fp}\n{'─'*60}\n\n{content}"
            )
        except Exception as e:
            self._viewer.setPlainText(f"Error reading snapshot: {e}")
