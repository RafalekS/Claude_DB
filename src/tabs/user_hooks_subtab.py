"""
User Hooks Sub-Tab - Manage user-level hooks configuration
Dedicated subtab for hooks in ~/.claude/settings.json
"""

import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QListWidget, QListWidgetItem, QSplitter, QTextBrowser
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme


class UserHooksSubTab(QWidget):
    """Dedicated subtab for user-level hooks configuration"""

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
        layout.setContentsMargins(10, 10, 10, 10)
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
        docs_btn.setStyleSheet(theme.get_button_style())
        docs_btn.setToolTip("Open official hooks documentation")
        docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://docs.claude.com/en/docs/claude-code/hooks")
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

        # Left panel - Hook events list and info
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        # Hook events list
        events_label = QLabel("Hook Events:")
        events_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY};")
        left_layout.addWidget(events_label)

        self.events_list = QListWidget()
        self.events_list.setStyleSheet(f"""
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
        self.events_list.itemClicked.connect(self.on_event_selected)
        left_layout.addWidget(self.events_list)

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

        self.hooks_editor = QTextEdit()
        self.hooks_editor.setStyleSheet(f"""
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
        right_layout.addWidget(self.hooks_editor)

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

        # Info footer
        footer = QLabel(
            "💡 <b>Hook Events:</b> PreToolUse, PostToolUse, UserPromptSubmit, Stop, SessionStart, etc. • "
            "<b>Exit Codes:</b> 0=Success, 2=Blocking error, Other=Non-blocking"
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

    def load_hooks(self):
        """Load hooks from user settings"""
        try:
            settings = self.settings_manager.get_user_settings()
            self.hooks_config = settings.get("hooks", {})

            # Detect old name-based format (keys that aren't in HOOK_EVENTS)
            old_format_hooks = []
            new_format_hooks = {}

            for key, value in self.hooks_config.items():
                if key in self.HOOK_EVENTS:
                    # New event-based format
                    new_format_hooks[key] = value
                else:
                    # Old name-based format
                    old_format_hooks.append(key)

            # Display in editor with warning if old format detected
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

            # Update events list
            self.update_events_list()

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load hooks:\n{str(e)}")

    def update_events_list(self):
        """Update the events list with configured hooks"""
        self.events_list.clear()

        # Add new format events
        for event in self.HOOK_EVENTS:
            # Check if hook is configured
            has_config = event in self.hooks_config and len(self.hooks_config[event]) > 0
            icon = "✓" if has_config else "○"

            item_text = f"{icon} {event}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, event)
            self.events_list.addItem(item)

        # Check for old format hooks (not in HOOK_EVENTS)
        old_format_hooks = [key for key in self.hooks_config.keys() if key not in self.HOOK_EVENTS]

        if old_format_hooks:
            # Add separator
            separator = QListWidgetItem("─── OLD FORMAT ───")
            separator.setFlags(Qt.ItemFlag.NoItemFlags)
            self.events_list.addItem(separator)

            # Add old format hooks
            for hook_name in old_format_hooks:
                item_text = f"⚠️ {hook_name} (old format)"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, hook_name)
                self.events_list.addItem(item)

    def on_event_selected(self, item):
        """Handle event selection - scroll to it in editor"""
        event_name = item.data(Qt.ItemDataRole.UserRole)

        if event_name:
            text = self.hooks_editor.toPlainText()
            search_text = f'"{event_name}"'

            # Find and highlight in editor
            cursor = self.hooks_editor.textCursor()
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

            # Load existing settings
            settings = self.settings_manager.get_user_settings()

            # Update hooks section
            settings["hooks"] = hooks

            # Save
            self.settings_manager.save_settings(
                self.config_manager.settings_file,
                settings
            )

            self.hooks_config = hooks
            self.update_events_list()
            QMessageBox.information(self, "Saved", "Hooks saved to user settings!")

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n{str(e)}")

    def add_hook(self):
        """Add a new hook for selected event"""
        selected_items = self.events_list.selectedItems()
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
        if event_name not in self.hooks_config:
            self.hooks_config[event_name] = []

        self.hooks_config[event_name].append(template_hook)

        # Update editor
        formatted_json = json.dumps({"hooks": self.hooks_config}, indent=2)
        self.hooks_editor.setPlainText(formatted_json)
        self.update_events_list()

        QMessageBox.information(
            self,
            "Hook Added",
            f"Template hook added to '{event_name}' event.\n\nEdit the matcher and command as needed, then Save."
        )

    def edit_hook(self):
        """Edit hooks for selected event"""
        selected_items = self.events_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a hook event from the list to edit."
            )
            return

        event_name = selected_items[0].data(Qt.ItemDataRole.UserRole)

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

        # Find the hook in the editor and highlight it
        text = self.hooks_editor.toPlainText()
        search_text = f'"{event_name}"'

        # Find and highlight in editor
        cursor = self.hooks_editor.textCursor()
        doc = self.hooks_editor.document()
        cursor = doc.find(search_text)

        if not cursor.isNull():
            # Select the entire hook block (rough estimation)
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
        selected_items = self.events_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a hook event from the list.")
            return

        event_name = selected_items[0].data(Qt.ItemDataRole.UserRole)

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

            # Update editor
            formatted_json = json.dumps({"hooks": self.hooks_config}, indent=2)
            self.hooks_editor.setPlainText(formatted_json)
            self.update_events_list()

            QMessageBox.information(self, "Removed", f"All hooks removed from '{event_name}' event.\n\nDon't forget to Save.")
