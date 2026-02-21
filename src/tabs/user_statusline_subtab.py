"""
User Statusline Sub-Tab - Manage user-level statusline configuration
Dedicated subtab for statusline in ~/.claude/settings.json
"""

import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QGroupBox, QLineEdit, QFormLayout
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme


class UserStatuslineSubTab(QWidget):
    """Dedicated subtab for user-level statusline configuration"""

    def __init__(self, config_manager, backup_manager, settings_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.settings_manager = settings_manager
        self.init_ui()
        self.load_statusline()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header
        header_layout = QHBoxLayout()

        header = QLabel("User Statusline Configuration")
        header.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; "
            f"font-weight: bold; "
            f"color: {theme.ACCENT_PRIMARY};"
        )

        docs_btn = QPushButton("📖 Statusline Docs")
        docs_btn.setStyleSheet(theme.get_button_style())
        docs_btn.setToolTip("Open official statusline documentation")
        docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://docs.claude.com/en/docs/claude-code/settings#statusline")
        ))

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(docs_btn)
        layout.addLayout(header_layout)

        # File path info
        path_label = QLabel(f"File: {self.config_manager.settings_file}")
        path_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(path_label)

        # Configuration section
        config_group = QGroupBox("Statusline Configuration")
        config_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: {theme.FG_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)

        config_layout = QVBoxLayout()

        # Command input
        command_layout = QFormLayout()
        command_layout.setSpacing(8)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("e.g., git branch --show-current 2>/dev/null || echo 'main'")
        self.command_input.setStyleSheet(theme.get_line_edit_style())
        command_layout.addRow("Command:", self.command_input)

        self.template_input = QLineEdit()
        self.template_input.setPlaceholderText("e.g., {{project_name}} [{{git_branch}}]")
        self.template_input.setStyleSheet(theme.get_line_edit_style())
        command_layout.addRow("Template:", self.template_input)

        config_layout.addLayout(command_layout)

        # JSON preview
        preview_label = QLabel("JSON Configuration:")
        preview_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY}; margin-top: 10px;")
        config_layout.addWidget(preview_label)

        self.json_preview = QTextEdit()
        self.json_preview.setReadOnly(True)
        self.json_preview.setMaximumHeight(150)
        self.json_preview.setStyleSheet(f"""
            QTextEdit {{
                font-family: 'Consolas', 'Monaco', monospace;
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                padding: 5px;
            }}
        """)
        config_layout.addWidget(self.json_preview)

        # Update preview button
        preview_btn = QPushButton("🔄 Update Preview")
        preview_btn.setStyleSheet(theme.get_button_style())
        preview_btn.clicked.connect(self.update_preview)
        config_layout.addWidget(preview_btn)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        load_btn = QPushButton("📂 Load Current")
        load_btn.setStyleSheet(theme.get_button_style())
        load_btn.setToolTip("Load current statusline from settings")
        load_btn.clicked.connect(self.load_statusline)

        save_btn = QPushButton("💾 Save")
        save_btn.setStyleSheet(theme.get_button_style())
        save_btn.setToolTip("Save statusline configuration")
        save_btn.clicked.connect(self.save_statusline)

        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.setStyleSheet(theme.get_button_style())
        clear_btn.setToolTip("Clear statusline configuration")
        clear_btn.clicked.connect(self.clear_statusline)

        btn_layout.addWidget(load_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(clear_btn)

        layout.addLayout(btn_layout)

        # Info footer
        footer = QLabel(
            "💡 <b>Template Variables:</b> {{project_name}}, {{git_branch}}, {{model}}, {{tokens}}, {{time}} • "
            "<b>Command:</b> Shell command to execute for dynamic values"
        )
        footer.setWordWrap(True)
        footer.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; "
            f"padding: 8px; "
            f"background-color: {theme.BG_MEDIUM}; "
            f"border-radius: 3px;"
        )
        layout.addWidget(footer)

        layout.addStretch()

    def load_statusline(self):
        """Load statusline from user settings"""
        try:
            settings = self.settings_manager.get_user_settings()
            # Note: Settings.json uses 'statusLine' (camelCase), not 'statusline'
            statusline = settings.get("statusLine", settings.get("statusline", {}))

            # Handle different formats
            if isinstance(statusline, str):
                # If it's a string, it's just the command
                self.command_input.setText(statusline)
                self.template_input.clear()
                self.update_preview()
            elif isinstance(statusline, dict):
                # If it's a dict, extract command and template
                # Can have 'command' directly or nested under 'type'
                command = statusline.get("command", "")
                template = statusline.get("template", "")
                self.command_input.setText(command)
                self.template_input.setText(template)
                self.update_preview()
            else:
                # Empty or unexpected format
                self.command_input.clear()
                self.template_input.clear()
                self.json_preview.setPlainText("# No statusline configured")
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load statusline:\n{str(e)}")

    def update_preview(self):
        """Update JSON preview"""
        try:
            command = self.command_input.text().strip()
            template = self.template_input.text().strip()

            if command or template:
                config = {}
                if command:
                    config["command"] = command
                if template:
                    config["template"] = template

                formatted = json.dumps(config, indent=2)
                self.json_preview.setPlainText(formatted)
            else:
                self.json_preview.setPlainText("# No configuration")
        except Exception as e:
            self.json_preview.setPlainText(f"# Error: {str(e)}")

    def save_statusline(self):
        """Save statusline configuration"""
        try:
            command = self.command_input.text().strip()
            template = self.template_input.text().strip()

            if not command and not template:
                QMessageBox.warning(
                    self,
                    "Empty Configuration",
                    "Please enter at least a command or template before saving."
                )
                return

            # Load settings
            settings = self.settings_manager.get_user_settings()

            # Update statusline (use camelCase 'statusLine' to match settings.json format)
            statusline_config = {}
            if command:
                statusline_config["command"] = command
            if template:
                statusline_config["template"] = template

            settings["statusLine"] = statusline_config

            # Save settings
            self.settings_manager.save_settings(
                self.config_manager.settings_file,
                settings
            )

            self.update_preview()
            QMessageBox.information(self, "Success", "Statusline configuration saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save statusline:\n{str(e)}")

    def clear_statusline(self):
        """Clear statusline configuration"""
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            "Are you sure you want to clear the statusline configuration?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Load settings
                settings = self.settings_manager.get_user_settings()

                # Remove statusline (check both camelCase and lowercase)
                if "statusLine" in settings:
                    del settings["statusLine"]
                if "statusline" in settings:
                    del settings["statusline"]

                # Save settings
                self.settings_manager.save_settings(
                    self.config_manager.settings_file,
                    settings
                )

                self.command_input.clear()
                self.template_input.clear()
                self.json_preview.setPlainText("# Statusline cleared")

                QMessageBox.information(self, "Success", "Statusline configuration cleared successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Clear Error", f"Failed to clear statusline:\n{str(e)}")
