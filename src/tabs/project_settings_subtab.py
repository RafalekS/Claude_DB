"""
Project Settings Sub-Tab - Complete Settings interface for Model, Theme, and Environment Variables
Includes Shared (.claude/settings.json) and Local (.claude/settings.local.json) tabs
"""

import json
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QScrollArea, QTextEdit, QMessageBox, QTabWidget,
    QComboBox, QFormLayout, QListWidget, QInputDialog,
    QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from utils import theme

logger = logging.getLogger(__name__)

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
        self.preview_texts = {}
        self.excludes_edits = {}
        self.plugins_lists = {}

        self.init_ui()

        # Connect to project context changes
        self.project_context.project_changed.connect(self.on_project_changed)

        # Load settings if project is set
        if self.project_context.has_project():
            self.load_all_settings()

    def init_ui(self):
        """Initialize the UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
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
                border-radius: 3px;
            }}
            QTabBar::tab {{
                padding: 6px 12px;
                margin-right: 2px;
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
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

        # File path info (stored as instance var so load_settings can update it)
        file_path_label = QLabel("(no project selected)")
        file_path_label.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; "
            f"font-style: italic;"
        )
        layout.addWidget(file_path_label)
        if scope == "shared":
            self.shared_path_label = file_path_label
        else:
            self.local_path_label = file_path_label

        # Scroll area for sections
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

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

        # Section 3: Advanced
        advanced_group = self.create_advanced_section(scope)
        scroll_layout.addWidget(advanced_group)

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
        refresh_btn.clicked.connect(lambda: self.load_settings(scope))

        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip(f"Save {scope} settings to file")
        save_btn.clicked.connect(lambda: self.save_settings(scope))

        backup_save_btn = QPushButton("📦 Backup & Save")
        backup_save_btn.setToolTip(f"Create backup before saving {scope} settings")
        backup_save_btn.clicked.connect(lambda: self.backup_and_save(scope))

        notif_btn = QPushButton("🔔 Set Notification")
        notif_btn.setToolTip("Set notification channel to terminal_bell")
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

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Model selector
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        model_combo = QComboBox()
        model_combo.addItems([
            "sonnet (Sonnet 5 — balanced default for coding)",
            "opus (Opus 5 — deepest reasoning)",
            "fable (Fable 5 — most capable; long-horizon agentic)",
            "haiku (Haiku 4.5 — fastest / cheapest)",
            "opusplan (Opus in Plan mode, Sonnet in execution)",
            "claude-sonnet-5 (pinned Sonnet 5)",
            "claude-opus-5 (pinned Opus 5)",
            "claude-fable-5 (pinned Fable 5)",
            "claude-haiku-4-5-20251001 (pinned Haiku 4.5)",
        ])
        model_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 8px;
                border-radius: 3px;
                font-family: {theme.FONT_FAMILY_MONO};
            }}
            QComboBox::drop-down {{
            }}
            QComboBox 
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

        layout = QFormLayout()
        layout.setSpacing(10)

        # Theme selector
        theme_combo = QComboBox()
        theme_combo.addItems([
            "dark",
            "light",
            "dark-daltonized",
            "light-daltonized",
            "dark-ansi",
            "light-ansi",
        ])
        theme_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 6px;
                border-radius: 3px;
            }}
            QComboBox 
        """)

        theme_label = QLabel("Theme:")
        theme_label.setStyleSheet(f"color: {theme.FG_PRIMARY}; font-weight: bold;")
        layout.addRow(theme_label, theme_combo)

        group.setLayout(layout)

        # Store reference
        self.theme_combos[scope] = theme_combo

        return group

    def create_advanced_section(self, scope: str) -> QGroupBox:
        """Create advanced settings section (claudeMdExcludes, enabledPlugins)"""
        group = QGroupBox("Advanced")
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # claudeMdExcludes
        excludes_label = QLabel("CLAUDE.md Excludes (glob patterns, comma-separated):")
        excludes_label.setStyleSheet(f"color: {theme.FG_PRIMARY}; font-weight: bold;")
        layout.addWidget(excludes_label)

        excludes_edit = QLineEdit()
        excludes_edit.setPlaceholderText("e.g. tests/**, docs/**")
        excludes_edit.setToolTip(
            "Glob patterns for files/directories excluded from CLAUDE.md context loading"
        )
        layout.addWidget(excludes_edit)

        excludes_tip = QLabel(
            "💡 Glob patterns that prevent CLAUDE.md files in matching paths from being loaded"
        )
        excludes_tip.setWordWrap(True)
        excludes_tip.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(excludes_tip)

        # enabledPlugins
        plugins_label = QLabel("Enabled Plugins:")
        plugins_label.setStyleSheet(
            f"color: {theme.FG_PRIMARY}; font-weight: bold; margin-top: {theme.MARGIN_SM}px;"
        )
        layout.addWidget(plugins_label)

        plugins_list = QListWidget()
        plugins_list.setMaximumHeight(100)
        layout.addWidget(plugins_list)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        add_plugin_btn = QPushButton("➕ Add")
        add_plugin_btn.setToolTip("Add plugin name")
        remove_plugin_btn = QPushButton("🗑 Remove")
        remove_plugin_btn.setToolTip("Remove selected plugin")
        add_plugin_btn.clicked.connect(lambda: self._add_plugin(scope))
        remove_plugin_btn.clicked.connect(lambda: self._remove_plugin(scope))
        btn_row.addWidget(add_plugin_btn)
        btn_row.addWidget(remove_plugin_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        plugins_tip = QLabel(
            "💡 Plugin names to enable for this project (overrides user-level enabledPlugins)"
        )
        plugins_tip.setWordWrap(True)
        plugins_tip.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(plugins_tip)

        group.setLayout(layout)

        self.excludes_edits[scope] = excludes_edit
        self.plugins_lists[scope] = plugins_list

        return group

    def _add_plugin(self, scope: str):
        """Add a plugin name to the enabled plugins list"""
        name, ok = QInputDialog.getText(self, "Add Plugin", "Plugin name:")
        if ok and name.strip():
            self.plugins_lists[scope].addItem(name.strip())

    def _remove_plugin(self, scope: str):
        """Remove selected plugin from the list"""
        lst = self.plugins_lists[scope]
        row = lst.currentRow()
        if row >= 0:
            lst.takeItem(row)

    def create_preview_section(self, scope: str) -> QGroupBox:
        """Create JSON preview section"""
        group = QGroupBox("JSON Preview")

        layout = QVBoxLayout()

        info = QLabel(f"Real-time preview of {scope} settings.json")
        info.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(info)

        preview_text = QTextEdit()
        preview_text.setReadOnly(True)
        preview_text.setMaximumHeight(200)
        preview_text.setStyleSheet(f"""
            QTextEdit {{
                font-family: {theme.FONT_FAMILY_MONO};
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

    def load_settings(self, scope: str):
        """Load settings from file for a specific scope"""
        if not self.project_context.has_project():
            # Clear UI if no project
            if scope in self.preview_texts:
                self.preview_texts[scope].clear()
            return

        project_path = self.project_context.get_project()
        if scope == "shared":
            full_path = project_path / ".claude" / "settings.json"
            self.shared_path_label.setText(f"File: {full_path} (team-shared, committed)")
        else:
            full_path = project_path / ".claude" / "settings.local.json"
            self.local_path_label.setText(f"File: {full_path} (user-specific, gitignored)")

        try:
            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(project_path)
            else:
                settings = self.settings_manager.get_project_local_settings(project_path)

            # Load model
            if scope in self.model_combos:
                model_id = settings.get("model", "")
                for i in range(self.model_combos[scope].count()):
                    if model_id and self.model_combos[scope].itemText(i).split(" (")[0] == model_id:
                        self.model_combos[scope].setCurrentIndex(i)
                        break

            # Load theme
            if scope in self.theme_combos:
                theme_name = settings.get("theme", "dark")
                index = self.theme_combos[scope].findText(theme_name)
                if index >= 0:
                    self.theme_combos[scope].setCurrentIndex(index)

            # Load claudeMdExcludes
            if scope in self.excludes_edits:
                excludes = settings.get("claudeMdExcludes", [])
                self.excludes_edits[scope].setText(", ".join(excludes))

            # Load enabledPlugins
            if scope in self.plugins_lists:
                self.plugins_lists[scope].clear()
                for plugin in settings.get("enabledPlugins", []):
                    self.plugins_lists[scope].addItem(plugin)

            # Update preview
            self.update_preview(settings, scope)

        except Exception as e:
            logger.error("Failed to load %s settings: %s", scope, e)
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

            # Update claudeMdExcludes
            if scope in self.excludes_edits:
                raw = self.excludes_edits[scope].text().strip()
                excludes = [p.strip() for p in raw.split(",") if p.strip()]
                if excludes:
                    settings["claudeMdExcludes"] = excludes
                elif "claudeMdExcludes" in settings:
                    del settings["claudeMdExcludes"]

            # Update enabledPlugins
            if scope in self.plugins_lists:
                lst = self.plugins_lists[scope]
                plugins = [lst.item(i).text() for i in range(lst.count())]
                if plugins:
                    settings["enabledPlugins"] = plugins
                elif "enabledPlugins" in settings:
                    del settings["enabledPlugins"]

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
            logger.error("Failed to save %s settings: %s", scope, e)
            QMessageBox.critical(self, "Save Error", f"Failed to save {scope} settings:\n{str(e)}")

    def backup_and_save(self, scope: str):
        """Create backup before saving"""
        if not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "No project selected. Please select a project first.")
            return

        try:
            project_path = self.project_context.get_project()
            if not project_path:
                return

            if scope == "shared":
                settings_file = project_path / ".claude" / "settings.json"
            else:
                settings_file = project_path / ".claude" / "settings.local.json"

            # Create backup if file exists
            if self.config_manager.fs.exists(settings_file):
                self.backup_manager.create_file_backup(settings_file)

            # Save settings
            self.save_settings(scope)

        except Exception as e:
            logger.error("Failed to create backup for %s settings: %s", scope, e)
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
            logger.error("Failed to set notification channel for %s settings: %s", scope, e)
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
