"""
Project Shell Snapshots SubTab — shell environment snapshots for the current project.

Snapshot filenames: snapshot-bash-<ms-timestamp>-<random>.sh
They are stored globally in ~/.claude/shell-snapshots/ with no per-project index.
We filter by time: a snapshot belongs to a project if its ms timestamp falls within
the [first_entry_time, last_entry_time] window of any of the project's sessions.
"""

import json
import re
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QSplitter, QTextEdit, QListWidget, QListWidgetItem,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from utils import theme
from utils.project_scanner import get_project_sessions
from utils.ui_state_manager import UIStateManager

_LOCAL_SNAPSHOT_DIR = Path.home() / ".claude" / "shell-snapshots"
_TS_RE = re.compile(r"snapshot-bash-(\d+)-")


def _session_time_windows(sessions: list[dict], fs=None) -> list[tuple[float, float]]:
    """Return (start_ts, end_ts) pairs in Unix seconds for each session."""
    windows = []
    for s in sessions:
        path = s["path"]
        first_ts: float | None = None
        last_ts: float | None = None
        try:
            if fs is not None:
                lines = fs.read_text(path).splitlines()
            else:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    lines = fh.readlines()
            for raw in lines:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    entry = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                ts_str = entry.get("timestamp", "")
                if not ts_str:
                    continue
                try:
                    ts = datetime.fromisoformat(
                        ts_str.replace("Z", "+00:00")
                    ).timestamp()
                    if first_ts is None:
                        first_ts = ts
                    last_ts = ts
                except Exception:
                    continue
        except Exception:
            pass

        if first_ts is not None and last_ts is not None:
            windows.append((first_ts - 300, last_ts + 300))
        elif s.get("mtime"):
            mtime = s["mtime"]
            windows.append((mtime - 3600, mtime + 300))

    return windows


def _snapshot_in_windows(snapshot_ms: int, windows: list[tuple[float, float]]) -> bool:
    ts = snapshot_ms / 1000.0
    return any(lo <= ts <= hi for lo, hi in windows)


class ProjectShellSnapshotsSubTab(QWidget):
    """Shell snapshot viewer filtered to the current project by timestamp."""

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
        self._list.currentItemChanged.connect(self._load_snapshot)

        self._viewer = QTextEdit()
        self._viewer.setReadOnly(True)
        self._viewer.setFont(QFont(theme.FONT_MONOSPACE, theme.FONT_SIZE_SMALL))
        self._viewer.setPlaceholderText("Click a snapshot to view its contents.")

        splitter.addWidget(self._list)
        splitter.addWidget(self._viewer)
        splitter.setSizes([320, 680])

        mgr = UIStateManager.instance()
        mgr.restore_splitter_state("proj_config.shell_snap_splitter", splitter)
        mgr.connect_splitter("proj_config.shell_snap_splitter", splitter)

        layout.addWidget(splitter, 1)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_fs_and_projects_dir(self):
        """Return (fs, projects_dir). None/None for local."""
        if self.config_manager is None:
            return None, None
        fs = self.config_manager.fs
        projects_dir = self.config_manager.claude_dir / "projects"
        return fs, projects_dir

    def _get_snapshot_dir(self):
        if self.config_manager is not None:
            return self.config_manager.claude_dir / "shell-snapshots"
        return _LOCAL_SNAPSHOT_DIR

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_project_changed(self, _):
        self._refresh()

    def _refresh(self):
        self._list.clear()
        self._viewer.clear()

        if not self.project_context.has_project():
            self._project_label.setText("No project selected")
            self._list.addItem("Select a project to see its shell snapshots.")
            return

        project_path = self.project_context.get_project()
        self._project_label.setText(str(project_path))

        fs, projects_dir = self._get_fs_and_projects_dir()
        snapshot_dir = self._get_snapshot_dir()

        # Check snapshot directory exists
        if fs is not None:
            if not fs.exists(snapshot_dir):
                self._list.addItem("No shell-snapshots directory found.")
                return
        else:
            if not snapshot_dir.exists():
                self._list.addItem("No shell-snapshots directory found (~/.claude/shell-snapshots/).")
                return

        sessions = get_project_sessions(project_path, projects_dir, fs)
        if not sessions:
            self._list.addItem("No sessions found for this project — cannot filter snapshots.")
            return

        windows = _session_time_windows(sessions, fs)
        if not windows:
            self._list.addItem("Could not determine session time windows.")
            return

        # List and filter snapshots
        if fs is not None:
            try:
                all_snaps = fs.glob(snapshot_dir, "snapshot-bash-*.sh")
            except Exception:
                all_snaps = []
            try:
                snapshots = sorted(all_snaps, key=lambda f: fs.stat(f).st_mtime, reverse=True)
            except Exception:
                snapshots = all_snaps

            def _fname(f):
                return f.name if hasattr(f, "name") else str(f).rsplit("/", 1)[-1]
        else:
            snapshots = sorted(
                snapshot_dir.glob("snapshot-bash-*.sh"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )

            def _fname(f):
                return f.name

        matched = []
        for f in snapshots:
            name = _fname(f)
            m = _TS_RE.search(name)
            if not m:
                continue
            snap_ms = int(m.group(1))
            if _snapshot_in_windows(snap_ms, windows):
                matched.append((f, snap_ms))

        if not matched:
            self._list.addItem("No shell snapshots found for this project's sessions.")
            return

        for f, snap_ms in matched:
            dt = datetime.fromtimestamp(snap_ms / 1000.0).strftime("%Y-%m-%d %H:%M:%S")
            item = QListWidgetItem(f"{dt}  {_fname(f)}")
            item.setData(Qt.ItemDataRole.UserRole, str(f))
            item.setForeground(QColor(theme.FG_SECONDARY))
            self._list.addItem(item)

        if self._list.count():
            self._list.setCurrentRow(0)

    def _load_snapshot(self, current: QListWidgetItem | None, _prev=None):
        if not current:
            return
        path = current.data(Qt.ItemDataRole.UserRole)
        if not path:
            return

        fs, _ = self._get_fs_and_projects_dir()
        if fs is not None:
            if not fs.exists(path):
                self._viewer.setPlainText("Snapshot file not found.")
                return
            try:
                self._viewer.setPlainText(fs.read_text(path))
            except Exception as e:
                self._viewer.setPlainText(f"Error reading snapshot: {e}")
        else:
            fp = Path(path)
            if not fp.exists():
                self._viewer.setPlainText("Snapshot file not found.")
                return
            try:
                self._viewer.setPlainText(fp.read_text(encoding="utf-8", errors="replace"))
            except Exception as e:
                self._viewer.setPlainText(f"Error reading snapshot: {e}")
