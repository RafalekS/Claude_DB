"""
Hooks Tab - Manage Claude Code hooks from all settings sources
"""

import json
from pathlib import Path
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QSplitter, QListWidget,
    QListWidgetItem, QTextBrowser, QLineEdit, QFileDialog, QTabWidget
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme


class HooksTab(QWidget):
    """Tab for managing Claude Code hooks"""

    # All available hook events
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

    def __init__(self, config_manager, backup_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.project_folder = Path.cwd()  # Default to current directory
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header with docs link
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        header = QLabel("Hooks Configuration")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")

        docs_btn = QPushButton("📖 Hooks Docs")
        docs_btn.setStyleSheet(theme.get_button_style())
        docs_btn.setToolTip("Open official hooks documentation in browser")
        docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://docs.claude.com/en/docs/claude-code/hooks")
        ))

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(docs_btn)

        layout.addLayout(header_layout)

        # Main tab widget for User / Project / Local
        self.main_tabs = QTabWidget()
        self.main_tabs.setStyleSheet(theme.get_tab_widget_style())

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

        # Info tip with event types and exit codes
        tip_label = QLabel(
            "💡 <b>Hook Events:</b> "
            "PreToolUse (before tool execution) • "
            "PostToolUse (after success) • "
            "UserPromptSubmit (before processing) • "
            "Stop/SubagentStop (response complete) • "
            "SessionStart (initialization) • "
            "Notification (alerts)"
            "<br><b>Exit Code Behavior:</b> "
            "0 = Success • "
            "2 = Blocking error (stderr sent to Claude) • "
            "Other = Non-blocking error (shown to user)"
            "<br><b>MCP Tool Patterns:</b> "
            "<code>mcp__&lt;server&gt;__&lt;tool&gt;</code> (e.g., <code>mcp__github__*</code> for all GitHub tools)"
            "<br><b>Security:</b> "
            "Always review hook commands before deployment • "
            "Hooks run with your user permissions"
        )
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(tip_label)

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

        # Store references for this scope
        if not hasattr(self, 'scope_widgets'):
            self.scope_widgets = {}

        self.scope_widgets[scope] = {
            'path_label': path_label,
            'config': {}
        }

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

        # Store references
        self.scope_widgets[scope]['events_list'] = events_list
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

        for btn in [add_btn, remove_btn, reload_btn, save_btn, backup_btn, validate_btn]:
            btn.setStyleSheet(theme.get_button_style())

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
        project_folder_edit.setStyleSheet(theme.get_line_edit_style())

        browse_folder_btn = QPushButton("Browse...")
        browse_folder_btn.setStyleSheet(theme.get_button_style())
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

        # Store references for this scope
        if not hasattr(self, 'scope_widgets'):
            self.scope_widgets = {}

        self.scope_widgets[scope] = {
            'path_label': path_label,
            'folder_edit': project_folder_edit,
            'config': {}
        }

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

        # Store references
        self.scope_widgets[scope]['events_list'] = events_list
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

        for btn in [add_btn, remove_btn, reload_btn, save_btn, backup_btn, validate_btn]:
            btn.setStyleSheet(theme.get_button_style())

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

        # Load initial data
        self.load_hooks(scope)

        return widget

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
                self.scope_widgets[scope]['folder_edit'].setText(str(Path.home()))
            # Update file path
            file_path = self.get_scope_file_path(scope)
            self.scope_widgets[scope]['path_label'].setText(f"File: {file_path}")
            # Reload hooks from new folder
            self.load_hooks(scope)

    def get_scope_display_name(self, scope):
        """Get display name for current scope"""
        return {
            "user": "User",
            "project": "Project",
            "local": "Local"
        }.get(scope, "Unknown")

    def load_hooks(self, scope):
        """Load hooks from current scope settings"""
        try:
            file_path = self.get_scope_file_path(scope)

            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = {}

            # Extract hooks section
            self.scope_widgets[scope]['config'] = settings.get("hooks", {})

            # Display in editor
            formatted_json = json.dumps({"hooks": self.scope_widgets[scope]['config']}, indent=2)
            self.scope_widgets[scope]['editor'].setPlainText(formatted_json)

            # Update events list
            self.update_events_list(scope)

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load hooks:\n{str(e)}")

    def update_events_list(self, scope):
        """Update the events list with configured hooks"""
        events_list = self.scope_widgets[scope]['events_list']
        hooks_config = self.scope_widgets[scope]['config']

        events_list.clear()

        for event in self.HOOK_EVENTS:
            # Check if hook is configured
            has_config = event in hooks_config and len(hooks_config[event]) > 0
            icon = "✓" if has_config else "○"
            color = theme.SUCCESS_COLOR if has_config else theme.FG_SECONDARY

            item_text = f"{icon} {event}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, event)
            events_list.addItem(item)

    def on_event_selected(self, scope, item):
        """Handle event selection - scroll to it in editor"""
        event_name = item.data(Qt.ItemDataRole.UserRole)
        editor = self.scope_widgets[scope]['editor']

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
        """Save hooks configuration"""
        if not self.validate_json(scope):
            return

        try:
            editor = self.scope_widgets[scope]['editor']
            content = editor.toPlainText()
            config = json.loads(content)
            hooks = config.get("hooks", {})

            file_path = self.get_scope_file_path(scope)

            # Load existing settings
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = {}
                file_path.parent.mkdir(parents=True, exist_ok=True)

            # Update hooks section
            settings["hooks"] = hooks

            # Save
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)

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
        events_list = self.scope_widgets[scope]['events_list']
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
        hooks_config = self.scope_widgets[scope]['config']
        if event_name not in hooks_config:
            hooks_config[event_name] = []

        hooks_config[event_name].append(template_hook)
        self.scope_widgets[scope]['config'] = hooks_config

        # Update editor
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
        events_list = self.scope_widgets[scope]['events_list']
        selected_items = events_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a hook event from the list.")
            return

        event_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
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

            # Update editor
            formatted_json = json.dumps({"hooks": hooks_config}, indent=2)
            self.scope_widgets[scope]['editor'].setPlainText(formatted_json)
            self.update_events_list(scope)

            QMessageBox.information(self, "Removed", f"All hooks removed from '{event_name}' event.\n\nDon't forget to Save.")
