"""
User Settings Sub-Tab - Complete Settings interface for Model, Theme, and Environment Variables
"""

import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QScrollArea, QTextEdit, QMessageBox, QComboBox,
    QSpinBox, QFormLayout, QListWidget, QListWidgetItem, QInputDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

sys.path.insert(0, str(Path(__file__).parent.parent))
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
        main_layout.setContentsMargins(10, 10, 10, 10)
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
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {theme.BG_DARK};
            }}
        """)

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

        # Section 3: Environment Variables
        env_group = self.create_env_vars_section()
        scroll_layout.addWidget(env_group)

        # Section 4: JSON Preview
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
        refresh_btn.setStyleSheet(theme.get_button_style())
        refresh_btn.clicked.connect(self.load_settings)

        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip("Save all settings to file")
        save_btn.setStyleSheet(theme.get_button_style())
        save_btn.clicked.connect(self.save_settings)

        backup_save_btn = QPushButton("📦 Backup & Save")
        backup_save_btn.setToolTip("Create backup before saving")
        backup_save_btn.setStyleSheet(theme.get_button_style())
        backup_save_btn.clicked.connect(self.backup_and_save)

        notif_btn = QPushButton("🔔 Set Notification")
        notif_btn.setToolTip("Set notification channel to terminal_bell")
        notif_btn.setStyleSheet(theme.get_button_style())
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
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: {theme.FG_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Model selector
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "claude-sonnet-4-5-20250929 (Sonnet 4.5 - Best for complex coding)",
            "claude-haiku-4-5-20251001 (Haiku 4.5 - Fastest, near-frontier)",
            "claude-opus-4-1-20250805 (Opus 4.1 - Exceptional reasoning)",
            "claude-sonnet-3-5-v2@20241022 (Sonnet 3.5 v2)",
            "claude-3-5-sonnet-20241022 (Sonnet 3.5)",
            "claude-3-5-haiku-20241022 (Haiku 3.5)",
        ])
        self.model_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 8px;
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                font-family: 'Consolas', 'Monaco', monospace;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                selection-background-color: {theme.ACCENT_PRIMARY};
            }}
        """)

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
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: {theme.FG_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)

        layout = QFormLayout()
        layout.setSpacing(10)

        # Theme selector
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([
            "dark",
            "light",
            "daltonized"
        ])
        self.theme_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 6px;
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                selection-background-color: {theme.ACCENT_PRIMARY};
            }}
        """)

        theme_label = QLabel("Theme:")
        theme_label.setStyleSheet(f"color: {theme.FG_PRIMARY}; font-weight: bold;")
        layout.addRow(theme_label, self.theme_combo)

        group.setLayout(layout)
        return group

    def create_env_vars_section(self) -> QGroupBox:
        """Create environment variables section"""
        group = QGroupBox("Environment Variables")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: {theme.FG_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(5)

        # Env vars list
        self.env_list = QListWidget()
        self.env_list.setMaximumHeight(150)
        self.env_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                padding: 3px;
                font-size: {theme.FONT_SIZE_SMALL}px;
                font-family: 'Consolas', 'Monaco', monospace;
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
            btn.setStyleSheet(theme.get_button_style())
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
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: {theme.FG_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)

        layout = QVBoxLayout()

        info = QLabel("Real-time preview of settings.json")
        info.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(info)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setStyleSheet(f"""
            QTextEdit {{
                font-family: 'Consolas', 'Monaco', monospace;
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
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
            model_id = settings.get("model", "claude-sonnet-4-5-20250929")
            for i in range(self.model_combo.count()):
                if model_id in self.model_combo.itemText(i):
                    self.model_combo.setCurrentIndex(i)
                    break

            # Load theme
            theme_name = settings.get("theme", "dark")
            index = self.theme_combo.findText(theme_name)
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)

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
