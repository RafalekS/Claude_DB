"""
Projects Tab - Manage Claude Code projects
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QGroupBox, QCheckBox, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from utils import theme
from utils.terminal_utils import run_in_terminal

class ProjectsTab(QWidget):
    """Tab for managing Claude Code projects"""

    def __init__(self, config_manager, backup_manager, project_context=None):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.project_context = project_context

        # Current selection — synced from project_context if provided
        self.current_project_path = None

        self.init_ui()

        if self.project_context is not None:
            self.project_context.project_changed.connect(self._on_context_changed)
            # Initialise from current context state
            if self.project_context.has_project():
                self._on_context_changed(self.project_context.get_project())

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Header
        header = QLabel("Projects Management")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")
        layout.addWidget(header)

        # Project Info
        info_tabs = self.create_info_tabs()
        layout.addWidget(info_tabs, 1)

        # Command Executor
        command_group = self.create_command_group()
        layout.addWidget(command_group)

        # Terminal Actions
        terminal_group = self.create_terminal_group()
        layout.addWidget(terminal_group)

    def _on_context_changed(self, new_project):
        """Sync current_project_path from project_context signal"""
        self.current_project_path = new_project
        self.load_project_info()

    def create_info_tabs(self):
        """Create project info viewer (simplified - only Project Info remains)"""
        # Project Info viewer
        self.info_viewer = QTextEdit()
        self.info_viewer.setReadOnly(True)
        self.info_viewer.setFont(QFont(theme.FONT_MONOSPACE, theme.FONT_SIZE_SMALL))

        return self.info_viewer

    def create_command_group(self):
        """Create command executor group"""
        group = QGroupBox("Execute Commands")
        layout = QVBoxLayout()

        def _row(commands):
            row = QHBoxLayout()
            for label, cmd, tooltip in commands:
                btn = QPushButton(label)
                btn.setToolTip(tooltip)
                btn.clicked.connect(lambda checked, c=cmd: self.execute_command(c))
                row.addWidget(btn)
            return row

        layout.addLayout(_row([
            ("📊 /status", "/status", "Show project status"),
            ("📈 /context", "/context", "Show context usage"),
            ("💰 /cost", "/cost", "Show token cost for current session"),
            ("🔐 /permissions", "/permissions", "Show permissions"),
        ]))

        layout.addLayout(_row([
            ("📦 /compact", "/compact", "Compact conversation to free context"),
            ("▶️ /resume", "/resume", "Open session picker or resume by ID"),
            ("🔄 /continue", "/continue", "Continue working"),
            ("🌿 /branch", "/branch", "Fork conversation from this point"),
        ]))

        layout.addLayout(_row([
            ("🤖 /agents", "/agents", "Browse subagents; create new ones"),
            ("🪝 /hooks", "/hooks", "Browse configured hooks"),
            ("🧠 /memory", "/memory", "Browse and edit memory files"),
            ("🔌 /mcp", "/mcp", "Manage MCP servers"),
        ]))

        layout.addLayout(_row([
            ("🏥 /doctors", "/doctors", "Check Claude Code installation health"),
            ("📝 /init", "/init", "Generate CLAUDE.md from codebase analysis"),
            ("🤖 /model", "/model", "Switch Claude model"),
            ("❓ /help", "/help", "Show all commands and shortcuts"),
        ]))

        group.setLayout(layout)
        return group

    def create_terminal_group(self):
        """Create terminal actions group"""
        group = QGroupBox("Terminal Actions")
        layout = QHBoxLayout()

        # Dangerous permissions checkbox
        self.dangerous_checkbox = QCheckBox("--dangerously-skip-permissions")
        self.dangerous_checkbox.setStyleSheet(f"color: {theme.ERROR_COLOR}; font-weight: bold;")
        self.dangerous_checkbox.setToolTip("⚠️ WARNING: Skip all permission prompts (use in controlled environments only)")
        self.dangerous_checkbox.stateChanged.connect(self.on_dangerous_checkbox_changed)
        layout.addWidget(self.dangerous_checkbox)

        layout.addStretch()

        # Open in terminal button
        open_terminal_btn = QPushButton("🖥️ Open in Terminal")
        open_terminal_btn.setToolTip("Open project directory in Windows Terminal")
        open_terminal_btn.clicked.connect(self.open_in_terminal)
        layout.addWidget(open_terminal_btn)

        group.setLayout(layout)
        return group


    def load_project_info(self):
        """Load project info into viewers"""
        if not self.current_project_path:
            self.clear_info_viewers()
            return

        project_path = self.current_project_path

        # Project Info
        info_text = f"Project: {project_path.name}\n"
        info_text += f"Path: {project_path}\n\n"

        claude_folder = project_path / ".claude"
        if self.config_manager.fs.exists(claude_folder):
            info_text += "✅ Claude-initialized project (.claude/ folder exists)\n\n"
            info_text += "Files in .claude/:\n"
            for file in self.config_manager.fs.iterdir(claude_folder):
                if self.config_manager.fs.is_file(file):
                    try:
                        size_kb = self.config_manager.fs.stat(file).st_size / 1024
                        info_text += f"  • {file.name} ({size_kb:.1f} KB)\n"
                    except Exception:
                        info_text += f"  • {file.name}\n"
                elif self.config_manager.fs.is_dir(file):
                    info_text += f"  📁 {file.name}/\n"
        else:
            info_text += "❌ Not a Claude-initialized project\n"
            info_text += "   (No .claude/ folder found)\n\n"
            info_text += "To initialize this project, run:\n"
            info_text += f"  cd \"{project_path}\"\n"
            info_text += "  claude /init\n"

        self.info_viewer.setText(info_text)

    def load_file_into_viewer(self, file_path, viewer, not_found_msg):
        """Load file content into text viewer"""
        if not file_path:
            viewer.setText(not_found_msg)
            return
        if self.config_manager.fs.exists(file_path):
            try:
                content = self.config_manager.fs.read_text(file_path)
                viewer.setText(content)
            except Exception as e:
                viewer.setText(f"Error reading file:\n{str(e)}")
        else:
            viewer.setText(not_found_msg)

    def clear_info_viewers(self):
        """Clear info viewer"""
        self.info_viewer.clear()

    def execute_command(self, command):
        """Execute Claude command in project directory"""
        if not self.current_project_path:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        # Build command
        cmd = f"claude {command}"

        # Add dangerous flag if checked
        if self.dangerous_checkbox.isChecked():
            cmd += " --dangerously-skip-permissions"

        # Execute in terminal
        run_in_terminal(
            cmd,
            cwd=str(self.current_project_path),
            title=f"Claude {command} - {self.current_project_path.name}"
        )

    def on_dangerous_checkbox_changed(self, state):
        """Handle dangerous checkbox state change"""
        if state == Qt.CheckState.Checked.value:
            reply = QMessageBox.warning(
                self,
                "⚠️ WARNING: Dangerous Mode",
                "You are about to enable --dangerously-skip-permissions\n\n"
                "This flag will:\n"
                "• Skip ALL permission prompts\n"
                "• Allow unrestricted file operations\n"
                "• Bypass safety checks\n\n"
                "ONLY use this in:\n"
                "• Controlled test environments\n"
                "• Sandboxed containers\n"
                "• When you fully trust the code\n\n"
                "Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                self.dangerous_checkbox.setChecked(False)

    def open_in_terminal(self):
        """Open project directory in terminal"""
        if not self.current_project_path:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        # Open terminal in project directory with a simple command to keep it open
        run_in_terminal(
            "Write-Host 'Ready'",  # Simple command to keep terminal open
            cwd=str(self.current_project_path),
            title=f"Project: {self.current_project_path.name}"
        )
