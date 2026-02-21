"""
User Permissions Sub-Tab - Full table UI with Add/Edit/Delete dialog
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
    QCheckBox, QGroupBox, QRadioButton
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QColor

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme



class AddPermissionDialog(QDialog):
    """Dialog for adding or editing a permission with improved UX"""

    # Tool definitions with patterns
    TOOLS = {
        "File Operations": {
            "Read": {
                "format": "Read(pattern)",
                "examples": ["**", "//c/Scripts/**", "//c/Users/r_sta/**", "*.py"],
                "placeholder": "//c/path/** or *.txt"
            },
            "Write": {
                "format": "Write(pattern)",
                "examples": ["**", "//c/Scripts/**", "//c/Users/r_sta/**", "*.txt"],
                "placeholder": "//c/path/** or *.txt"
            },
            "Edit": {
                "format": "Edit(pattern)",
                "examples": ["**", "//c/Scripts/**", "//c/Users/r_sta/**", "*.py"],
                "placeholder": "//c/path/** or *.py"
            },
            "NotebookEdit": {
                "format": "NotebookEdit(pattern)",
                "examples": ["**", "*.ipynb"],
                "placeholder": "*.ipynb or //c/notebooks/**"
            }
        },
        "Execution": {
            "Bash": {
                "format": "Bash(command:pattern)",
                "examples": ["*", "cat:*", "python:*", "git:*", "ls:*", "cd:*"],
                "placeholder": "command:* or just *"
            }
        },
        "Search": {
            "Glob": {
                "format": "Glob(pattern)",
                "examples": ["*", "**/*.py", "*.txt"],
                "placeholder": "**/*.py or *.txt"
            },
            "Grep": {
                "format": "Grep(pattern)",
                "examples": ["*"],
                "placeholder": "* for all patterns"
            }
        },
        "Web": {
            "WebFetch": {
                "format": "WebFetch(domain:pattern)",
                "examples": ["domain:*", "domain:github.com", "domain:*.anthropic.com", "domain:stackoverflow.com"],
                "placeholder": "domain:example.com"
            },
            "WebSearch": {
                "format": "WebSearch(pattern)",
                "examples": ["*"],
                "placeholder": "* for all searches"
            }
        },
        "System": {
            "Task": {
                "format": "Task(pattern)",
                "examples": ["*"],
                "placeholder": "* for all tasks"
            },
            "Skill": {
                "format": "Skill(pattern)",
                "examples": ["*"],
                "placeholder": "* for all skills"
            },
            "SlashCommand": {
                "format": "SlashCommand(pattern)",
                "examples": ["*", "/permissions", "/context"],
                "placeholder": "* or specific command"
            }
        },
        "MCP": {
            "MCP Tool": {
                "format": "mcp__server__tool",
                "examples": ["mcp__*", "mcp__gmail-imap__*"],
                "placeholder": "mcp__servername__toolname"
            }
        }
    }

    def __init__(self, parent=None, permission_data=None):
        super().__init__(parent)
        self.permission_data = permission_data
        self.setWindowTitle("Edit Permission" if permission_data else "Add Permission")
        self.setMinimumWidth(700)
        self.init_ui()

    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Advanced mode checkbox
        self.advanced_mode_cb = QCheckBox("Advanced Mode (Manual Entry)")
        self.advanced_mode_cb.setStyleSheet(f"color: {theme.FG_PRIMARY};")
        self.advanced_mode_cb.toggled.connect(self.toggle_advanced_mode)
        layout.addWidget(self.advanced_mode_cb)

        # === Simple Mode UI ===
        self.simple_widget = QWidget()
        simple_layout = QVBoxLayout(self.simple_widget)
        simple_layout.setContentsMargins(0, 0, 0, 0)

        # Category dropdown
        category_layout = QHBoxLayout()
        category_label = QLabel("Category:")
        category_label.setStyleSheet(theme.get_label_style("normal", "primary"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(list(self.TOOLS.keys()))
        self.category_combo.setStyleSheet(theme.get_combo_style())
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        category_layout.addWidget(category_label, 0)
        category_layout.addWidget(self.category_combo, 1)
        simple_layout.addLayout(category_layout)

        # Tool dropdown
        tool_layout = QHBoxLayout()
        tool_label = QLabel("Tool:")
        tool_label.setStyleSheet(theme.get_label_style("normal", "primary"))
        self.tool_combo = QComboBox()
        self.tool_combo.setStyleSheet(theme.get_combo_style())
        self.tool_combo.currentTextChanged.connect(self.on_tool_changed)
        tool_layout.addWidget(tool_label, 0)
        tool_layout.addWidget(self.tool_combo, 1)
        simple_layout.addLayout(tool_layout)

        # Pattern field
        pattern_layout = QHBoxLayout()
        pattern_label = QLabel("Pattern:")
        pattern_label.setStyleSheet(theme.get_label_style("normal", "primary"))
        self.pattern_edit = QLineEdit()
        self.pattern_edit.setStyleSheet(theme.get_line_edit_style())
        pattern_layout.addWidget(pattern_label, 0)
        pattern_layout.addWidget(self.pattern_edit, 1)
        simple_layout.addLayout(pattern_layout)

        # Common patterns group
        self.patterns_group = QGroupBox("Common Patterns (click to use)")
        self.patterns_group.setStyleSheet(theme.get_groupbox_style())
        self.patterns_layout = QHBoxLayout()
        self.patterns_layout.setSpacing(5)
        self.patterns_group.setLayout(self.patterns_layout)
        simple_layout.addWidget(self.patterns_group)

        # Info label
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; "
            f"background: {theme.BG_MEDIUM}; "
            f"padding: 8px; "
            f"border-radius: 3px; "
            f"font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        simple_layout.addWidget(self.info_label)

        layout.addWidget(self.simple_widget)

        # === Advanced Mode UI ===
        self.advanced_widget = QWidget()
        advanced_layout = QVBoxLayout(self.advanced_widget)
        advanced_layout.setContentsMargins(0, 0, 0, 0)

        adv_label = QLabel("Full Permission String:")
        adv_label.setStyleSheet(theme.get_label_style("normal", "primary"))
        advanced_layout.addWidget(adv_label)

        self.advanced_edit = QLineEdit()
        self.advanced_edit.setPlaceholderText("e.g., Read(//c/Scripts/**) or Bash(cat:*)")
        self.advanced_edit.setStyleSheet(theme.get_line_edit_style())
        advanced_layout.addWidget(self.advanced_edit)

        adv_info = QLabel("Enter the full permission string manually. Format: Tool(pattern)")
        adv_info.setWordWrap(True)
        adv_info.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        advanced_layout.addWidget(adv_info)

        layout.addWidget(self.advanced_widget)
        self.advanced_widget.setVisible(False)

        # Permission Level
        level_group = QGroupBox("Permission Level")
        level_group.setStyleSheet(theme.get_groupbox_style())
        level_layout = QHBoxLayout()

        self.allow_radio = QRadioButton("Allow")
        self.ask_radio = QRadioButton("Ask")
        self.deny_radio = QRadioButton("Deny")

        for radio in [self.allow_radio, self.ask_radio, self.deny_radio]:
            radio.setStyleSheet(f"color: {theme.FG_PRIMARY};")
            level_layout.addWidget(radio)

        self.allow_radio.setChecked(True)  # Default to Allow

        level_group.setLayout(level_layout)
        layout.addWidget(level_group)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.setStyleSheet(theme.get_button_style())
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Initialize
        self.on_category_changed(self.category_combo.currentText())

        # Pre-fill if editing
        if self.permission_data:
            self.load_permission_data()

    def toggle_advanced_mode(self, checked):
        """Toggle between simple and advanced mode"""
        self.simple_widget.setVisible(not checked)
        self.advanced_widget.setVisible(checked)

    def on_category_changed(self, category):
        """Update tool dropdown when category changes"""
        self.tool_combo.clear()
        if category in self.TOOLS:
            self.tool_combo.addItems(list(self.TOOLS[category].keys()))

    def on_tool_changed(self, tool):
        """Update pattern field and common patterns when tool changes"""
        category = self.category_combo.currentText()
        if category not in self.TOOLS or tool not in self.TOOLS[category]:
            return

        tool_info = self.TOOLS[category][tool]

        # Update placeholder
        self.pattern_edit.setPlaceholderText(tool_info.get("placeholder", ""))

        # Update info label
        self.info_label.setText(f"Format: {tool_info.get('format', '')}")

        # Clear and populate common patterns
        while self.patterns_layout.count():
            item = self.patterns_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        examples = tool_info.get("examples", [])
        for example in examples:
            btn = QPushButton(example)
            btn.setStyleSheet(theme.get_button_style())
            btn.setFixedHeight(25)
            btn.clicked.connect(lambda checked, text=example: self.pattern_edit.setText(text))
            self.patterns_layout.addWidget(btn)

        self.patterns_layout.addStretch()

    def validate_and_accept(self):
        """Validate inputs before accepting"""
        if self.advanced_mode_cb.isChecked():
            if not self.advanced_edit.text().strip():
                QMessageBox.warning(self, "Validation Error", "Permission string is required.")
                return
        else:
            if not self.pattern_edit.text().strip():
                QMessageBox.warning(self, "Validation Error", "Pattern is required.")
                return

        if not any([self.allow_radio.isChecked(), self.ask_radio.isChecked(), self.deny_radio.isChecked()]):
            QMessageBox.warning(self, "Validation Error", "Please select a permission level.")
            return

        self.accept()

    def get_permission_string(self):
        """Return the permission string in Claude Code format"""
        if self.advanced_mode_cb.isChecked():
            return self.advanced_edit.text().strip()

        category = self.category_combo.currentText()
        tool = self.tool_combo.currentText()
        pattern = self.pattern_edit.text().strip()

        if category == "MCP":
            return pattern  # MCP tools don't use Tool(pattern) format
        else:
            return f"{tool}({pattern})"

    def get_permission_level(self):
        """Get selected permission level"""
        if self.allow_radio.isChecked():
            return "allow"
        elif self.deny_radio.isChecked():
            return "deny"
        else:
            return "ask"

    def load_permission_data(self):
        """Load existing permission for editing"""
        if not self.permission_data:
            return

        pattern = self.permission_data.get('pattern', '')
        level = self.permission_data.get('level', 'ask')

        # Set level
        if level == 'allow':
            self.allow_radio.setChecked(True)
        elif level == 'deny':
            self.deny_radio.setChecked(True)
        else:
            self.ask_radio.setChecked(True)

        # Parse pattern
        match = re.match(r'^(\w+)\((.*)\)$', pattern)
        if match:
            tool = match.group(1)
            param = match.group(2)

            # Find category for this tool
            found = False
            for cat_name, tools in self.TOOLS.items():
                if tool in tools:
                    self.category_combo.setCurrentText(cat_name)
                    self.tool_combo.setCurrentText(tool)
                    self.pattern_edit.setText(param)
                    found = True
                    break

            if not found:
                # Use advanced mode for unknown tools
                self.advanced_mode_cb.setChecked(True)
                self.advanced_edit.setText(pattern)
        elif pattern.startswith("mcp__"):
            # MCP tool
            self.category_combo.setCurrentText("MCP")
            self.tool_combo.setCurrentText("MCP Tool")
            self.pattern_edit.setText(pattern)
        else:
            # Unknown format, use advanced mode
            self.advanced_mode_cb.setChecked(True)
            self.advanced_edit.setText(pattern)


class UserPermissionsSubTab(QWidget):
    """User permissions tab with table UI"""

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
        header_layout.addWidget(header)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # File path
        path_label = QLabel(f"File: {self.config_manager.settings_file}")
        path_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(path_label)

        # Table
        self.perm_table = QTableWidget()
        self.perm_table.setColumnCount(3)
        self.perm_table.setHorizontalHeaderLabels(["Type", "Pattern", "Level"])
        self.perm_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.perm_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.perm_table.setStyleSheet(theme.get_table_style())
        layout.addWidget(self.perm_table, 1)

        # Buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Add")
        add_btn.setStyleSheet(theme.get_button_style())
        add_btn.setFixedWidth(100)
        add_btn.clicked.connect(self.add_permission)

        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setStyleSheet(theme.get_button_style())
        edit_btn.setFixedWidth(100)
        edit_btn.clicked.connect(self.edit_permission)

        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setStyleSheet(theme.get_button_style())
        delete_btn.setFixedWidth(100)
        delete_btn.clicked.connect(self.delete_permission)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet(theme.get_button_style())
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self.refresh_permissions)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def refresh_permissions(self):
        """Refresh permissions (clears cache and reloads from disk)"""
        # Clear cache for user settings
        self.settings_manager.clear_cache(self.settings_manager.user_settings_path)

        # Reload from disk
        self.load_permissions()

    def load_permissions(self):
        """Load permissions from user settings"""
        try:
            self.perm_table.setRowCount(0)
            settings = self.settings_manager.get_user_settings()
            permissions = settings.get("permissions", {"allow": [], "deny": [], "ask": []})

            # Handle corrupted format (array instead of object)
            if isinstance(permissions, list):
                print(f"Warning: User permissions in wrong format (array). Converting to proper format.")
                permissions = {"allow": [], "deny": [], "ask": []}

            for level in ["allow", "deny", "ask"]:
                perms = permissions.get(level, [])
                for perm_string in perms:
                    perm_type, pattern = self.parse_permission_string(perm_string)
                    self.add_permission_to_table(perm_type, pattern, level)

        except Exception as e:
            print(f"Error loading permissions: {e}")

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

    def add_permission_to_table(self, perm_type, pattern, level):
        """Add permission row to table"""
        row = self.perm_table.rowCount()
        self.perm_table.insertRow(row)

        type_item = QTableWidgetItem(perm_type)
        type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.perm_table.setItem(row, 0, type_item)

        pattern_item = QTableWidgetItem(pattern)
        pattern_item.setFlags(pattern_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.perm_table.setItem(row, 1, pattern_item)

        level_item = QTableWidgetItem(level.upper())
        level_item.setFlags(level_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        if level == "allow":
            level_item.setForeground(QColor(theme.SUCCESS_COLOR))
        elif level == "deny":
            level_item.setForeground(QColor(theme.ERROR_COLOR))
        else:
            level_item.setForeground(QColor(theme.WARNING_COLOR))

        self.perm_table.setItem(row, 2, level_item)

    def add_permission(self):
        """Add new permission"""
        dialog = AddPermissionDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        perm_string = dialog.get_permission_string()
        level = dialog.get_permission_level()

        try:
            settings = self.settings_manager.get_user_settings()
            if "permissions" not in settings:
                settings["permissions"] = {"allow": [], "deny": [], "ask": []}

            permissions = settings["permissions"]
            if level not in permissions:
                permissions[level] = []

            permissions[level].append(perm_string)
            self.settings_manager.save_settings(self.config_manager.settings_file, settings)
            self.load_permissions()
            QMessageBox.information(self, "Success", "Permission added!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add permission:\n{str(e)}")

    def edit_permission(self):
        """Edit selected permission"""
        row = self.perm_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a permission to edit.")
            return

        perm_type = self.perm_table.item(row, 0).text()
        pattern = self.perm_table.item(row, 1).text()
        level = self.perm_table.item(row, 2).text().lower()

        dialog = AddPermissionDialog(self, {'type': perm_type, 'pattern': pattern, 'level': level})
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        new_perm_string = dialog.get_permission_string()
        new_level = dialog.get_permission_level()

        try:
            settings = self.settings_manager.get_user_settings()
            permissions = settings.get("permissions", {"allow": [], "deny": [], "ask": []})

            # Remove old
            if pattern in permissions.get(level, []):
                permissions[level].remove(pattern)

            # Add new
            if new_level not in permissions:
                permissions[new_level] = []
            permissions[new_level].append(new_perm_string)

            settings["permissions"] = permissions
            self.settings_manager.save_settings(self.config_manager.settings_file, settings)
            self.load_permissions()
            QMessageBox.information(self, "Success", "Permission updated!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit permission:\n{str(e)}")

    def delete_permission(self):
        """Delete selected permission"""
        row = self.perm_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a permission to delete.")
            return

        pattern = self.perm_table.item(row, 1).text()
        level = self.perm_table.item(row, 2).text().lower()

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete permission: {pattern}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            settings = self.settings_manager.get_user_settings()
            permissions = settings.get("permissions", {"allow": [], "deny": [], "ask": []})

            if pattern in permissions.get(level, []):
                permissions[level].remove(pattern)

            settings["permissions"] = permissions
            self.settings_manager.save_settings(self.config_manager.settings_file, settings)
            self.load_permissions()
            QMessageBox.information(self, "Success", "Permission deleted!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete permission:\n{str(e)}")
