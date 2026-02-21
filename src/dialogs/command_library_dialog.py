"""Command Library Dialog - manages command templates"""

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
from utils.theme import *
from utils.template_manager import get_template_manager


class CommandLibraryDialog(QDialog):
    """Dialog for managing command templates in config/templates/commands/"""

    def __init__(self, templates_dir, scope, parent=None):
        super().__init__(parent)
        self.templates_dir = Path(templates_dir)
        self.scope = scope
        self.template_mgr = get_template_manager()
        self.current_folder = ""  # Empty = root, otherwise subfolder name
        self.setWindowTitle("Command Library")
        self.setModal(True)
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("Command Library - Manage and deploy command templates")
        header.setStyleSheet(f"font-weight: bold; color: {FG_PRIMARY}; font-size: {FONT_SIZE_LARGE}px;")
        layout.addWidget(header)

        # Navigation bar with back button and path
        nav_layout = QHBoxLayout()

        self.back_btn = QPushButton("⬅ Back")
        self.back_btn.setStyleSheet(get_button_style())
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setVisible(False)  # Hidden at root level
        nav_layout.addWidget(self.back_btn)

        self.path_label = QLabel(f"📁 {self.templates_dir}")
        self.path_label.setStyleSheet(f"color: {FG_SECONDARY}; font-size: {FONT_SIZE_SMALL}px;")
        nav_layout.addWidget(self.path_label)
        nav_layout.addStretch()

        layout.addLayout(nav_layout)

        self.load_templates()

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["", "Name", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 200)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        self.table.doubleClicked.connect(self.on_double_click)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {BG_DARK};
                color: {FG_PRIMARY};
                border: 1px solid {BG_LIGHT};
                border-radius: 3px;
            }}
            QHeaderView::section {{
                background-color: {BG_MEDIUM};
                color: {FG_PRIMARY};
                padding: 5px;
                border: 1px solid {BG_LIGHT};
            }}
            QHeaderView::section:hover {{
                background-color: {BG_LIGHT};
            }}
        """)

        self.populate_table()
        layout.addWidget(self.table)

        manage_layout = QHBoxLayout()

        add_btn = QPushButton("➕ Add Template")
        add_btn.setStyleSheet(get_button_style())
        add_btn.clicked.connect(self.add_template)
        manage_layout.addWidget(add_btn)

        edit_btn = QPushButton("✏️ Edit Selected")
        edit_btn.setStyleSheet(get_button_style())
        edit_btn.clicked.connect(self.edit_template)
        manage_layout.addWidget(edit_btn)

        bulk_add_btn = QPushButton("📋 Bulk Add")
        bulk_add_btn.setStyleSheet(get_button_style())
        bulk_add_btn.clicked.connect(self.bulk_add_commands)
        manage_layout.addWidget(bulk_add_btn)

        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.setStyleSheet(get_button_style())
        delete_btn.clicked.connect(self.delete_selected)
        manage_layout.addWidget(delete_btn)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet(get_button_style())
        refresh_btn.clicked.connect(self.refresh_templates)
        manage_layout.addWidget(refresh_btn)

        open_folder_btn = QPushButton("📁 Open Folder")
        open_folder_btn.setStyleSheet(get_button_style())
        open_folder_btn.clicked.connect(self.open_folder)
        manage_layout.addWidget(open_folder_btn)

        manage_layout.addStretch()
        layout.addLayout(manage_layout)

        select_layout = QHBoxLayout()
        select_all_btn = QPushButton("✓ Select All")
        select_all_btn.setStyleSheet(get_button_style())
        select_all_btn.clicked.connect(self.select_all)
        select_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("✗ Deselect All")
        deselect_all_btn.setStyleSheet(get_button_style())
        deselect_all_btn.clicked.connect(self.deselect_all)
        select_layout.addWidget(deselect_all_btn)

        select_layout.addStretch()
        layout.addLayout(select_layout)

        info = QLabel("Select commands to deploy, then click OK. You can also drop .md files directly into the templates folder.")
        info.setStyleSheet(f"color: {FG_SECONDARY}; font-size: {FONT_SIZE_SMALL}px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_templates(self):
        """Load all templates and organize by folder"""
        self.templates = {}
        self.folders = set()
        template_names = self.template_mgr.list_templates('commands')

        for name in template_names:
            try:
                content = self.template_mgr.read_template('commands', name)
                info = self.template_mgr.get_template_info('commands', name)
                description = info.get('description', 'No description') if info else 'No description'
                self.templates[name] = {
                    'content': content,
                    'description': description
                }
                # Track folders
                if '/' in name:
                    folder = name.split('/')[0]
                    self.folders.add(folder)
            except Exception as e:
                print(f"Error loading template {name}: {e}")

    def populate_table(self):
        """Populate table based on current folder"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        # Update path label and back button
        if self.current_folder:
            self.path_label.setText(f"📁 {self.templates_dir / self.current_folder}")
            self.back_btn.setVisible(True)
        else:
            self.path_label.setText(f"📁 {self.templates_dir}")
            self.back_btn.setVisible(False)

        items_to_show = []

        if not self.current_folder:
            # At root level - show folders first, then root-level templates
            for folder in sorted(self.folders):
                items_to_show.append(('folder', folder, ''))

            # Show templates that are at root level (no folder)
            for name in sorted(self.templates.keys()):
                if '/' not in name:
                    desc = self.templates[name].get('description', 'No description')
                    items_to_show.append(('template', name, desc))
        else:
            # Inside a folder - show templates in this folder
            prefix = self.current_folder + '/'
            for name in sorted(self.templates.keys()):
                if name.startswith(prefix):
                    # Get just the template name without folder prefix
                    template_name = name[len(prefix):]
                    # Only show if it's directly in this folder (no further subfolders)
                    if '/' not in template_name:
                        desc = self.templates[name].get('description', 'No description')
                        items_to_show.append(('template', name, desc))

        self.table.setRowCount(len(items_to_show))

        for row, (item_type, name, description) in enumerate(items_to_show):
            if item_type == 'folder':
                icon_item = QTableWidgetItem("📁")
                icon_item.setData(Qt.ItemDataRole.UserRole, 'folder')
                name_item = QTableWidgetItem(name)
                name_item.setForeground(QColor(ACCENT_PRIMARY))
                desc_item = QTableWidgetItem("")
            else:
                icon_item = QTableWidgetItem("📄")
                icon_item.setData(Qt.ItemDataRole.UserRole, 'template')
                display_name = name.split('/')[-1] if '/' in name else name
                name_item = QTableWidgetItem(display_name)
                name_item.setForeground(QColor(FG_PRIMARY))
                desc_item = QTableWidgetItem(description)
                desc_item.setForeground(QColor(FG_SECONDARY))

            # Store full name in UserRole for later retrieval
            name_item.setData(Qt.ItemDataRole.UserRole, name)
            icon_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row, 0, icon_item)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, desc_item)

        self.table.setSortingEnabled(True)
        self.table.sortItems(1, Qt.SortOrder.AscendingOrder)

    def on_double_click(self, index):
        """Handle double-click on table row"""
        row = index.row()
        icon_item = self.table.item(row, 0)
        name_item = self.table.item(row, 1)

        if icon_item and icon_item.data(Qt.ItemDataRole.UserRole) == 'folder':
            # Enter folder
            folder_name = name_item.text()
            self.current_folder = folder_name
            self.populate_table()

    def go_back(self):
        """Navigate back to root folder"""
        self.current_folder = ""
        self.populate_table()

    def select_all(self):
        self.table.selectAll()

    def deselect_all(self):
        self.table.clearSelection()

    def get_selected_commands(self):
        """Get selected templates (not folders)"""
        selected = []
        for row in range(self.table.rowCount()):
            icon_item = self.table.item(row, 0)
            name_item = self.table.item(row, 1)
            if name_item and name_item.isSelected():
                # Only include templates, not folders
                if icon_item and icon_item.data(Qt.ItemDataRole.UserRole) == 'template':
                    full_name = name_item.data(Qt.ItemDataRole.UserRole)
                    if full_name in self.templates:
                        selected.append((full_name, self.templates[full_name]['content']))
        return selected

    def add_template(self):
        """Add a new template"""
        dialog = NewCommandTemplateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            template_data = dialog.get_template_data()
            try:
                content = self._build_template_content(template_data)
                # If in a folder, save to that folder
                if self.current_folder:
                    full_name = f"{self.current_folder}/{template_data['name']}"
                else:
                    full_name = template_data['name']
                self.template_mgr.save_template('commands', full_name, content)
                self.refresh_templates()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save template:\n{str(e)}")

    def _build_template_content(self, data):
        """Build markdown content from template data"""
        content_parts = [
            f"# {data['name']}",
            "",
            "## Description",
            data['description'],
            ""
        ]

        # Add Requirements if provided
        if data.get('requirements'):
            content_parts.extend([
                "## Requirements",
                data['requirements'],
                ""
            ])

        content_parts.extend([
            "## Instructions",
            data['instructions'],
            "",
            "## Examples",
            data['examples'],
            ""
        ])

        # Add Important Notes if provided
        if data.get('notes'):
            content_parts.extend([
                "## Important Notes",
                data['notes'],
                ""
            ])

        return "\n".join(content_parts)

    def edit_template(self):
        """Edit selected template with form dialog"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a template to edit.")
            return

        # Edit the first selected template
        row = selected_rows[0].row()
        icon_item = self.table.item(row, 0)
        name_item = self.table.item(row, 1)

        # Check if it's a folder
        if icon_item and icon_item.data(Qt.ItemDataRole.UserRole) == 'folder':
            QMessageBox.warning(self, "Cannot Edit Folder", "Double-click on a folder to open it.")
            return

        # Get the full template name from UserRole
        command_name = name_item.data(Qt.ItemDataRole.UserRole)
        if command_name not in self.templates:
            QMessageBox.warning(self, "Error", f"Template '{command_name}' not found.")
            return

        content = self.templates[command_name]['content']

        # Get display name and folder prefix
        display_name = command_name.split('/')[-1] if '/' in command_name else command_name
        folder_prefix = command_name.rsplit('/', 1)[0] + '/' if '/' in command_name else ""

        dialog = EditCommandTemplateDialog(display_name, content, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_template_data()
            try:
                # Regenerate content using shared method
                new_content = self._build_template_content(new_data)

                # Construct new full name with folder prefix
                new_full_name = folder_prefix + new_data['name']

                # Handle renaming: delete old template if name changed
                if new_full_name != command_name:
                    self.template_mgr.delete_template('commands', command_name)

                # Save with new name
                self.template_mgr.save_template('commands', new_full_name, new_content)
                self.refresh_templates()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save template:\n{str(e)}")

    def bulk_add_commands(self):
        """Open bulk add dialog"""
        from dialogs.bulk_command_add_dialog import BulkCommandAddDialog
        dialog = BulkCommandAddDialog(self.templates_dir, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_templates()

    def delete_selected(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select templates to delete.")
            return

        # Get selected template names (skip folders)
        selected = []
        for row_index in selected_rows:
            row = row_index.row()
            icon_item = self.table.item(row, 0)
            name_item = self.table.item(row, 1)
            if icon_item and icon_item.data(Qt.ItemDataRole.UserRole) == 'template':
                full_name = name_item.data(Qt.ItemDataRole.UserRole)
                selected.append(full_name)

        if not selected:
            QMessageBox.warning(self, "No Templates Selected", "Please select templates to delete (folders cannot be deleted directly).")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete {len(selected)} template(s)?\n\n" + "\n".join(selected),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            for name in selected:
                try:
                    self.template_mgr.delete_template('commands', name)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to delete {name}:\n{str(e)}")

            QMessageBox.information(self, "Success", f"Deleted {len(selected)} template(s)!")
            self.refresh_templates()

    def refresh_templates(self):
        self.load_templates()
        self.populate_table()

    def open_folder(self):
        import subprocess
        import platform
        if platform.system() == 'Windows':
            subprocess.Popen(['explorer', str(self.templates_dir)])
        elif platform.system() == 'Darwin':
            subprocess.Popen(['open', str(self.templates_dir)])
        else:
            subprocess.Popen(['xdg-open', str(self.templates_dir)])


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

        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., bash-timeout")
        self.name_edit.setStyleSheet(get_line_edit_style())
        form.addRow("Template Name*:", self.name_edit)

        # Description field
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("What the command does (role, purpose, overview)")
        self.description_edit.setStyleSheet(get_text_edit_style())
        self.description_edit.setMinimumHeight(100)
        form.addRow("Description*:", self.description_edit)

        # Requirements field
        self.requirements_edit = QTextEdit()
        self.requirements_edit.setPlaceholderText("Arguments, parameters, prerequisites...")
        self.requirements_edit.setStyleSheet(get_text_edit_style())
        self.requirements_edit.setMinimumHeight(100)
        form.addRow("Requirements:", self.requirements_edit)

        # Instructions field
        self.instructions_edit = QTextEdit()
        self.instructions_edit.setPlaceholderText("Step-by-step instructions for using this command...")
        self.instructions_edit.setStyleSheet(get_text_edit_style())
        self.instructions_edit.setMinimumHeight(120)
        form.addRow("Instructions*:", self.instructions_edit)

        # Examples field
        self.examples_edit = QTextEdit()
        self.examples_edit.setPlaceholderText("Code examples, usage examples, reference workflows...")
        self.examples_edit.setStyleSheet(get_text_edit_style())
        self.examples_edit.setMinimumHeight(120)
        form.addRow("Examples*:", self.examples_edit)

        # Important Notes field
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Important notes, warnings, limitations, considerations...")
        self.notes_edit.setStyleSheet(get_text_edit_style())
        self.notes_edit.setMinimumHeight(100)
        form.addRow("Important Notes:", self.notes_edit)

        layout.addLayout(form)

        info_label = QLabel("* Required fields")
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {FG_SECONDARY}; background: {BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {FONT_SIZE_SMALL}px;")
        layout.addWidget(info_label)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.setStyleSheet(get_button_style())
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

        # Parse markdown content to extract all sections - flexible matching
        import re

        def find_section(content, patterns):
            """Find section matching any of the given patterns"""
            for pattern in patterns:
                match = re.search(rf'##\s+{pattern}\s*\n(.+?)(?=\n##|\Z)', content, re.DOTALL | re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            return ""

        # Extract title (# Title)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        parsed_name = title_match.group(1).strip() if title_match else self.template_name

        # Flexible section matching - try multiple common variations
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

        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setText(parsed_name)
        self.name_edit.setStyleSheet(get_line_edit_style())
        form.addRow("Template Name*:", self.name_edit)

        # Description field
        self.description_edit = QTextEdit()
        self.description_edit.setPlainText(parsed_desc)
        self.description_edit.setStyleSheet(get_text_edit_style())
        self.description_edit.setMinimumHeight(100)
        form.addRow("Description*:", self.description_edit)

        # Requirements field
        self.requirements_edit = QTextEdit()
        self.requirements_edit.setPlainText(parsed_requirements)
        self.requirements_edit.setStyleSheet(get_text_edit_style())
        self.requirements_edit.setMinimumHeight(100)
        form.addRow("Requirements:", self.requirements_edit)

        # Instructions field
        self.instructions_edit = QTextEdit()
        self.instructions_edit.setPlainText(parsed_instructions)
        self.instructions_edit.setStyleSheet(get_text_edit_style())
        self.instructions_edit.setMinimumHeight(120)
        form.addRow("Instructions*:", self.instructions_edit)

        # Examples field
        self.examples_edit = QTextEdit()
        self.examples_edit.setPlainText(parsed_examples)
        self.examples_edit.setStyleSheet(get_text_edit_style())
        self.examples_edit.setMinimumHeight(120)
        form.addRow("Examples*:", self.examples_edit)

        # Important Notes field
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlainText(parsed_notes)
        self.notes_edit.setStyleSheet(get_text_edit_style())
        self.notes_edit.setMinimumHeight(100)
        form.addRow("Important Notes:", self.notes_edit)

        layout.addLayout(form)

        info_label = QLabel("* Required fields")
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {FG_SECONDARY}; background: {BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {FONT_SIZE_SMALL}px;")
        layout.addWidget(info_label)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.setStyleSheet(get_button_style())
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
