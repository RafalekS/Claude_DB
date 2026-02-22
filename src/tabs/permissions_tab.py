"""
Permissions Tab - Manage Claude Code permissions
Supports User settings, Project (Local) settings, and Project settings
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QMessageBox, QListWidget, QSplitter, QLineEdit,
    QFileDialog, QTabWidget, QDialog, QComboBox, QFormLayout,
    QDialogButtonBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import json
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme
from utils.ui_state_manager import UIStateManager
class AddPermissionDialog(QDialog):
    """Dialog for adding or editing a permission"""

    def __init__(self, parent=None, permission_data=None):
        super().__init__(parent)
        self.permission_data = permission_data  # For edit mode
        self.setWindowTitle("Edit Permission" if permission_data else "Add Permission")
        self.setMinimumWidth(600)
        self.init_ui()

    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Permission Type
        type_layout = QHBoxLayout()
        type_label = QLabel("Permission Type:")
        type_label.setStyleSheet(theme.get_label_style("normal", "primary"))
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Tool Permission",
            "File Path Permission",
            "Bash Command Permission",
            "WebFetch Domain Permission",
            "MCP Tool Permission"
        ])
        self.type_combo.setStyleSheet(theme.get_combo_style())
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo, 1)
        layout.addLayout(type_layout)

        # Dynamic form area
        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setSpacing(8)
        layout.addWidget(self.form_widget)

        # Create form fields
        self.create_form_fields()

        # Permission Level
        level_group = QGroupBox("Permission Level")
        level_group.setStyleSheet(theme.get_groupbox_style())
        level_layout = QHBoxLayout()

        self.allow_radio = QCheckBox("Allow")
        self.ask_radio = QCheckBox("Ask")
        self.deny_radio = QCheckBox("Deny")

        for radio in [self.allow_radio, self.ask_radio, self.deny_radio]:
            radio.setStyleSheet(f"color: {theme.FG_PRIMARY};")
            radio.toggled.connect(self.on_radio_toggled)
            level_layout.addWidget(radio)

        level_group.setLayout(level_layout)
        layout.addWidget(level_group)

        # Info label
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(self.info_label)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.setStyleSheet(theme.get_button_style())
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Set initial type
        self.on_type_changed(self.type_combo.currentText())

        # Pre-fill if editing
        if self.permission_data:
            self.load_permission_data()

    def on_radio_toggled(self):
        """Ensure only one radio button is checked"""
        sender = self.sender()
        if sender.isChecked():
            for radio in [self.allow_radio, self.ask_radio, self.deny_radio]:
                if radio != sender:
                    radio.setChecked(False)

    def create_form_fields(self):
        """Create all form fields"""
        # Tool name
        self.tool_name_edit = QLineEdit()
        self.tool_name_edit.setPlaceholderText("e.g., Read, Write, Bash")
        self.tool_name_edit.setStyleSheet(theme.get_line_edit_style())

        # File path pattern
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("e.g., /path/to/file.txt or /path/to/**")
        self.file_path_edit.setStyleSheet(theme.get_line_edit_style())

        # Bash command pattern
        self.bash_cmd_edit = QLineEdit()
        self.bash_cmd_edit.setPlaceholderText("e.g., ls:*, git status, python:*")
        self.bash_cmd_edit.setStyleSheet(theme.get_line_edit_style())

        # WebFetch domain
        self.domain_edit = QLineEdit()
        self.domain_edit.setPlaceholderText("e.g., github.com, api.example.com")
        self.domain_edit.setStyleSheet(theme.get_line_edit_style())

        # MCP tool
        self.mcp_tool_edit = QLineEdit()
        self.mcp_tool_edit.setPlaceholderText("e.g., mcp__server__tool_name")
        self.mcp_tool_edit.setStyleSheet(theme.get_line_edit_style())

    def on_type_changed(self, perm_type):
        """Update form based on selected permission type"""
        # Clear existing form
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().setVisible(False)

        # Add appropriate fields
        if perm_type == "Tool Permission":
            self.form_layout.addRow("Tool Name*:", self.tool_name_edit)
            self.tool_name_edit.setVisible(True)
            self.info_label.setText(
                "Tool permissions control which built-in tools Claude Code can use.\n"
                "Examples: Read, Write, Edit, Bash, WebFetch, Grep, Glob"
            )

        elif perm_type == "File Path Permission":
            self.form_layout.addRow("File Path Pattern*:", self.file_path_edit)
            self.file_path_edit.setVisible(True)
            self.info_label.setText(
                "File path permissions control access to specific files or directories.\n"
                "Use ** for wildcards: /path/to/** matches all files in directory"
            )

        elif perm_type == "Bash Command Permission":
            self.form_layout.addRow("Command Pattern*:", self.bash_cmd_edit)
            self.bash_cmd_edit.setVisible(True)
            self.info_label.setText(
                "Bash command permissions control which shell commands can be executed.\n"
                "Examples: 'ls:*' (allow all ls commands), 'git status' (specific command)"
            )

        elif perm_type == "WebFetch Domain Permission":
            self.form_layout.addRow("Domain*:", self.domain_edit)
            self.domain_edit.setVisible(True)
            self.info_label.setText(
                "WebFetch domain permissions control which domains can be accessed.\n"
                "Examples: github.com, api.example.com, *.mydomain.com"
            )

        elif perm_type == "MCP Tool Permission":
            self.form_layout.addRow("MCP Tool*:", self.mcp_tool_edit)
            self.mcp_tool_edit.setVisible(True)
            self.info_label.setText(
                "MCP tool permissions control which MCP server tools can be used.\n"
                "Format: mcp__<server>__<tool> (e.g., mcp__filesystem__read_file)"
            )

    def validate_and_accept(self):
        """Validate inputs before accepting"""
        perm_type = self.type_combo.currentText()

        # Check that at least one permission level is selected
        if not any([self.allow_radio.isChecked(), self.ask_radio.isChecked(), self.deny_radio.isChecked()]):
            QMessageBox.warning(self, "Validation Error", "Please select a permission level (Allow/Ask/Deny).")
            return

        # Check that required field is filled
        if perm_type == "Tool Permission" and not self.tool_name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Tool name is required.")
            return
        elif perm_type == "File Path Permission" and not self.file_path_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "File path pattern is required.")
            return
        elif perm_type == "Bash Command Permission" and not self.bash_cmd_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Command pattern is required.")
            return
        elif perm_type == "WebFetch Domain Permission" and not self.domain_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Domain is required.")
            return
        elif perm_type == "MCP Tool Permission" and not self.mcp_tool_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "MCP tool name is required.")
            return

        self.accept()

    def get_permission_data(self):
        """Return the permission data as a dictionary"""
        perm_type = self.type_combo.currentText()

        # Get permission level
        level = "ask"  # default
        if self.allow_radio.isChecked():
            level = "allow"
        elif self.deny_radio.isChecked():
            level = "deny"

        data = {
            "type": perm_type,
            "level": level
        }

        # Get value based on type
        if perm_type == "Tool Permission":
            data["tool"] = self.tool_name_edit.text().strip()
        elif perm_type == "File Path Permission":
            data["path"] = self.file_path_edit.text().strip()
        elif perm_type == "Bash Command Permission":
            data["command"] = self.bash_cmd_edit.text().strip()
        elif perm_type == "WebFetch Domain Permission":
            data["domain"] = self.domain_edit.text().strip()
        elif perm_type == "MCP Tool Permission":
            data["mcp_tool"] = self.mcp_tool_edit.text().strip()

        return data

    def load_permission_data(self):
        """Load existing permission data for editing"""
        if not self.permission_data:
            return

        perm_type = self.permission_data.get('type', '')
        pattern = self.permission_data.get('pattern', '')
        level = self.permission_data.get('level', 'ask')

        # Set permission level
        if level == 'allow':
            self.allow_radio.setChecked(True)
        elif level == 'deny':
            self.deny_radio.setChecked(True)
        else:
            self.ask_radio.setChecked(True)

        # Set type and pattern based on permission type
        if perm_type == "File Tool":
            self.type_combo.setCurrentText("Tool Permission")
            # Extract tool name from pattern like "Read(//c/...)"
            import re
            match = re.match(r'^(\w+)\((.*)\)$', pattern)
            if match:
                self.tool_name_edit.setText(match.group(1))
        elif perm_type == "Bash":
            self.type_combo.setCurrentText("Bash Command Permission")
            self.bash_cmd_edit.setText(pattern)
        elif perm_type == "WebFetch":
            self.type_combo.setCurrentText("WebFetch Domain Permission")
            # Extract domain from "domain:github.com"
            if pattern.startswith("domain:"):
                self.domain_edit.setText(pattern.replace("domain:", ""))
            else:
                self.domain_edit.setText(pattern)
        elif perm_type == "MCP Tool":
            self.type_combo.setCurrentText("MCP Tool Permission")
            self.mcp_tool_edit.setText(pattern)
        else:  # Tool
            self.type_combo.setCurrentText("Tool Permission")
            self.tool_name_edit.setText(pattern)


class PermissionsTab(QWidget):
    """Tab for managing Claude Code permissions"""

    def __init__(self, config_manager, backup_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.project_folder = Path.cwd()  # Default to current directory
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        header = QLabel("Permissions")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")

        header_layout.addWidget(header)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Main tab widget for User / Project (Local) / Project
        self.main_tabs = QTabWidget()
        self.main_tabs.setStyleSheet(theme.get_tab_widget_style())

        # User tab (~/.claude/settings.json)
        self.user_tab = self.create_permissions_editor("user")
        self.main_tabs.addTab(self.user_tab, "User (~/.claude/settings.json)")

        # Project (Local) tab (./.claude/settings.local.json)
        self.project_local_tab = self.create_permissions_editor_with_folder("project_local")
        self.main_tabs.addTab(self.project_local_tab, "Project (Local) (.claude/settings.local.json)")

        # Project tab (./.claude/settings.json)
        self.project_tab = self.create_permissions_editor_with_folder("project")
        self.main_tabs.addTab(self.project_tab, "Project (.claude/settings.json)")

        layout.addWidget(self.main_tabs)

        # Info tip
        tip_label = QLabel(
            "💡 <b>Permissions Best Practices:</b> "
            "Use 'ask' for sensitive operations • "
            "Use 'allow' for trusted, frequent operations • "
            "Use 'deny' to block dangerous operations • "
            "Workspace folders define trusted directories for file operations"
            "<br><b>Permission Hierarchy:</b> "
            "Project (Local) > Project > User (most specific wins)"
        )
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(tip_label)

    def create_permissions_editor(self, scope):
        """Create permissions editor for a specific scope (without folder picker)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # File path label
        settings_file = self.get_scope_settings_file(scope)
        path_label = QLabel(f"File: {settings_file}")
        path_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_SMALL}px; color: {theme.FG_SECONDARY};")
        layout.addWidget(path_label)

        # Store references for this scope
        if not hasattr(self, 'scope_widgets'):
            self.scope_widgets = {}

        self.scope_widgets[scope] = {'path_label': path_label}

        # Permissions content
        content = self.create_permissions_content(scope)
        layout.addWidget(content, 1)

        # Load initial data
        self.load_permissions(scope)

        return widget

    def create_permissions_editor_with_folder(self, scope):
        """Create permissions editor with folder picker for project scopes"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Project folder picker
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(5)

        folder_label = QLabel("Project Folder:")
        folder_label.setStyleSheet(f"color: {theme.FG_PRIMARY}; font-weight: bold;")

        project_folder_edit = QLineEdit()
        project_folder_edit.setText(str(Path.home()))
        project_folder_edit.setReadOnly(True)
        project_folder_edit.setStyleSheet(theme.get_line_edit_style())

        browse_folder_btn = QPushButton("Browse...")
        browse_folder_btn.setStyleSheet(theme.get_button_style())
        browse_folder_btn.setToolTip("Select a different project folder")
        browse_folder_btn.clicked.connect(lambda: self.browse_project_folder(scope))

        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(project_folder_edit, 1)
        folder_layout.addWidget(browse_folder_btn)

        layout.addLayout(folder_layout)

        # File path label
        settings_file = self.get_scope_settings_file(scope)
        path_label = QLabel(f"File: {settings_file}")
        path_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_SMALL}px; color: {theme.FG_SECONDARY};")
        layout.addWidget(path_label)

        # Store references for this scope
        if not hasattr(self, 'scope_widgets'):
            self.scope_widgets = {}

        self.scope_widgets[scope] = {
            'path_label': path_label,
            'folder_edit': project_folder_edit
        }

        # Permissions content
        content = self.create_permissions_content(scope)
        layout.addWidget(content, 1)

        # Load initial data
        self.load_permissions(scope)

        return widget

    def create_permissions_content(self, scope):
        """Create the main permissions content area"""
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top section - Permissions table
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(5)

        # Permissions label and buttons
        perm_header = QHBoxLayout()
        perm_label = QLabel("Permissions")
        perm_label.setStyleSheet(theme.get_label_style("normal", "primary"))

        add_perm_btn = QPushButton("Add")
        add_perm_btn.setToolTip("Add a new permission")
        edit_perm_btn = QPushButton("Edit")
        edit_perm_btn.setToolTip("Edit selected permission")
        refresh_perm_btn = QPushButton("Refresh")
        refresh_perm_btn.setToolTip("Reload permissions from file")
        del_perm_btn = QPushButton("Delete")
        del_perm_btn.setToolTip("Delete selected permission")

        for btn in [add_perm_btn, edit_perm_btn, refresh_perm_btn]:
            btn.setStyleSheet(theme.get_button_style())

        # Delete button with orange border
        del_perm_btn.setStyleSheet(theme.get_button_style() + f"""
            QPushButton {{
                border: 2px solid {theme.WARNING_COLOR};
            }}
        """)

        add_perm_btn.clicked.connect(lambda: self.add_permission(scope))
        edit_perm_btn.clicked.connect(lambda: self.edit_permission(scope))
        refresh_perm_btn.clicked.connect(lambda: self.load_permissions(scope))
        del_perm_btn.clicked.connect(lambda: self.delete_permission(scope))

        perm_header.addWidget(perm_label)
        perm_header.addStretch()
        perm_header.addWidget(add_perm_btn)
        perm_header.addWidget(edit_perm_btn)
        perm_header.addWidget(refresh_perm_btn)
        perm_header.addWidget(del_perm_btn)
        top_layout.addLayout(perm_header)

        # Permissions table
        perm_table = QTableWidget()
        perm_table.setColumnCount(3)
        perm_table.setHorizontalHeaderLabels(["Type", "Pattern", "Level"])
        perm_table.horizontalHeader().setStretchLastSection(False)
        perm_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        perm_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        perm_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        UIStateManager.instance().restore_table_state("permissions.user_table", perm_table)
        UIStateManager.instance().connect_table("permissions.user_table", perm_table)
        perm_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        perm_table.setStyleSheet(f"""
            QTableWidget {{
                background: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
            }}
            QTableWidget::item:selected {{
                background: {theme.ACCENT_PRIMARY};
                color: {theme.BG_DARK};
            }}
            QHeaderView::section {{
                background: {theme.BG_MEDIUM};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                padding: 5px;
                font-weight: bold;
            }}
        """)
        top_layout.addWidget(perm_table)

        splitter.addWidget(top_widget)

        # Bottom section - Workspace folders
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(5)

        # Workspace label and buttons
        workspace_header = QHBoxLayout()
        workspace_label = QLabel("Workspace Folders")
        workspace_label.setStyleSheet(theme.get_label_style("normal", "primary"))

        add_workspace_btn = QPushButton("Add Folder")
        add_workspace_btn.setToolTip("Add a folder to workspace")
        remove_workspace_btn = QPushButton("Remove")
        remove_workspace_btn.setToolTip("Remove selected workspace folder")

        add_workspace_btn.setStyleSheet(theme.get_button_style())
        remove_workspace_btn.setStyleSheet(theme.get_button_style() + f"""
            QPushButton {{
                border: 2px solid {theme.WARNING_COLOR};
            }}
        """)

        add_workspace_btn.clicked.connect(lambda: self.add_workspace_folder(scope))
        remove_workspace_btn.clicked.connect(lambda: self.remove_workspace_folder(scope))

        workspace_header.addWidget(workspace_label)
        workspace_header.addStretch()
        workspace_header.addWidget(add_workspace_btn)
        workspace_header.addWidget(remove_workspace_btn)
        bottom_layout.addLayout(workspace_header)

        # Workspace list
        workspace_list = QListWidget()
        workspace_list.setStyleSheet(theme.get_list_widget_style())
        bottom_layout.addWidget(workspace_list)

        splitter.addWidget(bottom_widget)
        splitter.setSizes([400, 200])

        # Store references
        self.scope_widgets[scope]['perm_table'] = perm_table
        self.scope_widgets[scope]['workspace_list'] = workspace_list

        return splitter

    def get_scope_settings_file(self, scope):
        """Get settings file path for the given scope"""
        if scope == "user":
            return self.config_manager.claude_dir / "settings.json"
        elif scope == "project_local":
            return self.project_folder / ".claude" / "settings.local.json"
        else:  # project
            return self.project_folder / ".claude" / "settings.json"

    def browse_project_folder(self, scope):
        """Browse for project folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Project Folder",
            str(Path.home())
        )
        if folder:
            self.project_folder = Path(folder)
            if 'folder_edit' in self.scope_widgets[scope]:
                self.scope_widgets[scope]['folder_edit'].setText(str(Path.home()))
            # Update path
            settings_file = self.get_scope_settings_file(scope)
            self.scope_widgets[scope]['path_label'].setText(f"File: {settings_file}")
            # Reload permissions from new folder
            self.load_permissions(scope)

    def load_permissions(self, scope):
        """Load permissions for the given scope"""
        try:
            settings_file = self.get_scope_settings_file(scope)

            perm_table = self.scope_widgets[scope]['perm_table']
            workspace_list = self.scope_widgets[scope]['workspace_list']

            perm_table.setRowCount(0)
            workspace_list.clear()

            if not settings_file.exists():
                return

            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            # Load permissions
            permissions = settings.get("permissions", {})

            # Process each level (allow, deny, ask)
            for level in ["allow", "deny", "ask"]:
                perms = permissions.get(level, [])
                for perm_string in perms:
                    perm_type, pattern = self.parse_permission_string(perm_string)
                    self.add_permission_to_table(perm_table, perm_type, pattern, level)

            # Load workspace folders
            workspace = settings.get("workspace", [])
            for folder in workspace:
                workspace_list.addItem(folder)

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load permissions:\n{str(e)}")

    def parse_permission_string(self, perm_string):
        """Parse a permission string into type and pattern"""
        import re

        # Check for function-style permissions: ToolName(pattern)
        match = re.match(r'^(\w+)\((.*)\)$', perm_string)
        if match:
            tool = match.group(1)
            pattern = match.group(2)

            # Determine type based on tool
            if tool in ["Read", "Write", "Edit", "Glob"]:
                return "File Tool", f"{tool}({pattern})"
            elif tool == "Bash":
                return "Bash", pattern
            elif tool == "WebFetch":
                return "WebFetch", pattern
            else:
                return "Tool", f"{tool}({pattern})"

        # Check for MCP tool permissions: mcp__server__tool
        if perm_string.startswith("mcp__"):
            return "MCP Tool", perm_string

        # Plain tool name
        return "Tool", perm_string

    def add_permission_to_table(self, table, perm_type, pattern, level):
        """Add a permission row to the table"""
        row = table.rowCount()
        table.insertRow(row)

        # Type
        type_item = QTableWidgetItem(perm_type)
        type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        table.setItem(row, 0, type_item)

        # Pattern
        pattern_item = QTableWidgetItem(pattern)
        pattern_item.setFlags(pattern_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        table.setItem(row, 1, pattern_item)

        # Level (with color coding)
        level_item = QTableWidgetItem(level.upper())
        level_item.setFlags(level_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        # Color code based on level
        if level == "allow":
            level_item.setForeground(QColor(theme.SUCCESS_COLOR))
        elif level == "deny":
            level_item.setForeground(QColor(theme.ERROR_COLOR))
        else:  # ask
            level_item.setForeground(QColor(theme.WARNING_COLOR))

        table.setItem(row, 2, level_item)

    def add_permission(self, scope):
        """Add a new permission"""
        dialog = AddPermissionDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        perm_data = dialog.get_permission_data()

        # TODO: Add permission to settings file
        QMessageBox.information(self, "Not Implemented", f"Permission add: {perm_data}")

    def edit_permission(self, scope):
        """Edit selected permission"""
        perm_table = self.scope_widgets[scope]['perm_table']
        current_row = perm_table.currentRow()

        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a permission to edit.")
            return

        # Get current permission data from table
        perm_type = perm_table.item(current_row, 0).text()
        pattern = perm_table.item(current_row, 1).text()
        level = perm_table.item(current_row, 2).text().lower()

        # Create permission data dict for dialog
        permission_data = {
            'type': perm_type,
            'pattern': pattern,
            'level': level
        }

        # Open dialog pre-filled with current data
        dialog = AddPermissionDialog(self, permission_data=permission_data)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        new_perm_data = dialog.get_permission_data()

        try:
            settings_file = self.get_scope_settings_file(scope)

            # Read current settings
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = {"permissions": {"allow": [], "deny": [], "ask": []}}

            permissions = settings.get("permissions", {"allow": [], "deny": [], "ask": []})

            # Remove old permission from its level
            old_perm_string = self.build_permission_string(perm_type, pattern)
            for lvl in ["allow", "deny", "ask"]:
                if old_perm_string in permissions.get(lvl, []):
                    permissions[lvl].remove(old_perm_string)
                    break

            # Add new permission to new level
            new_perm_string = self.build_permission_string_from_data(new_perm_data)
            new_level = new_perm_data['level']
            if new_level not in permissions:
                permissions[new_level] = []
            permissions[new_level].append(new_perm_string)

            # Save back to file
            settings['permissions'] = permissions

            # Backup first (only for user settings, not project settings)
            if settings_file.exists():
                if scope == "user":
                    self.backup_manager.create_file_backup(settings_file)
                else:
                    # For project files, create backup in same directory
                    import shutil
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_file = settings_file.parent / f"{settings_file.stem}_backup_{timestamp}{settings_file.suffix}"
                    shutil.copy2(settings_file, backup_file)

            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)

            # Reload table
            self.load_permissions(scope)

            QMessageBox.information(self, "Success", "Permission updated successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update permission:\n{str(e)}")

    def delete_permission(self, scope):
        """Delete selected permission"""
        perm_table = self.scope_widgets[scope]['perm_table']
        current_row = perm_table.currentRow()

        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a permission to delete.")
            return

        # Get permission data from table
        perm_type = perm_table.item(current_row, 0).text()
        pattern = perm_table.item(current_row, 1).text()
        level = perm_table.item(current_row, 2).text().lower()

        reply = QMessageBox.question(
            self, "Delete Permission",
            f"Are you sure you want to delete this permission?\n\nType: {perm_type}\nPattern: {pattern}\nLevel: {level.upper()}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                settings_file = self.get_scope_settings_file(scope)

                # Read current settings
                if not settings_file.exists():
                    QMessageBox.warning(self, "File Not Found", "Settings file does not exist.")
                    return

                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                permissions = settings.get("permissions", {"allow": [], "deny": [], "ask": []})

                # Build permission string and remove from its level
                perm_string = self.build_permission_string(perm_type, pattern)

                if perm_string in permissions.get(level, []):
                    permissions[level].remove(perm_string)
                else:
                    QMessageBox.warning(self, "Not Found", "Permission not found in settings file.")
                    return

                # Save back to file
                settings['permissions'] = permissions

                # Backup first (only for user settings, not project settings)
                if scope == "user":
                    self.backup_manager.create_file_backup(settings_file)
                else:
                    # For project files, create backup in same directory
                    import shutil
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_file = settings_file.parent / f"{settings_file.stem}_backup_{timestamp}{settings_file.suffix}"
                    shutil.copy2(settings_file, backup_file)

                with open(settings_file, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2)

                # Reload table
                self.load_permissions(scope)

                QMessageBox.information(self, "Success", "Permission deleted successfully!")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete permission:\n{str(e)}")

    def add_workspace_folder(self, scope):
        """Add a folder to workspace"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Workspace Folder",
            str(self.project_folder if scope != "user" else Path.home())
        )

        if folder:
            workspace_list = self.scope_widgets[scope]['workspace_list']
            workspace_list.addItem(folder)
            # TODO: Save to settings file

    def remove_workspace_folder(self, scope):
        """Remove selected workspace folder"""
        workspace_list = self.scope_widgets[scope]['workspace_list']
        current_item = workspace_list.currentItem()

        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a workspace folder to remove.")
            return

        reply = QMessageBox.question(
            self, "Remove Folder", f"Remove folder from workspace?\n{current_item.text()}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            workspace_list.takeItem(workspace_list.row(current_item))
            # TODO: Save to settings file

    def build_permission_string(self, perm_type, pattern):
        """Build permission string from type and pattern"""
        # Reconstruct original permission string from parsed data
        if perm_type == "File Tool":
            # Pattern is already like "Read(//c/...)"
            return pattern
        elif perm_type == "Bash":
            # Pattern is like "python:*", need to wrap in Bash()
            return f"Bash({pattern})"
        elif perm_type == "WebFetch":
            # Pattern might be "domain:github.com" or already formatted
            if not pattern.startswith("WebFetch("):
                return f"WebFetch({pattern})"
            return pattern
        elif perm_type == "MCP Tool":
            # Pattern is already the full MCP tool name
            return pattern
        else:  # Tool
            # Plain tool or already formatted
            return pattern

    def build_permission_string_from_data(self, perm_data):
        """Build permission string from permission data dict"""
        perm_type = perm_data['type']

        if perm_type == "Tool Permission":
            tool = perm_data.get('tool', '')
            return tool
        elif perm_type == "File Path Permission":
            path = perm_data.get('path', '')
            # Assume Read by default for file paths
            return f"Read({path})"
        elif perm_type == "Bash Command Permission":
            command = perm_data.get('command', '')
            return f"Bash({command})"
        elif perm_type == "WebFetch Domain Permission":
            domain = perm_data.get('domain', '')
            return f"WebFetch(domain:{domain})"
        elif perm_type == "MCP Tool Permission":
            mcp_tool = perm_data.get('mcp_tool', '')
            return mcp_tool

        return ""
