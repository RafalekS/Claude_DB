"""
Permissions Subtab - Manage Claude Code permissions
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QMessageBox, QListWidget, QSplitter, QLineEdit, QInputDialog
)
from PyQt6.QtCore import Qt
import sys
import json
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.theme import *


class PermissionsSubtab(QWidget):
    """Subtab for managing Claude Code permissions (single-scope)"""

    def __init__(self, config_manager, backup_manager, scope, project_context=None):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.scope = scope
        self.project_context = project_context

        # Validate parameters
        if scope == "project" and not project_context:
            raise ValueError("project_context is required when scope='project'")

        self.init_ui()

        # Connect to project changes if project scope
        if self.scope == "project" and self.project_context:
            self.project_context.project_changed.connect(self.on_project_changed)

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        scope_label = "User" if self.scope == "user" else "Project"
        header = QLabel(f"Permissions ({scope_label})")
        header.setStyleSheet(f"font-size: {FONT_SIZE_LARGE}px; font-weight: bold; color: {ACCENT_PRIMARY};")

        header_layout.addWidget(header)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Permissions editor for current scope
        editor_widget = self.create_permissions_editor()
        layout.addWidget(editor_widget, 1)

        # Info tip
        tip_label = QLabel(
            "💡 <b>Permissions:</b> Control tool access and auto-approval patterns. "
            "Define allow/deny rules for Bash, Read, Write, and other tools. "
            "User permissions (~/.claude/permissions/) apply globally. "
            "Project permissions (./.claude/permissions/) are shared via git. "
            "Each permission is a JSON file with description and permissions configuration."
        )
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet(f"color: {FG_SECONDARY}; background: {BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {FONT_SIZE_SMALL}px;")
        layout.addWidget(tip_label)

    def create_permissions_editor(self):
        """Create permissions editor for the current scope"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # File path label
        permissions_dir = self.get_scope_permissions_dir()
        path_label = QLabel(f"Directory: {permissions_dir}")
        path_label.setStyleSheet(f"font-size: {FONT_SIZE_SMALL}px; color: {FG_SECONDARY};")
        layout.addWidget(path_label)

        # Store references
        self.path_label = path_label
        self.current_permission = None

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - permission list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        # Search
        search_box = QLineEdit()
        search_box.setPlaceholderText("Search...")
        search_box.textChanged.connect(self.filter_permissions)
        search_box.setStyleSheet(get_line_edit_style())
        left_layout.addWidget(search_box)

        # Permission list
        permission_list = QListWidget()
        permission_list.itemClicked.connect(self.load_permission_content)
        permission_list.setStyleSheet(get_list_widget_style())
        left_layout.addWidget(permission_list)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        new_btn = QPushButton("➕ New")
        new_btn.setToolTip("Create a new permission")
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setToolTip("Load selected permission for editing")
        del_btn = QPushButton("🗑️ Delete")
        del_btn.setToolTip("Delete the selected permission")
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setToolTip("Reload the permissions list")

        for btn in [new_btn, edit_btn, del_btn, refresh_btn]:
            btn.setStyleSheet(get_button_style())

        new_btn.clicked.connect(self.create_new_permission)
        edit_btn.clicked.connect(self.edit_permission)
        del_btn.clicked.connect(self.delete_permission)
        refresh_btn.clicked.connect(self.load_permissions)

        btn_layout.addWidget(new_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(refresh_btn)
        left_layout.addLayout(btn_layout)

        splitter.addWidget(left_panel)

        # Right panel - editor
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)

        # Editor buttons
        editor_btn_layout = QHBoxLayout()
        editor_btn_layout.setSpacing(5)

        permission_name_label = QLabel("No permission selected")
        permission_name_label.setStyleSheet(get_label_style("normal", "secondary"))

        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip("Save the current permission to file")
        backup_save_btn = QPushButton("📦 Backup & Save")
        backup_save_btn.setToolTip("Create timestamped backup before saving permission")
        revert_btn = QPushButton("Revert")
        revert_btn.setToolTip("Revert to saved version (discards unsaved changes)")

        for btn in [save_btn, backup_save_btn, revert_btn]:
            btn.setStyleSheet(get_button_style())

        save_btn.clicked.connect(self.save_permission)
        backup_save_btn.clicked.connect(self.backup_and_save_permission)
        revert_btn.clicked.connect(self.revert_permission)

        editor_btn_layout.addWidget(permission_name_label)
        editor_btn_layout.addStretch()
        editor_btn_layout.addWidget(save_btn)
        editor_btn_layout.addWidget(backup_save_btn)
        editor_btn_layout.addWidget(revert_btn)
        right_layout.addLayout(editor_btn_layout)

        # JSON Editor
        permission_editor = QTextEdit()
        permission_editor.setStyleSheet(get_text_edit_style())
        permission_editor.setPlaceholderText("Select a permission to edit or create a new one...")
        right_layout.addWidget(permission_editor)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 1000])

        layout.addWidget(splitter, 1)

        # Store references
        self.search_box = search_box
        self.permission_list = permission_list
        self.permission_name_label = permission_name_label
        self.permission_editor = permission_editor

        # Load initial data
        self.load_permissions()

        return widget

    def get_scope_permissions_dir(self):
        """Get permissions directory for the current scope"""
        if self.scope == "user":
            return Path.home() / ".claude" / "permissions"
        else:  # project
            if not self.project_context.has_project():
                return None
            return self.project_context.get_project() / ".claude" / "permissions"

    def on_project_changed(self, project_path: Path):
        """Handle project context change"""
        # Update path label
        permissions_dir = self.get_scope_permissions_dir()
        if permissions_dir:
            self.path_label.setText(f"Directory: {permissions_dir}")
        # Reload permissions from new project
        self.load_permissions()

    def load_permissions(self):
        """Load all permissions for the current scope"""
        try:
            self.permission_list.clear()

            permissions_dir = self.get_scope_permissions_dir()

            if not permissions_dir or not permissions_dir.exists():
                return

            # List all .json files in permissions directory
            permissions = list(permissions_dir.glob("*.json"))
            for permission_path in sorted(permissions):
                # Show just the filename
                self.permission_list.addItem(permission_path.name)

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load permissions:\n{str(e)}")

    def filter_permissions(self, text):
        """Filter permissions based on search text"""
        for i in range(self.permission_list.count()):
            item = self.permission_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def load_permission_content(self, item):
        """Load content of selected permission"""
        try:
            permission_name = item.text()
            permissions_dir = self.get_scope_permissions_dir()
            permission_path = permissions_dir / permission_name

            if permission_path.exists():
                with open(permission_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Validate and pretty-print JSON
                    try:
                        json_data = json.loads(content)
                        content = json.dumps(json_data, indent=2)
                    except json.JSONDecodeError:
                        pass  # Keep original if invalid JSON

                self.current_permission = permission_path
                self.permission_name_label.setText(f"Editing: {permission_name}")
                self.permission_editor.setPlainText(content)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load permission:\n{str(e)}")

    def edit_permission(self):
        """Load selected permission for editing"""
        current_item = self.permission_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a permission to edit.")
            return
        self.load_permission_content(current_item)

    def save_permission(self):
        """Save current permission with JSON validation"""
        if not self.current_permission:
            QMessageBox.warning(self, "No Permission Selected", "Please select a permission to save.")
            return
        try:
            content = self.permission_editor.toPlainText()

            # Validate JSON
            try:
                json_data = json.loads(content)
                # Pretty-print it
                content = json.dumps(json_data, indent=2)
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Invalid JSON", f"JSON validation failed:\n{str(e)}")
                return

            with open(self.current_permission, 'w', encoding='utf-8') as f:
                f.write(content)

            # Update editor with formatted JSON
            self.permission_editor.setPlainText(content)
            QMessageBox.information(self, "Save Success", "Permission saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save permission:\n{str(e)}")

    def backup_and_save_permission(self):
        """Backup and save current permission"""
        if not self.current_permission:
            QMessageBox.warning(self, "No Permission Selected", "Please select a permission to save.")
            return
        try:
            # Validate JSON first
            content = self.permission_editor.toPlainText()
            try:
                json_data = json.loads(content)
                content = json.dumps(json_data, indent=2)
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Invalid JSON", f"JSON validation failed:\n{str(e)}")
                return

            self.backup_manager.create_file_backup(self.current_permission)
            with open(self.current_permission, 'w', encoding='utf-8') as f:
                f.write(content)

            # Update editor with formatted JSON
            self.permission_editor.setPlainText(content)
            QMessageBox.information(self, "Backup & Save Success", "Backup created and permission saved!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to backup and save:\n{str(e)}")

    def revert_permission(self):
        """Revert permission to saved version"""
        if not self.current_permission:
            return
        reply = QMessageBox.question(
            self, "Revert Changes", "Are you sure you want to revert to the saved version?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with open(self.current_permission, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.permission_editor.setPlainText(content)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to revert:\n{str(e)}")

    def create_new_permission(self):
        """Create a new permission"""
        name, ok = QInputDialog.getText(
            self,
            "New Permission",
            "Enter permission name (without .json extension):"
        )
        if ok and name:
            # Clean up the name
            name = name.strip()
            if not name.endswith('.json'):
                name += '.json'

            permissions_dir = self.get_scope_permissions_dir()
            permissions_dir.mkdir(parents=True, exist_ok=True)
            permission_path = permissions_dir / name

            if permission_path.exists():
                QMessageBox.warning(self, "Permission Exists", f"Permission '{name}' already exists.")
                return
            try:
                # Get just the filename for the template
                permission_name = Path(name).stem

                template = {
                    "description": f"Permission: {permission_name}",
                    "permissions": {
                        "allow": [
                            "Bash(ls:*)",
                            "Bash(git status)",
                            "Read(*.py)"
                        ]
                    }
                }

                with open(permission_path, 'w', encoding='utf-8') as f:
                    json.dump(template, f, indent=2)

                self.load_permissions()
                QMessageBox.information(self, "Permission Created", f"Permission '{name}' created successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create permission:\n{str(e)}")

    def delete_permission(self):
        """Delete selected permission"""
        if not self.current_permission:
            QMessageBox.warning(self, "No Permission Selected", "Please select a permission to delete.")
            return
        reply = QMessageBox.question(
            self, "Delete Permission", f"Are you sure you want to delete:\n{self.current_permission.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.current_permission.unlink()
                self.permission_editor.clear()
                self.permission_name_label.setText("No permission selected")
                self.current_permission = None
                self.load_permissions()
                QMessageBox.information(self, "Delete Success", "Permission deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete permission:\n{str(e)}")
