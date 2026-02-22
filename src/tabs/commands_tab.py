"""
Commands Tab - Manage Claude Code commands
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QMessageBox, QListWidget, QSplitter, QLineEdit, QInputDialog,
    QFileDialog, QTabWidget, QDialog, QDialogButtonBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QCheckBox, QAbstractItemView, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import sys
import json
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme
from utils.template_manager import get_template_manager
from dialogs.command_library_dialog import CommandLibraryDialog


class CommandsTab(QWidget):
    """Tab for managing Claude Code commands (single-scope)"""

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
        header = QLabel(f"Commands ({scope_label})")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")

        header_layout.addWidget(header)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Single commands editor for current scope
        editor_widget = self.create_commands_editor()
        layout.addWidget(editor_widget, 1)

        # Info tip with essential commands
        tip_label = QLabel(
            "💡 <b>Essential Built-in Commands:</b> "
            "/add-dir (add directories) • "
            "/agents (manage subagents) • "
            "/clear (erase history) • "
            "/config (settings) • "
            "/cost (token usage) • "
            "/doctor (health check) • "
            "/init (create CLAUDE.md) • "
            "/mcp (MCP servers) • "
            "/memory (edit CLAUDE.md) • "
            "/model (change model) • "
            "/permissions (tool access) • "
            "/review (code review) • "
            "/status (account) • "
            "/vim (vim mode)"
            "<br><b>Custom Commands:</b> "
            "Create .md files in commands/ directory • "
            "User commands (~/.claude/commands/) are global • "
            "Project commands (./.claude/commands/) are shared via git • "
            "Use <code>/command-name</code> to invoke"
        )
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(tip_label)

    def create_commands_editor(self):
        """Create commands editor for the current scope"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # File path label
        commands_dir = self.get_scope_commands_dir()
        path_label = QLabel(f"Directory: {commands_dir}")
        path_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_SMALL}px; color: {theme.FG_SECONDARY};")
        layout.addWidget(path_label)

        # Store references
        self.path_label = path_label
        self.current_command = None

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - command list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        # Search
        search_box = QLineEdit()
        search_box.setPlaceholderText("Search...")
        search_box.textChanged.connect(self.filter_commands)
        search_box.setStyleSheet(theme.get_line_edit_style())
        left_layout.addWidget(search_box)

        # Command list
        command_list = QListWidget()
        command_list.itemClicked.connect(self.load_command_content)
        command_list.setStyleSheet(theme.get_list_widget_style())
        left_layout.addWidget(command_list)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        new_btn = QPushButton("➕ New")
        new_btn.setToolTip("Create a new command")
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setToolTip("Load selected command for editing")
        del_btn = QPushButton("🗑️ Delete")
        del_btn.setToolTip("Delete the selected command")
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setToolTip("Reload the commands list")
        library_btn = QPushButton("📚 Command Library")
        library_btn.setToolTip("Browse and add commands from library templates")

        for btn in [new_btn, edit_btn, del_btn, refresh_btn, library_btn]:
            btn.setStyleSheet(theme.get_button_style())

        new_btn.clicked.connect(self.create_new_command)
        edit_btn.clicked.connect(self.edit_command)
        del_btn.clicked.connect(self.delete_command)
        refresh_btn.clicked.connect(self.load_commands)
        library_btn.clicked.connect(self.open_command_library)

        btn_layout.addWidget(new_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(library_btn)
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

        command_name_label = QLabel("No command selected")
        command_name_label.setStyleSheet(theme.get_label_style("normal", "secondary"))

        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip("Save the current command to file")
        backup_save_btn = QPushButton("📦 Backup & Save")
        backup_save_btn.setToolTip("Create timestamped backup before saving command")
        revert_btn = QPushButton("Revert")
        revert_btn.setToolTip("Revert to saved version (discards unsaved changes)")

        for btn in [save_btn, backup_save_btn, revert_btn]:
            btn.setStyleSheet(theme.get_button_style())

        save_btn.clicked.connect(self.save_command)
        backup_save_btn.clicked.connect(self.backup_and_save_command)
        revert_btn.clicked.connect(self.revert_command)

        editor_btn_layout.addWidget(command_name_label)
        editor_btn_layout.addStretch()
        editor_btn_layout.addWidget(save_btn)
        editor_btn_layout.addWidget(backup_save_btn)
        editor_btn_layout.addWidget(revert_btn)
        right_layout.addLayout(editor_btn_layout)

        # Editor
        command_editor = QTextEdit()
        command_editor.setStyleSheet(theme.get_text_edit_style())
        right_layout.addWidget(command_editor)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 1000])

        layout.addWidget(splitter, 1)

        # Store references
        self.search_box = search_box
        self.command_list = command_list
        self.command_name_label = command_name_label
        self.command_editor = command_editor

        # Load initial data
        self.load_commands()

        return widget

    def get_scope_commands_dir(self):
        """Get commands directory for the current scope"""
        if self.scope == "user":
            return self.config_manager.commands_dir
        else:  # project
            if not self.project_context.has_project():
                return None
            return self.project_context.get_project() / ".claude" / "commands"

    def on_project_changed(self, project_path: Path):
        """Handle project context change"""
        # Update path label
        commands_dir = self.get_scope_commands_dir()
        if commands_dir:
            self.path_label.setText(f"Directory: {commands_dir}")
        # Reload commands from new project
        self.load_commands()

    def load_commands(self):
        """Load all commands for the current scope"""
        try:
            self.command_list.clear()

            commands_dir = self.get_scope_commands_dir()

            if not commands_dir or not commands_dir.exists():
                return

            # List all .md files in commands directory and subdirectories (recursive)
            commands = list(commands_dir.glob("**/*.md"))
            for command_path in sorted(commands):
                # Show relative path from commands_dir
                rel_path = command_path.relative_to(commands_dir)
                self.command_list.addItem(str(rel_path))

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load commands:\n{str(e)}")

    def filter_commands(self, text):
        """Filter commands based on search text"""
        for i in range(self.command_list.count()):
            item = self.command_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def load_command_content(self, item):
        """Load content of selected command"""
        try:
            command_name = item.text()
            commands_dir = self.get_scope_commands_dir()
            command_path = commands_dir / command_name

            if command_path.exists():
                with open(command_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.current_command = command_path
                self.command_name_label.setText(f"Editing: {command_name}")
                self.command_editor.setPlainText(content)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load command:\n{str(e)}")

    def edit_command(self):
        """Edit selected command with dialog"""
        current_item = self.command_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a command to edit.")
            return

        command_name = current_item.text()
        commands_dir = self.get_scope_commands_dir()
        command_path = commands_dir / command_name

        if not command_path.exists():
            QMessageBox.warning(self, "Error", "Command file not found.")
            return

        try:
            with open(command_path, 'r', encoding='utf-8') as f:
                content = f.read()

            dialog = EditCommandDialog(command_name, content, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_data = dialog.get_command_data()
                # Regenerate content
                new_content = f"""# {new_data['display_name'] or Path(command_name).stem}

## Description
{new_data['description']}

## Usage
When to use this command.

## Instructions
Detailed instructions for the command.
"""
                with open(command_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                self.load_commands()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit command:\n{str(e)}")

    def save_command(self):
        """Save current command"""
        if not self.current_command:
            QMessageBox.warning(self, "No Command Selected", "Please select a command to save.")
            return
        try:
            content = self.command_editor.toPlainText()
            with open(self.current_command, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(self, "Save Success", "Command saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save command:\n{str(e)}")

    def backup_and_save_command(self):
        """Backup and save current command"""
        if not self.current_command:
            QMessageBox.warning(self, "No Command Selected", "Please select a command to save.")
            return
        try:
            self.backup_manager.create_file_backup(self.current_command)
            content = self.command_editor.toPlainText()
            with open(self.current_command, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(self, "Backup & Save Success", "Backup created and command saved!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to backup and save:\n{str(e)}")

    def revert_command(self):
        """Revert command to saved version"""
        if not self.current_command:
            return
        reply = QMessageBox.question(
            self, "Revert Changes", "Are you sure you want to revert to the saved version?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with open(self.current_command, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.command_editor.setPlainText(content)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to revert:\n{str(e)}")

    def create_new_command(self):
        """Create a new command"""
        dialog = NewCommandDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        command_data = dialog.get_command_data()
        name = command_data['name'].strip()
        if not name.endswith('.md'):
            name += '.md'

        commands_dir = self.get_scope_commands_dir()
        command_path = commands_dir / name

        if command_path.exists():
            QMessageBox.warning(self, "Command Exists", f"Command '{name}' already exists.")
            return

        try:
            # Create parent directories if they don't exist
            command_path.parent.mkdir(parents=True, exist_ok=True)

            # Build content
            content = f"""# {command_data['display_name'] or Path(name).stem}

## Description
{command_data['description']}

## Usage
When to use this command.

## Instructions
Detailed instructions for the command.
"""
            with open(command_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.load_commands()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create command:\n{str(e)}")

    def delete_command(self):
        """Delete selected command"""
        if not self.current_command:
            QMessageBox.warning(self, "No Command Selected", "Please select a command to delete.")
            return
        reply = QMessageBox.question(
            self, "Delete Command", f"Are you sure you want to delete:\n{self.current_command.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.current_command.unlink()
                self.command_editor.clear()
                self.command_name_label.setText("No command selected")
                self.current_command = None
                self.load_commands()
                QMessageBox.information(self, "Delete Success", "Command deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete command:\n{str(e)}")

    def open_command_library(self):
        """Open command library to browse and manage templates"""
        template_mgr = get_template_manager()
        templates_dir = template_mgr.get_templates_dir('commands')

        dialog = CommandLibraryDialog(templates_dir, self.scope, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.get_selected_commands()
            if selected:
                self.deploy_commands(selected)
                self.load_commands()

    def deploy_commands(self, commands):
        """Deploy selected commands to the current scope"""
        commands_dir = self.get_scope_commands_dir()
        commands_dir.mkdir(parents=True, exist_ok=True)

        added_count = 0
        skipped_count = 0

        for command_name, command_content in commands:
            command_file = commands_dir / f"{command_name}.md"
            if command_file.exists():
                skipped_count += 1
                continue

            try:
                with open(command_file, 'w', encoding='utf-8') as f:
                    f.write(command_content)
                added_count += 1
            except Exception as e:
                QMessageBox.warning(self, "Deploy Error", f"Failed to deploy {command_name}:\n{str(e)}")

        # Show summary
        msg = f"Deployed {added_count} command(s)"
        if skipped_count > 0:
            msg += f"\nSkipped {skipped_count} (already exist)"
        QMessageBox.information(self, "Deploy Complete", msg)


class NewCommandDialog(QDialog):
    """Dialog for creating a new command with proper fields"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Command")
        self.setMinimumWidth(500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., bash-timeout")
        self.name_edit.setStyleSheet(theme.get_line_edit_style())
        form.addRow("Command Name*:", self.name_edit)

        # Display Name field
        self.display_name_edit = QLineEdit()
        self.display_name_edit.setPlaceholderText("e.g., Bash Timeout")
        self.display_name_edit.setStyleSheet(theme.get_line_edit_style())
        form.addRow("Display Name:", self.display_name_edit)

        # Description field
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("e.g., Runs bash commands with timeout")
        self.description_edit.setStyleSheet(theme.get_text_edit_style())
        self.description_edit.setMinimumHeight(100)
        self.description_edit.setMaximumHeight(150)
        form.addRow("Description*:", self.description_edit)

        layout.addLayout(form)

        # Info label
        info_label = QLabel("* Required fields")
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(info_label)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.setStyleSheet(theme.get_button_style())
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Command name is required.")
            return
        if not self.description_edit.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Description is required.")
            return
        self.accept()

    def get_command_data(self):
        return {
            'name': self.name_edit.text().strip(),
            'display_name': self.display_name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip()
        }


class EditCommandDialog(QDialog):
    """Dialog for editing a command with form fields"""

    def __init__(self, command_name, content, parent=None):
        super().__init__(parent)
        self.command_name = command_name
        self.setWindowTitle(f"Edit Command: {command_name}")
        self.setMinimumWidth(500)
        self.init_ui(content)

    def init_ui(self, content):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Parse markdown content
        import re
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        desc_match = re.search(r'##\s+Description\s*\n(.+?)(?=\n##|\Z)', content, re.DOTALL)

        parsed_display_name = title_match.group(1).strip() if title_match else Path(self.command_name).stem
        parsed_desc = desc_match.group(1).strip() if desc_match else ""

        form = QFormLayout()
        form.setSpacing(8)

        # Display Name field
        self.display_name_edit = QLineEdit()
        self.display_name_edit.setText(parsed_display_name)
        self.display_name_edit.setStyleSheet(theme.get_line_edit_style())
        form.addRow("Display Name:", self.display_name_edit)

        # Description field
        self.description_edit = QTextEdit()
        self.description_edit.setPlainText(parsed_desc)
        self.description_edit.setStyleSheet(theme.get_text_edit_style())
        self.description_edit.setMinimumHeight(100)
        self.description_edit.setMaximumHeight(150)
        form.addRow("Description*:", self.description_edit)

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
        if not self.description_edit.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Description is required.")
            return
        self.accept()

    def get_command_data(self):
        return {
            'display_name': self.display_name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip()
        }
