"""
Project Permissions Sub-Tab - Full table UI with Shared/Local tabs
Copied from working permissions_tab.py implementation
Uses official Claude Code format: {"allow": [...], "deny": [...], "ask": [...]}
"""

import sys
import json
import re
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QComboBox, QFormLayout, QLineEdit, QDialogButtonBox,
    QCheckBox, QGroupBox, QTabWidget
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QColor

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme

# Import the same AddPermissionDialog from user_permissions_subtab
from tabs.user_permissions_subtab import AddPermissionDialog


class ProjectPermissionsSubTab(QWidget):
    """Project permissions tab with Shared/Local subtabs"""

    def __init__(self, config_manager, backup_manager, settings_manager, project_context):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.settings_manager = settings_manager
        self.project_context = project_context
        self.tables = {}
        self.init_ui()

        # Connect to project changes
        if self.project_context:
            self.project_context.project_changed.connect(self.on_project_changed)

            # If project already exists (auto-detected on startup), update label now
            if self.project_context.has_project():
                current_project = self.project_context.get_project()
                self.project_label.setText(f"Project: {current_project}")

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
        header_layout.addWidget(header)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Project info
        self.project_label = QLabel("No project selected")
        self.project_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(self.project_label)

        # Tabs for Shared and Local
        tabs = QTabWidget()
        tabs.setStyleSheet(theme.get_tab_widget_style())

        # Shared tab
        shared_widget = self.create_permissions_panel("shared")
        tabs.addTab(shared_widget, "📁 Shared (.claude/settings.json)")

        # Local tab
        local_widget = self.create_permissions_panel("local")
        tabs.addTab(local_widget, "🔒 Local (.claude/settings.local.json)")

        layout.addWidget(tabs, 1)

    def create_permissions_panel(self, scope: str) -> QWidget:
        """Create permissions panel for a scope"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # File path
        file_name = "settings.json" if scope == "shared" else "settings.local.json"
        path_label = QLabel(f"File: .claude/{file_name}")
        path_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(path_label)

        # Table
        perm_table = QTableWidget()
        perm_table.setColumnCount(3)
        perm_table.setHorizontalHeaderLabels(["Type", "Pattern", "Level"])
        perm_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        perm_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        perm_table.setStyleSheet(theme.get_table_style())
        layout.addWidget(perm_table, 1)

        # Buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Add")
        add_btn.setStyleSheet(theme.get_button_style())
        add_btn.setFixedWidth(100)
        add_btn.clicked.connect(lambda: self.add_permission(scope))

        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setStyleSheet(theme.get_button_style())
        edit_btn.setFixedWidth(100)
        edit_btn.clicked.connect(lambda: self.edit_permission(scope))

        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setStyleSheet(theme.get_button_style())
        delete_btn.setFixedWidth(100)
        delete_btn.clicked.connect(lambda: self.delete_permission(scope))

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet(theme.get_button_style())
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(lambda: self.refresh_permissions(scope))

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Store table reference
        self.tables[scope] = perm_table

        return panel

    def on_project_changed(self, project_path: Path):
        """Handle project change"""
        if project_path:
            self.project_label.setText(f"Project: {project_path}")
            self.load_all_permissions()
        else:
            self.project_label.setText("No project selected")
            for table in self.tables.values():
                table.setRowCount(0)

    def load_all_permissions(self):
        """Load permissions for both scopes"""
        self.load_permissions("shared")
        self.load_permissions("local")

    def refresh_permissions(self, scope: str):
        """Refresh permissions for a scope (clears cache and reloads from disk)"""
        if not self.project_context or not self.project_context.has_project():
            return

        # Clear cache for this project's settings files
        project_path = self.project_context.get_project()
        if scope == "shared":
            settings_path = project_path / ".claude" / "settings.json"
        else:
            settings_path = project_path / ".claude" / "settings.local.json"

        self.settings_manager.clear_cache(settings_path)

        # Reload from disk
        self.load_permissions(scope)

    def load_permissions(self, scope: str):
        """Load permissions for a scope"""
        if not self.project_context or not self.project_context.has_project():
            return

        try:
            project_path = self.project_context.get_project()
            table = self.tables[scope]
            table.setRowCount(0)

            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(project_path)
            else:
                settings = self.settings_manager.get_project_local_settings(project_path)

            permissions = settings.get("permissions", {"allow": [], "deny": [], "ask": []})

            # Handle corrupted format (array instead of object)
            if isinstance(permissions, list):
                print(f"Warning: {scope} permissions in wrong format (array). Converting to proper format.")
                permissions = {"allow": [], "deny": [], "ask": []}

            for level in ["allow", "deny", "ask"]:
                perms = permissions.get(level, [])
                for perm_string in perms:
                    perm_type, pattern = self.parse_permission_string(perm_string)
                    self.add_permission_to_table(table, perm_type, pattern, level)

        except Exception as e:
            print(f"Error loading {scope} permissions: {e}")

    def parse_permission_string(self, perm_string):
        """Parse permission string into type and pattern"""
        match = re.match(r'^(\w+)\((.*)\)$', perm_string)
        if match:
            tool = match.group(1)
            if tool in ["Read", "Write", "Edit"]:
                return "File Tool", perm_string
            elif tool == "Bash":
                return "Bash", perm_string
            elif tool == "WebFetch":
                return "WebFetch", perm_string
            else:
                return "Tool", perm_string

        if perm_string.startswith("mcp__"):
            return "MCP Tool", perm_string

        return "Tool", perm_string

    def add_permission_to_table(self, table, perm_type, pattern, level):
        """Add permission row to table"""
        row = table.rowCount()
        table.insertRow(row)

        type_item = QTableWidgetItem(perm_type)
        type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        table.setItem(row, 0, type_item)

        pattern_item = QTableWidgetItem(pattern)
        pattern_item.setFlags(pattern_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        table.setItem(row, 1, pattern_item)

        level_item = QTableWidgetItem(level.upper())
        level_item.setFlags(level_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        if level == "allow":
            level_item.setForeground(QColor(theme.SUCCESS_COLOR))
        elif level == "deny":
            level_item.setForeground(QColor(theme.ERROR_COLOR))
        else:
            level_item.setForeground(QColor(theme.WARNING_COLOR))

        table.setItem(row, 2, level_item)

    def add_permission(self, scope: str):
        """Add new permission"""
        if not self.project_context or not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        dialog = AddPermissionDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        perm_string = dialog.get_permission_string()
        level = dialog.get_permission_level()

        try:
            project_path = self.project_context.get_project()

            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(project_path)
                settings_file = project_path / ".claude" / "settings.json"
            else:
                settings = self.settings_manager.get_project_local_settings(project_path)
                settings_file = project_path / ".claude" / "settings.local.json"

            if "permissions" not in settings:
                settings["permissions"] = {"allow": [], "deny": [], "ask": []}

            permissions = settings["permissions"]
            if level not in permissions:
                permissions[level] = []

            permissions[level].append(perm_string)
            self.settings_manager.save_settings(settings_file, settings)
            self.load_permissions(scope)
            QMessageBox.information(self, "Success", f"{scope.capitalize()} permission added!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add permission:\n{str(e)}")

    def edit_permission(self, scope: str):
        """Edit selected permission"""
        if not self.project_context or not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        table = self.tables[scope]
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a permission to edit.")
            return

        perm_type = table.item(row, 0).text()
        pattern = table.item(row, 1).text()
        level = table.item(row, 2).text().lower()

        dialog = AddPermissionDialog(self, {'type': perm_type, 'pattern': pattern, 'level': level})
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        new_perm_string = dialog.get_permission_string()
        new_level = dialog.get_permission_level()

        try:
            project_path = self.project_context.get_project()

            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(project_path)
                settings_file = project_path / ".claude" / "settings.json"
            else:
                settings = self.settings_manager.get_project_local_settings(project_path)
                settings_file = project_path / ".claude" / "settings.local.json"

            permissions = settings.get("permissions", {"allow": [], "deny": [], "ask": []})

            # Remove old
            if pattern in permissions.get(level, []):
                permissions[level].remove(pattern)

            # Add new
            if new_level not in permissions:
                permissions[new_level] = []
            permissions[new_level].append(new_perm_string)

            settings["permissions"] = permissions
            self.settings_manager.save_settings(settings_file, settings)
            self.load_permissions(scope)
            QMessageBox.information(self, "Success", "Permission updated!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit permission:\n{str(e)}")

    def delete_permission(self, scope: str):
        """Delete selected permission"""
        if not self.project_context or not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        table = self.tables[scope]
        row = table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a permission to delete.")
            return

        pattern = table.item(row, 1).text()
        level = table.item(row, 2).text().lower()

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete permission: {pattern}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            project_path = self.project_context.get_project()

            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(project_path)
                settings_file = project_path / ".claude" / "settings.json"
            else:
                settings = self.settings_manager.get_project_local_settings(project_path)
                settings_file = project_path / ".claude" / "settings.local.json"

            permissions = settings.get("permissions", {"allow": [], "deny": [], "ask": []})

            if pattern in permissions.get(level, []):
                permissions[level].remove(pattern)

            settings["permissions"] = permissions
            self.settings_manager.save_settings(settings_file, settings)
            self.load_permissions(scope)
            QMessageBox.information(self, "Success", "Permission deleted!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete permission:\n{str(e)}")
