"""
ClaudeKit Tab - ClaudeKit tools with config-based commands
"""

import subprocess
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QGridLayout, QMessageBox, QInputDialog, QScrollArea,
    QRadioButton, QButtonGroup, QLineEdit, QFileDialog
)
from utils import theme


class ClaudeKitTab(QWidget):
    """Tab for ClaudeKit tools - loads commands from config"""

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
        self.commands = self.load_commands()
        self.init_ui()

    def load_commands(self):
        """Load commands from config/config.json"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            return config.get("claudekit_commands", {})
        except Exception as e:
            QMessageBox.warning(
                None,
                "Config Load Error",
                f"Failed to load commands from config.json:\n{str(e)}\n\nUsing empty command set."
            )
            return {}

    def init_ui(self):
        """Initialize the UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        # Header
        header = QLabel("ClaudeKit Integration")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY}; margin-bottom: 10px;")
        main_layout.addWidget(header)

        # Working Directory Context Selector
        context_group = self.create_context_selector()
        main_layout.addWidget(context_group)

        # Create scrollable area for all command groups
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {theme.BG_DARK};
            }}
        """)

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet(f"background-color: {theme.BG_DARK};")
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(8)

        # Create command groups dynamically from config
        group_titles = {
            "setup_installation": "Setup & Installation",
            "list_show": "List & Show Commands",
            "diagnostics": "Diagnostics",
            "linting": "Linting & Validation",
            "hooks": "Hook Management"
        }

        for group_key, group_title in group_titles.items():
            if group_key in self.commands:
                group = self.create_command_group(group_title, self.commands[group_key])
                scroll_layout.addWidget(group)

        scroll_layout.addStretch(1)
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll, 1)  # Stretch factor to fill space

    def create_context_selector(self):
        """Create working directory context selector"""
        group = QGroupBox("Working Directory Context")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: {theme.FG_PRIMARY};
                background-color: {theme.BG_MEDIUM};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: {theme.BG_MEDIUM};
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Radio buttons
        radio_layout = QHBoxLayout()

        self.radio_global = QRadioButton("Global (~/.claude)")
        self.radio_global.setChecked(True)
        self.radio_global.setStyleSheet(f"color: {theme.FG_PRIMARY}; font-size: {theme.FONT_SIZE_NORMAL}px;")

        self.radio_project = QRadioButton("Project Folder:")
        self.radio_project.setStyleSheet(f"color: {theme.FG_PRIMARY}; font-size: {theme.FONT_SIZE_NORMAL}px;")

        self.button_group = QButtonGroup()
        self.button_group.addButton(self.radio_global)
        self.button_group.addButton(self.radio_project)

        radio_layout.addWidget(self.radio_global)
        radio_layout.addWidget(self.radio_project)
        radio_layout.addStretch()

        layout.addLayout(radio_layout)

        # Project folder selector
        folder_layout = QHBoxLayout()

        self.project_path_edit = QLineEdit()
        self.project_path_edit.setPlaceholderText("Select project folder...")
        self.project_path_edit.setEnabled(False)
        self.project_path_edit.setStyleSheet(theme.get_line_edit_style())

        browse_btn = QPushButton("Browse...")
        browse_btn.setEnabled(False)
        browse_btn.setToolTip("Browse for project folder (enabled when Project radio button is selected)")
        browse_btn.clicked.connect(self.browse_project_folder)
        browse_btn.setStyleSheet(theme.get_button_style())

        # Connect radio button to enable/disable project path controls
        self.radio_global.toggled.connect(lambda checked: self.project_path_edit.setEnabled(not checked))
        self.radio_global.toggled.connect(lambda checked: browse_btn.setEnabled(not checked))

        folder_layout.addWidget(self.project_path_edit, 1)
        folder_layout.addWidget(browse_btn)

        layout.addLayout(folder_layout)

        # Current context display
        self.context_display = QLabel()
        self.update_context_display()
        self.context_display.setStyleSheet(f"color: {theme.SUCCESS_COLOR}; font-size: {theme.FONT_SIZE_SMALL}px; font-weight: bold; padding: 5px;")
        layout.addWidget(self.context_display)

        # Connect signals to update display
        self.radio_global.toggled.connect(lambda: self.update_context_display())
        self.radio_project.toggled.connect(lambda: self.update_context_display())
        self.project_path_edit.textChanged.connect(lambda: self.update_context_display())

        group.setLayout(layout)
        return group

    def browse_project_folder(self):
        """Open folder browser dialog"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Project Folder",
            str(Path.home())
        )
        if folder:
            self.project_path_edit.setText(folder)

    def update_context_display(self):
        """Update the context display label"""
        if self.radio_global.isChecked():
            self.context_display.setText("🌍 Commands will run in: ~/.claude (Global)")
            self.context_display.setStyleSheet(f"color: {theme.SUCCESS_COLOR}; font-size: {theme.FONT_SIZE_SMALL}px; font-weight: bold; padding: 5px;")
        else:
            project_path = self.project_path_edit.text()
            if project_path:
                self.context_display.setText(f"📁 Commands will run in: {project_path}")
                self.context_display.setStyleSheet(f"color: {theme.SUCCESS_COLOR}; font-size: {theme.FONT_SIZE_SMALL}px; font-weight: bold; padding: 5px;")
            else:
                self.context_display.setText("⚠️ Please select a project folder")
                self.context_display.setStyleSheet(f"color: {theme.WARNING_COLOR}; font-size: {theme.FONT_SIZE_SMALL}px; font-weight: bold; padding: 5px;")

    def get_working_directory(self):
        """Get the current working directory based on context selection"""
        if self.radio_global.isChecked():
            return str(Path.home() / ".claude")
        else:
            project_path = self.project_path_edit.text()
            if not project_path:
                raise ValueError("Project folder not specified")
            return project_path

    def create_command_group(self, title, commands):
        """Create a group of command buttons from config data"""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: {theme.FG_PRIMARY};
                background-color: {theme.BG_MEDIUM};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: {theme.BG_MEDIUM};
            }}
        """)

        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setContentsMargins(10, 10, 10, 10)

        row = 0
        col = 0
        for cmd_config in commands:
            button_text = cmd_config.get("button_text", "Unknown")
            tooltip = cmd_config.get("tooltip", "")

            btn = QPushButton(button_text)
            btn.setToolTip(tooltip)
            btn.clicked.connect(lambda checked, cfg=cmd_config: self.handle_command(cfg))
            btn.setStyleSheet(theme.get_button_style())

            grid.addWidget(btn, row, col)

            col += 1
            if col > 2:  # 3 columns
                col = 0
                row += 1

        group.setLayout(grid)
        return group

    def handle_command(self, cmd_config):
        """Handle command execution based on config"""
        try:
            command_template = cmd_config.get("command", "")
            button_text = cmd_config.get("button_text", "Command")

            # Build the command based on requirements
            command = command_template

            # Handle input requirements
            if cmd_config.get("requires_input", False):
                input_prompt = cmd_config.get("input_prompt", "Enter value:")
                input_label = cmd_config.get("input_label", "Value")

                user_input, ok = QInputDialog.getText(
                    self,
                    input_label,
                    input_prompt
                )

                if not ok or not user_input:
                    return

                # Replace placeholder in command
                if "{agent_id}" in command:
                    command = command.replace("{agent_id}", user_input)
                elif "{command_id}" in command:
                    command = command.replace("{command_id}", user_input)
                elif "{hook_name}" in command:
                    command = command.replace("{hook_name}", user_input)

                # Handle JSON format option
                if cmd_config.get("has_json_format", False):
                    reply = QMessageBox.question(
                        self,
                        "JSON Format",
                        "Would you like to also view in JSON format?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        json_command = command + " -f json"
                        self.run_tool(json_command, f"{button_text} (JSON)")
                        return

            # Handle number input requirements (for iterations, etc.)
            if cmd_config.get("requires_number", False):
                number_prompt = cmd_config.get("number_prompt", "Enter number:")
                number_label = cmd_config.get("number_label", "Number")
                number_default = cmd_config.get("number_default", 1)
                number_min = cmd_config.get("number_min", 1)
                number_max = cmd_config.get("number_max", 100)

                number, ok = QInputDialog.getInt(
                    self,
                    number_label,
                    number_prompt,
                    value=number_default,
                    min=number_min,
                    max=number_max
                )

                if not ok:
                    return

                command = command.replace("{iterations}", str(number))

            # Execute the command
            self.run_tool(command, button_text)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Command Error",
                f"Failed to execute command:\n{str(e)}"
            )

    def run_tool(self, command, tool_name):
        """Run external tool directly in PowerShell 7"""
        try:
            # Check if this is a setup command (only setup accepts --user/--project flags)
            is_setup_command = command.strip().startswith("claudekit setup")

            # Build the full command
            if self.radio_global.isChecked():
                # For GLOBAL mode
                if is_setup_command:
                    # Setup commands: use --user flag
                    full_command = f"{command} --user; Read-Host 'Press Enter to close'"
                else:
                    # Other commands: cd to ~/.claude first
                    claude_dir = str(Path.home() / ".claude").replace('\\', '/')
                    full_command = f"cd '{claude_dir}'; {command}; Read-Host 'Press Enter to close'"

            elif self.radio_project.isChecked():
                # For PROJECT mode
                try:
                    working_dir = self.get_working_directory()
                except ValueError as e:
                    QMessageBox.warning(self, "No Project Folder", str(e))
                    return

                working_dir_ps = working_dir.replace('\\', '/')

                if is_setup_command:
                    # Setup commands: use --project flag
                    full_command = f"{command} --project '{working_dir_ps}'; Read-Host 'Press Enter to close'"
                else:
                    # Other commands: cd to project folder first
                    full_command = f"cd '{working_dir_ps}'; {command}; Read-Host 'Press Enter to close'"
            else:
                # Fallback
                full_command = f"{command}; Read-Host 'Press Enter to close'"

            # Launch pwsh directly
            subprocess.Popen(
                [
                    'pwsh.exe',
                    '-NoProfile',
                    '-Command', full_command
                ],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to run {tool_name}:\n{str(e)}\n\nCommand: {command}"
            )
