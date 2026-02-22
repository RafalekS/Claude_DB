"""Command Library Dialog - manages command templates"""

import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QCheckBox, QWidget, QDialogButtonBox, QInputDialog,
    QFormLayout, QLineEdit, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme
from utils.template_manager import get_template_manager
from dialogs.base_library_dialog import BaseLibraryDialog


class CommandLibraryDialog(BaseLibraryDialog):
    """Dialog for managing command templates in config/templates/commands/"""

    def get_template_type(self):
        return 'commands'

    def get_dialog_title(self):
        return "Command Library"

    def get_header_text(self):
        return "Command Library - Manage and deploy command templates"

    def get_info_text(self):
        return "Select commands to deploy, then click OK. You can also drop .md files directly into the templates folder."

    def get_bulk_add_class(self):
        from dialogs.bulk_command_add_dialog import BulkCommandAddDialog
        return BulkCommandAddDialog

    def load_templates(self):
        """Load all templates and organise by folder"""
        self.templates = {}
        self.folders = set()
        template_names = self.template_mgr.list_templates('commands')
        for name in template_names:
            try:
                content = self.template_mgr.read_template('commands', name)
                info = self.template_mgr.get_template_info('commands', name)
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
    def get_selected_commands(self):
        return self.get_selected_items()

    def _build_template_content(self, data):
        """Build markdown content from template data"""
        parts = [
            f"# {data['name']}", "",
            "## Description", data['description'], ""
        ]
        if data.get('requirements'):
            parts += ["## Requirements", data['requirements'], ""]
        parts += [
            "## Instructions", data['instructions'], "",
            "## Examples", data['examples'], ""
        ]
        if data.get('notes'):
            parts += ["## Important Notes", data['notes'], ""]
        return "\n".join(parts)

    def add_template(self):
        """Add a new template"""
        dialog = NewCommandTemplateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            template_data = dialog.get_template_data()
            try:
                content = self._build_template_content(template_data)
                full_name = (f"{self.current_folder}/{template_data['name']}"
                             if self.current_folder else template_data['name'])
                self.template_mgr.save_template('commands', full_name, content)
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

        command_name = name_item.data(Qt.ItemDataRole.UserRole)
        if command_name not in self.templates:
            QMessageBox.warning(self, "Error", f"Template '{command_name}' not found.")
            return

        content = self.templates[command_name]['content']
        display_name = command_name.split('/')[-1] if '/' in command_name else command_name
        folder_prefix = command_name.rsplit('/', 1)[0] + '/' if '/' in command_name else ""

        dialog = EditCommandTemplateDialog(display_name, content, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_template_data()
            try:
                new_content = self._build_template_content(new_data)
                new_full_name = folder_prefix + new_data['name']
                if new_full_name != command_name:
                    self.template_mgr.delete_template('commands', command_name)
                self.template_mgr.save_template('commands', new_full_name, new_content)
                self.refresh_templates()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save template:\n{str(e)}")


class NewCommandTemplateDialog(QDialog):
    """Dialog for creating a new command template"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Command Template")
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., bash-timeout")
        self.name_edit.setStyleSheet(theme.get_line_edit_style())
        form.addRow("Template Name*:", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("What the command does (role, purpose, overview)")
        self.description_edit.setStyleSheet(theme.get_text_edit_style())
        self.description_edit.setMinimumHeight(100)
        form.addRow("Description*:", self.description_edit)

        self.requirements_edit = QTextEdit()
        self.requirements_edit.setPlaceholderText("Arguments, parameters, prerequisites...")
        self.requirements_edit.setStyleSheet(theme.get_text_edit_style())
        self.requirements_edit.setMinimumHeight(100)
        form.addRow("Requirements:", self.requirements_edit)

        self.instructions_edit = QTextEdit()
        self.instructions_edit.setPlaceholderText("Step-by-step instructions for using this command...")
        self.instructions_edit.setStyleSheet(theme.get_text_edit_style())
        self.instructions_edit.setMinimumHeight(120)
        form.addRow("Instructions*:", self.instructions_edit)

        self.examples_edit = QTextEdit()
        self.examples_edit.setPlaceholderText("Code examples, usage examples, reference workflows...")
        self.examples_edit.setStyleSheet(theme.get_text_edit_style())
        self.examples_edit.setMinimumHeight(120)
        form.addRow("Examples*:", self.examples_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Important notes, warnings, limitations, considerations...")
        self.notes_edit.setStyleSheet(theme.get_text_edit_style())
        self.notes_edit.setMinimumHeight(100)
        form.addRow("Important Notes:", self.notes_edit)

        layout.addLayout(form)

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
        if not self.instructions_edit.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Instructions are required.")
            return
        if not self.examples_edit.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Examples are required.")
            return
        self.accept()

    def get_template_data(self):
        return {
            'name': self.name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'requirements': self.requirements_edit.toPlainText().strip(),
            'instructions': self.instructions_edit.toPlainText().strip(),
            'examples': self.examples_edit.toPlainText().strip(),
            'notes': self.notes_edit.toPlainText().strip()
        }


class EditCommandTemplateDialog(QDialog):
    """Dialog for editing a command template with form fields"""

    def __init__(self, template_name, content, parent=None):
        super().__init__(parent)
        self.template_name = template_name
        self.setWindowTitle(f"Edit Command Template: {template_name}")
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)
        self.init_ui(content)

    def init_ui(self, content):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        def find_section(text, patterns):
            for pattern in patterns:
                match = re.search(rf'##\s+{pattern}\s*\n(.+?)(?=\n##|\Z)', text, re.DOTALL | re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            return ""

        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        parsed_name = title_match.group(1).strip() if title_match else self.template_name

        parsed_desc = find_section(content, [
            'Description', 'Role and Purpose', 'Purpose', 'Overview',
            'Role', 'About', 'Summary', 'Context Overview', 'Role Statement'
        ])
        parsed_requirements = find_section(content, [
            'Requirements', 'Arguments', 'Prerequisites', 'Parameters',
            'Core Requirements', 'Requirements and Argument Handling',
            'Input Parameters', 'Inputs'
        ])
        parsed_instructions = find_section(content, [
            'Instructions', 'How to Use', 'Steps', 'Usage Instructions',
            'Guide', 'Directions', 'Implementation', 'How it Works',
            'Context Extraction Strategies'
        ])
        parsed_examples = find_section(content, [
            'Examples', 'Code Examples', 'Usage Examples', 'Reference Workflows',
            'Use Cases', 'Practical Usage', 'Usage', 'Sample Usage'
        ])
        parsed_notes = find_section(content, [
            'Important Notes', 'Notes', 'Warnings', 'Limitations',
            'Caveats', 'Considerations', 'Limitations and Considerations',
            'Advanced Integration Capabilities', 'Future Roadmap'
        ])

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
        form.addRow("Description*:", self.description_edit)

        self.requirements_edit = QTextEdit()
        self.requirements_edit.setPlainText(parsed_requirements)
        self.requirements_edit.setStyleSheet(theme.get_text_edit_style())
        self.requirements_edit.setMinimumHeight(100)
        form.addRow("Requirements:", self.requirements_edit)

        self.instructions_edit = QTextEdit()
        self.instructions_edit.setPlainText(parsed_instructions)
        self.instructions_edit.setStyleSheet(theme.get_text_edit_style())
        self.instructions_edit.setMinimumHeight(120)
        form.addRow("Instructions*:", self.instructions_edit)

        self.examples_edit = QTextEdit()
        self.examples_edit.setPlainText(parsed_examples)
        self.examples_edit.setStyleSheet(theme.get_text_edit_style())
        self.examples_edit.setMinimumHeight(120)
        form.addRow("Examples*:", self.examples_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlainText(parsed_notes)
        self.notes_edit.setStyleSheet(theme.get_text_edit_style())
        self.notes_edit.setMinimumHeight(100)
        form.addRow("Important Notes:", self.notes_edit)

        layout.addLayout(form)

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
        if not self.instructions_edit.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Instructions are required.")
            return
        if not self.examples_edit.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Examples are required.")
            return
        self.accept()

    def get_template_data(self):
        return {
            'name': self.name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'requirements': self.requirements_edit.toPlainText().strip(),
            'instructions': self.instructions_edit.toPlainText().strip(),
            'examples': self.examples_edit.toPlainText().strip(),
            'notes': self.notes_edit.toPlainText().strip()
        }
