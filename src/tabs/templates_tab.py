"""
Templates Tab - Claude Code template management with config-based commands
"""

import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QGridLayout, QInputDialog, QGroupBox
)
from utils import theme


class TemplatesTab(QWidget):
    """Tab for Claude Code template management - loads commands from config"""

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
        self.commands = self.load_commands()
        self.init_ui()

    def load_commands(self):
        """Load template commands from config/config.json"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            return config.get("templates_tools", [])
        except Exception as e:
            QMessageBox.warning(
                None,
                "Config Load Error",
                f"Failed to load templates from config.json:\n{str(e)}\n\nUsing empty command set."
            )
            return []

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        header = QLabel("Claude Code Templates")
        header.setStyleSheet(f"""
            font-size: {theme.FONT_SIZE_LARGE}px;
            font-weight: bold;
            color: {theme.ACCENT_PRIMARY};
            padding: 5px;
        """)
        layout.addWidget(header)

        # Description
        desc = QLabel(
            "Manage Claude Code templates using npx claude-code-templates@latest. "
            "Templates provide pre-configured setups for agents, commands, hooks, and workflows."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(theme.get_label_style("normal", "secondary"))
        layout.addWidget(desc)

        # Commands group
        commands_group = self.create_commands_group()
        layout.addWidget(commands_group)

        layout.addStretch()

    def create_commands_group(self):
        """Create command buttons grid"""
        group = QGroupBox("Template Commands")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {theme.BG_LIGHT};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 15px;
                color: {theme.ACCENT_SECONDARY};
                font-size: {theme.FONT_SIZE_NORMAL}px;
                background-color: {theme.BG_MEDIUM};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: {theme.BG_MEDIUM};
            }}
        """)

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setContentsMargins(15, 15, 15, 15)

        row = 0
        col = 0
        for cmd_config in self.commands:
            button_text = cmd_config.get("button_text", "Unknown")
            tooltip = cmd_config.get("tooltip", "")

            btn = QPushButton(button_text)
            btn.setToolTip(tooltip)
            btn.clicked.connect(lambda checked, cfg=cmd_config: self.handle_command(cfg))
            btn.setStyleSheet(f"""
                QPushButton {{
                    padding: 10px 15px;
                    background-color: {theme.ACCENT_PRIMARY};
                    color: {theme.BG_DARK};
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: {theme.FONT_SIZE_NORMAL}px;
                    min-width: 200px;
                    min-height: 40px;
                }}
                QPushButton:hover {{
                    background-color: {theme.ACCENT_SECONDARY};
                }}
                QPushButton:pressed {{
                    background-color: {theme.BG_LIGHT};
                    color: {theme.FG_PRIMARY};
                }}
            """)

            grid.addWidget(btn, row, col)

            col += 1
            if col > 1:  # 2 columns
                col = 0
                row += 1

        group.setLayout(grid)
        return group

    def handle_command(self, cmd_config):
        """Handle command execution with input if required"""
        command = cmd_config.get("command", "")
        button_text = cmd_config.get("button_text", "Command")

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
            command = command.replace("{template_name}", user_input)

        # Execute the command
        self.run_tool(command, button_text)

    def run_tool(self, command, tool_name):
        """Run template tool in a cross-platform terminal"""
        from utils.terminal_utils import run_in_terminal
        run_in_terminal(command, title=tool_name, parent_widget=self)
