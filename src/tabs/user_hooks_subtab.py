"""
User Hooks Sub-Tab - Manage user-level hooks configuration
Dedicated subtab for hooks in ~/.claude/settings.json
"""

import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QTreeWidget, QTreeWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont

from utils import theme
from tabs.hooks_shared import HOOK_EVENT_GROUPS, HOOK_EVENTS, HookReferenceDialog


class UserHooksSubTab(QWidget):
    """Dedicated subtab for user-level hooks configuration"""

    def __init__(self, config_manager, backup_manager, settings_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.settings_manager = settings_manager
        self.hooks_config = {}
        self.init_ui()
        self.load_hooks()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        # Header
        header_layout = QHBoxLayout()

        header = QLabel("User Hooks Configuration")
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

        # File path info
        path_label = QLabel(f"File: {self.config_manager.settings_file}")
        path_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(path_label)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Hook events tree + reference button
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        # Hook events label
        events_label = QLabel("Hook Events:")
        events_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY};")
        left_layout.addWidget(events_label)

        # Grouped tree widget
        self.events_tree = QTreeWidget()
        self.events_tree.setHeaderHidden(True)
        self.events_tree.setStyleSheet(f"""
            QTreeWidget {{
                border-radius: 3px;
                padding: 3px;
                font-size: {theme.FONT_SIZE_NORMAL}px;
            }}
            QTreeWidget::item {{
                padding: 3px;
            }}
        """)
        self._build_event_tree()
        self.events_tree.expandAll()
        self.events_tree.itemClicked.connect(self.on_event_selected)
        left_layout.addWidget(self.events_tree)

        # Reference button (replaces inline info browser)
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

        self.hooks_editor = QTextEdit()
        self.hooks_editor.setStyleSheet(f"""
            QTextEdit {{
                border-radius: 3px;
                padding: 8px;
                font-family: {theme.FONT_FAMILY_MONO};
                font-size: {theme.FONT_SIZE_NORMAL}px;
            }}
        """)
        right_layout.addWidget(self.hooks_editor)

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

        add_btn.clicked.connect(self.add_hook)
        edit_btn.clicked.connect(self.edit_hook)
        remove_btn.clicked.connect(self.remove_hook)
        reload_btn.clicked.connect(self.load_hooks)
        save_btn.clicked.connect(self.save_hooks)
        validate_btn.clicked.connect(self.validate_json)

        button_layout.addWidget(add_btn)
        button_layout.addWidget(edit_btn)
        button_layout.addWidget(remove_btn)
        button_layout.addStretch()
        button_layout.addWidget(reload_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(validate_btn)

        layout.addLayout(button_layout)

    # ── Tree helpers ──────────────────────────────────────────────────────────

    def _build_event_tree(self):
        """Populate the QTreeWidget with grouped hook events."""
        bold = QFont()
        bold.setBold(True)
        for group_label, events in HOOK_EVENT_GROUPS.items():
            group_item = QTreeWidgetItem([group_label])
            group_item.setFont(0, bold)
            group_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            group_item.setData(0, Qt.ItemDataRole.UserRole, None)
            self.events_tree.addTopLevelItem(group_item)
            for event in events:
                child = QTreeWidgetItem([f"○ {event}"])
                child.setData(0, Qt.ItemDataRole.UserRole, event)
                group_item.addChild(child)

    def _get_selected_event(self) -> str | None:
        """Return the selected event name, or None if nothing / group selected."""
        selected = self.events_tree.selectedItems()
        if not selected:
            return None
        return selected[0].data(0, Qt.ItemDataRole.UserRole)

    # ── Data methods ──────────────────────────────────────────────────────────

    def load_hooks(self):
        """Load hooks from user settings"""
        try:
            settings = self.settings_manager.get_user_settings()
            self.hooks_config = settings.get("hooks", {})

            # Detect old name-based format (keys that aren't in HOOK_EVENTS)
            old_format_hooks = [key for key in self.hooks_config if key not in HOOK_EVENTS]

            if old_format_hooks:
                warning = (
                    "# WARNING: Old name-based hooks detected!\n"
                    f"# These hooks use old format: {', '.join(old_format_hooks)}\n"
                    "# Old format: {\"test\": {\"command\": \"bash\", ...}}\n"
                    "# New format: {\"PreToolUse\": [{\"matcher\": \"*\", \"hooks\": [...]}]}\n"
                    "# Please migrate to new event-based format.\n\n"
                )
                formatted_json = json.dumps({"hooks": self.hooks_config}, indent=2)
                self.hooks_editor.setPlainText(warning + formatted_json)
            else:
                formatted_json = json.dumps({"hooks": self.hooks_config}, indent=2)
                self.hooks_editor.setPlainText(formatted_json)

            self.update_events_list()

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load hooks:\n{str(e)}")

    def update_events_list(self):
        """Update tree icons to reflect configured hooks."""
        for i in range(self.events_tree.topLevelItemCount()):
            group = self.events_tree.topLevelItem(i)
            for j in range(group.childCount()):
                child = group.child(j)
                event = child.data(0, Qt.ItemDataRole.UserRole)
                has_config = event in self.hooks_config and len(self.hooks_config[event]) > 0
                icon = "✓" if has_config else "○"
                child.setText(0, f"{icon} {event}")

    def on_event_selected(self, item: QTreeWidgetItem, column: int):
        """Handle event selection — scroll to it in the editor."""
        event_name = item.data(0, Qt.ItemDataRole.UserRole)
        if not event_name:
            return  # group header clicked

        search_text = f'"{event_name}"'
        doc = self.hooks_editor.document()
        cursor = doc.find(search_text)

        if not cursor.isNull():
            cursor.movePosition(cursor.MoveOperation.StartOfLine)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 10)
            self.hooks_editor.setTextCursor(cursor)
            self.hooks_editor.ensureCursorVisible()

    def validate_json(self):
        """Validate JSON in editor"""
        try:
            json.loads(self.hooks_editor.toPlainText())
            QMessageBox.information(self, "Valid", "JSON is valid!")
            return True
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Invalid JSON", f"Invalid JSON:\n{str(e)}")
            return False

    def save_hooks(self):
        """Save hooks configuration"""
        if not self.validate_json():
            return

        try:
            content = self.hooks_editor.toPlainText()
            config = json.loads(content)
            hooks = config.get("hooks", {})

            settings = self.settings_manager.get_user_settings()
            settings["hooks"] = hooks
            self.settings_manager.save_settings(
                self.config_manager.settings_file,
                settings
            )

            self.hooks_config = hooks
            self.update_events_list()
            QMessageBox.information(self, "Saved", "Hooks saved to user settings!")

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n{str(e)}")

    # Templates for each handler type
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

    def add_hook(self):
        """Add a new hook for selected event"""
        event_name = self._get_selected_event()
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

        if event_name not in self.hooks_config:
            self.hooks_config[event_name] = []
        self.hooks_config[event_name].append(template_hook)

        formatted_json = json.dumps({"hooks": self.hooks_config}, indent=2)
        self.hooks_editor.setPlainText(formatted_json)
        self.update_events_list()

        QMessageBox.information(
            self,
            "Hook Added",
            f"{hook_type} hook template added to '{event_name}'.\n\nEdit the fields as needed, then Save."
        )

    def edit_hook(self):
        """Edit hooks for selected event"""
        event_name = self._get_selected_event()
        if not event_name:
            QMessageBox.warning(self, "No Selection", "Please select a hook event from the list to edit.")
            return

        if event_name not in self.hooks_config or len(self.hooks_config[event_name]) == 0:
            reply = QMessageBox.question(
                self,
                "No Hooks",
                f"No hooks configured for '{event_name}'.\n\nWould you like to add one?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.add_hook()
            return

        search_text = f'"{event_name}"'
        doc = self.hooks_editor.document()
        cursor = doc.find(search_text)

        if not cursor.isNull():
            cursor.movePosition(cursor.MoveOperation.StartOfLine)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 15)
            self.hooks_editor.setTextCursor(cursor)
            self.hooks_editor.ensureCursorVisible()
            self.hooks_editor.setFocus()

        QMessageBox.information(
            self,
            "Edit Hook",
            f"Hooks for '{event_name}' are highlighted in the editor.\n\n"
            "Edit the JSON directly, then click 'Validate JSON' to check syntax "
            "and 'Save' to save changes."
        )

    def remove_hook(self):
        """Remove hook for selected event"""
        event_name = self._get_selected_event()
        if not event_name:
            QMessageBox.warning(self, "No Selection", "Please select a hook event from the list.")
            return

        if event_name not in self.hooks_config or len(self.hooks_config[event_name]) == 0:
            QMessageBox.warning(self, "No Hooks", f"No hooks configured for '{event_name}' event.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Remove all hooks for '{event_name}' event?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            del self.hooks_config[event_name]

            formatted_json = json.dumps({"hooks": self.hooks_config}, indent=2)
            self.hooks_editor.setPlainText(formatted_json)
            self.update_events_list()

            QMessageBox.information(self, "Removed", f"All hooks removed from '{event_name}' event.\n\nDon't forget to Save.")
