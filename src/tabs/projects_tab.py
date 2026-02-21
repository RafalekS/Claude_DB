"""
Projects Tab - Manage Claude Code projects
"""

import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QTextEdit, QGroupBox, QCheckBox, QMessageBox,
    QTabWidget
)
from PyQt6.QtCore import Qt
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme
from utils.terminal_utils import run_in_terminal


class ProjectsTab(QWidget):
    """Tab for managing Claude Code projects"""

    def __init__(self, config_manager, backup_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager

        # Paths
        self.claude_dir = Path.home() / ".claude"
        self.projects_dir = self.claude_dir / "projects"

        # Current selection
        self.current_project_path = None

        self.init_ui()
        self.load_projects()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        header = QLabel("Projects Management")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")
        layout.addWidget(header)

        # Project Selector
        selector_group = self.create_selector_group()
        layout.addWidget(selector_group)

        # Project Info Tabs
        info_tabs = self.create_info_tabs()
        layout.addWidget(info_tabs, 1)

        # Command Executor
        command_group = self.create_command_group()
        layout.addWidget(command_group)

        # Terminal Actions
        terminal_group = self.create_terminal_group()
        layout.addWidget(terminal_group)

    def create_selector_group(self):
        """Create project selector group"""
        group = QGroupBox("Select Project")
        group.setStyleSheet(theme.get_groupbox_style())
        layout = QHBoxLayout()

        # Project dropdown
        self.project_combo = QComboBox()
        self.project_combo.setStyleSheet(theme.get_line_edit_style() + "QComboBox { combobox-popup: 0; }")
        self.project_combo.setMaxVisibleItems(10)
        # Limit dropdown height
        self.project_combo.view().setStyleSheet("QListView { max-height: 300px; }")
        self.project_combo.currentIndexChanged.connect(self.on_project_selected)
        layout.addWidget(self.project_combo, 1)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet(theme.get_button_style())
        refresh_btn.setToolTip("Reload projects list")
        refresh_btn.clicked.connect(self.load_projects)
        layout.addWidget(refresh_btn)

        group.setLayout(layout)
        return group

    def create_info_tabs(self):
        """Create project info viewer (simplified - only Project Info remains)"""
        # Project Info viewer
        self.info_viewer = QTextEdit()
        self.info_viewer.setReadOnly(True)
        self.info_viewer.setStyleSheet(theme.get_text_edit_style())

        return self.info_viewer

    def create_command_group(self):
        """Create command executor group"""
        group = QGroupBox("Execute Commands")
        group.setStyleSheet(theme.get_groupbox_style())
        layout = QVBoxLayout()

        # Info commands row
        info_layout = QHBoxLayout()

        commands_info = [
            ("📊 /status", "/status", "Show project status"),
            ("📈 /context", "/context", "Show context usage"),
            ("💰 /usage", "/usage", "Show token usage"),
            ("🔐 /permissions", "/permissions", "Show permissions")
        ]

        for label, cmd, tooltip in commands_info:
            btn = QPushButton(label)
            btn.setStyleSheet(theme.get_button_style())
            btn.setToolTip(tooltip)
            btn.clicked.connect(lambda checked, c=cmd: self.execute_command(c))
            info_layout.addWidget(btn)

        layout.addLayout(info_layout)

        # Session commands row
        session_layout = QHBoxLayout()

        commands_session = [
            ("📦 /compact", "/compact", "Compact conversation"),
            ("▶️ /resume", "/resume", "Resume session"),
            ("🔄 /continue", "/continue", "Continue working"),
            ("👁️ /review", "/review", "Review changes")
        ]

        for label, cmd, tooltip in commands_session:
            btn = QPushButton(label)
            btn.setStyleSheet(theme.get_button_style())
            btn.setToolTip(tooltip)
            btn.clicked.connect(lambda checked, c=cmd: self.execute_command(c))
            session_layout.addWidget(btn)

        layout.addLayout(session_layout)

        # Config commands row
        config_layout = QHBoxLayout()

        commands_config = [
            ("🔌 /mcp", "/mcp", "Manage MCP servers"),
            ("🤖 /model", "/model", "Select model")
        ]

        for label, cmd, tooltip in commands_config:
            btn = QPushButton(label)
            btn.setStyleSheet(theme.get_button_style())
            btn.setToolTip(tooltip)
            btn.clicked.connect(lambda checked, c=cmd: self.execute_command(c))
            config_layout.addWidget(btn)

        layout.addLayout(config_layout)

        group.setLayout(layout)
        return group

    def create_terminal_group(self):
        """Create terminal actions group"""
        group = QGroupBox("Terminal Actions")
        group.setStyleSheet(theme.get_groupbox_style())
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
        open_terminal_btn.setStyleSheet(theme.get_button_style())
        open_terminal_btn.setToolTip("Open project directory in Windows Terminal")
        open_terminal_btn.clicked.connect(self.open_in_terminal)
        layout.addWidget(open_terminal_btn)

        group.setLayout(layout)
        return group

    def decode_project_directory_name(self, dir_name):
        """
        Decode project directory name to actual path

        Example: C--Scripts-python-Claude_DB -> C:\\Scripts\\python\\Claude_DB

        Encoding: : becomes --, both \\ and - become -, _ becomes -
        Special: -- in middle means \\. (dot directory)

        Since encoding is ambiguous (both - and _ become -), try all combinations.

        Args:
            dir_name: Encoded directory name

        Returns:
            Path object or None if can't decode
        """
        # Find first occurrence of --
        idx = dir_name.find('--')
        if idx == -1:
            return None

        # Everything before -- is drive letter
        drive = dir_name[:idx]

        # Everything after first -- is the rest
        rest = dir_name[idx+2:]

        # Handle dot directories: -- means \. (backslash-dot)
        # Example: C--Users-r-sta--claude → C:\Users\r_sta\.claude
        # Replace -- with special marker that becomes \. (not just .)
        rest = rest.replace('--', '\x00BSDOT\x00')

        # Now we have rest with single - characters
        # Each - could be either \ or - or _ or .
        # Try combinations by replacing - with \ first (most common)

        def try_path(s):
            """Helper to restore backslash-dots and try path"""
            # \x00BSDOT\x00 → \.
            return Path(f"{drive}:\\{s.replace('\x00BSDOT\x00', '\\.')}")

        # Strategy 1: All - become \
        path1 = try_path(rest.replace('-', '\\'))
        if path1.exists():
            return path1

        # Strategy 2: All - stay as -
        path2 = try_path(rest)
        if path2.exists():
            return path2

        # Strategy 3: All - become _
        path3 = try_path(rest.replace('-', '_'))
        if path3.exists():
            return path3

        # Strategy 3b: All - become . (for files like Microsoft.WindowsTerminal)
        path3b = try_path(rest.replace('-', '.'))
        if path3b.exists():
            return path3b

        # Strategy 4: Try mixed combinations
        # Most common: path\separator\with-dashes-in-name or dots/underscores
        parts = rest.split('-')

        if len(parts) >= 2:
            # Try: first parts are path separators, last part keeps dashes/dots/underscores
            for split_point in range(1, len(parts)):
                path_part = '\\'.join(parts[:split_point])
                name_part = '-'.join(parts[split_point:])

                # Try different encodings in the name part
                variants = [
                    name_part,  # Keep dashes
                    name_part.replace('-', '_'),  # All underscores
                    name_part.replace('-', '.'),  # All dots
                ]

                # Also try mixed dot and underscore (like Microsoft.WindowsTerminal_8wekyb3d8bbwe)
                if '-' in name_part:
                    name_parts = name_part.split('-')
                    if len(name_parts) >= 2:
                        # Try first dot, rest underscore
                        mixed = '.'.join(name_parts[:2]) + '_' + '_'.join(name_parts[2:]) if len(name_parts) > 2 else '.'.join(name_parts)
                        variants.append(mixed)

                for variant in variants:
                    combined = f"{path_part}\\{variant}"
                    test_path = try_path(combined)
                    if test_path.exists():
                        return test_path

        return None

    def scan_projects(self):
        """
        Scan for Claude Code projects by reading ~/.claude/projects/

        Returns:
            list of dict: [{"name": "project_name", "path": Path, "sessions": int}]
        """
        projects = []

        if not self.projects_dir.exists():
            return projects

        # Each subdirectory represents a project
        for project_dir in self.projects_dir.iterdir():
            if not project_dir.is_dir():
                continue

            # Decode directory name to get actual path
            project_path = self.decode_project_directory_name(project_dir.name)

            # Only include if decoding succeeded AND path exists
            if project_path is not None:
                projects.append({
                    "name": project_path.name,
                    "path": project_path,
                    "sessions": len(list(project_dir.glob("*.jsonl")))
                })

        return projects

    def load_projects(self):
        """Load and populate projects list"""
        self.project_combo.clear()
        projects = self.scan_projects()

        if not projects:
            self.project_combo.addItem("No projects found")
            self.current_project_path = None
            self.clear_info_viewers()
            return

        # Sort by full path
        projects.sort(key=lambda x: str(x["path"]).lower())

        for project in projects:
            # Show full path, not just name
            display_name = f"{project['path']} ({project['sessions']} sessions)"
            self.project_combo.addItem(display_name, project["path"])

        # Auto-select first project
        if self.project_combo.count() > 0:
            self.on_project_selected(0)

    def on_project_selected(self, index):
        """Handle project selection"""
        if index < 0 or self.project_combo.count() == 0:
            return

        project_path = self.project_combo.itemData(index)
        if not project_path:
            return

        self.current_project_path = project_path
        self.load_project_info()

    def load_project_info(self):
        """Load project info into viewers"""
        if not self.current_project_path:
            self.clear_info_viewers()
            return

        project_path = self.current_project_path

        # Project Info
        info_text = f"Project: {project_path.name}\n"
        info_text += f"Path: {project_path}\n\n"

        # Check for .claude folder
        claude_folder = project_path / ".claude"
        if claude_folder.exists():
            info_text += "✅ Claude-initialized project (.claude/ folder exists)\n\n"
            info_text += "Files in .claude/:\n"
            for file in claude_folder.iterdir():
                if file.is_file():
                    size_kb = file.stat().st_size / 1024
                    info_text += f"  • {file.name} ({size_kb:.1f} KB)\n"
                elif file.is_dir():
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
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
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
