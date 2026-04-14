"""
Memory Tab - Claude Code memory and checkpointing
"""

import json
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextBrowser, QHBoxLayout, QPushButton,
    QMessageBox, QTabWidget, QListWidget, QListWidgetItem, QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from utils import theme
from utils.ui_state_manager import UIStateManager

class MemoryTab(QWidget):
    """Tab for memory and checkpointing info"""

    def __init__(self, config_manager, backup_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        header = QLabel("Memory & Checkpointing")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setToolTip("Refresh all memory and history data")
        refresh_btn.clicked.connect(self.refresh_all)

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Tab widget for different memory types
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            
            QTabBar::tab {{
                padding: 8px 16px;
                margin-right: 2px;
            }}
            
            
        """)

        # Create tabs
        self.tab_widget.addTab(self.create_overview_tab(), "Overview")
        self.tab_widget.addTab(self.create_history_tab(), "Conversation History")
        self.tab_widget.addTab(self.create_projects_tab(), "Projects")
        self.tab_widget.addTab(self.create_file_history_tab(), "File History")
        self.tab_widget.addTab(self.create_shell_snapshots_tab(), "Shell Snapshots")

        layout.addWidget(self.tab_widget, 1)

        # Load initial data
        self.refresh_all()

    def create_overview_tab(self):
        """Create overview tab with general info"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)

        info = QTextBrowser()
        info.setHtml(f"""
            <h3 style="color: {theme.ACCENT_PRIMARY};">Claude Code Memory System</h3>

            <h4 style="color: {theme.ACCENT_PRIMARY}; margin-top: 12px;">Memory Hierarchy (Highest → Lowest Precedence)</h4>
            <ol style="line-height: 1.8;">
                <li><b>Enterprise Policy:</b> <code>/etc/claude/CLAUDE.md</code> (Linux) or <code>C:\\ProgramData\\ClaudeCode\\CLAUDE.md</code> (Windows)</li>
                <li><b>User Memory:</b> <code>~/.claude/CLAUDE.md</code> — personal, applies to all projects</li>
                <li><b>Project Memory:</b> <code>./CLAUDE.md</code> — checked into git, shared with team</li>
                <li><b>Local Project Memory:</b> <code>./CLAUDE.local.md</code> — personal, this project only (gitignored)</li>
            </ol>
            <p style="color:{theme.FG_SECONDARY};">
                <b>Quick add:</b> Prefix a prompt with <code>#</code> to save it to memory instantly. &nbsp;|&nbsp;
                <b>Edit:</b> Use <code>/memory</code> in the REPL to open CLAUDE.md in your editor.
            </p>

            <h4 style="color: {theme.ACCENT_PRIMARY}; margin-top: 12px;">Auto Memory</h4>
            <p>When <code>autoMemoryEnabled: true</code> is set in settings, Claude Code automatically extracts
            and persists important information from conversations to <code>autoMemoryDirectory</code>
            (default: <code>~/.claude/memory/</code>).</p>
            <p>Configure in <b>User Config → Settings → Advanced Settings</b>.</p>

            <h4 style="color: {theme.ACCENT_PRIMARY}; margin-top: 12px;">Context Compaction</h4>
            <ul style="line-height: 1.8;">
                <li><code>/compact</code> — Compact conversation history to free context window</li>
                <li><code>/compact &lt;instructions&gt;</code> — Compact with custom focus instructions</li>
                <li>Hook: <code>PostCompact</code> fires after compaction completes</li>
            </ul>

            <h4 style="color: {theme.ACCENT_PRIMARY}; margin-top: 12px;">Conversation Storage</h4>
            <ul style="line-height: 1.8;">
                <li><b>Global history:</b> <code>~/.claude/history.jsonl</code> — all recent prompts</li>
                <li><b>Per-project conversations:</b> <code>~/.claude/projects/&lt;encoded-path&gt;/&lt;uuid&gt;.jsonl</code></li>
                <li><b>Resume:</b> <code>claude -c</code> (continue last) or <code>claude -r &lt;uuid&gt;</code> (specific session)</li>
            </ul>

            <h4 style="color: {theme.ACCENT_PRIMARY}; margin-top: 12px;">File History</h4>
            <p><b>Location:</b> <code>~/.claude/file-history/&lt;conversation-id&gt;/</code></p>
            <p>Pre-edit snapshots of every file Claude touched — enables per-file undo.</p>

            <h4 style="color: {theme.ACCENT_PRIMARY}; margin-top: 12px;">Shell Snapshots</h4>
            <p><b>Location:</b> <code>~/.claude/shell-snapshots/</code></p>
            <p>Saved shell environment state (env vars, cwd) captured between tool calls.</p>

            <h4 style="color: {theme.ACCENT_PRIMARY}; margin-top: 12px;">Tasks &amp; Todos</h4>
            <p>Claude Code persists <code>TodoWrite</code> task lists in <code>~/.claude/todos/</code>
            and task outputs in <code>~/.claude/tasks/</code>.</p>
        """)
        layout.addWidget(info)

        return widget

    def create_history_tab(self):
        """Create conversation history tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Splitter for list and content
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # File list
        self.history_list = QListWidget()
        self.history_list.setStyleSheet(f"""
            QListWidget {{
                font-family: {theme.FONT_FAMILY_MONO};
                font-size: {theme.FONT_SIZE_SMALL}px;
            }}
            QListWidget::item:selected {{ background-color: {theme.ACCENT_PRIMARY}; color: {theme.BG_DARK}; }}
        """)
        self.history_list.itemClicked.connect(self.load_history_content)

        # Content viewer
        self.history_viewer = QTextEdit()
        self.history_viewer.setReadOnly(True)

        splitter.addWidget(self.history_list)
        splitter.addWidget(self.history_viewer)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        mgr = UIStateManager.instance()
        mgr.restore_splitter_state("memory.history_splitter", splitter)
        mgr.connect_splitter("memory.history_splitter", splitter)

        layout.addWidget(splitter)

        return widget

    def create_file_history_tab(self):
        """Create file history tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Splitter for list and content
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # File list
        self.file_history_list = QListWidget()
        self.file_history_list.setStyleSheet(f"""
            QListWidget {{
                font-family: {theme.FONT_FAMILY_MONO};
                font-size: {theme.FONT_SIZE_SMALL}px;
            }}
            QListWidget::item:selected {{ background-color: {theme.ACCENT_PRIMARY}; color: {theme.BG_DARK}; }}
        """)
        self.file_history_list.itemClicked.connect(self.load_file_history_content)

        # Content viewer
        self.file_history_viewer = QTextEdit()
        self.file_history_viewer.setReadOnly(True)

        splitter.addWidget(self.file_history_list)
        splitter.addWidget(self.file_history_viewer)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        mgr = UIStateManager.instance()
        mgr.restore_splitter_state("memory.file_history_splitter", splitter)
        mgr.connect_splitter("memory.file_history_splitter", splitter)

        layout.addWidget(splitter)

        return widget

    def create_shell_snapshots_tab(self):
        """Create shell snapshots tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Splitter for list and content
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # File list
        self.shell_list = QListWidget()
        self.shell_list.setStyleSheet(f"""
            QListWidget {{
                font-family: {theme.FONT_FAMILY_MONO};
                font-size: {theme.FONT_SIZE_SMALL}px;
            }}
            QListWidget::item:selected {{ background-color: {theme.ACCENT_PRIMARY}; color: {theme.BG_DARK}; }}
        """)
        self.shell_list.itemClicked.connect(self.load_shell_content)

        # Content viewer
        self.shell_viewer = QTextEdit()
        self.shell_viewer.setReadOnly(True)

        splitter.addWidget(self.shell_list)
        splitter.addWidget(self.shell_viewer)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        mgr = UIStateManager.instance()
        mgr.restore_splitter_state("memory.shell_splitter", splitter)
        mgr.connect_splitter("memory.shell_splitter", splitter)

        layout.addWidget(splitter)

        return widget

    def create_projects_tab(self):
        """Create project conversations browser tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.projects_list = QListWidget()
        self.projects_list.itemClicked.connect(self.load_project_session)

        self.projects_viewer = QTextEdit()
        self.projects_viewer.setReadOnly(True)

        splitter.addWidget(self.projects_list)
        splitter.addWidget(self.projects_viewer)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        mgr = UIStateManager.instance()
        mgr.restore_splitter_state("memory.projects_splitter", splitter)
        mgr.connect_splitter("memory.projects_splitter", splitter)

        layout.addWidget(splitter)
        return widget

    @staticmethod
    def _decode_project_path(folder_name: str) -> str:
        """Decode Claude Code's folder-name encoding back to a readable path.

        Claude Code encodes the absolute project path by replacing each '/' with '-'
        and prepending '-' for the root '/'.  e.g. /home/pi/myproject → -home-pi-myproject
        We reverse that: strip the leading '-', re-insert '/', then try to
        shorten ~/ for the current user's home directory.
        """
        import os
        raw = folder_name.lstrip("-")
        path = "/" + raw.replace("-", "/")
        home = os.path.expanduser("~")
        if path.startswith(home):
            path = "~" + path[len(home):]
        return path

    def refresh_projects(self):
        """Refresh project conversations — grouped by project folder."""
        self.projects_list.clear()
        projects_dir = self.config_manager.claude_dir / "projects"

        if not projects_dir.exists():
            self.projects_list.addItem("No projects directory found")
            return

        # Collect sessions grouped by project folder
        by_project: dict[str, list[dict]] = {}
        try:
            for project_dir in projects_dir.iterdir():
                if not project_dir.is_dir():
                    continue
                sessions = []
                for jsonl_file in project_dir.glob("*.jsonl"):
                    sessions.append({
                        'path': jsonl_file,
                        'uuid': jsonl_file.stem,
                        'mtime': jsonl_file.stat().st_mtime,
                    })
                if sessions:
                    by_project[project_dir.name] = sorted(
                        sessions, key=lambda x: x['mtime'], reverse=True)
        except Exception as e:
            self.projects_list.addItem(f"Error: {str(e)}")
            return

        if not by_project:
            self.projects_list.addItem("No project sessions found")
            return

        # Sort projects by most-recent session date
        sorted_projects = sorted(
            by_project.items(),
            key=lambda kv: kv[1][0]['mtime'],
            reverse=True
        )

        for folder_name, sessions in sorted_projects:
            readable = self._decode_project_path(folder_name)
            latest = datetime.fromtimestamp(sessions[0]['mtime']).strftime("%Y-%m-%d")

            # Project header row (non-selectable)
            header_item = QListWidgetItem(f"📁 {readable}  ({len(sessions)} sessions, latest {latest})")
            header_item.setFlags(Qt.ItemFlag.NoItemFlags)
            header_item.setForeground(QColor(theme.ACCENT_PRIMARY))
            header_item.setFont(QFont(header_item.font().family(), -1, QFont.Weight.Bold))
            self.projects_list.addItem(header_item)

            # Session rows (selectable), capped at 20 per project
            for s in sessions[:20]:
                mod_time = datetime.fromtimestamp(s['mtime']).strftime("%Y-%m-%d %H:%M")
                session_item = QListWidgetItem(f"    📋 {mod_time}  {s['uuid'][:12]}…")
                session_item.setData(Qt.ItemDataRole.UserRole, str(s['path']))
                session_item.setForeground(QColor(theme.FG_SECONDARY))
                self.projects_list.addItem(session_item)

            if len(sessions) > 20:
                more_item = QListWidgetItem(f"    … {len(sessions) - 20} more sessions")
                more_item.setFlags(Qt.ItemFlag.NoItemFlags)
                more_item.setForeground(QColor(theme.FG_DIM))
                self.projects_list.addItem(more_item)

    def load_project_session(self, item):
        """Load a project session JSONL file"""
        path = item.data(Qt.ItemDataRole.UserRole)
        if not path:
            return
        file_path = Path(path)
        if not file_path.exists():
            self.projects_viewer.setPlainText("File not found")
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            formatted = [f"Session: {file_path.name}\nProject: {file_path.parent.name}\nEntries: {len(lines)}\n{'='*60}\n\n"]
            for i, line in enumerate(lines[:50], 1):  # first 50 entries
                try:
                    entry = json.loads(line)
                    ts = entry.get('timestamp', 0)
                    date_str = datetime.fromtimestamp(ts / 1000).strftime("%H:%M:%S") if ts else ""
                    role = entry.get('role', entry.get('type', '?'))
                    content = entry.get('content', '')
                    if isinstance(content, list):
                        content = ' '.join(c.get('text', '') if isinstance(c, dict) else str(c) for c in content)
                    preview = str(content)[:200].replace('\n', ' ')
                    formatted.append(f"[{i}] {date_str} {role}: {preview}\n")
                except Exception:
                    formatted.append(f"[{i}] {line[:100]}\n")
            if len(lines) > 50:
                formatted.append(f"\n... {len(lines) - 50} more entries")
            self.projects_viewer.setPlainText("".join(formatted))
        except Exception as e:
            self.projects_viewer.setPlainText(f"Error: {str(e)}")

    def refresh_all(self):
        """Refresh all tabs"""
        self.refresh_history()
        self.refresh_projects()
        self.refresh_file_history()
        self.refresh_shell_snapshots()

    def refresh_history(self):
        """Refresh conversation history list"""
        self.history_list.clear()
        history_file = self.config_manager.claude_dir / "history.jsonl"

        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    self.history_list.addItem(f"history.jsonl ({len(lines)} entries)")
            except Exception as e:
                self.history_list.addItem(f"Error reading history: {str(e)}")
        else:
            self.history_list.addItem("No history file found")

    def refresh_file_history(self):
        """Refresh file history list"""
        self.file_history_list.clear()
        file_history_dir = self.config_manager.claude_dir / "file-history"

        if not file_history_dir.exists():
            self.file_history_list.addItem("No file history directory found")
            return

        # Collect all files from all conversation subdirectories
        all_files = []
        try:
            # Each subdirectory is a conversation ID
            for conv_dir in file_history_dir.iterdir():
                if conv_dir.is_dir():
                    # Get all files in this conversation directory
                    for file in conv_dir.iterdir():
                        if file.is_file():
                            all_files.append({
                                'path': file,
                                'conv_id': conv_dir.name,
                                'name': file.name,
                                'mtime': file.stat().st_mtime
                            })
        except Exception as e:
            self.file_history_list.addItem(f"Error reading file history: {str(e)}")
            return

        if not all_files:
            self.file_history_list.addItem("No file history found")
            return

        # Sort by modification time (newest first)
        all_files.sort(key=lambda x: x['mtime'], reverse=True)

        # Add to list with conversation grouping
        for file_info in all_files:
            mod_time = datetime.fromtimestamp(file_info['mtime']).strftime("%Y-%m-%d %H:%M:%S")
            conv_id_short = file_info['conv_id'][:8]  # Show first 8 chars of conversation ID
            display_text = f"[{conv_id_short}] {file_info['name']} ({mod_time})"
            self.file_history_list.addItem(display_text)

    def refresh_shell_snapshots(self):
        """Refresh shell snapshots list"""
        self.shell_list.clear()
        shell_dir = self.config_manager.claude_dir / "shell-snapshots"

        if shell_dir.exists():
            files = sorted(shell_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
            for file in files:
                if file.is_file():
                    mod_time = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    self.shell_list.addItem(f"{file.name} ({mod_time})")
        else:
            self.shell_list.addItem("No shell snapshots directory found")

    def load_history_content(self, item):
        """Load conversation history content"""
        history_file = self.config_manager.claude_dir / "history.jsonl"

        if not history_file.exists():
            self.history_viewer.setPlainText("History file not found")
            return

        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Format JSONL for display with better formatting
            formatted = []
            for i, line in enumerate(lines, 1):
                try:
                    entry = json.loads(line)

                    # Convert timestamp to readable date
                    timestamp = entry.get('timestamp', 0)
                    if timestamp:
                        date_str = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        date_str = "Unknown"

                    # Build formatted entry
                    entry_text = f"{'='*80}\n"
                    entry_text += f"ENTRY #{i}\n"
                    entry_text += f"{'='*80}\n\n"

                    entry_text += f"Timestamp:  {date_str}\n"
                    entry_text += f"Display:    {entry.get('display', 'N/A')}\n"
                    entry_text += f"Project:    {entry.get('project', 'N/A')}\n"

                    # Show pasted contents if any
                    pasted = entry.get('pastedContents', {})
                    if pasted:
                        entry_text += f"\nPasted Contents:\n"
                        entry_text += json.dumps(pasted, indent=2)

                    # Show any other fields
                    other_fields = {k: v for k, v in entry.items()
                                   if k not in ['timestamp', 'display', 'project', 'pastedContents']}
                    if other_fields:
                        entry_text += f"\n\nOther Data:\n"
                        entry_text += json.dumps(other_fields, indent=2)

                    entry_text += f"\n\n"
                    formatted.append(entry_text)

                except Exception as e:
                    formatted.append(f"{'='*80}\nEntry {i}: [Parse Error: {str(e)}]\n{line}\n{'='*80}\n\n")

            self.history_viewer.setPlainText("".join(formatted))

        except Exception as e:
            self.history_viewer.setPlainText(f"Error loading history: {str(e)}")

    def load_file_history_content(self, item):
        """Load file history content"""
        text = item.text()

        # Parse format: [conv_id] filename (timestamp)
        try:
            # Extract conversation ID (between brackets)
            if not text.startswith('['):
                self.file_history_viewer.setPlainText("Invalid file format")
                return

            conv_id_end = text.index(']')
            conv_id_short = text[1:conv_id_end]

            # Extract filename (between ] and last ()
            remainder = text[conv_id_end + 2:]  # Skip '] '
            filename = remainder.split(" (")[0]

            # Find the full conversation directory that starts with this short ID
            file_history_dir = self.config_manager.claude_dir / "file-history"
            conv_dir = None
            for d in file_history_dir.iterdir():
                if d.is_dir() and d.name.startswith(conv_id_short):
                    conv_dir = d
                    break

            if not conv_dir:
                self.file_history_viewer.setPlainText(f"Conversation directory not found for ID: {conv_id_short}")
                return

            file_path = conv_dir / filename

            if not file_path.exists():
                self.file_history_viewer.setPlainText(f"File not found: {file_path}")
                return

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Add header with file info
            header = f"File: {filename}\nConversation: {conv_dir.name}\nPath: {file_path}\n\n{'='*80}\n\n"
            self.file_history_viewer.setPlainText(header + content)

        except Exception as e:
            self.file_history_viewer.setPlainText(f"Error loading file: {str(e)}")

    def load_shell_content(self, item):
        """Load shell snapshot content"""
        filename = item.text().split(" (")[0]  # Remove timestamp
        file_path = self.config_manager.claude_dir / "shell-snapshots" / filename

        if not file_path.exists():
            self.shell_viewer.setPlainText("File not found")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.shell_viewer.setPlainText(content)
        except Exception as e:
            self.shell_viewer.setPlainText(f"Error loading file: {str(e)}")
