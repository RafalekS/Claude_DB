"""
Project Hooks Sub-Tab - Manage project-level hooks configuration
Dedicated subtab for hooks in .claude/settings.json (Shared) and .claude/settings.local.json (Local)
"""

import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QListWidget, QListWidgetItem, QSplitter, QTabWidget, QTextBrowser
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme


class ProjectHooksSubTab(QWidget):
    """Dedicated subtab for project-level hooks configuration (Shared/Local)"""

    # All available hook events (EVENT-BASED, not name-based)
    HOOK_EVENTS = [
        "PreToolUse",
        "PostToolUse",
        "Notification",
        "UserPromptSubmit",
        "Stop",
        "SubagentStop",
        "PreCompact",
        "SessionStart",
        "SessionEnd"
    ]

    def __init__(self, config_manager, backup_manager, settings_manager, project_context):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.settings_manager = settings_manager
        self.project_context = project_context
        self.init_ui()

        # Connect to project context changes
        self.project_context.project_changed.connect(self.on_project_changed)

        # Load if project is set
        if self.project_context.has_project():
            self.load_all_hooks()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
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
        docs_btn.setStyleSheet(theme.get_button_style())
        docs_btn.setToolTip("Open official hooks documentation")
        docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://docs.claude.com/en/docs/claude-code/hooks")
        ))

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(docs_btn)
        layout.addLayout(header_layout)

        # Nested tabs for Shared vs Local
        self.scope_tabs = QTabWidget()
        self.scope_tabs.setStyleSheet(theme.get_tab_widget_style())

        # Shared tab (.claude/settings.json)
        self.shared_editor = self.create_hooks_editor("shared")
        self.scope_tabs.addTab(self.shared_editor, "📤 Shared (.claude/settings.json)")

        # Local tab (.claude/settings.local.json)
        self.local_editor = self.create_hooks_editor("local")
        self.scope_tabs.addTab(self.local_editor, "🔒 Local (.claude/settings.local.json)")

        layout.addWidget(self.scope_tabs, 1)

        # Info footer
        footer = QLabel(
            "💡 <b>Shared:</b> Team-shared hooks (committed to git) • "
            "<b>Local:</b> User-specific overrides (gitignored) • "
            "<b>Hook Events:</b> PreToolUse, PostToolUse, UserPromptSubmit, Stop, SessionStart, etc."
        )
        footer.setWordWrap(True)
        footer.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; "
            f"padding: 8px; "
            f"background-color: {theme.BG_MEDIUM}; "
            f"border-radius: 3px;"
        )
        layout.addWidget(footer)

    def create_hooks_editor(self, scope: str) -> QWidget:
        """Create hooks editor for a specific scope (shared or local)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # File path label
        path_label = QLabel()
        if scope == "shared":
            path_label.setText(".claude/settings.json (team-shared)")
        else:
            path_label.setText(".claude/settings.local.json (user-specific)")
        path_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(path_label)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Hook events list and info
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        # Hook events list
        events_label = QLabel("Hook Events:")
        events_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY};")
        left_layout.addWidget(events_label)

        events_list = QListWidget()
        events_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                padding: 5px;
                font-size: {theme.FONT_SIZE_NORMAL}px;
            }}
            QListWidget::item {{
                padding: 5px;
            }}
            QListWidget::item:selected {{
                background-color: {theme.ACCENT_PRIMARY};
                color: {theme.BG_DARK};
            }}
        """)
        events_list.itemClicked.connect(lambda item: self.on_event_selected(scope, item))
        left_layout.addWidget(events_list)

        # Info browser
        info_label = QLabel("Hook Info:")
        info_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY};")
        left_layout.addWidget(info_label)

        info_browser = QTextBrowser()
        info_browser.setOpenExternalLinks(True)
        info_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                padding: 8px;
                font-size: {theme.FONT_SIZE_SMALL}px;
            }}
        """)
        self.load_hook_info(info_browser)
        left_layout.addWidget(info_browser)

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
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: {theme.FONT_SIZE_NORMAL}px;
            }}
        """)
        right_layout.addWidget(editor)

        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])
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

        for btn in [add_btn, edit_btn, remove_btn, reload_btn, save_btn, validate_btn]:
            btn.setStyleSheet(theme.get_button_style())

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
        if not hasattr(self, 'editors'):
            self.editors = {}
        self.editors[scope] = {
            'events_list': events_list,
            'editor': editor,
            'hooks_config': {}
        }

        return widget

    def load_hook_info(self, info_browser):
        """Load hook information into info browser"""
        html = f"""
        <html>
        <body style="color: {theme.FG_PRIMARY};">
            <h3 style="color: {theme.ACCENT_PRIMARY};">Hook Events</h3>
            <p><b>PreToolUse</b> - Before tool execution</p>
            <p><b>PostToolUse</b> - After tool execution</p>
            <p><b>Notification</b> - On notifications</p>
            <p><b>UserPromptSubmit</b> - When user submits prompt</p>
            <p><b>Stop</b> - When agent finishes</p>
            <p><b>SubagentStop</b> - When subagent finishes</p>
            <p><b>PreCompact</b> - Before context compaction</p>
            <p><b>SessionStart</b> - Session startup</p>
            <p><b>SessionEnd</b> - Session termination</p>

            <h3 style="color: {theme.ACCENT_PRIMARY}; margin-top: 15px;">Example</h3>
            <pre style="background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px;">{{
  "hooks": {{
    "PostToolUse": [{{
      "matcher": "Write",
      "hooks": [{{
        "type": "command",
        "command": "echo 'File written'",
        "timeout": 60
      }}]
    }}]
  }}
}}</pre>
        </body>
        </html>
        """
        info_browser.setHtml(html)

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

        try:
            editor_data = self.editors[scope]

            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(self.project_context.get_project())
            else:
                settings = self.settings_manager.get_project_local_settings(self.project_context.get_project())

            hooks_config = settings.get("hooks", {})
            editor_data['hooks_config'] = hooks_config

            # Detect old name-based format (keys that aren't in HOOK_EVENTS)
            old_format_hooks = [key for key in hooks_config.keys() if key not in self.HOOK_EVENTS]

            # Display in editor with warning if old format detected
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

            # Update events list
            self.update_events_list(scope)

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load {scope} hooks:\n{str(e)}")

    def update_events_list(self, scope: str):
        """Update the events list with configured hooks"""
        editor_data = self.editors[scope]
        events_list = editor_data['events_list']
        hooks_config = editor_data['hooks_config']

        events_list.clear()

        # Add new format events
        for event in self.HOOK_EVENTS:
            # Check if hook is configured
            has_config = event in hooks_config and len(hooks_config[event]) > 0
            icon = "✓" if has_config else "○"

            item_text = f"{icon} {event}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, event)
            events_list.addItem(item)

        # Check for old format hooks (not in HOOK_EVENTS)
        old_format_hooks = [key for key in hooks_config.keys() if key not in self.HOOK_EVENTS]

        if old_format_hooks:
            # Add separator
            separator = QListWidgetItem("─── OLD FORMAT ───")
            separator.setFlags(Qt.ItemFlag.NoItemFlags)
            events_list.addItem(separator)

            # Add old format hooks
            for hook_name in old_format_hooks:
                item_text = f"⚠️ {hook_name} (old format)"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, hook_name)
                events_list.addItem(item)

    def on_event_selected(self, scope: str, item):
        """Handle event selection - scroll to it in editor"""
        event_name = item.data(Qt.ItemDataRole.UserRole)
        editor_data = self.editors[scope]
        editor = editor_data['editor']

        if event_name:
            text = editor.toPlainText()
            search_text = f'"{event_name}"'

            # Find and highlight in editor
            cursor = editor.textCursor()
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

            # Update hooks section
            settings["hooks"] = hooks

            # Save
            self.settings_manager.save_settings(settings_file, settings)

            editor_data['hooks_config'] = hooks
            self.update_events_list(scope)
            QMessageBox.information(self, "Saved", f"Hooks saved to {scope} settings!")

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n{str(e)}")

    def add_hook(self, scope: str):
        """Add a new hook for selected event"""
        if not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        editor_data = self.editors[scope]
        events_list = editor_data['events_list']
        selected_items = events_list.selectedItems()

        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a hook event from the list.")
            return

        event_name = selected_items[0].data(Qt.ItemDataRole.UserRole)

        # Create a template hook entry
        template_hook = {
            "matcher": "ToolName",  # or * for all tools
            "hooks": [
                {
                    "type": "command",
                    "command": "echo 'Hook triggered'",
                    "timeout": 60
                }
            ]
        }

        # Add to hooks config
        hooks_config = editor_data['hooks_config']
        if event_name not in hooks_config:
            hooks_config[event_name] = []

        hooks_config[event_name].append(template_hook)
        editor_data['hooks_config'] = hooks_config

        # Update editor
        formatted_json = json.dumps({"hooks": hooks_config}, indent=2)
        editor_data['editor'].setPlainText(formatted_json)
        self.update_events_list(scope)

        QMessageBox.information(
            self,
            "Hook Added",
            f"Template hook added to '{event_name}' event.\n\nEdit the matcher and command as needed, then Save."
        )

    def edit_hook(self, scope: str):
        """Edit hooks for selected event"""
        if not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        editor_data = self.editors[scope]
        events_list = editor_data['events_list']
        selected_items = events_list.selectedItems()

        if not selected_items:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a hook event from the list to edit."
            )
            return

        event_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
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

        # Find the hook in the editor and highlight it
        text = editor.toPlainText()
        search_text = f'"{event_name}"'

        # Find and highlight in editor
        cursor = editor.textCursor()
        doc = editor.document()
        cursor = doc.find(search_text)

        if not cursor.isNull():
            # Select the entire hook block (rough estimation)
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

        editor_data = self.editors[scope]
        events_list = editor_data['events_list']
        selected_items = events_list.selectedItems()

        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a hook event from the list.")
            return

        event_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
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

            # Update editor
            formatted_json = json.dumps({"hooks": hooks_config}, indent=2)
            editor_data['editor'].setPlainText(formatted_json)
            self.update_events_list(scope)

            QMessageBox.information(self, "Removed", f"All hooks removed from '{event_name}' event.\n\nDon't forget to Save.")
