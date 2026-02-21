"""
Settings Tab - Manage Claude Code settings.json
"""

import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QMessageBox, QTabWidget, QLineEdit, QFileDialog
)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.theme import *


class SettingsTab(QWidget):
    """Tab for managing Claude Code settings"""

    def __init__(self, config_manager, backup_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.project_folder = Path.cwd()  # Default to current directory
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)

        # Compact header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(3)

        header = QLabel("Settings")
        header.setStyleSheet("font-size: 12px; font-weight: bold; color: #667eea;")
        header_layout.addWidget(header)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Tabs for User / Project settings
        self.settings_tabs = QTabWidget()
        self.settings_tabs.setStyleSheet(get_tab_widget_style())

        # User settings tab (~/.claude/settings.json)
        self.user_tab = self.create_settings_editor(
            self.config_manager.settings_file,
            "User Settings (~/.claude/settings.json)"
        )
        self.settings_tabs.addTab(self.user_tab, "User Settings")

        # Project settings tab (./.claude/settings.json)
        self.project_tab = self.create_project_settings_editor()
        self.settings_tabs.addTab(self.project_tab, "Project Settings")

        layout.addWidget(self.settings_tabs)

        # Best Practices Tip
        tip_label = QLabel(
            "💡 <b>Settings Hierarchy:</b> "
            "Enterprise Policy (system-wide) → Project (./CLAUDE.md) → User (~/.claude/CLAUDE.md) → Local (./CLAUDE.local.md) • "
            "<br><b>Key Config Commands:</b> "
            "<code>claude config set &lt;key&gt; &lt;value&gt;</code> | "
            "<code>claude config get &lt;key&gt;</code> | "
            "<code>claude config list</code> | "
            "<code>claude config set -g &lt;key&gt; &lt;value&gt;</code> (global)"
            "<br><b>Useful Settings:</b> "
            "preferredNotifChannel (terminal_bell recommended) • "
            "theme (dark/light/daltonized) • "
            "autoUpdates (true/false) • "
            "verbose (true/false)"
            "<br><b>Security:</b> "
            "Use --allowedTools for scoped permissions • "
            "Never use --dangerously-skip-permissions in production • "
            "Keep ~/.claude.json private (chmod 600)"
        )
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet(f"color: {FG_SECONDARY}; background: {BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {FONT_SIZE_SMALL}px;")
        layout.addWidget(tip_label)

    def create_settings_editor(self, file_path, description):
        """Create a settings editor for a specific file"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Buttons row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(3)

        info_label = QLabel(str(file_path))
        info_label.setStyleSheet("color: #999; font-size: 9px;")

        load_btn = QPushButton("Reload")
        load_btn.setToolTip("Reload settings from file (discards unsaved changes)")
        save_btn = QPushButton("Save")
        save_btn.setToolTip("Save current settings to file")
        backup_save_btn = QPushButton("Backup & Save")
        backup_save_btn.setToolTip("Create timestamped backup before saving")
        validate_btn = QPushButton("Validate")
        validate_btn.setToolTip("Check if JSON syntax is valid")
        set_notif_btn = QPushButton("🔔 Set Notification")
        set_notif_btn.setToolTip("Set notification channel to terminal_bell")

        for btn in [load_btn, save_btn, backup_save_btn, validate_btn, set_notif_btn]:
            btn.setStyleSheet(get_button_style())

        btn_layout.addWidget(info_label)
        btn_layout.addWidget(set_notif_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(load_btn)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(backup_save_btn)
        btn_layout.addWidget(validate_btn)

        layout.addLayout(btn_layout)

        # Editor - FILLS ALL SPACE
        editor = QTextEdit()
        editor.setStyleSheet(get_text_edit_style())

        # Load content
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    editor.setPlainText(json.dumps(content, indent=2))
            else:
                editor.setPlainText("// File does not exist\n{}")
        except Exception as e:
            editor.setPlainText(f"// Error loading: {str(e)}\n{{}}")

        layout.addWidget(editor)

        # Connect buttons
        load_btn.clicked.connect(lambda: self.load_settings(file_path, editor))
        save_btn.clicked.connect(lambda: self.save_settings(file_path, editor))
        backup_save_btn.clicked.connect(lambda: self.backup_and_save(file_path, editor))
        validate_btn.clicked.connect(lambda: self.validate_json(editor))
        set_notif_btn.clicked.connect(lambda: self.set_notification_channel(file_path, editor))

        return widget

    def create_project_settings_editor(self):
        """Create project settings editor with folder picker and local/shared tabs"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Folder picker row
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(5)

        folder_label = QLabel("Project Folder:")
        folder_label.setStyleSheet("color: #ddd; font-weight: bold;")

        self.project_folder_edit = QLineEdit()
        self.project_folder_edit.setText("C:\Scripts")
        self.project_folder_edit.setReadOnly(True)
        self.project_folder_edit.setStyleSheet(get_line_edit_style())

        browse_folder_btn = QPushButton("Browse...")
        browse_folder_btn.setStyleSheet(get_button_style())
        browse_folder_btn.setToolTip("Select a different project folder")
        browse_folder_btn.clicked.connect(self.browse_project_folder)

        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.project_folder_edit, 1)
        folder_layout.addWidget(browse_folder_btn)

        layout.addLayout(folder_layout)

        # Sub-tabs for settings.json and settings.local.json
        self.project_settings_tabs = QTabWidget()
        self.project_settings_tabs.setStyleSheet(get_tab_widget_style())

        # Shared project settings (.claude/settings.json)
        self.shared_settings_widget = self.create_project_settings_editor_widget("shared")
        self.project_settings_tabs.addTab(self.shared_settings_widget, "Shared (settings.json)")

        # Local project settings (.claude/settings.local.json)
        self.local_settings_widget = self.create_project_settings_editor_widget("local")
        self.project_settings_tabs.addTab(self.local_settings_widget, "Local (settings.local.json)")

        layout.addWidget(self.project_settings_tabs)

        return widget

    def create_project_settings_editor_widget(self, settings_type):
        """Create a settings editor widget for shared or local project settings"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Determine file path based on type
        if settings_type == "shared":
            filename = "settings.json"
        else:  # local
            filename = "settings.local.json"

        file_path = self.project_folder / ".claude" / filename

        # Buttons row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(3)

        # Path label
        path_label = QLabel(str(file_path))
        path_label.setStyleSheet("color: #999; font-size: 9px;")

        # Create buttons
        load_btn = QPushButton("Reload")
        load_btn.setToolTip("Reload project settings from file (discards unsaved changes)")
        save_btn = QPushButton("Save")
        save_btn.setToolTip("Save current project settings to file")
        backup_save_btn = QPushButton("Backup & Save")
        backup_save_btn.setToolTip("Create timestamped backup before saving project settings")
        validate_btn = QPushButton("Validate")
        validate_btn.setToolTip("Check if JSON syntax is valid")

        for btn in [load_btn, save_btn, backup_save_btn, validate_btn]:
            btn.setStyleSheet(get_button_style())

        btn_layout.addWidget(path_label)
        btn_layout.addStretch()
        btn_layout.addWidget(load_btn)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(backup_save_btn)
        btn_layout.addWidget(validate_btn)

        layout.addLayout(btn_layout)

        # Editor
        editor = QTextEdit()
        editor.setStyleSheet(get_text_edit_style())

        # Load initial content
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    editor.setPlainText(json.dumps(content, indent=2))
            else:
                editor.setPlainText("// File does not exist\n{}")
        except Exception as e:
            editor.setPlainText(f"// Error loading: {str(e)}\n{{}}")

        layout.addWidget(editor)

        # Store references
        if settings_type == "shared":
            self.project_shared_editor = editor
            self.project_shared_path_label = path_label
        else:
            self.project_local_editor = editor
            self.project_local_path_label = path_label

        # Connect buttons
        load_btn.clicked.connect(lambda: self.load_project_settings_by_type(settings_type))
        save_btn.clicked.connect(lambda: self.save_project_settings_by_type(settings_type))
        backup_save_btn.clicked.connect(lambda: self.backup_and_save_project_by_type(settings_type))
        validate_btn.clicked.connect(lambda: self.validate_json(editor))

        return widget

    def browse_project_folder(self):
        """Browse for project folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Project Folder",
            "C:\Scripts"
        )
        if folder:
            self.project_folder = Path(folder)
            self.project_folder_edit.setText("C:\Scripts")
            # Update path labels
            self.project_shared_path_label.setText(str(self.project_folder / ".claude" / "settings.json"))
            self.project_local_path_label.setText(str(self.project_folder / ".claude" / "settings.local.json"))
            # Reload both editors
            self.load_project_settings_by_type("shared")
            self.load_project_settings_by_type("local")

    def load_project_settings_by_type(self, settings_type):
        """Load project settings by type (shared or local)"""
        if settings_type == "shared":
            filename = "settings.json"
            editor = self.project_shared_editor
        else:
            filename = "settings.local.json"
            editor = self.project_local_editor

        file_path = self.project_folder / ".claude" / filename
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    editor.setPlainText(json.dumps(content, indent=2))
            else:
                editor.setPlainText("// File does not exist\n{}")
        except Exception as e:
            editor.setPlainText(f"// Error loading: {str(e)}\n{{}}")

    def save_project_settings_by_type(self, settings_type):
        """Save project settings by type"""
        if settings_type == "shared":
            filename = "settings.json"
            editor = self.project_shared_editor
        else:
            filename = "settings.local.json"
            editor = self.project_local_editor

        file_path = self.project_folder / ".claude" / filename
        self.save_settings(file_path, editor)

    def backup_and_save_project_by_type(self, settings_type):
        """Backup and save project settings by type"""
        if settings_type == "shared":
            filename = "settings.json"
            editor = self.project_shared_editor
        else:
            filename = "settings.local.json"
            editor = self.project_local_editor

        file_path = self.project_folder / ".claude" / filename
        self.backup_and_save(file_path, editor)

    def load_settings(self, file_path, editor):
        """Load settings from file"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    editor.setPlainText(json.dumps(content, indent=2))
            else:
                editor.setPlainText("// File does not exist\n{}")
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load:\n{str(e)}")

    def validate_json(self, editor):
        """Validate JSON in editor"""
        try:
            json.loads(editor.toPlainText())
            QMessageBox.information(self, "Valid", "JSON is valid!")
            return True
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Invalid JSON", f"Invalid JSON:\n{str(e)}")
            return False

    def save_settings(self, file_path, editor):
        """Save settings to file"""
        if not self.validate_json(editor):
            return
        try:
            content = editor.toPlainText()
            settings = json.loads(content)

            # Create parent directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)

            QMessageBox.information(self, "Saved", f"Settings saved to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n{str(e)}")

    def backup_and_save(self, file_path, editor):
        """Backup and save settings"""
        try:
            if file_path.exists():
                self.backup_manager.create_file_backup(file_path)

            if self.validate_json(editor):
                content = editor.toPlainText()
                settings = json.loads(content)

                file_path.parent.mkdir(parents=True, exist_ok=True)

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2)

                QMessageBox.information(self, "Saved", "Backup created and settings saved!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed:\n{str(e)}")

    def set_notification_channel(self, file_path, editor):
        """Set notification channel to terminal_bell in settings"""
        try:
            # Load current settings from the file
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = {}

            # Set the notification channel
            settings["preferredNotifChannel"] = "terminal_bell"

            # Save settings back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)

            # Reload settings in editor to show the change
            self.load_settings(file_path, editor)

            QMessageBox.information(
                self,
                "Success",
                "Notification channel set to terminal_bell!\n\n" +
                "Claude Code will now use terminal bell for notifications.\n\n" +
                f"Setting saved to: {file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to set notification channel:\n{str(e)}")
