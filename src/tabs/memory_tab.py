"""
Memory Tab - Claude Code memory and checkpointing
"""

import json
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextBrowser, QHBoxLayout, QPushButton,
    QMessageBox, QTabWidget, QListWidget, QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.theme import *


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
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        header = QLabel("Memory & Checkpointing")
        header.setStyleSheet(f"font-size: {FONT_SIZE_LARGE}px; font-weight: bold; color: {ACCENT_PRIMARY};")

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet(get_button_style())
        refresh_btn.setToolTip("Refresh all memory and history data")
        refresh_btn.clicked.connect(self.refresh_all)

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Tab widget for different memory types
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {BG_LIGHT};
                background-color: {BG_MEDIUM};
            }}
            QTabBar::tab {{
                background-color: {BG_DARK};
                color: {FG_PRIMARY};
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid {BG_LIGHT};
            }}
            QTabBar::tab:selected {{
                background-color: {ACCENT_PRIMARY};
                color: white;
            }}
            QTabBar::tab:hover {{
                background-color: {BG_LIGHT};
            }}
        """)

        # Create tabs
        self.tab_widget.addTab(self.create_overview_tab(), "Overview")
        self.tab_widget.addTab(self.create_history_tab(), "Conversation History")
        self.tab_widget.addTab(self.create_file_history_tab(), "File History")
        self.tab_widget.addTab(self.create_shell_snapshots_tab(), "Shell Snapshots")

        layout.addWidget(self.tab_widget, 1)

        # Load initial data
        self.refresh_all()

    def create_overview_tab(self):
        """Create overview tab with general info"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        info = QTextBrowser()
        info.setHtml(f"""
            <h3 style="color: {ACCENT_PRIMARY};">Claude Code Memory System</h3>

            <h4 style="color: {ACCENT_PRIMARY}; margin-top: 15px;">Memory Hierarchy (Precedence Order)</h4>
            <p>Claude Code loads memory from multiple locations with the following precedence:</p>
            <ol style="line-height: 1.8;">
                <li><b>Enterprise Policy:</b> System-wide (<code>C:\\ProgramData\\ClaudeCode\\CLAUDE.md</code> on Windows)</li>
                <li><b>Project Memory:</b> <code>./CLAUDE.md</code> (shared with team via git)</li>
                <li><b>User Memory:</b> <code>~/.claude/CLAUDE.md</code> (personal, all projects)</li>
                <li><b>Local Project Memory:</b> <code>./CLAUDE.local.md</code> (personal, this project only)</li>
            </ol>
            <p><b>Tip:</b> Use <code>/memory</code> to edit CLAUDE.md files • Use <code>#</code> prefix in prompts to quickly add content</p>

            <h4 style="color: {ACCENT_PRIMARY}; margin-top: 15px;">Conversation History</h4>
            <p><b>Location:</b> <code>~/.claude/history.jsonl</code></p>
            <p>Stores all conversation turns for context persistence across sessions.</p>

            <h4 style="color: {ACCENT_PRIMARY}; margin-top: 15px;">Checkpointing</h4>
            <p>Save conversation state and rollback if needed:</p>
            <ul style="line-height: 1.8;">
                <li><code>/checkpoint</code> - Create a checkpoint at current state</li>
                <li><code>/checkpoints</code> - List all available checkpoints</li>
                <li><code>/restore &lt;id&gt;</code> - Restore to a specific checkpoint</li>
            </ul>

            <h4 style="color: {ACCENT_PRIMARY}; margin-top: 15px;">File History</h4>
            <p><b>Location:</b> <code>~/.claude/file-history/</code></p>
            <p>Tracks all file modifications made during sessions.</p>

            <h4 style="color: {ACCENT_PRIMARY}; margin-top: 15px;">Project Memory</h4>
            <p><b>Location:</b> <code>./.claude/</code></p>
            <p>Project-specific context and settings stored in your project directory.</p>

            <h4 style="color: {ACCENT_PRIMARY}; margin-top: 15px;">Memory Management</h4>
            <ul style="line-height: 1.8;">
                <li><b>Token Usage:</b> Claude Code tracks context window usage</li>
                <li><b>Auto Pruning:</b> Automatically manages conversation length</li>
                <li><b>CLAUDE.md:</b> Persistent project instructions</li>
            </ul>

            <h4 style="color: {ACCENT_PRIMARY}; margin-top: 15px;">Shell Snapshots</h4>
            <p><b>Location:</b> <code>~/.claude/shell-snapshots/</code></p>
            <p>Snapshots of shell command outputs for reference.</p>
        """)
        info.setStyleSheet(get_text_browser_style())
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
                background-color: {BG_DARK};
                color: {FG_PRIMARY};
                border: 1px solid {BG_LIGHT};
                font-family: 'Consolas', 'Monaco', monospace;
            }}
            QListWidget::item:selected {{
                background-color: {ACCENT_PRIMARY};
                color: white;
            }}
        """)
        self.history_list.itemClicked.connect(self.load_history_content)

        # Content viewer
        self.history_viewer = QTextEdit()
        self.history_viewer.setReadOnly(True)
        self.history_viewer.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_DARK};
                color: {FG_PRIMARY};
                border: 1px solid {BG_LIGHT};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: {FONT_SIZE_SMALL}px;
            }}
        """)

        splitter.addWidget(self.history_list)
        splitter.addWidget(self.history_viewer)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

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
                background-color: {BG_DARK};
                color: {FG_PRIMARY};
                border: 1px solid {BG_LIGHT};
                font-family: 'Consolas', 'Monaco', monospace;
            }}
            QListWidget::item:selected {{
                background-color: {ACCENT_PRIMARY};
                color: white;
            }}
        """)
        self.file_history_list.itemClicked.connect(self.load_file_history_content)

        # Content viewer
        self.file_history_viewer = QTextEdit()
        self.file_history_viewer.setReadOnly(True)
        self.file_history_viewer.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_DARK};
                color: {FG_PRIMARY};
                border: 1px solid {BG_LIGHT};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: {FONT_SIZE_SMALL}px;
            }}
        """)

        splitter.addWidget(self.file_history_list)
        splitter.addWidget(self.file_history_viewer)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

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
                background-color: {BG_DARK};
                color: {FG_PRIMARY};
                border: 1px solid {BG_LIGHT};
                font-family: 'Consolas', 'Monaco', monospace;
            }}
            QListWidget::item:selected {{
                background-color: {ACCENT_PRIMARY};
                color: white;
            }}
        """)
        self.shell_list.itemClicked.connect(self.load_shell_content)

        # Content viewer
        self.shell_viewer = QTextEdit()
        self.shell_viewer.setReadOnly(True)
        self.shell_viewer.setStyleSheet(f"""
            QTextEdit {{
                background-color: {BG_DARK};
                color: {FG_PRIMARY};
                border: 1px solid {BG_LIGHT};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: {FONT_SIZE_SMALL}px;
            }}
        """)

        splitter.addWidget(self.shell_list)
        splitter.addWidget(self.shell_viewer)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        return widget

    def refresh_all(self):
        """Refresh all tabs"""
        self.refresh_history()
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
