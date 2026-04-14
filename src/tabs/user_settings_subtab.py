"""
User Settings Sub-Tab - Complete Settings interface for Model, Theme, and Environment Variables
"""

import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QScrollArea, QTextEdit, QMessageBox, QComboBox,
    QSpinBox, QFormLayout, QListWidget, QListWidgetItem, QInputDialog,
    QCheckBox, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from utils import theme

class UserSettingsSubTab(QWidget):
    """Settings interface for Model, Theme, and Environment Variables (user-level settings.json)"""

    def __init__(self, config_manager, backup_manager, settings_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.settings_manager = settings_manager
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize the UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(5)

        # Header
        header = QLabel("User Settings")
        header.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; "
            f"font-weight: bold; "
            f"color: {theme.ACCENT_PRIMARY};"
        )
        main_layout.addWidget(header)

        # File path info
        file_info = QLabel(f"File: {self.config_manager.settings_file}")
        file_info.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        main_layout.addWidget(file_info)

        # Scroll area for sections
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(10)

        # Section 1: Model Configuration
        model_group = self.create_model_section()
        scroll_layout.addWidget(model_group)

        # Section 2: Theme Configuration
        theme_group = self.create_theme_section()
        scroll_layout.addWidget(theme_group)

        # Section 3: Advanced Settings
        advanced_group = self.create_advanced_section()
        scroll_layout.addWidget(advanced_group)

        # Section 4: Environment Variables
        env_group = self.create_env_vars_section()
        scroll_layout.addWidget(env_group)

        # Section 5: JSON Preview
        preview_group = self.create_preview_section()
        scroll_layout.addWidget(preview_group)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll, 1)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        refresh_btn = QPushButton("🔄 Reload")
        refresh_btn.setToolTip("Reload settings from file")
        refresh_btn.clicked.connect(self.load_settings)

        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip("Save all settings to file")
        save_btn.clicked.connect(self.save_settings)

        backup_save_btn = QPushButton("📦 Backup & Save")
        backup_save_btn.setToolTip("Create backup before saving")
        backup_save_btn.clicked.connect(self.backup_and_save)

        notif_btn = QPushButton("🔔 Set Notification")
        notif_btn.setToolTip("Set notification channel to terminal_bell")
        notif_btn.clicked.connect(self.set_notification_channel)

        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(notif_btn)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(backup_save_btn)

        main_layout.addLayout(button_layout)

    def create_model_section(self) -> QGroupBox:
        """Create model configuration section"""
        group = QGroupBox("Model Configuration")

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Model selector
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.model_combo = QComboBox()
        self.model_combo.addItems([
            # Claude 4.x (latest)
            "claude-sonnet-4-6 (Sonnet 4.6 — Best coding model)",
            "claude-opus-4-6 (Opus 4.6 — Deepest reasoning)",
            "claude-haiku-4-5-20251001 (Haiku 4.5 — Fastest, cost-efficient)",
            # Claude 4.5
            "claude-sonnet-4-5-20250929 (Sonnet 4.5)",
            "claude-opus-4-5 (Opus 4.5 — Extended thinking)",
            # Claude 3.5
            "claude-sonnet-3-5-v2@20241022 (Sonnet 3.5 v2)",
            "claude-3-5-sonnet-20241022 (Sonnet 3.5)",
            "claude-3-5-haiku-20241022 (Haiku 3.5)",
        ])

        model_label = QLabel("Default Model:")
        model_label.setStyleSheet(f"color: {theme.FG_PRIMARY}; font-weight: bold;")
        form_layout.addRow(model_label, self.model_combo)

        layout.addLayout(form_layout)

        # Info tip
        tip = QLabel("💡 Select the default Claude model for new sessions")
        tip.setWordWrap(True)
        tip.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px; padding: 5px;")
        layout.addWidget(tip)

        group.setLayout(layout)
        return group

    def create_theme_section(self) -> QGroupBox:
        """Create theme configuration section"""
        group = QGroupBox("Theme & Appearance")

        layout = QFormLayout()
        layout.setSpacing(10)

        # Theme selector
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            "dark",
            "light",
            "daltonized"
        ])

        theme_label = QLabel("Theme:")
        theme_label.setStyleSheet(f"color: {theme.FG_PRIMARY}; font-weight: bold;")
        layout.addRow(theme_label, self.theme_combo)

        group.setLayout(layout)
        return group

    def create_advanced_section(self) -> QGroupBox:
        """Create advanced settings section (memory, rules, etc.)"""
        group = QGroupBox("Advanced Settings")

        layout = QFormLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(6, 8, 6, 6)

        lbl_style = f"color: {theme.FG_PRIMARY}; font-weight: bold;"
        sub_style = f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;"

        # autoMemoryEnabled
        self.auto_memory_check = QCheckBox("Enable auto memory")
        self.auto_memory_check.setToolTip(
            "When enabled, Claude automatically saves notes across sessions:\n"
            "build commands, debugging insights, code style preferences, and workflow habits.\n"
            "Stored in ~/.claude/projects/<project>/memory/MEMORY.md\n"
            "Settings key: autoMemoryEnabled (default: true)"
        )
        auto_mem_lbl = QLabel("Auto Memory:")
        auto_mem_lbl.setStyleSheet(lbl_style)
        layout.addRow(auto_mem_lbl, self.auto_memory_check)

        auto_mem_desc = QLabel("Claude saves build commands, debugging insights, code style preferences, and workflow habits across sessions")
        auto_mem_desc.setStyleSheet(sub_style)
        auto_mem_desc.setWordWrap(True)
        layout.addRow("", auto_mem_desc)

        # autoMemoryDirectory
        mem_dir_lbl = QLabel("Memory Directory:")
        mem_dir_lbl.setStyleSheet(lbl_style)
        self.memory_dir_edit = QLineEdit()
        self.memory_dir_edit.setPlaceholderText("~/.claude/projects/<project>/memory/ (default)")
        self.memory_dir_edit.setStyleSheet(f"""
            QLineEdit {{
                padding: 5px;
                border-radius: 3px;
                font-family: {theme.FONT_FAMILY_MONO};
            }}
        """)
        self.memory_dir_edit.setToolTip(
            "Custom directory for auto memory files.\n"
            "Accepts ~/expanded paths. Not accepted in project settings.\n"
            "Settings key: autoMemoryDirectory"
        )
        layout.addRow(mem_dir_lbl, self.memory_dir_edit)

        # claudeMdExcludes
        excludes_lbl = QLabel("CLAUDE.md Excludes:")
        excludes_lbl.setStyleSheet(lbl_style)
        self.claude_md_excludes_edit = QLineEdit()
        self.claude_md_excludes_edit.setPlaceholderText("e.g. vendor/**, node_modules/** (comma-separated globs)")
        self.claude_md_excludes_edit.setStyleSheet(f"""
            QLineEdit {{
                padding: 5px;
                border-radius: 3px;
                font-family: {theme.FONT_FAMILY_MONO};
            }}
        """)
        self.claude_md_excludes_edit.setToolTip(
            "Glob patterns for paths whose CLAUDE.md files should NOT be loaded.\n"
            "Comma-separated. Settings key: claudeMdExcludes"
        )
        layout.addRow(excludes_lbl, self.claude_md_excludes_edit)

        excludes_desc = QLabel("Prevent CLAUDE.md from being loaded in matching paths (e.g. vendor/**)")
        excludes_desc.setStyleSheet(sub_style)
        excludes_desc.setWordWrap(True)
        layout.addRow("", excludes_desc)

        # agentsAllowed
        self.agents_allowed_check = QCheckBox("Allow agent invocations")
        self.agents_allowed_check.setChecked(True)
        self.agents_allowed_check.setToolTip(
            "Note: 'agentsAllowed' is not an official Claude Code settings key.\n"
            "To restrict subagent spawning, use permissions.deny: [\"Task\"] instead."
        )
        agents_lbl = QLabel("Agents Allowed:")
        agents_lbl.setStyleSheet(lbl_style)
        layout.addRow(agents_lbl, self.agents_allowed_check)

        group.setLayout(layout)
        return group

    def create_env_vars_section(self) -> QGroupBox:
        """Create environment variables section"""
        group = QGroupBox("Environment Variables")

        layout = QVBoxLayout()
        layout.setSpacing(5)

        # Env vars list
        self.env_list = QListWidget()
        self.env_list.setMaximumHeight(150)
        self.env_list.setStyleSheet(f"""
            QListWidget {{
                border-radius: 3px;
                padding: 3px;
                font-size: {theme.FONT_SIZE_SMALL}px;
                font-family: {theme.FONT_FAMILY_MONO};
            }}
        """)
        layout.addWidget(self.env_list)

        # Buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Add")
        add_btn.setToolTip("Add environment variable")
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setToolTip("Edit selected variable")
        remove_btn = QPushButton("🗑 Remove")
        remove_btn.setToolTip("Remove selected variable")

        for btn in [add_btn, edit_btn, remove_btn]:
            btn.setMaximumWidth(80)

        add_btn.clicked.connect(self.add_env_var)
        edit_btn.clicked.connect(self.edit_env_var)
        remove_btn.clicked.connect(self.remove_env_var)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        group.setLayout(layout)
        return group

    def create_preview_section(self) -> QGroupBox:
        """Create JSON preview section"""
        group = QGroupBox("JSON Preview")

        layout = QVBoxLayout()

        info = QLabel("Real-time preview of settings.json")
        info.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(info)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setStyleSheet(f"""
            QTextEdit {{
                font-family: {theme.FONT_FAMILY_MONO};
                border-radius: 3px;
                padding: 5px;
                font-size: {theme.FONT_SIZE_SMALL}px;
            }}
        """)
        layout.addWidget(self.preview_text)

        group.setLayout(layout)
        return group

    def load_env_vars(self, settings: dict):
        """Load environment variables into list"""
        self.env_list.clear()
        env_vars = settings.get('env', {})

        if not env_vars:
            item = QListWidgetItem("No environment variables configured")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(QColor(theme.FG_SECONDARY))
            self.env_list.addItem(item)
        else:
            for key, value in sorted(env_vars.items()):
                # Mask sensitive values
                if any(s in key.upper() for s in ['KEY', 'TOKEN', 'PASSWORD', 'SECRET']):
                    display_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                else:
                    display_value = value
                item = QListWidgetItem(f"{key} = {display_value}")
                item.setData(Qt.ItemDataRole.UserRole, {'key': key, 'value': value})
                item.setForeground(QColor(theme.ACCENT_PRIMARY))
                self.env_list.addItem(item)

    def add_env_var(self):
        """Add new environment variable"""
        key, ok = QInputDialog.getText(
            self,
            "Add Environment Variable",
            "Variable name (e.g., ANTHROPIC_API_KEY):"
        )
        if not ok or not key:
            return
        key = key.strip().upper().replace(' ', '_')

        value, ok = QInputDialog.getText(
            self,
            "Add Environment Variable",
            f"Value for {key}:"
        )
        if not ok:
            return

        try:
            settings = self.settings_manager.get_user_settings()
            if 'env' not in settings:
                settings['env'] = {}
            settings['env'][key] = value

            self.settings_manager.save_user_settings(settings)
            self.load_settings()
            QMessageBox.information(self, "Added", f"Environment variable '{key}' added successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add variable:\n{str(e)}")

    def edit_env_var(self):
        """Edit selected environment variable"""
        current = self.env_list.currentItem()
        if not current or not current.data(Qt.ItemDataRole.UserRole):
            QMessageBox.warning(self, "No Selection", "Please select a variable to edit")
            return

        data = current.data(Qt.ItemDataRole.UserRole)
        key = data['key']
        old_value = data['value']

        value, ok = QInputDialog.getText(
            self,
            "Edit Environment Variable",
            f"New value for {key}:",
            text=old_value
        )
        if not ok:
            return

        try:
            settings = self.settings_manager.get_user_settings()
            settings['env'][key] = value

            self.settings_manager.save_user_settings(settings)
            self.load_settings()
            QMessageBox.information(self, "Updated", f"Environment variable '{key}' updated!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update variable:\n{str(e)}")

    def remove_env_var(self):
        """Remove selected environment variable"""
        current = self.env_list.currentItem()
        if not current or not current.data(Qt.ItemDataRole.UserRole):
            QMessageBox.warning(self, "No Selection", "Please select a variable to remove")
            return

        data = current.data(Qt.ItemDataRole.UserRole)
        key = data['key']

        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Remove '{key}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return

        try:
            settings = self.settings_manager.get_user_settings()
            if 'env' in settings and key in settings['env']:
                del settings['env'][key]

            self.settings_manager.save_user_settings(settings)
            self.load_settings()
            QMessageBox.information(self, "Removed", f"Environment variable '{key}' removed!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove variable:\n{str(e)}")

    def load_settings(self):
        """Load settings from file"""
        try:
            settings = self.settings_manager.get_user_settings()

            # Load model
            model_id = settings.get("model", "claude-sonnet-4-6")
            for i in range(self.model_combo.count()):
                if model_id in self.model_combo.itemText(i):
                    self.model_combo.setCurrentIndex(i)
                    break

            # Load theme
            theme_name = settings.get("theme", "dark")
            index = self.theme_combo.findText(theme_name)
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)

            # Load advanced settings
            self.auto_memory_check.setChecked(settings.get("autoMemoryEnabled", False))
            self.memory_dir_edit.setText(settings.get("autoMemoryDirectory", ""))
            excludes = settings.get("claudeMdExcludes", [])
            if isinstance(excludes, list):
                self.claude_md_excludes_edit.setText(", ".join(excludes))
            else:
                self.claude_md_excludes_edit.setText(str(excludes))
            self.agents_allowed_check.setChecked(settings.get("agentsAllowed", True))

            # Load environment variables
            self.load_env_vars(settings)

            # Update preview
            self.update_preview(settings)

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load settings:\n{str(e)}")

    def save_settings(self):
        """Save settings to file"""
        try:
            settings = self.settings_manager.get_user_settings()

            # Update model
            selected_text = self.model_combo.currentText()
            model_id = selected_text.split(" (")[0]  # Extract model ID
            settings["model"] = model_id

            # Update theme
            settings["theme"] = self.theme_combo.currentText()

            # Update advanced settings
            settings["autoMemoryEnabled"] = self.auto_memory_check.isChecked()

            mem_dir = self.memory_dir_edit.text().strip()
            if mem_dir:
                settings["autoMemoryDirectory"] = mem_dir
            elif "autoMemoryDirectory" in settings:
                del settings["autoMemoryDirectory"]

            excludes_text = self.claude_md_excludes_edit.text().strip()
            if excludes_text:
                settings["claudeMdExcludes"] = [p.strip() for p in excludes_text.split(",") if p.strip()]
            elif "claudeMdExcludes" in settings:
                del settings["claudeMdExcludes"]

            settings["agentsAllowed"] = self.agents_allowed_check.isChecked()

            # Save
            self.settings_manager.save_user_settings(settings)

            # Refresh preview
            self.update_preview(settings)

            QMessageBox.information(
                self,
                "Saved",
                f"Settings saved successfully!\n\nModel: {model_id}\nTheme: {settings['theme']}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save settings:\n{str(e)}")

    def backup_and_save(self):
        """Create backup before saving"""
        try:
            # Create backup
            if self.config_manager.settings_file.exists():
                self.backup_manager.create_file_backup(self.config_manager.settings_file)

            # Save settings
            self.save_settings()

        except Exception as e:
            QMessageBox.critical(self, "Backup Error", f"Failed to create backup:\n{str(e)}")

    def set_notification_channel(self):
        """Set notification channel to terminal_bell"""
        try:
            settings = self.settings_manager.get_user_settings()

            # Set the notification channel
            settings["preferredNotifChannel"] = "terminal_bell"

            # Save settings
            self.settings_manager.save_user_settings(settings)

            # Reload to update UI
            self.load_settings()

            QMessageBox.information(
                self,
                "Success",
                "Notification channel set to terminal_bell!\n\n"
                "Claude Code will now use terminal bell for notifications."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to set notification channel:\n{str(e)}")

    def update_preview(self, settings: dict):
        """Update JSON preview"""
        try:
            formatted = json.dumps(settings, indent=2)
            self.preview_text.setPlainText(formatted)
        except Exception as e:
            self.preview_text.setPlainText(f"Error formatting JSON: {e}")
