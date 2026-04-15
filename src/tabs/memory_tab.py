"""
Memory Tab — Claude Code memory and conversation history.

Subtabs:
  Overview          — docs on how Claude Code memory works
  Conversations     — project sessions parsed from JSONL; QTreeWidget grouped by project
  Project Memories  — .md files from ~/.claude/projects/<encoded>/memory/
  File History      — per-file pre-edit snapshots
  Shell Snapshots   — saved shell environment state
"""

import json
import os
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser, QPushButton,
    QTabWidget, QSplitter, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QListWidget, QListWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from utils import theme
from utils.ui_state_manager import UIStateManager


# ─── JSONL helpers ────────────────────────────────────────────────────────────

def _extract_text(content) -> str:
    """Return human-readable text from a message content value."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    name = block.get("name", "?")
                    inp = block.get("input", {})
                    cmd = inp.get("command", inp.get("description", ""))
                    parts.append(f"[tool: {name}{' — ' + cmd[:80] if cmd else ''}]")
                elif block.get("type") == "tool_result":
                    parts.append("[tool result]")
            else:
                parts.append(str(block))
        return "\n".join(p for p in parts if p)
    return str(content)


def _is_noise(entry: dict) -> bool:
    """Return True for entries that should be hidden in the conversation view."""
    if entry.get("type") == "progress":
        return True
    msg = entry.get("message") or {}
    content = msg.get("content", "")
    if isinstance(content, str) and content.startswith("file-history-snapshot:"):
        return True
    if isinstance(content, str) and content.startswith("<function_calls>"):
        return True
    return False


def _parse_conversation(path: Path) -> list[dict]:
    """Parse a JSONL file into a list of {role, text, time} dicts."""
    messages = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    entry = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if _is_noise(entry):
                    continue
                msg = entry.get("message") or {}
                role = msg.get("role") or entry.get("type", "?")
                if role not in ("user", "assistant"):
                    continue
                content = msg.get("content", "")
                text = _extract_text(content).strip()
                if not text:
                    continue
                ts = entry.get("timestamp", "")
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    time_str = dt.strftime("%H:%M:%S")
                except Exception:
                    time_str = ""
                messages.append({"role": role, "text": text, "time": time_str})
    except Exception:
        pass
    return messages


# ─── Path helpers ─────────────────────────────────────────────────────────────

def _decode_project_path(folder_name: str) -> str:
    """Decode Claude Code's folder-name encoding back to a readable path."""
    raw = folder_name.lstrip("-")
    path = "/" + raw.replace("-", "/")
    home = os.path.expanduser("~")
    if path.startswith(home):
        path = "~" + path[len(home):]
    return path


# ─── Main Tab ─────────────────────────────────────────────────────────────────

class MemoryTab(QWidget):
    """Tab for Claude Code memory and conversation history."""

    def __init__(self, config_manager, backup_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        # Header
        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(5)
        hdr = QLabel("Memory & Checkpointing")
        hdr.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};"
        )
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setToolTip("Reload all data")
        refresh_btn.clicked.connect(self.refresh_all)
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        hdr_row.addWidget(refresh_btn)
        layout.addLayout(hdr_row)

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget, 1)

        self.tab_widget.addTab(self._build_overview(), "Overview")
        self.tab_widget.addTab(self._build_conversations_tab(), "Conversations")
        self.tab_widget.addTab(self._build_project_memories_tab(), "Project Memories")
        self.tab_widget.addTab(self._build_file_history_tab(), "File History")
        self.tab_widget.addTab(self._build_shell_snapshots_tab(), "Shell Snapshots")

        self.refresh_all()

    # ── Overview ──────────────────────────────────────────────────────────────

    def _build_overview(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)
        info = QTextBrowser()
        info.setHtml(f"""
            <h3 style="color:{theme.ACCENT_PRIMARY};">Claude Code Memory System</h3>

            <h4 style="color:{theme.ACCENT_PRIMARY}; margin-top:12px;">Memory Hierarchy (Highest → Lowest)</h4>
            <ol style="line-height:1.8;">
                <li><b>Enterprise Policy:</b> <code>/etc/claude/CLAUDE.md</code></li>
                <li><b>User Memory:</b> <code>~/.claude/CLAUDE.md</code> — all projects</li>
                <li><b>Project Memory:</b> <code>./CLAUDE.md</code> — in git, shared with team</li>
                <li><b>Local Project:</b> <code>./CLAUDE.local.md</code> — personal, gitignored</li>
            </ol>
            <p><b>Quick add:</b> prefix prompt with <code>#</code> to save to memory. &nbsp;|&nbsp;
               <b>Edit:</b> <code>/memory</code> opens CLAUDE.md in editor.</p>

            <h4 style="color:{theme.ACCENT_PRIMARY}; margin-top:12px;">Auto Memory</h4>
            <p>When <code>autoMemoryEnabled: true</code> in settings, Claude Code automatically
            extracts key information to <code>autoMemoryDirectory</code>
            (default: <code>~/.claude/memory/</code>).</p>

            <h4 style="color:{theme.ACCENT_PRIMARY}; margin-top:12px;">Context Compaction</h4>
            <ul style="line-height:1.8;">
                <li><code>/compact</code> — compact history to free context window</li>
                <li><code>/compact &lt;instructions&gt;</code> — compact with focus</li>
                <li>Hook: <code>PostCompact</code> fires after compaction</li>
            </ul>

            <h4 style="color:{theme.ACCENT_PRIMARY}; margin-top:12px;">Conversation Storage</h4>
            <ul style="line-height:1.8;">
                <li><b>Global history:</b> <code>~/.claude/history.jsonl</code></li>
                <li><b>Per-project:</b> <code>~/.claude/projects/&lt;encoded-path&gt;/&lt;uuid&gt;.jsonl</code></li>
                <li><b>Resume:</b> <code>claude -c</code> (last) or <code>claude -r &lt;uuid&gt;</code></li>
            </ul>

            <h4 style="color:{theme.ACCENT_PRIMARY}; margin-top:12px;">Project Memories</h4>
            <p>Per-project memory files at <code>~/.claude/projects/&lt;encoded-path&gt;/memory/</code> —
            shown in the <b>Project Memories</b> tab.</p>
        """)
        layout.addWidget(info)
        return widget

    # ── Conversations ─────────────────────────────────────────────────────────

    def _build_conversations_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(5)

        # Left: tree of projects / sessions
        self.conv_tree = QTreeWidget()
        self.conv_tree.setHeaderLabel("Projects & Sessions")
        self.conv_tree.setColumnCount(1)
        self.conv_tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.conv_tree.itemClicked.connect(self._load_conversation)

        # Right: conversation viewer
        self.conv_viewer = QTextEdit()
        self.conv_viewer.setReadOnly(True)
        self.conv_viewer.setFont(QFont(theme.FONT_MONOSPACE, theme.FONT_SIZE_SMALL))

        splitter.addWidget(self.conv_tree)
        splitter.addWidget(self.conv_viewer)
        splitter.setSizes([350, 650])

        mgr = UIStateManager.instance()
        mgr.restore_splitter_state("memory.conv_splitter", splitter)
        mgr.connect_splitter("memory.conv_splitter", splitter)

        layout.addWidget(splitter)
        return widget

    def _refresh_conversations(self):
        self.conv_tree.clear()
        projects_dir = self.config_manager.claude_dir / "projects"
        if not projects_dir.exists():
            return

        by_project: dict[str, list[dict]] = {}
        try:
            for pdir in projects_dir.iterdir():
                if not pdir.is_dir():
                    continue
                sessions = []
                for jf in pdir.glob("*.jsonl"):
                    sessions.append({
                        "path": jf,
                        "uuid": jf.stem,
                        "mtime": jf.stat().st_mtime,
                    })
                if sessions:
                    by_project[pdir.name] = sorted(sessions, key=lambda x: x["mtime"], reverse=True)
        except Exception as e:
            root = QTreeWidgetItem(self.conv_tree, [f"Error: {e}"])
            return

        sorted_projects = sorted(
            by_project.items(), key=lambda kv: kv[1][0]["mtime"], reverse=True
        )

        for folder_name, sessions in sorted_projects:
            readable = _decode_project_path(folder_name)
            latest = datetime.fromtimestamp(sessions[0]["mtime"]).strftime("%Y-%m-%d")
            proj_item = QTreeWidgetItem(
                self.conv_tree,
                [f"{readable}  ({len(sessions)} sessions, latest {latest})"]
            )
            proj_item.setForeground(0, QColor(theme.ACCENT_PRIMARY))
            proj_item.setFont(0, QFont(self.conv_tree.font().family(), -1, QFont.Weight.Bold))

            for s in sessions:
                mod_time = datetime.fromtimestamp(s["mtime"]).strftime("%Y-%m-%d %H:%M")
                sess_item = QTreeWidgetItem(
                    proj_item,
                    [f"{mod_time}  {s['uuid'][:16]}…"]
                )
                sess_item.setData(0, Qt.ItemDataRole.UserRole, str(s["path"]))
                sess_item.setForeground(0, QColor(theme.FG_SECONDARY))

    def _load_conversation(self, item: QTreeWidgetItem, _col: int = 0):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path:
            return
        file_path = Path(path)
        if not file_path.exists():
            self.conv_viewer.setPlainText("File not found")
            return

        messages = _parse_conversation(file_path)
        if not messages:
            self.conv_viewer.setPlainText(
                f"No readable messages found in:\n{file_path}\n\n"
                "(All entries may be progress/tool/snapshot records.)"
            )
            return

        lines = [f"Session: {file_path.stem}\nMessages: {len(messages)}\n{'─'*60}\n"]
        for m in messages:
            role_label = "You" if m["role"] == "user" else "Claude"
            time_str = f"  [{m['time']}]" if m["time"] else ""
            lines.append(f"\n{'─'*40}\n{role_label}{time_str}\n{'─'*40}\n{m['text']}\n")

        self.conv_viewer.setPlainText("".join(lines))

    # ── Project Memories ──────────────────────────────────────────────────────

    def _build_project_memories_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(5)

        # Left: tree of projects with .md memory files
        self.mem_tree = QTreeWidget()
        self.mem_tree.setHeaderLabel("Project Memory Files")
        self.mem_tree.setColumnCount(1)
        self.mem_tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.mem_tree.itemClicked.connect(self._load_memory_file)

        # Right: file content
        self.mem_viewer = QTextEdit()
        self.mem_viewer.setReadOnly(True)
        self.mem_viewer.setFont(QFont(theme.FONT_MONOSPACE, theme.FONT_SIZE_SMALL))

        splitter.addWidget(self.mem_tree)
        splitter.addWidget(self.mem_viewer)
        splitter.setSizes([350, 650])

        mgr = UIStateManager.instance()
        mgr.restore_splitter_state("memory.mem_splitter", splitter)
        mgr.connect_splitter("memory.mem_splitter", splitter)

        layout.addWidget(splitter)
        return widget

    def _refresh_project_memories(self):
        self.mem_tree.clear()
        projects_dir = self.config_manager.claude_dir / "projects"
        if not projects_dir.exists():
            return

        found = False
        try:
            for pdir in sorted(projects_dir.iterdir()):
                if not pdir.is_dir():
                    continue
                mem_dir = pdir / "memory"
                if not mem_dir.exists():
                    continue
                md_files = sorted(mem_dir.glob("*.md"))
                if not md_files:
                    continue
                found = True
                readable = _decode_project_path(pdir.name)
                proj_item = QTreeWidgetItem(self.mem_tree, [readable])
                proj_item.setForeground(0, QColor(theme.ACCENT_PRIMARY))
                proj_item.setFont(0, QFont(self.mem_tree.font().family(), -1, QFont.Weight.Bold))
                for md in md_files:
                    size = md.stat().st_size
                    file_item = QTreeWidgetItem(proj_item, [f"{md.name}  ({size} bytes)"])
                    file_item.setData(0, Qt.ItemDataRole.UserRole, str(md))
                    file_item.setForeground(0, QColor(theme.FG_SECONDARY))
        except Exception as e:
            QTreeWidgetItem(self.mem_tree, [f"Error: {e}"])
            return

        if not found:
            QTreeWidgetItem(self.mem_tree, ["No project memory files found"])

    def _load_memory_file(self, item: QTreeWidgetItem, _col: int = 0):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path:
            return
        fp = Path(path)
        if not fp.exists():
            self.mem_viewer.setPlainText("File not found")
            return
        try:
            self.mem_viewer.setPlainText(fp.read_text(encoding="utf-8", errors="replace"))
        except Exception as e:
            self.mem_viewer.setPlainText(f"Error: {e}")

    # ── File History ──────────────────────────────────────────────────────────

    def _build_file_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(5)

        self.file_history_list = QListWidget()
        self.file_history_list.itemClicked.connect(self._load_file_history_content)

        self.file_history_viewer = QTextEdit()
        self.file_history_viewer.setReadOnly(True)
        self.file_history_viewer.setFont(QFont(theme.FONT_MONOSPACE, theme.FONT_SIZE_SMALL))

        splitter.addWidget(self.file_history_list)
        splitter.addWidget(self.file_history_viewer)
        splitter.setSizes([350, 650])

        mgr = UIStateManager.instance()
        mgr.restore_splitter_state("memory.file_history_splitter", splitter)
        mgr.connect_splitter("memory.file_history_splitter", splitter)

        layout.addWidget(splitter)
        return widget

    def _refresh_file_history(self):
        self.file_history_list.clear()
        fh_dir = self.config_manager.claude_dir / "file-history"
        if not fh_dir.exists():
            self.file_history_list.addItem("No file history directory")
            return

        all_files = []
        try:
            for conv_dir in fh_dir.iterdir():
                if conv_dir.is_dir():
                    for f in conv_dir.iterdir():
                        if f.is_file():
                            all_files.append({
                                "path": f,
                                "conv_id": conv_dir.name,
                                "name": f.name,
                                "mtime": f.stat().st_mtime,
                            })
        except Exception as e:
            self.file_history_list.addItem(f"Error: {e}")
            return

        if not all_files:
            self.file_history_list.addItem("No file history found")
            return

        all_files.sort(key=lambda x: x["mtime"], reverse=True)
        for fi in all_files:
            mod = datetime.fromtimestamp(fi["mtime"]).strftime("%Y-%m-%d %H:%M")
            item = QListWidgetItem(f"[{fi['conv_id'][:8]}] {fi['name']}  ({mod})")
            item.setData(Qt.ItemDataRole.UserRole, str(fi["path"]))
            self.file_history_list.addItem(item)

    def _load_file_history_content(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        if not path:
            return
        fp = Path(path)
        if not fp.exists():
            self.file_history_viewer.setPlainText("File not found")
            return
        try:
            content = fp.read_text(encoding="utf-8", errors="replace")
            self.file_history_viewer.setPlainText(
                f"File: {fp.name}\nPath: {fp}\n{'─'*60}\n\n{content}"
            )
        except Exception as e:
            self.file_history_viewer.setPlainText(f"Error: {e}")

    # ── Shell Snapshots ───────────────────────────────────────────────────────

    def _build_shell_snapshots_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(5)

        self.shell_list = QListWidget()
        self.shell_list.itemClicked.connect(self._load_shell_content)

        self.shell_viewer = QTextEdit()
        self.shell_viewer.setReadOnly(True)
        self.shell_viewer.setFont(QFont(theme.FONT_MONOSPACE, theme.FONT_SIZE_SMALL))

        splitter.addWidget(self.shell_list)
        splitter.addWidget(self.shell_viewer)
        splitter.setSizes([350, 650])

        mgr = UIStateManager.instance()
        mgr.restore_splitter_state("memory.shell_splitter", splitter)
        mgr.connect_splitter("memory.shell_splitter", splitter)

        layout.addWidget(splitter)
        return widget

    def _refresh_shell_snapshots(self):
        self.shell_list.clear()
        snap_dir = self.config_manager.claude_dir / "shell-snapshots"
        if not snap_dir.exists():
            self.shell_list.addItem("No shell snapshots directory")
            return
        files = sorted(snap_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
        for f in files:
            if f.is_file():
                mod = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                item = QListWidgetItem(f"{f.name}  ({mod})")
                item.setData(Qt.ItemDataRole.UserRole, str(f))
                self.shell_list.addItem(item)
        if not files:
            self.shell_list.addItem("No shell snapshots found")

    def _load_shell_content(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        if not path:
            return
        fp = Path(path)
        if not fp.exists():
            self.shell_viewer.setPlainText("File not found")
            return
        try:
            self.shell_viewer.setPlainText(fp.read_text(encoding="utf-8", errors="replace"))
        except Exception as e:
            self.shell_viewer.setPlainText(f"Error: {e}")

    # ── Refresh all ───────────────────────────────────────────────────────────

    def refresh_all(self):
        self._refresh_conversations()
        self._refresh_project_memories()
        self._refresh_file_history()
        self._refresh_shell_snapshots()
