"""
Project Permissions Sub-Tab - Simple JSON editor for project permissions
Handles both shared (.claude/settings.json) and local (.claude/settings.local.json)
Uses object format {"allow": [...], "deny": [...], "ask": [...]} - the standard Claude Code format
"""

import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QTabWidget
)
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme


class ProjectPermissionsSubTab(QWidget):
    """Simple JSON editor for project-level permissions (Shared/Local)"""

    def __init__(self, config_manager, backup_manager, settings_manager, project_context):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.settings_manager = settings_manager
        self.project_context = project_context
        self.editors = {}
        self.init_ui()

        # Connect to project changes
        if self.project_context:
            self.project_context.project_changed.connect(self.on_project_changed)

        # Initial load
        self.load_all_permissions()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        header = QLabel("Project Permissions Configuration")
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

        # Project info
        self.project_label = QLabel("No project selected")
        self.project_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(self.project_label)

        # Tabs for Shared and Local
        tabs = QTabWidget()
        tabs.setStyleSheet(theme.get_tab_widget_style())

        # Shared tab
        shared_widget = self.create_editor_panel("shared")
        tabs.addTab(shared_widget, "📁 Shared (.claude/settings.json)")

        # Local tab
        local_widget = self.create_editor_panel("local")
        tabs.addTab(local_widget, "🔒 Local (.claude/settings.local.json)")

        layout.addWidget(tabs, 1)

    def create_editor_panel(self, scope: str) -> QWidget:
        """Create editor panel for a scope (shared or local)"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # File path
        file_name = "settings.json" if scope == "shared" else "settings.local.json"
        path_label = QLabel(f"File: .claude/{file_name}")
        path_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(path_label)

        # JSON Editor
        editor_label = QLabel("Permissions JSON:")
        editor_label.setStyleSheet(theme.get_label_style("normal", "secondary"))
        layout.addWidget(editor_label)

        editor = QTextEdit()
        editor.setStyleSheet(theme.get_text_edit_style())
        layout.addWidget(editor, 1)

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
        save_btn.clicked.connect(lambda: self.save_permissions(scope))

        backup_save_btn = QPushButton("📦 Backup & Save")
        backup_save_btn.setStyleSheet(theme.get_button_style())
        backup_save_btn.setFixedWidth(160)
        backup_save_btn.clicked.connect(lambda: self.backup_and_save(scope))

        revert_btn = QPushButton("Revert")
        revert_btn.setStyleSheet(theme.get_button_style())
        revert_btn.setFixedWidth(100)
        revert_btn.clicked.connect(lambda: self.load_permissions(scope))

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(backup_save_btn)
        btn_layout.addWidget(revert_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Store editor reference
        self.editors[scope] = editor

        return panel

    def on_project_changed(self, project_path: Path):
        """Handle project change"""
        if project_path:
            self.project_label.setText(f"Project: {project_path}")
            self.load_all_permissions()
        else:
            self.project_label.setText("No project selected")
            # Clear editors
            for editor in self.editors.values():
                editor.clear()

    def load_all_permissions(self):
        """Load permissions for both scopes"""
        self.load_permissions("shared")
        self.load_permissions("local")

    def load_permissions(self, scope: str):
        """Load permissions for a scope"""
        if not self.project_context or not self.project_context.has_project():
            return

        try:
            project_path = self.project_context.get_project()

            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(project_path)
            else:
                settings = self.settings_manager.get_project_local_settings(project_path)

            permissions = settings.get("permissions", {"allow": [], "deny": [], "ask": []})

            # Format as JSON
            formatted = json.dumps(permissions, indent=2)
            self.editors[scope].setPlainText(formatted)

        except Exception as e:
            print(f"Error loading {scope} permissions: {e}")
            # Don't show popup during init, just show empty editor
            self.editors[scope].setPlainText('{\n  "allow": [],\n  "deny": [],\n  "ask": []\n}')

    def save_permissions(self, scope: str):
        """Save permissions for a scope"""
        if not self.project_context or not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        try:
            project_path = self.project_context.get_project()

            # Parse JSON
            permissions_json = self.editors[scope].toPlainText()
            permissions = json.loads(permissions_json)

            # Validate format
            if not isinstance(permissions, dict):
                raise ValueError("Permissions must be a JSON object")

            # Get settings file path
            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(project_path)
                settings_file = project_path / ".claude" / "settings.json"
            else:
                settings = self.settings_manager.get_project_local_settings(project_path)
                settings_file = project_path / ".claude" / "settings.local.json"

            # Update permissions
            settings["permissions"] = permissions

            # Save
            self.settings_manager.save_settings(settings_file, settings)

            QMessageBox.information(self, "Success", f"{scope.capitalize()} permissions saved!")
            self.load_permissions(scope)

        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "JSON Error", f"Invalid JSON:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n{str(e)}")

    def backup_and_save(self, scope: str):
        """Create backup then save"""
        if not self.project_context or not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        try:
            project_path = self.project_context.get_project()

            # Get settings file path
            if scope == "shared":
                settings_file = project_path / ".claude" / "settings.json"
            else:
                settings_file = project_path / ".claude" / "settings.local.json"

            # Create backup
            backup_path = self.backup_manager.create_backup(
                settings_file,
                f"project_{scope}_permissions"
            )

            # Save
            self.save_permissions(scope)

            QMessageBox.information(
                self,
                "Success",
                f"Backup created and {scope} permissions saved!\n\nBackup: {backup_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Backup Error", f"Failed to create backup:\n{str(e)}")
