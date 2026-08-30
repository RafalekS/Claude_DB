"""
Hooks Subtab - Manage Claude Code hooks
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


class HooksSubtab(QWidget):
    """Subtab for managing Claude Code hooks (single-scope)"""

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
        header = QLabel(f"Hooks ({scope_label})")
        header.setStyleSheet(f"font-size: {FONT_SIZE_LARGE}px; font-weight: bold; color: {ACCENT_PRIMARY};")

        header_layout.addWidget(header)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Hooks editor for current scope
        editor_widget = self.create_hooks_editor()
        layout.addWidget(editor_widget, 1)

        # Info tip
        tip_label = QLabel(
            "💡 <b>Hooks:</b> Shell commands that execute in response to events "
            "(SessionStart, PreToolUse, PostToolUse, etc.). "
            "User hooks (~/.claude/hooks/) apply globally. "
            "Project hooks (./.claude/hooks/) are shared via git. "
            "Each hook is a JSON file with description and hooks configuration."
        )
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet(f"color: {FG_SECONDARY}; background: {BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {FONT_SIZE_SMALL}px;")
        layout.addWidget(tip_label)

    def create_hooks_editor(self):
        """Create hooks editor for the current scope"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # File path label
        hooks_dir = self.get_scope_hooks_dir()
        path_label = QLabel(f"Directory: {hooks_dir}")
        path_label.setStyleSheet(f"font-size: {FONT_SIZE_SMALL}px; color: {FG_SECONDARY};")
        layout.addWidget(path_label)

        # Store references
        self.path_label = path_label
        self.current_hook = None

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - hook list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        # Search
        search_box = QLineEdit()
        search_box.setPlaceholderText("Search...")
        search_box.textChanged.connect(self.filter_hooks)
        search_box.setStyleSheet(get_line_edit_style())
        left_layout.addWidget(search_box)

        # Hook list
        hook_list = QListWidget()
        hook_list.itemClicked.connect(self.load_hook_content)
        hook_list.setStyleSheet(get_list_widget_style())
        left_layout.addWidget(hook_list)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        new_btn = QPushButton("➕ New")
        new_btn.setToolTip("Create a new hook")
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setToolTip("Load selected hook for editing")
        del_btn = QPushButton("🗑️ Delete")
        del_btn.setToolTip("Delete the selected hook")
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setToolTip("Reload the hooks list")

        for btn in [new_btn, edit_btn, del_btn, refresh_btn]:
            btn.setStyleSheet(get_button_style())

        new_btn.clicked.connect(self.create_new_hook)
        edit_btn.clicked.connect(self.edit_hook)
        del_btn.clicked.connect(self.delete_hook)
        refresh_btn.clicked.connect(self.load_hooks)

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

        hook_name_label = QLabel("No hook selected")
        hook_name_label.setStyleSheet(get_label_style("normal", "secondary"))

        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip("Save the current hook to file")
        backup_save_btn = QPushButton("📦 Backup & Save")
        backup_save_btn.setToolTip("Create timestamped backup before saving hook")
        revert_btn = QPushButton("Revert")
        revert_btn.setToolTip("Revert to saved version (discards unsaved changes)")

        for btn in [save_btn, backup_save_btn, revert_btn]:
            btn.setStyleSheet(get_button_style())

        save_btn.clicked.connect(self.save_hook)
        backup_save_btn.clicked.connect(self.backup_and_save_hook)
        revert_btn.clicked.connect(self.revert_hook)

        editor_btn_layout.addWidget(hook_name_label)
        editor_btn_layout.addStretch()
        editor_btn_layout.addWidget(save_btn)
        editor_btn_layout.addWidget(backup_save_btn)
        editor_btn_layout.addWidget(revert_btn)
        right_layout.addLayout(editor_btn_layout)

        # JSON Editor
        hook_editor = QTextEdit()
        hook_editor.setStyleSheet(get_text_edit_style())
        hook_editor.setPlaceholderText("Select a hook to edit or create a new one...")
        right_layout.addWidget(hook_editor)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 1000])

        layout.addWidget(splitter, 1)

        # Store references
        self.search_box = search_box
        self.hook_list = hook_list
        self.hook_name_label = hook_name_label
        self.hook_editor = hook_editor

        # Load initial data
        self.load_hooks()

        return widget

    def get_scope_hooks_dir(self):
        """Get hooks directory for the current scope"""
        if self.scope == "user":
            return Path.home() / ".claude" / "hooks"
        else:  # project
            if not self.project_context.has_project():
                return None
            return self.project_context.get_project() / ".claude" / "hooks"

    def on_project_changed(self, project_path: Path):
        """Handle project context change"""
        # Update path label
        hooks_dir = self.get_scope_hooks_dir()
        if hooks_dir:
            self.path_label.setText(f"Directory: {hooks_dir}")
        # Reload hooks from new project
        self.load_hooks()

    def load_hooks(self):
        """Load all hooks for the current scope"""
        try:
            self.hook_list.clear()

            hooks_dir = self.get_scope_hooks_dir()

            if not hooks_dir or not hooks_dir.exists():
                return

            # List all .json files in hooks directory
            hooks = list(hooks_dir.glob("*.json"))
            for hook_path in sorted(hooks):
                # Show just the filename
                self.hook_list.addItem(hook_path.name)

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load hooks:\n{str(e)}")

    def filter_hooks(self, text):
        """Filter hooks based on search text"""
        for i in range(self.hook_list.count()):
            item = self.hook_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def load_hook_content(self, item):
        """Load content of selected hook"""
        try:
            hook_name = item.text()
            hooks_dir = self.get_scope_hooks_dir()
            hook_path = hooks_dir / hook_name

            if hook_path.exists():
                with open(hook_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Validate and pretty-print JSON
                    try:
                        json_data = json.loads(content)
                        content = json.dumps(json_data, indent=2)
                    except json.JSONDecodeError:
                        pass  # Keep original if invalid JSON

                self.current_hook = hook_path
                self.hook_name_label.setText(f"Editing: {hook_name}")
                self.hook_editor.setPlainText(content)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load hook:\n{str(e)}")

    def edit_hook(self):
        """Load selected hook for editing"""
        current_item = self.hook_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a hook to edit.")
            return
        self.load_hook_content(current_item)

    def save_hook(self):
        """Save current hook with JSON validation"""
        if not self.current_hook:
            QMessageBox.warning(self, "No Hook Selected", "Please select a hook to save.")
            return
        try:
            content = self.hook_editor.toPlainText()

            # Validate JSON
            try:
                json_data = json.loads(content)
                # Pretty-print it
                content = json.dumps(json_data, indent=2)
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Invalid JSON", f"JSON validation failed:\n{str(e)}")
                return

            with open(self.current_hook, 'w', encoding='utf-8') as f:
                f.write(content)

            # Update editor with formatted JSON
            self.hook_editor.setPlainText(content)
            QMessageBox.information(self, "Save Success", "Hook saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save hook:\n{str(e)}")

    def backup_and_save_hook(self):
        """Backup and save current hook"""
        if not self.current_hook:
            QMessageBox.warning(self, "No Hook Selected", "Please select a hook to save.")
            return
        try:
            # Validate JSON first
            content = self.hook_editor.toPlainText()
            try:
                json_data = json.loads(content)
                content = json.dumps(json_data, indent=2)
            except json.JSONDecodeError as e:
                QMessageBox.critical(self, "Invalid JSON", f"JSON validation failed:\n{str(e)}")
                return

            self.backup_manager.create_file_backup(self.current_hook)
            with open(self.current_hook, 'w', encoding='utf-8') as f:
                f.write(content)

            # Update editor with formatted JSON
            self.hook_editor.setPlainText(content)
            QMessageBox.information(self, "Backup & Save Success", "Backup created and hook saved!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to backup and save:\n{str(e)}")

    def revert_hook(self):
        """Revert hook to saved version"""
        if not self.current_hook:
            return
        reply = QMessageBox.question(
            self, "Revert Changes", "Are you sure you want to revert to the saved version?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with open(self.current_hook, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.hook_editor.setPlainText(content)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to revert:\n{str(e)}")

    def create_new_hook(self):
        """Create a new hook"""
        name, ok = QInputDialog.getText(
            self,
            "New Hook",
            "Enter hook name (without .json extension):"
        )
        if ok and name:
            # Clean up the name
            name = name.strip()
            if not name.endswith('.json'):
                name += '.json'

            hooks_dir = self.get_scope_hooks_dir()
            hooks_dir.mkdir(parents=True, exist_ok=True)
            hook_path = hooks_dir / name

            if hook_path.exists():
                QMessageBox.warning(self, "Hook Exists", f"Hook '{name}' already exists.")
                return
            try:
                # Get just the filename for the template
                hook_name = Path(name).stem

                template = {
                    "description": f"Hook: {hook_name}",
                    "hooks": {
                        "SessionStart": [
                            {
                                "matcher": "startup|resume",
                                "hooks": [
                                    {
                                        "type": "command",
                                        "command": "echo 'Hook executed'",
                                        "timeout": 30
                                    }
                                ]
                            }
                        ]
                    }
                }

                with open(hook_path, 'w', encoding='utf-8') as f:
                    json.dump(template, f, indent=2)

                self.load_hooks()
                QMessageBox.information(self, "Hook Created", f"Hook '{name}' created successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create hook:\n{str(e)}")

    def delete_hook(self):
        """Delete selected hook"""
        if not self.current_hook:
            QMessageBox.warning(self, "No Hook Selected", "Please select a hook to delete.")
            return
        reply = QMessageBox.question(
            self, "Delete Hook", f"Are you sure you want to delete:\n{self.current_hook.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.current_hook.unlink()
                self.hook_editor.clear()
                self.hook_name_label.setText("No hook selected")
                self.current_hook = None
                self.load_hooks()
                QMessageBox.information(self, "Delete Success", "Hook deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete hook:\n{str(e)}")
