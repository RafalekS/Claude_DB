"""
Files Tab — Claude Code memory and conversation history.

Subtabs:
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
    QListWidget, QListWidgetItem, QHeaderView, QLineEdit, QApplication,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QTextCursor

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


def _parse_conversation(path, fs=None) -> list[dict]:
    """Parse a JSONL file into a list of {role, text, time} dicts.

    fs — when provided (remote mode), content is read via fs.read_text().
         When None, the file is opened locally with open().
    """
    messages = []
    try:
        if fs is not None:
            lines = fs.read_text(path).splitlines()
        else:
            with open(path, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        for raw in lines:
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
    """Decode Claude Code's folder-name encoding back to a readable path.

    Uses project_scanner's robust decoder (which probes the filesystem and the
    session JSONL cwd) and falls back to the naive '-' → '/' swap.
    """
    try:
        from utils.project_scanner import decode_project_directory_name
        decoded = decode_project_directory_name(folder_name)
        if decoded is not None:
            path = str(decoded)
        else:
            path = "/" + folder_name.lstrip("-").replace("-", "/")
    except Exception:
        path = "/" + folder_name.lstrip("-").replace("-", "/")
    home = os.path.expanduser("~")
    if path.startswith(home):
        path = "~" + path[len(home):]
    return path


# ─── Search helpers ───────────────────────────────────────────────────────────

def _get_snippet(text: str, term: str, context: int = 80) -> str:
    """Extract a short text snippet centred on the first occurrence of term."""
    lo = text.lower().find(term.lower())
    if lo == -1:
        return (text[:context] + "…").replace("\n", " ")
    start = max(0, lo - context // 2)
    end = min(len(text), lo + len(term) + context // 2)
    snippet = text[start:end].replace("\n", " ")
    return ("…" if start > 0 else "") + snippet + ("…" if end < len(text) else "")


def _highlight_in_viewer(viewer: QTextEdit, term: str) -> None:
    """Highlight all occurrences of term in a QTextEdit via extra selections."""
    if not term:
        viewer.setExtraSelections([])
        return
    fmt = QTextCharFormat()
    fmt.setBackground(QColor("#E8B000"))
    fmt.setForeground(QColor("#000000"))
    doc = viewer.document()
    cursor = QTextCursor(doc)
    selections = []
    while True:
        cursor = doc.find(term, cursor)
        if cursor.isNull():
            break
        sel = QTextEdit.ExtraSelection()
        sel.cursor = cursor
        sel.format = fmt
        selections.append(sel)
    viewer.setExtraSelections(selections)
    if selections:
        viewer.setTextCursor(selections[0].cursor)
        viewer.ensureCursorVisible()


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

        self.tab_widget.addTab(self._build_conversations_tab(), "Conversations")
        self.tab_widget.addTab(self._build_project_memories_tab(), "Project Memories")
        self.tab_widget.addTab(self._build_file_history_tab(), "File History")
        self.tab_widget.addTab(self._build_shell_snapshots_tab(), "Shell Snapshots")

        self.refresh_all()

    # ── Conversations ─────────────────────────────────────────────────────────

    def _build_conversations_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(4)

        self._conv_active_search = ""

        # Search bar
        search_row = QHBoxLayout()
        search_row.setSpacing(4)
        self._conv_search_bar = QLineEdit()
        self._conv_search_bar.setPlaceholderText("Search all conversations…")
        self._conv_search_bar.returnPressed.connect(self._search_conversations)
        search_btn = QPushButton("🔍 Search")
        search_btn.clicked.connect(self._search_conversations)
        clear_btn = QPushButton("✕ Clear")
        clear_btn.clicked.connect(self._clear_conv_search)
        self._conv_search_status = QLabel("")
        self._conv_search_status.setStyleSheet(
            f"color: {theme.FG_DIM}; font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        search_row.addWidget(self._conv_search_bar, 1)
        search_row.addWidget(search_btn)
        search_row.addWidget(clear_btn)
        search_row.addWidget(self._conv_search_status)
        layout.addLayout(search_row)

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

        layout.addWidget(splitter, 1)
        return widget

    def _refresh_conversations(self):
        if self._conv_active_search:
            return  # keep search results; user clears with ✕ Clear
        self.conv_tree.clear()
        fs = self.config_manager.fs
        projects_dir = self.config_manager.claude_dir / "projects"
        if not fs.exists(projects_dir):
            return

        by_project: dict[str, list[dict]] = {}
        try:
            for pdir in fs.iterdir(projects_dir):
                if not fs.is_dir(pdir):
                    continue
                sessions = []
                for jf in fs.glob(pdir, "*.jsonl"):
                    sessions.append({
                        "path": jf,
                        "uuid": jf.stem,
                        "mtime": fs.stat(jf).st_mtime,
                    })
                if sessions:
                    by_project[pdir.name] = sorted(sessions, key=lambda x: x["mtime"], reverse=True)
        except Exception as e:
            QTreeWidgetItem(self.conv_tree, [f"Error: {e}"])
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
        fs = self.config_manager.fs
        if not fs.exists(path):
            self.conv_viewer.setPlainText("File not found")
            return

        messages = _parse_conversation(path, fs)
        if not messages:
            self.conv_viewer.setPlainText(
                f"No readable messages found in:\n{path}\n\n"
                "(All entries may be progress/tool/snapshot records.)"
            )
            return

        stem = Path(str(path)).stem
        lines = [f"Session: {stem}\nMessages: {len(messages)}\n{'─'*60}\n"]
        for m in messages:
            role_label = "You" if m["role"] == "user" else "Claude"
            time_str = f"  [{m['time']}]" if m["time"] else ""
            lines.append(f"\n{'─'*40}\n{role_label}{time_str}\n{'─'*40}\n{m['text']}\n")

        self.conv_viewer.setPlainText("".join(lines))
        if self._conv_active_search:
            _highlight_in_viewer(self.conv_viewer, self._conv_active_search)

    # ── Conversation search ───────────────────────────────────────────────────

    def _search_conversations(self):
        term = self._conv_search_bar.text().strip()
        if not term:
            self._clear_conv_search()
            return

        self._conv_active_search = term
        self._conv_search_status.setText("Searching…")
        QApplication.processEvents()

        self.conv_tree.clear()
        self.conv_viewer.clear()
        self.conv_viewer.setExtraSelections([])

        fs = self.config_manager.fs
        projects_dir = self.config_manager.claude_dir / "projects"
        if not fs.exists(projects_dir):
            self._conv_search_status.setText("No projects directory found")
            return

        term_lower = term.lower()
        by_project: dict[str, list[dict]] = {}

        try:
            for pdir in fs.iterdir(projects_dir):
                if not fs.is_dir(pdir):
                    continue
                readable = _decode_project_path(pdir.name)
                project_matches = []
                for jf in fs.glob(pdir, "*.jsonl"):
                    messages = _parse_conversation(jf, fs)
                    snippet = ""
                    for m in messages:
                        if term_lower in m["text"].lower():
                            snippet = _get_snippet(m["text"], term)
                            break
                    if snippet:
                        project_matches.append({
                            "path": jf,
                            "uuid": jf.stem,
                            "mtime": fs.stat(jf).st_mtime,
                            "snippet": snippet,
                        })
                if project_matches:
                    by_project[readable] = sorted(
                        project_matches, key=lambda x: x["mtime"], reverse=True
                    )
        except Exception as e:
            self._conv_search_status.setText(f"Error: {e}")
            return

        total = sum(len(v) for v in by_project.values())
        if total == 0:
            self._conv_search_status.setText("No matches found")
            self.conv_tree.addTopLevelItem(
                QTreeWidgetItem([f"No sessions contain '{term}'"])
            )
            return

        self._conv_search_status.setText(
            f"{total} session(s) in {len(by_project)} project(s)"
        )

        sorted_projects = sorted(
            by_project.items(), key=lambda kv: kv[1][0]["mtime"], reverse=True
        )
        for proj_name, sessions in sorted_projects:
            n = len(sessions)
            label = f"📁 {proj_name}  ({n} match{'es' if n != 1 else ''})"
            proj_item = QTreeWidgetItem(self.conv_tree, [label])
            proj_item.setForeground(0, QColor(theme.ACCENT_PRIMARY))
            proj_item.setFont(0, QFont(self.conv_tree.font().family(), -1, QFont.Weight.Bold))

            for s in sessions:
                mod = datetime.fromtimestamp(s["mtime"]).strftime("%Y-%m-%d %H:%M")
                sess_item = QTreeWidgetItem(proj_item, [f"{mod}  {s['uuid'][:16]}…"])
                sess_item.setData(0, Qt.ItemDataRole.UserRole, str(s["path"]))
                sess_item.setForeground(0, QColor(theme.FG_SECONDARY))

                snip_item = QTreeWidgetItem(sess_item, [f"  ↳ {s['snippet']}"])
                snip_item.setForeground(0, QColor(theme.FG_DIM))

        self.conv_tree.expandAll()

    def _clear_conv_search(self):
        self._conv_active_search = ""
        self._conv_search_bar.clear()
        self._conv_search_status.setText("")
        self.conv_viewer.clear()
        self.conv_viewer.setExtraSelections([])
        self._refresh_conversations()

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
        fs = self.config_manager.fs
        projects_dir = self.config_manager.claude_dir / "projects"
        if not fs.exists(projects_dir):
            return

        found = False
        try:
            for pdir in sorted(fs.iterdir(projects_dir), key=lambda p: str(p)):
                if not fs.is_dir(pdir):
                    continue
                mem_dir = pdir / "memory"
                if not fs.exists(mem_dir):
                    continue
                md_files = sorted(fs.glob(mem_dir, "*.md"), key=lambda p: str(p))
                if not md_files:
                    continue
                found = True
                readable = _decode_project_path(pdir.name)
                proj_item = QTreeWidgetItem(self.mem_tree, [readable])
                proj_item.setForeground(0, QColor(theme.ACCENT_PRIMARY))
                proj_item.setFont(0, QFont(self.mem_tree.font().family(), -1, QFont.Weight.Bold))
                for md in md_files:
                    size = fs.stat(md).st_size
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
        fs = self.config_manager.fs
        if not fs.exists(path):
            self.mem_viewer.setPlainText("File not found")
            return
        try:
            self.mem_viewer.setPlainText(fs.read_text(path))
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
        fs = self.config_manager.fs
        fh_dir = self.config_manager.claude_dir / "file-history"
        if not fs.exists(fh_dir):
            self.file_history_list.addItem("No file history directory")
            return

        all_files = []
        try:
            for conv_dir in fs.iterdir(fh_dir):
                if fs.is_dir(conv_dir):
                    for f in fs.iterdir(conv_dir):
                        if fs.is_file(f):
                            all_files.append({
                                "path": f,
                                "conv_id": conv_dir.name,
                                "name": f.name,
                                "mtime": fs.stat(f).st_mtime,
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
        fs = self.config_manager.fs
        if not fs.exists(path):
            self.file_history_viewer.setPlainText("File not found")
            return
        try:
            content = fs.read_text(path)
            name = Path(str(path)).name
            self.file_history_viewer.setPlainText(
                f"File: {name}\nPath: {path}\n{'─'*60}\n\n{content}"
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
        fs = self.config_manager.fs
        snap_dir = self.config_manager.claude_dir / "shell-snapshots"
        if not fs.exists(snap_dir):
            self.shell_list.addItem("No shell snapshots directory")
            return
        try:
            all_items = fs.glob(snap_dir, "*")
            files = sorted(
                [f for f in all_items if fs.is_file(f)],
                key=lambda x: fs.stat(x).st_mtime,
                reverse=True,
            )
        except Exception as e:
            self.shell_list.addItem(f"Error: {e}")
            return
        if not files:
            self.shell_list.addItem("No shell snapshots found")
            return
        for f in files:
            mod = datetime.fromtimestamp(fs.stat(f).st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            item = QListWidgetItem(f"{f.name}  ({mod})")
            item.setData(Qt.ItemDataRole.UserRole, str(f))
            self.shell_list.addItem(item)

    def _load_shell_content(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        if not path:
            return
        fs = self.config_manager.fs
        if not fs.exists(path):
            self.shell_viewer.setPlainText("File not found")
            return
        try:
            self.shell_viewer.setPlainText(fs.read_text(path))
        except Exception as e:
            self.shell_viewer.setPlainText(f"Error: {e}")

    # ── Refresh all ───────────────────────────────────────────────────────────

    def refresh_all(self):
        self.config_manager.clear_fs_cache()
        self._refresh_conversations()
        self._refresh_project_memories()
        self._refresh_file_history()
        self._refresh_shell_snapshots()
