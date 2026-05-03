"""
Project Hooks Sub-Tab - Manage project-level hooks configuration
Dedicated subtab for hooks in .claude/settings.json (Shared) and .claude/settings.local.json (Local)
"""

import json
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QTreeWidget, QTreeWidgetItem, QSplitter, QTabWidget
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont

from utils import theme
from tabs.hooks_shared import HOOK_EVENT_GROUPS, HOOK_EVENTS, HookReferenceDialog

logger = logging.getLogger(__name__)


class ProjectHooksSubTab(QWidget):
    """Dedicated subtab for project-level hooks configuration (Shared/Local)"""

    def __init__(self, config_manager, backup_manager, settings_manager, project_context):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.settings_manager = settings_manager
        self.project_context = project_context
        self.editors = {}
        self.init_ui()

        # Connect to project context changes
        self.project_context.project_changed.connect(self.on_project_changed)

        # Load if project is set
        if self.project_context.has_project():
            self.load_all_hooks()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        # Header
        header_layout = QHBoxLayout()

        header = QLabel("Project Hooks Configuration")
        header.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; "
            f"font-weight: bold; "
            f"color: {theme.ACCENT_PRIMARY};"
        )

        docs_btn = QPushButton("📖 Hooks Docs")
        docs_btn.setToolTip("Open official hooks documentation")
        docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://code.claude.com/docs/en/hooks")
        ))

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(docs_btn)
        layout.addLayout(header_layout)

        # Nested tabs for Shared vs Local
        self.scope_tabs = QTabWidget()

        # Shared tab (.claude/settings.json)
        self.shared_editor = self.create_hooks_editor("shared")
        self.scope_tabs.addTab(self.shared_editor, "📤 Shared (.claude/settings.json)")

        # Local tab (.claude/settings.local.json)
        self.local_editor = self.create_hooks_editor("local")
        self.scope_tabs.addTab(self.local_editor, "🔒 Local (.claude/settings.local.json)")

        layout.addWidget(self.scope_tabs, 1)

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

    def create_hooks_editor(self, scope: str) -> QWidget:
        """Create hooks editor for a specific scope (shared or local)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # File path label (stored as instance var so load_hooks can update it)
        path_label = QLabel("(no project selected)")
        path_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(path_label)
        if scope == "shared":
            self.shared_path_label = path_label
        else:
            self.local_path_label = path_label

        # Splitter
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

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        add_btn = QPushButton("➕ Add Hook")
        add_btn.setToolTip("Add a new hook event")
        edit_btn = QPushButton("✏️ Edit Hooks")
        edit_btn.setToolTip("Edit hooks for selected event in JSON editor")
        remove_btn = QPushButton("➖ Remove Hook")
        remove_btn.setToolTip("Remove the selected hook event")
        reload_btn = QPushButton("🔄 Reload")
        reload_btn.setToolTip("Reload hooks configuration from file")
        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip("Save hooks configuration to settings.json")
        validate_btn = QPushButton("✓ Validate JSON")
        validate_btn.setToolTip("Validate hooks configuration JSON syntax")

        add_btn.clicked.connect(lambda: self.add_hook(scope))
        edit_btn.clicked.connect(lambda: self.edit_hook(scope))
        remove_btn.clicked.connect(lambda: self.remove_hook(scope))
        reload_btn.clicked.connect(lambda: self.load_hooks(scope))
        save_btn.clicked.connect(lambda: self.save_hooks(scope))
        validate_btn.clicked.connect(lambda: self.validate_json(scope))

        button_layout.addWidget(add_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(remove_btn)
        button_layout.addStretch()
        button_layout.addWidget(reload_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(validate_btn)

        layout.addLayout(button_layout)

        # Store references
        self.editors[scope] = {
            'events_tree': events_tree,
            'editor': editor,
            'hooks_config': {}
        }

        return widget

    # ── Tree helpers ──────────────────────────────────────────────────────────

    def _get_selected_event(self, scope: str) -> str | None:
        """Return the selected event name for a scope, or None."""
        tree = self.editors[scope]['events_tree']
        selected = tree.selectedItems()
        if not selected:
            return None
        return selected[0].data(0, Qt.ItemDataRole.UserRole)

    # ── Data methods ──────────────────────────────────────────────────────────

    def on_project_changed(self, project_path: Path):
        """Handle project change"""
        self.load_all_hooks()

    def load_all_hooks(self):
        """Load hooks for both scopes"""
        self.load_hooks("shared")
        self.load_hooks("local")

    def load_hooks(self, scope: str):
        """Load hooks for a specific scope"""
        if not self.project_context.has_project():
            return

        project_path = self.project_context.get_project()
        if scope == "shared":
            full_path = project_path / ".claude" / "settings.json"
            self.shared_path_label.setText(f"File: {full_path} (team-shared)")
        else:
            full_path = project_path / ".claude" / "settings.local.json"
            self.local_path_label.setText(f"File: {full_path} (user-specific)")

        try:
            editor_data = self.editors[scope]

            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(project_path)
            else:
                settings = self.settings_manager.get_project_local_settings(project_path)

            hooks_config = settings.get("hooks", {})
            editor_data['hooks_config'] = hooks_config

            old_format_hooks = [key for key in hooks_config if key not in HOOK_EVENTS]

            if old_format_hooks:
                warning = (
                    "# WARNING: Old name-based hooks detected!\n"
                    f"# These hooks use old format: {', '.join(old_format_hooks)}\n"
                    "# Old format: {\"test\": {\"command\": \"bash\", ...}}\n"
                    "# New format: {\"PreToolUse\": [{\"matcher\": \"*\", \"hooks\": [...]}]}\n"
                    "# Please migrate to new event-based format.\n\n"
                )
                formatted_json = json.dumps({"hooks": hooks_config}, indent=2)
                editor_data['editor'].setPlainText(warning + formatted_json)
            else:
                formatted_json = json.dumps({"hooks": hooks_config}, indent=2)
                editor_data['editor'].setPlainText(formatted_json)

            self.update_events_list(scope)

        except Exception as e:
            logger.error("Failed to load %s hooks: %s", scope, e)
            QMessageBox.critical(self, "Load Error", f"Failed to load {scope} hooks:\n{str(e)}")

    def update_events_list(self, scope: str):
        """Update tree icons to reflect configured hooks."""
        tree = self.editors[scope]['events_tree']
        hooks_config = self.editors[scope]['hooks_config']

        for i in range(tree.topLevelItemCount()):
            group = tree.topLevelItem(i)
            for j in range(group.childCount()):
                child = group.child(j)
                event = child.data(0, Qt.ItemDataRole.UserRole)
                has_config = event in hooks_config and len(hooks_config[event]) > 0
                icon = "✓" if has_config else "○"
                child.setText(0, f"{icon} {event}")

    def on_event_selected(self, scope: str, item: QTreeWidgetItem, column: int):
        """Handle event selection — scroll to it in editor."""
        event_name = item.data(0, Qt.ItemDataRole.UserRole)
        if not event_name:
            return  # group header clicked

        editor = self.editors[scope]['editor']
        search_text = f'"{event_name}"'
        doc = editor.document()
        cursor = doc.find(search_text)

        if not cursor.isNull():
            cursor.movePosition(cursor.MoveOperation.StartOfLine)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 10)
            editor.setTextCursor(cursor)
            editor.ensureCursorVisible()

    def validate_json(self, scope: str):
        """Validate JSON in editor"""
        try:
            editor_data = self.editors[scope]
            json.loads(editor_data['editor'].toPlainText())
            QMessageBox.information(self, "Valid", "JSON is valid!")
            return True
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in %s hooks editor: %s", scope, e)
            QMessageBox.critical(self, "Invalid JSON", f"Invalid JSON:\n{str(e)}")
            return False

    def save_hooks(self, scope: str):
        """Save hooks configuration"""
        if not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        if not self.validate_json(scope):
            return

        try:
            editor_data = self.editors[scope]
            content = editor_data['editor'].toPlainText()
            config = json.loads(content)
            hooks = config.get("hooks", {})

            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(self.project_context.get_project())
                settings_file = self.project_context.get_project() / ".claude" / "settings.json"
            else:
                settings = self.settings_manager.get_project_local_settings(self.project_context.get_project())
                settings_file = self.project_context.get_project() / ".claude" / "settings.local.json"

            settings["hooks"] = hooks
            self.settings_manager.save_settings(settings_file, settings)

            editor_data['hooks_config'] = hooks
            self.update_events_list(scope)
            QMessageBox.information(self, "Saved", f"Hooks saved to {scope} settings!")

        except Exception as e:
            logger.error("Failed to save %s hooks: %s", scope, e)
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n{str(e)}")

    HOOK_TEMPLATES = {
        "command": {
            "type": "command",
            "command": "echo 'Hook triggered'",
            "timeout": 600,
            "async": False,
            "statusMessage": ""
        },
        "http": {
            "type": "http",
            "url": "https://example.com/webhook",
            "headers": {"Content-Type": "application/json"},
            "allowedEnvVars": [],
            "timeout": 30
        },
        "prompt": {
            "type": "prompt",
            "model": "claude-haiku-4-5-20251001",
            "prompt": "Should this action proceed? Reply with only yes or no.",
            "timeout": 30
        },
        "agent": {
            "type": "agent",
            "agent": "code-reviewer",
            "model": "claude-haiku-4-5-20251001",
            "timeout": 60
        }
    }

    def add_hook(self, scope: str):
        """Add a new hook for selected event"""
        if not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        event_name = self._get_selected_event(scope)
        if not event_name:
            QMessageBox.warning(self, "No Selection", "Please select a hook event from the list.")
            return

        from PyQt6.QtWidgets import QInputDialog
        hook_type, ok = QInputDialog.getItem(
            self,
            "Hook Handler Type",
            f"Select handler type for '{event_name}':",
            ["command", "http", "prompt", "agent"],
            0,
            False
        )
        if not ok:
            return

        handler = dict(self.HOOK_TEMPLATES[hook_type])
        template_hook = {"matcher": "*", "hooks": [handler]}

        editor_data = self.editors[scope]
        hooks_config = editor_data['hooks_config']
        if event_name not in hooks_config:
            hooks_config[event_name] = []
        hooks_config[event_name].append(template_hook)
        editor_data['hooks_config'] = hooks_config

        formatted_json = json.dumps({"hooks": hooks_config}, indent=2)
        editor_data['editor'].setPlainText(formatted_json)
        self.update_events_list(scope)

        QMessageBox.information(
            self,
            "Hook Added",
            f"{hook_type} hook template added to '{event_name}'.\n\nEdit the fields as needed, then Save."
        )

    def edit_hook(self, scope: str):
        """Edit hooks for selected event"""
        if not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        event_name = self._get_selected_event(scope)
        if not event_name:
            QMessageBox.warning(self, "No Selection", "Please select a hook event from the list to edit.")
            return

        editor_data = self.editors[scope]
        hooks_config = editor_data['hooks_config']
        editor = editor_data['editor']

        if event_name not in hooks_config or len(hooks_config[event_name]) == 0:
            reply = QMessageBox.question(
                self,
                "No Hooks",
                f"No hooks configured for '{event_name}'.\n\nWould you like to add one?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.add_hook(scope)
            return

        search_text = f'"{event_name}"'
        doc = editor.document()
        cursor = doc.find(search_text)

        if not cursor.isNull():
            cursor.movePosition(cursor.MoveOperation.StartOfLine)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 15)
            editor.setTextCursor(cursor)
            editor.ensureCursorVisible()
            editor.setFocus()

        QMessageBox.information(
            self,
            "Edit Hook",
            f"Hooks for '{event_name}' are highlighted in the editor.\n\n"
            "Edit the JSON directly, then click 'Validate JSON' to check syntax "
            "and 'Save' to save changes."
        )

    def remove_hook(self, scope: str):
        """Remove hook for selected event"""
        if not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        event_name = self._get_selected_event(scope)
        if not event_name:
            QMessageBox.warning(self, "No Selection", "Please select a hook event from the list.")
            return

        editor_data = self.editors[scope]
        hooks_config = editor_data['hooks_config']

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
            editor_data['hooks_config'] = hooks_config

            formatted_json = json.dumps({"hooks": hooks_config}, indent=2)
            editor_data['editor'].setPlainText(formatted_json)
            self.update_events_list(scope)

            QMessageBox.information(self, "Removed", f"All hooks removed from '{event_name}' event.\n\nDon't forget to Save.")
