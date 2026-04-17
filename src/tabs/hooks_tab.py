"""
Hooks Tab - Manage Claude Code hooks from all settings sources
"""

import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QSplitter, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QFileDialog, QTabWidget
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont

from utils import theme
from tabs.hooks_shared import HOOK_EVENT_GROUPS, HOOK_EVENTS, HookReferenceDialog


class HooksTab(QWidget):
    """Tab for managing Claude Code hooks"""

    def __init__(self, config_manager, backup_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.project_folder = Path.cwd()  # Default to current directory
        self.scope_widgets = {}
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        # Header with docs link
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        header = QLabel("Hooks Configuration")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")

        docs_btn = QPushButton("📖 Hooks Docs")
        docs_btn.setToolTip("Open official hooks documentation in browser")
        docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://code.claude.com/docs/en/docs/claude-code/hooks")
        ))

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(docs_btn)

        layout.addLayout(header_layout)

        # Main tab widget for User / Project / Local
        self.main_tabs = QTabWidget()

        # User tab (~/.claude/settings.json)
        self.user_tab = self.create_hooks_editor("user")
        self.main_tabs.addTab(self.user_tab, "User (~/.claude/settings.json)")

        # Project tab (./.claude/settings.json)
        self.project_tab = self.create_hooks_editor_with_folder("project")
        self.main_tabs.addTab(self.project_tab, "Project (./.claude/settings.json)")

        # Local tab (./.claude/settings.local.json)
        self.local_tab = self.create_hooks_editor_with_folder("local")
        self.main_tabs.addTab(self.local_tab, "Local (./.claude/settings.local.json)")

        layout.addWidget(self.main_tabs)

    # ── Tree helpers ──────────────────────────────────────────────────────────

    def _build_event_tree(self, tree: QTreeWidget):
        """Populate a QTreeWidget with grouped hook events."""
        bold = QFont()
        bold.setBold(True)
        for group_label, events in HOOK_EVENT_GROUPS.items():
            group_item = QTreeWidgetItem([group_label])
            group_item.setFont(0, bold)
            group_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            group_item.setData(0, Qt.ItemDataRole.UserRole, None)
            tree.addTopLevelItem(group_item)
            for event in events:
                child = QTreeWidgetItem([f"○ {event}"])
                child.setData(0, Qt.ItemDataRole.UserRole, event)
                group_item.addChild(child)

    def _get_selected_event(self, scope: str) -> str | None:
        """Return the selected event name for a scope, or None."""
        tree = self.scope_widgets[scope]['events_tree']
        selected = tree.selectedItems()
        if not selected:
            return None
        return selected[0].data(0, Qt.ItemDataRole.UserRole)

    # ── Editor factory ────────────────────────────────────────────────────────

    def create_hooks_editor(self, scope):
        """Create hooks editor for a specific scope (without folder picker)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # File path label
        file_path = self.get_scope_file_path(scope)
        path_label = QLabel(f"File: {file_path}")
        path_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_SMALL}px; color: {theme.FG_SECONDARY};")
        layout.addWidget(path_label)

        self.scope_widgets[scope] = {
            'path_label': path_label,
            'config': {}
        }

        self._add_splitter_content(layout, scope)

        # Load initial data
        self.load_hooks(scope)

        return widget

    def create_hooks_editor_with_folder(self, scope):
        """Create hooks editor with folder picker for project/local scopes"""
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

        browse_folder_btn = QPushButton("Browse...")
        browse_folder_btn.setToolTip("Select a different project folder")
        browse_folder_btn.clicked.connect(lambda: self.browse_project_folder(scope))

        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(project_folder_edit, 1)
        folder_layout.addWidget(browse_folder_btn)

        layout.addLayout(folder_layout)

        # File path label
        file_path = self.get_scope_file_path(scope)
        path_label = QLabel(f"File: {file_path}")
        path_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_SMALL}px; color: {theme.FG_SECONDARY};")
        layout.addWidget(path_label)

        self.scope_widgets[scope] = {
            'path_label': path_label,
            'folder_edit': project_folder_edit,
            'config': {}
        }

        self._add_splitter_content(layout, scope)

        # Load initial data
        self.load_hooks(scope)

        return widget

    def _add_splitter_content(self, layout: QVBoxLayout, scope: str):
        """Build and add the splitter (event tree + JSON editor) and action buttons."""
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Hook events tree + reference button
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        events_label = QLabel("Hook Events:")
        events_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY};")
        left_layout.addWidget(events_label)

        events_tree = QTreeWidget()
        events_tree.setHeaderHidden(True)
        events_tree.setStyleSheet(f"""
            QTreeWidget {{
                border-radius: 3px;
                padding: 3px;
                font-size: {theme.FONT_SIZE_NORMAL}px;
            }}
            QTreeWidget::item {{
                padding: 3px;
            }}
        """)
        self._build_event_tree(events_tree)
        events_tree.expandAll()
        events_tree.itemClicked.connect(
            lambda item, col, s=scope: self.on_event_selected(s, item, col)
        )
        left_layout.addWidget(events_tree)

        # Reference button
        ref_btn = QPushButton("ℹ️ Hook Reference")
        ref_btn.setToolTip("Show full hooks reference documentation")
        ref_btn.clicked.connect(lambda: HookReferenceDialog(self).exec())
        left_layout.addWidget(ref_btn)

        splitter.addWidget(left_panel)

        # Right panel - Hooks JSON editor
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)

        editor_label = QLabel("Hooks Configuration (JSON):")
        editor_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY};")
        right_layout.addWidget(editor_label)

        editor = QTextEdit()
        editor.setStyleSheet(f"""
            QTextEdit {{
                border-radius: 3px;
                padding: 8px;
                font-family: {theme.FONT_FAMILY_MONO};
                font-size: {theme.FONT_SIZE_NORMAL}px;
            }}
        """)
        right_layout.addWidget(editor)

        splitter.addWidget(right_panel)
        splitter.setSizes([350, 650])
        layout.addWidget(splitter, 1)

        # Store references
        self.scope_widgets[scope]['events_tree'] = events_tree
        self.scope_widgets[scope]['editor'] = editor

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        add_btn = QPushButton("➕ Add Hook")
        add_btn.setToolTip("Add a new hook event")
        remove_btn = QPushButton("➖ Remove Hook")
        remove_btn.setToolTip("Remove the selected hook event")
        reload_btn = QPushButton("🔄 Reload")
        reload_btn.setToolTip("Reload hooks configuration from file")
        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip("Save hooks configuration to settings.json")
        backup_btn = QPushButton("📦 Backup & Save")
        backup_btn.setToolTip("Create timestamped backup before saving hooks configuration")
        validate_btn = QPushButton("✓ Validate JSON")
        validate_btn.setToolTip("Validate hooks configuration JSON syntax")

        add_btn.clicked.connect(lambda: self.add_hook(scope))
        remove_btn.clicked.connect(lambda: self.remove_hook(scope))
        reload_btn.clicked.connect(lambda: self.load_hooks(scope))
        save_btn.clicked.connect(lambda: self.save_hooks(scope))
        backup_btn.clicked.connect(lambda: self.backup_and_save(scope))
        validate_btn.clicked.connect(lambda: self.validate_json(scope))

        button_layout.addWidget(add_btn)
        button_layout.addWidget(remove_btn)
        button_layout.addStretch()
        button_layout.addWidget(reload_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(backup_btn)
        button_layout.addWidget(validate_btn)

        layout.addLayout(button_layout)

    # ── Scope helpers ─────────────────────────────────────────────────────────

    def get_scope_file_path(self, scope):
        """Get file path for the given scope"""
        if scope == "user":
            return self.config_manager.settings_file
        elif scope == "project":
            return self.project_folder / ".claude" / "settings.json"
        else:  # local
            return self.project_folder / ".claude" / "settings.local.json"

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
                self.scope_widgets[scope]['folder_edit'].setText(folder)
            file_path = self.get_scope_file_path(scope)
            self.scope_widgets[scope]['path_label'].setText(f"File: {file_path}")
            self.load_hooks(scope)

    def get_scope_display_name(self, scope):
        """Get display name for current scope"""
        return {"user": "User", "project": "Project", "local": "Local"}.get(scope, "Unknown")

    # ── Data methods ──────────────────────────────────────────────────────────

    def load_hooks(self, scope):
        """Load hooks from current scope settings"""
        try:
            file_path = self.get_scope_file_path(scope)

            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = {}

            self.scope_widgets[scope]['config'] = settings.get("hooks", {})

            formatted_json = json.dumps({"hooks": self.scope_widgets[scope]['config']}, indent=2)
            self.scope_widgets[scope]['editor'].setPlainText(formatted_json)

            self.update_events_list(scope)

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load hooks:\n{str(e)}")

    def update_events_list(self, scope):
        """Update tree icons to reflect configured hooks."""
        tree = self.scope_widgets[scope]['events_tree']
        hooks_config = self.scope_widgets[scope]['config']

        for i in range(tree.topLevelItemCount()):
            group = tree.topLevelItem(i)
            for j in range(group.childCount()):
                child = group.child(j)
                event = child.data(0, Qt.ItemDataRole.UserRole)
                has_config = event in hooks_config and len(hooks_config[event]) > 0
                icon = "✓" if has_config else "○"
                child.setText(0, f"{icon} {event}")

    def on_event_selected(self, scope, item: QTreeWidgetItem, column: int):
        """Handle event selection — scroll to it in editor."""
        event_name = item.data(0, Qt.ItemDataRole.UserRole)
        if not event_name:
            return  # group header clicked

        editor = self.scope_widgets[scope]['editor']
        search_text = f'"{event_name}"'
        doc = editor.document()
        cursor = doc.find(search_text)

        if not cursor.isNull():
            cursor.movePosition(cursor.MoveOperation.StartOfLine)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 10)
            editor.setTextCursor(cursor)
            editor.ensureCursorVisible()

    def validate_json(self, scope):
        """Validate JSON in editor"""
        try:
            editor = self.scope_widgets[scope]['editor']
            json.loads(editor.toPlainText())
            QMessageBox.information(self, "Valid", "JSON is valid!")
            return True
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Invalid JSON", f"Invalid JSON:\n{str(e)}")
            return False

    def save_hooks(self, scope):
        """Save hooks configuration (atomic write via temp-file-and-rename)."""
        if not self.validate_json(scope):
            return

        try:
            import shutil
            import tempfile

            editor = self.scope_widgets[scope]['editor']
            config = json.loads(editor.toPlainText())
            hooks = config.get("hooks", {})

            file_path = self.get_scope_file_path(scope)

            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = {}
                file_path.parent.mkdir(parents=True, exist_ok=True)

            settings["hooks"] = hooks

            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False,
                dir=file_path.parent, encoding='utf-8'
            ) as tmp:
                json.dump(settings, tmp, indent=2)
                tmp_path = tmp.name
            shutil.move(tmp_path, file_path)

            self.scope_widgets[scope]['config'] = hooks
            self.update_events_list(scope)
            QMessageBox.information(self, "Saved", f"Hooks saved to {self.get_scope_display_name(scope)} scope!")

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n{str(e)}")

    def backup_and_save(self, scope):
        """Create backup before saving"""
        try:
            file_path = self.get_scope_file_path(scope)
            if file_path.exists():
                self.backup_manager.create_file_backup(file_path)
            self.save_hooks(scope)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed:\n{str(e)}")

    def add_hook(self, scope):
        """Add a new hook for selected event"""
        event_name = self._get_selected_event(scope)
        if not event_name:
            QMessageBox.warning(self, "No Selection", "Please select a hook event from the list.")
            return

        template_hook = {
            "matcher": "ToolName",
            "hooks": [
                {
                    "type": "command",
                    "command": "echo 'Hook triggered'",
                    "timeout": 600
                }
            ]
        }

        hooks_config = self.scope_widgets[scope]['config']
        if event_name not in hooks_config:
            hooks_config[event_name] = []

        hooks_config[event_name].append(template_hook)
        self.scope_widgets[scope]['config'] = hooks_config

        formatted_json = json.dumps({"hooks": hooks_config}, indent=2)
        self.scope_widgets[scope]['editor'].setPlainText(formatted_json)
        self.update_events_list(scope)

        QMessageBox.information(
            self,
            "Hook Added",
            f"Template hook added to '{event_name}' event.\n\nEdit the matcher and command as needed, then Save."
        )

    def remove_hook(self, scope):
        """Remove hook for selected event"""
        event_name = self._get_selected_event(scope)
        if not event_name:
            QMessageBox.warning(self, "No Selection", "Please select a hook event from the list.")
            return

        hooks_config = self.scope_widgets[scope]['config']

        if event_name not in hooks_config or len(hooks_config[event_name]) == 0:
            QMessageBox.warning(self, "No Hooks", f"No hooks configured for '{event_name}' event.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Remove all hooks for '{event_name}' event?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            del hooks_config[event_name]
            self.scope_widgets[scope]['config'] = hooks_config

            formatted_json = json.dumps({"hooks": hooks_config}, indent=2)
            self.scope_widgets[scope]['editor'].setPlainText(formatted_json)
            self.update_events_list(scope)

            QMessageBox.information(self, "Removed", f"All hooks removed from '{event_name}' event.\n\nDon't forget to Save.")
