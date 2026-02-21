"""
Project Settings Sub-Tab - Complete Settings interface for Model, Theme, and Environment Variables
Includes Shared (.claude/settings.json) and Local (.claude/settings.local.json) tabs
"""

import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QScrollArea, QTextEdit, QMessageBox, QTabWidget,
    QComboBox, QFormLayout, QListWidget, QListWidgetItem, QInputDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme


class ProjectSettingsSubTab(QWidget):
    """Settings interface for Model, Theme, and Environment Variables (project-level settings.json)"""

    def __init__(self, config_manager, backup_manager, settings_manager, project_context):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.settings_manager = settings_manager
        self.project_context = project_context

        # Storage for UI widgets by scope
        self.model_combos = {}
        self.theme_combos = {}
        self.env_lists = {}
        self.preview_texts = {}

        self.init_ui()

        # Connect to project context changes
        self.project_context.project_changed.connect(self.on_project_changed)

        # Load settings if project is set
        if self.project_context.has_project():
            self.load_all_settings()

    def init_ui(self):
        """Initialize the UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        # Header
        header = QLabel("Project Settings")
        header.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; "
            f"font-weight: bold; "
            f"color: {theme.ACCENT_PRIMARY};"
        )
        main_layout.addWidget(header)

        # Nested tabs for Shared vs Local
        self.settings_tabs = QTabWidget()
        self.settings_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                background-color: {theme.BG_DARK};
            }}
            QTabBar::tab {{
                background-color: {theme.BG_MEDIUM};
                color: {theme.FG_PRIMARY};
                padding: 6px 12px;
                margin-right: 2px;
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
            }}
            QTabBar::tab:selected {{
                background-color: {theme.ACCENT_PRIMARY};
                color: {theme.BG_DARK};
            }}
            QTabBar::tab:hover {{
                background-color: {theme.BG_LIGHT};
            }}
        """)

        # Shared settings tab
        self.shared_tab = self.create_settings_editor("shared")
        self.settings_tabs.addTab(self.shared_tab, "📤 Shared (.claude/settings.json)")

        # Local settings tab
        self.local_tab = self.create_settings_editor("local")
        self.settings_tabs.addTab(self.local_tab, "🔒 Local (.claude/settings.local.json)")

        main_layout.addWidget(self.settings_tabs, 1)

        # Info footer
        footer = QLabel(
            "💡 <b>Shared</b>: Team-shared settings (committed to git). "
            "<b>Local</b>: User-specific overrides (gitignored)."
        )
        footer.setWordWrap(True)
        footer.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; "
            f"padding: 5px; "
            f"background-color: {theme.BG_MEDIUM}; "
            f"border-left: 3px solid {theme.ACCENT_SECONDARY}; "
            f"border-radius: 3px;"
        )
        main_layout.addWidget(footer)

    def create_settings_editor(self, scope: str) -> QWidget:
        """Create settings editor for a specific scope (shared or local)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # File path info
        file_path_label = QLabel()
        if scope == "shared":
            file_path_label.setText(".claude/settings.json (team-shared, committed)")
        else:
            file_path_label.setText(".claude/settings.local.json (user-specific, gitignored)")

        file_path_label.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; "
            f"font-style: italic;"
        )
        layout.addWidget(file_path_label)

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
        model_group = self.create_model_section(scope)
        scroll_layout.addWidget(model_group)

        # Section 2: Theme Configuration
        theme_group = self.create_theme_section(scope)
        scroll_layout.addWidget(theme_group)

        # Section 3: Environment Variables
        env_group = self.create_env_vars_section(scope)
        scroll_layout.addWidget(env_group)

        # Section 4: JSON Preview
        preview_group = self.create_preview_section(scope)
        scroll_layout.addWidget(preview_group)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        refresh_btn = QPushButton("🔄 Reload")
        refresh_btn.setToolTip(f"Reload {scope} settings from file")
        refresh_btn.setStyleSheet(theme.get_button_style())
        refresh_btn.clicked.connect(lambda: self.load_settings(scope))

        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip(f"Save {scope} settings to file")
        save_btn.setStyleSheet(theme.get_button_style())
        save_btn.clicked.connect(lambda: self.save_settings(scope))

        backup_save_btn = QPushButton("📦 Backup & Save")
        backup_save_btn.setToolTip(f"Create backup before saving {scope} settings")
        backup_save_btn.setStyleSheet(theme.get_button_style())
        backup_save_btn.clicked.connect(lambda: self.backup_and_save(scope))

        notif_btn = QPushButton("🔔 Set Notification")
        notif_btn.setToolTip("Set notification channel to terminal_bell")
        notif_btn.setStyleSheet(theme.get_button_style())
        notif_btn.clicked.connect(lambda: self.set_notification_channel(scope))

        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(notif_btn)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(backup_save_btn)

        layout.addLayout(button_layout)

        return widget

    def create_model_section(self, scope: str) -> QGroupBox:
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

        model_combo = QComboBox()
        model_combo.addItems([
            "claude-sonnet-4-5-20250929 (Sonnet 4.5 - Best for complex coding)",
            "claude-haiku-4-5-20251001 (Haiku 4.5 - Fastest, near-frontier)",
            "claude-opus-4-1-20250805 (Opus 4.1 - Exceptional reasoning)",
            "claude-sonnet-3-5-v2@20241022 (Sonnet 3.5 v2)",
            "claude-3-5-sonnet-20241022 (Sonnet 3.5)",
            "claude-3-5-haiku-20241022 (Haiku 3.5)",
        ])
        model_combo.setStyleSheet(f"""
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
        form_layout.addRow(model_label, model_combo)

        layout.addLayout(form_layout)

        # Info tip
        tip = QLabel("💡 Select the default Claude model for this project")
        tip.setWordWrap(True)
        tip.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px; padding: 5px;")
        layout.addWidget(tip)

        group.setLayout(layout)

        # Store reference
        self.model_combos[scope] = model_combo

        return group

    def create_theme_section(self, scope: str) -> QGroupBox:
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
        theme_combo = QComboBox()
        theme_combo.addItems([
            "dark",
            "light",
            "daltonized"
        ])
        theme_combo.setStyleSheet(f"""
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
        layout.addRow(theme_label, theme_combo)

        group.setLayout(layout)

        # Store reference
        self.theme_combos[scope] = theme_combo

        return group

    def create_env_vars_section(self, scope: str) -> QGroupBox:
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
        env_list = QListWidget()
        env_list.setMaximumHeight(150)
        env_list.setStyleSheet(f"""
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
        layout.addWidget(env_list)

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

        add_btn.clicked.connect(lambda: self.add_env_var(scope))
        edit_btn.clicked.connect(lambda: self.edit_env_var(scope))
        remove_btn.clicked.connect(lambda: self.remove_env_var(scope))

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        group.setLayout(layout)

        # Store reference
        self.env_lists[scope] = env_list

        return group

    def create_preview_section(self, scope: str) -> QGroupBox:
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

        info = QLabel(f"Real-time preview of {scope} settings.json")
        info.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(info)

        preview_text = QTextEdit()
        preview_text.setReadOnly(True)
        preview_text.setMaximumHeight(200)
        preview_text.setStyleSheet(f"""
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
        layout.addWidget(preview_text)

        group.setLayout(layout)

        # Store reference
        self.preview_texts[scope] = preview_text

        return group

    def load_env_vars(self, settings: dict, scope: str):
        """Load environment variables into list"""
        if scope not in self.env_lists:
            return

        env_list = self.env_lists[scope]
        env_list.clear()
        env_vars = settings.get('env', {})

        if not env_vars:
            item = QListWidgetItem("No environment variables configured")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(QColor(theme.FG_SECONDARY))
            env_list.addItem(item)
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
                env_list.addItem(item)

    def add_env_var(self, scope: str):
        """Add new environment variable"""
        if not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "No project selected. Please select a project first.")
            return

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
            project_path = self.project_context.get_project()

            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(project_path)
            else:
                settings = self.settings_manager.get_project_local_settings(project_path)

            if 'env' not in settings:
                settings['env'] = {}
            settings['env'][key] = value

            if scope == "shared":
                self.settings_manager.save_project_shared_settings(project_path, settings)
            else:
                self.settings_manager.save_project_local_settings(project_path, settings)

            self.load_settings(scope)
            QMessageBox.information(self, "Added", f"Environment variable '{key}' added successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add variable:\n{str(e)}")

    def edit_env_var(self, scope: str):
        """Edit selected environment variable"""
        if not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "No project selected. Please select a project first.")
            return

        if scope not in self.env_lists:
            return

        env_list = self.env_lists[scope]
        current = env_list.currentItem()
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
            project_path = self.project_context.get_project()

            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(project_path)
            else:
                settings = self.settings_manager.get_project_local_settings(project_path)

            settings['env'][key] = value

            if scope == "shared":
                self.settings_manager.save_project_shared_settings(project_path, settings)
            else:
                self.settings_manager.save_project_local_settings(project_path, settings)

            self.load_settings(scope)
            QMessageBox.information(self, "Updated", f"Environment variable '{key}' updated!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update variable:\n{str(e)}")

    def remove_env_var(self, scope: str):
        """Remove selected environment variable"""
        if not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "No project selected. Please select a project first.")
            return

        if scope not in self.env_lists:
            return

        env_list = self.env_lists[scope]
        current = env_list.currentItem()
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
            project_path = self.project_context.get_project()

            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(project_path)
            else:
                settings = self.settings_manager.get_project_local_settings(project_path)

            if 'env' in settings and key in settings['env']:
                del settings['env'][key]

            if scope == "shared":
                self.settings_manager.save_project_shared_settings(project_path, settings)
            else:
                self.settings_manager.save_project_local_settings(project_path, settings)

            self.load_settings(scope)
            QMessageBox.information(self, "Removed", f"Environment variable '{key}' removed!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove variable:\n{str(e)}")

    def load_settings(self, scope: str):
        """Load settings from file for a specific scope"""
        if not self.project_context.has_project():
            # Clear UI if no project
            if scope in self.preview_texts:
                self.preview_texts[scope].clear()
            return

        try:
            project_path = self.project_context.get_project()

            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(project_path)
            else:
                settings = self.settings_manager.get_project_local_settings(project_path)

            # Load model
            if scope in self.model_combos:
                model_id = settings.get("model", "claude-sonnet-4-5-20250929")
                for i in range(self.model_combos[scope].count()):
                    if model_id in self.model_combos[scope].itemText(i):
                        self.model_combos[scope].setCurrentIndex(i)
                        break

            # Load theme
            if scope in self.theme_combos:
                theme_name = settings.get("theme", "dark")
                index = self.theme_combos[scope].findText(theme_name)
                if index >= 0:
                    self.theme_combos[scope].setCurrentIndex(index)

            # Load environment variables
            self.load_env_vars(settings, scope)

            # Update preview
            self.update_preview(settings, scope)

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load {scope} settings:\n{str(e)}")

    def load_all_settings(self):
        """Load both shared and local settings"""
        self.load_settings("shared")
        self.load_settings("local")

    def save_settings(self, scope: str):
        """Save settings to file for a specific scope"""
        if not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "No project selected. Please select a project first.")
            return

        try:
            project_path = self.project_context.get_project()

            # Get current settings
            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(project_path)
            else:
                settings = self.settings_manager.get_project_local_settings(project_path)

            # Update model
            if scope in self.model_combos:
                selected_text = self.model_combos[scope].currentText()
                model_id = selected_text.split(" (")[0]  # Extract model ID
                settings["model"] = model_id

            # Update theme
            if scope in self.theme_combos:
                settings["theme"] = self.theme_combos[scope].currentText()

            # Save
            if scope == "shared":
                self.settings_manager.save_project_shared_settings(project_path, settings)
            else:
                self.settings_manager.save_project_local_settings(project_path, settings)

            # Refresh preview
            self.update_preview(settings, scope)

            QMessageBox.information(
                self,
                "Saved",
                f"{scope.capitalize()} settings saved successfully!\n\n"
                f"Model: {settings.get('model', 'N/A')}\n"
                f"Theme: {settings.get('theme', 'N/A')}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save {scope} settings:\n{str(e)}")

    def backup_and_save(self, scope: str):
        """Create backup before saving"""
        if not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "No project selected. Please select a project first.")
            return

        try:
            project_path = self.project_context.get_project()

            if scope == "shared":
                settings_file = project_path / ".claude" / "settings.json"
            else:
                settings_file = project_path / ".claude" / "settings.local.json"

            # Create backup if file exists
            if settings_file.exists():
                self.backup_manager.create_file_backup(settings_file)

            # Save settings
            self.save_settings(scope)

        except Exception as e:
            QMessageBox.critical(self, "Backup Error", f"Failed to create backup:\n{str(e)}")

    def set_notification_channel(self, scope: str):
        """Set notification channel to terminal_bell"""
        if not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "No project selected. Please select a project first.")
            return

        try:
            project_path = self.project_context.get_project()

            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(project_path)
            else:
                settings = self.settings_manager.get_project_local_settings(project_path)

            # Set the notification channel
            settings["preferredNotifChannel"] = "terminal_bell"

            # Save settings
            if scope == "shared":
                self.settings_manager.save_project_shared_settings(project_path, settings)
            else:
                self.settings_manager.save_project_local_settings(project_path, settings)

            # Reload to update UI
            self.load_settings(scope)

            QMessageBox.information(
                self,
                "Success",
                f"Notification channel set to terminal_bell in {scope} settings!\n\n"
                "Claude Code will now use terminal bell for notifications."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to set notification channel:\n{str(e)}")

    def update_preview(self, settings: dict, scope: str):
        """Update JSON preview for a specific scope"""
        if scope not in self.preview_texts:
            return

        try:
            formatted = json.dumps(settings, indent=2)
            self.preview_texts[scope].setPlainText(formatted)
        except Exception as e:
            self.preview_texts[scope].setPlainText(f"Error formatting JSON: {e}")

    def on_project_changed(self, new_project: Path):
        """Handle project context changes (reload settings)"""
        if new_project:
            self.load_all_settings()
        else:
            # Clear all previews
            for preview in self.preview_texts.values():
                preview.clear()
