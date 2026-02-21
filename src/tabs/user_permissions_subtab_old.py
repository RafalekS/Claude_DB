"""
User Permissions Sub-Tab - Simple JSON editor for permissions
Uses object format {"allow": [...], "deny": [...], "ask": [...]} - the standard Claude Code format
"""

import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox
)
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme


class UserPermissionsSubTab(QWidget):
    """Simple JSON editor for user-level permissions"""

    def __init__(self, config_manager, backup_manager, settings_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.settings_manager = settings_manager
        self.init_ui()
        self.load_permissions()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        header = QLabel("User Permissions Configuration")
        header.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; "
            f"font-weight: bold; "
            f"color: {theme.ACCENT_PRIMARY};"
        )

        docs_btn = QPushButton("📖 Docs")
        docs_btn.setStyleSheet(theme.get_button_style())
        docs_btn.setFixedWidth(100)
        docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://docs.claude.com/en/docs/claude-code/settings#permissions")
        ))

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(docs_btn)
        layout.addLayout(header_layout)

        # File path
        path_label = QLabel(f"File: {self.config_manager.settings_file}")
        path_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(path_label)

        # JSON Editor
        editor_label = QLabel("Permissions JSON:")
        editor_label.setStyleSheet(theme.get_label_style("normal", "secondary"))
        layout.addWidget(editor_label)

        self.editor = QTextEdit()
        self.editor.setStyleSheet(theme.get_text_edit_style())
        layout.addWidget(self.editor, 1)

        # Help text
        help_text = QLabel(
            '💡 <b>Format:</b> Use object format with allow/deny/ask arrays:<br>'
            '<code>{"allow": ["Read", "Write"], "deny": [], "ask": []}</code>'
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; "
            f"padding: 8px; "
            f"background-color: {theme.BG_MEDIUM}; "
            f"border-radius: 3px;"
        )
        layout.addWidget(help_text)

        # Buttons
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("💾 Save")
        save_btn.setStyleSheet(theme.get_button_style())
        save_btn.setFixedWidth(120)
        save_btn.clicked.connect(self.save_permissions)

        backup_save_btn = QPushButton("📦 Backup & Save")
        backup_save_btn.setStyleSheet(theme.get_button_style())
        backup_save_btn.setFixedWidth(160)
        backup_save_btn.clicked.connect(self.backup_and_save)

        revert_btn = QPushButton("Revert")
        revert_btn.setStyleSheet(theme.get_button_style())
        revert_btn.setFixedWidth(100)
        revert_btn.clicked.connect(self.load_permissions)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(backup_save_btn)
        btn_layout.addWidget(revert_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def load_permissions(self):
        """Load permissions from user settings"""
        try:
            settings = self.settings_manager.get_user_settings()
            permissions = settings.get("permissions", {"allow": [], "deny": [], "ask": []})

            # Format as JSON
            formatted = json.dumps(permissions, indent=2)
            self.editor.setPlainText(formatted)

        except Exception as e:
            print(f"Error loading permissions: {e}")
            # Don't show popup during init, just show empty editor
            self.editor.setPlainText('{\n  "allow": [],\n  "deny": [],\n  "ask": []\n}')

    def save_permissions(self):
        """Save permissions to user settings"""
        try:
            # Parse JSON
            permissions_json = self.editor.toPlainText()
            permissions = json.loads(permissions_json)

            # Validate format - should be object with allow/deny/ask keys
            if not isinstance(permissions, dict):
                raise ValueError("Permissions must be a JSON object")

            # Load current settings
            settings = self.settings_manager.get_user_settings()
            settings["permissions"] = permissions

            # Save
            self.settings_manager.save_settings(
                self.config_manager.settings_file,
                settings
            )

            QMessageBox.information(self, "Success", "Permissions saved!")
            self.load_permissions()

        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "JSON Error", f"Invalid JSON:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n{str(e)}")

    def backup_and_save(self):
        """Create backup then save"""
        try:
            # Create backup
            backup_path = self.backup_manager.create_backup(
                self.config_manager.settings_file,
                "user_permissions"
            )

            # Save
            self.save_permissions()

            QMessageBox.information(
                self,
                "Success",
                f"Backup created and permissions saved!\n\nBackup: {backup_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Backup Error", f"Failed to create backup:\n{str(e)}")
