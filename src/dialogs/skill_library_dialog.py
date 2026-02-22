"""Skill Library Dialog - manages skill templates"""

import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QCheckBox, QWidget, QDialogButtonBox, QInputDialog,
    QLineEdit, QFormLayout, QTextEdit, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme
from utils.template_manager import get_template_manager
from dialogs.base_library_dialog import BaseLibraryDialog

# Load AVAILABLE_TOOLS from config, fall back to defaults
_config_file = Path(__file__).parent.parent.parent / "config" / "config.json"
try:
    with open(_config_file) as f:
        _app_config = json.load(f)
    AVAILABLE_TOOLS = _app_config.get("claude_tools", {}).get("available_tools", [
        "Read", "Write", "Edit", "MultiEdit", "Grep", "Glob", "Bash",
        "WebFetch", "WebSearch", "Task", "TodoWrite", "NotebookEdit",
        "AskUserQuestion", "Skill", "SlashCommand"
    ])
except Exception:
    AVAILABLE_TOOLS = [
        "Read", "Write", "Edit", "MultiEdit", "Grep", "Glob", "Bash",
        "WebFetch", "WebSearch", "Task", "TodoWrite", "NotebookEdit",
        "AskUserQuestion", "Skill", "SlashCommand"
    ]


class SkillLibraryDialog(BaseLibraryDialog):
    """Dialog for managing skill templates in config/templates/skills/"""

    def get_template_type(self):
        return 'skills'

    def get_dialog_title(self):
        return "Skill Library"

    def get_header_text(self):
        return "Skill Library - Manage and deploy skill templates"

    def get_info_text(self):
        return "Select skills to deploy, then click OK. You can also drop .md files directly into the templates folder."

    def get_bulk_add_class(self):
        from dialogs.bulk_skill_add_dialog import BulkSkillAddDialog
        return BulkSkillAddDialog

    def load_templates(self):
        """Load all templates and organise by folder"""
        self.templates = {}
        self.folders = set()
        template_names = self.template_mgr.list_templates('skills')
        for name in template_names:
            try:
                content = self.template_mgr.read_template('skills', name)
                info = self.template_mgr.get_template_info('skills', name)
                description = info.get('description', 'No description') if info else 'No description'
                self.templates[name] = {'content': content, 'description': description}
                if '/' in name:
                    self.folders.add(name.split('/')[0])
            except Exception as e:
                print(f"Error loading template {name}: {e}")

    def populate_table(self):
        """Populate table based on current folder"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self._update_nav()

        items_to_show = []
        if not self.current_folder:
            for folder in sorted(self.folders):
                items_to_show.append(('folder', folder, ''))
            for name in sorted(self.templates.keys()):
                if '/' not in name:
                    desc = self.templates[name].get('description', 'No description')
                    items_to_show.append(('template', name, desc))
        else:
            prefix = self.current_folder + '/'
            for name in sorted(self.templates.keys()):
                if name.startswith(prefix):
                    template_name = name[len(prefix):]
                    if '/' not in template_name:
                        desc = self.templates[name].get('description', 'No description')
                        items_to_show.append(('template', name, desc))

        self.table.setRowCount(len(items_to_show))
        for row, (item_type, name, description) in enumerate(items_to_show):
            self._set_table_row(row, item_type, name, description)

        self.table.setSortingEnabled(True)
        self.table.sortItems(1, Qt.SortOrder.AscendingOrder)

    def get_selected_items(self):
        """Get selected templates (not folders) as list of (name, content)"""
        selected = []
        for row in range(self.table.rowCount()):
            icon_item = self.table.item(row, 0)
            name_item = self.table.item(row, 1)
            if name_item and name_item.isSelected():
                if icon_item and icon_item.data(Qt.ItemDataRole.UserRole) == 'template':
                    full_name = name_item.data(Qt.ItemDataRole.UserRole)
                    if full_name in self.templates:
                        selected.append((full_name, self.templates[full_name]['content']))
        return selected

    # Keep old name for backward compatibility
    def get_selected_skills(self):
        return self.get_selected_items()

    def add_template(self):
        """Add a new template"""
        dialog = NewSkillTemplateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            template_data = dialog.get_template_data()
            try:
                content = f"""---
name: {template_data['name']}
description: {template_data['description']}
allowed-tools: {template_data['allowed_tools']}
---

# {template_data['name']}

{template_data['description']}

## Usage

How to use this skill.
"""
                full_name = (f"{self.current_folder}/{template_data['name']}"
                             if self.current_folder else template_data['name'])
                self.template_mgr.save_template('skills', full_name, content)
                self.refresh_templates()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save template:\n{str(e)}")

    def edit_template(self):
        """Edit selected template with form dialog"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a template to edit.")
            return

        row = selected_rows[0].row()
        icon_item = self.table.item(row, 0)
        name_item = self.table.item(row, 1)

        if icon_item and icon_item.data(Qt.ItemDataRole.UserRole) == 'folder':
            QMessageBox.warning(self, "Cannot Edit Folder", "Double-click on a folder to open it.")
            return

        skill_name = name_item.data(Qt.ItemDataRole.UserRole)
        if skill_name not in self.templates:
            QMessageBox.warning(self, "Error", f"Template '{skill_name}' not found.")
            return

        content = self.templates[skill_name]['content']
        display_name = skill_name.split('/')[-1] if '/' in skill_name else skill_name
        folder_prefix = skill_name.rsplit('/', 1)[0] + '/' if '/' in skill_name else ""

        dialog = EditSkillTemplateDialog(display_name, content, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_template_data()
            try:
                new_content = f"""---
name: {new_data['name']}
description: {new_data['description']}
allowed-tools: {new_data['allowed_tools']}
---

# {new_data['name']}

{new_data['description']}

## Usage

How to use this skill.
"""
                new_full_name = folder_prefix + new_data['name']
                if new_full_name != skill_name:
                    self.template_mgr.delete_template('skills', skill_name)
                self.template_mgr.save_template('skills', new_full_name, new_content)
                self.refresh_templates()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save template:\n{str(e)}")


class NewSkillTemplateDialog(QDialog):
    """Dialog for creating a new skill template"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Skill Template")
        self.setMinimumWidth(500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., example-skill")
        self.name_edit.setStyleSheet(theme.get_line_edit_style())
        form.addRow("Template Name*:", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("e.g., A skill that does something useful")
        self.description_edit.setStyleSheet(theme.get_text_edit_style())
        self.description_edit.setMinimumHeight(100)
        self.description_edit.setMaximumHeight(150)
        form.addRow("Description*:", self.description_edit)

        layout.addLayout(form)

        tools_label = QLabel("Allowed Tools (optional):")
        tools_label.setStyleSheet(f"color: {theme.FG_PRIMARY}; font-weight: bold;")
        layout.addWidget(tools_label)

        self.tool_checkboxes = {}
        tools_grid = QGridLayout()
        tools_grid.setSpacing(5)

        for idx, tool in enumerate(AVAILABLE_TOOLS):
            checkbox = QCheckBox(tool)
            checkbox.setStyleSheet(f"color: {theme.FG_PRIMARY};")
            if tool in ["Read", "Grep", "Glob"]:
                checkbox.setChecked(True)
            self.tool_checkboxes[tool] = checkbox
            tools_grid.addWidget(checkbox, idx // 3, idx % 3)

        tools_widget = QWidget()
        tools_widget.setLayout(tools_grid)
        tools_widget.setStyleSheet(f"background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px;")
        layout.addWidget(tools_widget)

        info_label = QLabel("* Required fields")
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(info_label)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.setStyleSheet(theme.get_button_style())
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Template name is required.")
            return
        if not self.description_edit.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Description is required.")
            return
        self.accept()

    def get_template_data(self):
        selected_tools = [tool for tool, cb in self.tool_checkboxes.items() if cb.isChecked()]
        return {
            'name': self.name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'allowed_tools': ", ".join(selected_tools) if selected_tools else ""
        }


class EditSkillTemplateDialog(QDialog):
    """Dialog for editing a skill template with form fields"""

    def __init__(self, template_name, content, parent=None):
        super().__init__(parent)
        self.template_name = template_name
        self.setWindowTitle(f"Edit Skill Template: {template_name}")
        self.setMinimumWidth(500)
        self.init_ui(content)

    def init_ui(self, content):
        import re
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        frontmatter_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            fm = frontmatter_match.group(1)
            name_match = re.search(r'name:\s*(.+)', fm)
            desc_match = re.search(r'description:\s*(.+)', fm)
            tools_match = re.search(r'allowed-tools:\s*(.+)', fm)
            parsed_name = name_match.group(1).strip() if name_match else self.template_name
            parsed_desc = desc_match.group(1).strip() if desc_match else ""
            parsed_tools = tools_match.group(1).strip() if tools_match else "Read, Grep, Glob"
        else:
            parsed_name = self.template_name
            parsed_desc = ""
            parsed_tools = "Read, Grep, Glob"

        form = QFormLayout()
        form.setSpacing(8)

        self.name_edit = QLineEdit()
        self.name_edit.setText(parsed_name)
        self.name_edit.setStyleSheet(theme.get_line_edit_style())
        form.addRow("Template Name*:", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setPlainText(parsed_desc)
        self.description_edit.setStyleSheet(theme.get_text_edit_style())
        self.description_edit.setMinimumHeight(100)
        self.description_edit.setMaximumHeight(150)
        form.addRow("Description*:", self.description_edit)

        layout.addLayout(form)

        tools_label = QLabel("Allowed Tools (optional):")
        tools_label.setStyleSheet(f"color: {theme.FG_PRIMARY}; font-weight: bold;")
        layout.addWidget(tools_label)

        self.tool_checkboxes = {}
        tools_grid = QGridLayout()
        tools_grid.setSpacing(5)

        existing_tools = {t.strip() for t in parsed_tools.split(',')} if parsed_tools else set()

        for idx, tool in enumerate(AVAILABLE_TOOLS):
            checkbox = QCheckBox(tool)
            checkbox.setStyleSheet(f"color: {theme.FG_PRIMARY};")
            checkbox.setChecked(tool in existing_tools)
            self.tool_checkboxes[tool] = checkbox
            tools_grid.addWidget(checkbox, idx // 3, idx % 3)

        tools_widget = QWidget()
        tools_widget.setLayout(tools_grid)
        tools_widget.setStyleSheet(f"background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px;")
        layout.addWidget(tools_widget)

        info_label = QLabel("* Required fields")
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(info_label)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.setStyleSheet(theme.get_button_style())
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Template name is required.")
            return
        if not self.description_edit.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Description is required.")
            return
        self.accept()

    def get_template_data(self):
        selected_tools = [tool for tool, cb in self.tool_checkboxes.items() if cb.isChecked()]
        return {
            'name': self.name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'allowed_tools': ", ".join(selected_tools) if selected_tools else ""
        }
