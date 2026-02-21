"""
Statusline Subtab - Manage Claude Code statusline configurations
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


class StatuslineSubtab(QWidget):
    """Subtab for managing Claude Code statusline configurations (single-scope)"""

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
        header = QLabel(f"Statusline ({scope_label})")
        header.setStyleSheet(f"font-size: {FONT_SIZE_LARGE}px; font-weight: bold; color: {ACCENT_PRIMARY};")

        header_layout.addWidget(header)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Statusline editor for current scope
        editor_widget = self.create_statusline_editor()
        layout.addWidget(editor_widget, 1)

        # Info tip
        tip_label = QLabel(
            "💡 <b>Statusline:</b> Configure the status line display in Claude Code. "
            "Define custom commands to show project info, git status, context usage, etc. "
            "User statusline (~/.claude/statusline/) applies globally. "
            "Project statusline (./.claude/statusline/) is shared via git. "
            "Each statusline is a JSON file with description and statusLine configuration."
        )
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet(f"color: {FG_SECONDARY}; background: {BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {FONT_SIZE_SMALL}px;")
        layout.addWidget(tip_label)

    def create_statusline_editor(self):
        """Create statusline editor for the current scope"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # File path label
        statusline_dir = self.get_scope_statusline_dir()
        path_label = QLabel(f"Directory: {statusline_dir}")
        path_label.setStyleSheet(f"font-size: {FONT_SIZE_SMALL}px; color: {FG_SECONDARY};")
        layout.addWidget(path_label)

        # Store references
        self.path_label = path_label
        self.current_statusline = None

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - statusline list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        # Search
        search_box = QLineEdit()
        search_box.setPlaceholderText("Search...")
        search_box.textChanged.connect(self.filter_statuslines)
        search_box.setStyleSheet(get_line_edit_style())
        left_layout.addWidget(search_box)

        # Statusline list
        statusline_list = QListWidget()
        statusline_list.itemClicked.connect(self.load_statusline_content)
        statusline_list.setStyleSheet(get_list_widget_style())
        left_layout.addWidget(statusline_list)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        new_btn = QPushButton("➕ New")
        new_btn.setToolTip("Create a new statusline")
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setToolTip("Load selected statusline for editing")
        del_btn = QPushButton("🗑️ Delete")
        del_btn.setToolTip("Delete the selected statusline")
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setToolTip("Reload the statuslines list")

        for btn in [new_btn, edit_btn, del_btn, refresh_btn]:
            btn.setStyleSheet(get_button_style())

        new_btn.clicked.connect(self.create_new_statusline)
        edit_btn.clicked.connect(self.edit_statusline)
        del_btn.clicked.connect(self.delete_statusline)
        refresh_btn.clicked.connect(self.load_statuslines)

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

        statusline_name_label = QLabel("No statusline selected")
        statusline_name_label.setStyleSheet(get_label_style("normal", "secondary"))

        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip("Save the current statusline to file")
        backup_save_btn = QPushButton("📦 Backup & Save")
        backup_save_btn.setToolTip("Create timestamped backup before saving statusline")
        revert_btn = QPushButton("Revert")
        revert_btn.setToolTip("Revert to saved version (discards unsaved changes)")

        for btn in [save_btn, backup_save_btn, revert_btn]:
            btn.setStyleSheet(get_button_style())

        save_btn.clicked.connect(self.save_statusline)
        backup_save_btn.clicked.connect(self.backup_and_save_statusline)
        revert_btn.clicked.connect(self.revert_statusline)

        editor_btn_layout.addWidget(statusline_name_label)
        editor_btn_layout.addStretch()
        editor_btn_layout.addWidget(save_btn)
        editor_btn_layout.addWidget(backup_save_btn)
        editor_btn_layout.addWidget(revert_btn)
        right_layout.addLayout(editor_btn_layout)

        # JSON Editor
        statusline_editor = QTextEdit()
        statusline_editor.setStyleSheet(get_text_edit_style())
        statusline_editor.setPlaceholderText("Select a statusline to edit or create a new one...")
        right_layout.addWidget(statusline_editor)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 1000])

        layout.addWidget(splitter, 1)

        # Store references
        self.search_box = search_box
        self.statusline_list = statusline_list
        self.statusline_name_label = statusline_name_label
        self.statusline_editor = statusline_editor

        # Load initial data
        self.load_statuslines()

        return widget

    def get_scope_statusline_dir(self):
        """Get statusline directory for the current scope"""
        if self.scope == "user":
            return Path.home() / ".claude" / "statusline"
        else:  # project
            if not self.project_context.has_project():
                return None
            return self.project_context.get_project() / ".claude" / "statusline"

    def on_project_changed(self, project_path: Path):
        """Handle project context change"""
        # Update path label
        statusline_dir = self.get_scope_statusline_dir()
        if statusline_dir:
            self.path_label.setText(f"Directory: {statusline_dir}")
        # Reload statuslines from new project
        self.load_statuslines()

    def load_statuslines(self):
        """Load all statuslines for the current scope"""
        try:
            self.statusline_list.clear()

            statusline_dir = self.get_scope_statusline_dir()

            if not statusline_dir or not statusline_dir.exists():
                return

            # List all .json files in statusline directory
            statuslines = list(statusline_dir.glob("*.json"))
            for statusline_path in sorted(statuslines):
                # Show just the filename
                self.statusline_list.addItem(statusline_path.name)

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load statuslines:\n{str(e)}")

    def filter_statuslines(self, text):
        """Filter statuslines based on search text"""
        for i in range(self.statusline_list.count()):
            item = self.statusline_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def load_statusline_content(self, item):
        """Load content of selected statusline"""
        try:
            statusline_name = item.text()
            statusline_dir = self.get_scope_statusline_dir()
            statusline_path = statusline_dir / statusline_name

            if statusline_path.exists():
                with open(statusline_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Validate and pretty-print JSON
                    try:
                        json_data = json.loads(content)
                        content = json.dumps(json_data, indent=2)
                    except json.JSONDecodeError:
                        pass  # Keep original if invalid JSON

                self.current_statusline = statusline_path
                self.statusline_name_label.setText(f"Editing: {statusline_name}")
                self.statusline_editor.setPlainText(content)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load statusline:\n{str(e)}")

    def edit_statusline(self):
        """Load selected statusline for editing"""
        current_item = self.statusline_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a statusline to edit.")
            return
        self.load_statusline_content(current_item)

    def save_statusline(self):
        """Save current statusline with JSON validation"""
        if not self.current_statusline:
            QMessageBox.warning(self, "No Statusline Selected", "Please select a statusline to save.")
            return
        try:
            content = self.statusline_editor.toPlainText()

            # Validate JSON
            try:
                json_data = json.loads(content)
                # Pretty-print it
                content = json.dumps(json_data, indent=2)
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Invalid JSON", f"JSON validation failed:\n{str(e)}")
                return

            with open(self.current_statusline, 'w', encoding='utf-8') as f:
                f.write(content)

            # Update editor with formatted JSON
            self.statusline_editor.setPlainText(content)
            QMessageBox.information(self, "Save Success", "Statusline saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save statusline:\n{str(e)}")

    def backup_and_save_statusline(self):
        """Backup and save current statusline"""
        if not self.current_statusline:
            QMessageBox.warning(self, "No Statusline Selected", "Please select a statusline to save.")
            return
        try:
            # Validate JSON first
            content = self.statusline_editor.toPlainText()
            try:
                json_data = json.loads(content)
                content = json.dumps(json_data, indent=2)
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Invalid JSON", f"JSON validation failed:\n{str(e)}")
                return

            self.backup_manager.create_file_backup(self.current_statusline)
            with open(self.current_statusline, 'w', encoding='utf-8') as f:
                f.write(content)

            # Update editor with formatted JSON
            self.statusline_editor.setPlainText(content)
            QMessageBox.information(self, "Backup & Save Success", "Backup created and statusline saved!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to backup and save:\n{str(e)}")

    def revert_statusline(self):
        """Revert statusline to saved version"""
        if not self.current_statusline:
            return
        reply = QMessageBox.question(
            self, "Revert Changes", "Are you sure you want to revert to the saved version?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with open(self.current_statusline, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.statusline_editor.setPlainText(content)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to revert:\n{str(e)}")

    def create_new_statusline(self):
        """Create a new statusline"""
        name, ok = QInputDialog.getText(
            self,
            "New Statusline",
            "Enter statusline name (without .json extension):"
        )
        if ok and name:
            # Clean up the name
            name = name.strip()
            if not name.endswith('.json'):
                name += '.json'

            statusline_dir = self.get_scope_statusline_dir()
            statusline_dir.mkdir(parents=True, exist_ok=True)
            statusline_path = statusline_dir / name

            if statusline_path.exists():
                QMessageBox.warning(self, "Statusline Exists", f"Statusline '{name}' already exists.")
                return
            try:
                # Get just the filename for the template
                statusline_name = Path(name).stem

                template = {
                    "description": f"Statusline: {statusline_name}",
                    "statusLine": {
                        "type": "command",
                        "command": "echo 'Status: OK'",
                        "padding": 0
                    }
                }

                with open(statusline_path, 'w', encoding='utf-8') as f:
                    json.dump(template, f, indent=2)

                self.load_statuslines()
                QMessageBox.information(self, "Statusline Created", f"Statusline '{name}' created successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create statusline:\n{str(e)}")

    def delete_statusline(self):
        """Delete selected statusline"""
        if not self.current_statusline:
            QMessageBox.warning(self, "No Statusline Selected", "Please select a statusline to delete.")
            return
        reply = QMessageBox.question(
            self, "Delete Statusline", f"Are you sure you want to delete:\n{self.current_statusline.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.current_statusline.unlink()
                self.statusline_editor.clear()
                self.statusline_name_label.setText("No statusline selected")
                self.current_statusline = None
                self.load_statuslines()
                QMessageBox.information(self, "Delete Success", "Statusline deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete statusline:\n{str(e)}")
