"""
Project Statusline Sub-Tab - Manage project-level statusline configuration
Dedicated subtab for statusline in .claude/settings.json (Shared) and .claude/settings.local.json (Local)
"""

import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QTabWidget, QLineEdit, QFormLayout, QGroupBox
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme


class ProjectStatuslineSubTab(QWidget):
    """Dedicated subtab for project-level statusline configuration (Shared/Local)"""

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
            self.load_all_statuslines()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header
        header_layout = QHBoxLayout()

        header = QLabel("Project Statusline Configuration")
        header.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; "
            f"font-weight: bold; "
            f"color: {theme.ACCENT_PRIMARY};"
        )

        docs_btn = QPushButton("📖 Statusline Docs")
        docs_btn.setStyleSheet(theme.get_button_style())
        docs_btn.setToolTip("Open official statusline documentation")
        docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://docs.claude.com/en/docs/claude-code/settings#statusline")
        ))

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(docs_btn)
        layout.addLayout(header_layout)

        # Nested tabs for Shared vs Local
        self.scope_tabs = QTabWidget()
        self.scope_tabs.setStyleSheet(theme.get_tab_widget_style())

        # Shared tab
        self.shared_editor = self.create_statusline_editor("shared")
        self.scope_tabs.addTab(self.shared_editor, "📤 Shared (.claude/settings.json)")

        # Local tab
        self.local_editor = self.create_statusline_editor("local")
        self.scope_tabs.addTab(self.local_editor, "🔒 Local (.claude/settings.local.json)")

        layout.addWidget(self.scope_tabs, 1)

        # Info footer
        footer = QLabel(
            "💡 <b>Shared:</b> Team-shared statusline (committed to git) • "
            "<b>Local:</b> User-specific override (gitignored) • "
            "<b>Variables:</b> {{project_name}}, {{git_branch}}, {{model}}, {{tokens}}"
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

    def create_statusline_editor(self, scope: str) -> QWidget:
        """Create statusline editor for a specific scope"""
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

        # Configuration section
        config_group = QGroupBox("Statusline Configuration")
        config_group.setStyleSheet(f"""
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

        config_layout = QVBoxLayout()

        # Form inputs
        form_layout = QFormLayout()
        form_layout.setSpacing(8)

        command_input = QLineEdit()
        command_input.setPlaceholderText("e.g., git branch --show-current 2>/dev/null || echo 'main'")
        command_input.setStyleSheet(theme.get_line_edit_style())
        form_layout.addRow("Command:", command_input)

        template_input = QLineEdit()
        template_input.setPlaceholderText("e.g., {{project_name}} [{{git_branch}}]")
        template_input.setStyleSheet(theme.get_line_edit_style())
        form_layout.addRow("Template:", template_input)

        config_layout.addLayout(form_layout)

        # JSON preview
        preview_label = QLabel("JSON Configuration:")
        preview_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY}; margin-top: 10px;")
        config_layout.addWidget(preview_label)

        json_preview = QTextEdit()
        json_preview.setReadOnly(True)
        json_preview.setMaximumHeight(120)
        json_preview.setStyleSheet(f"""
            QTextEdit {{
                font-family: 'Consolas', 'Monaco', monospace;
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                padding: 5px;
            }}
        """)
        config_layout.addWidget(json_preview)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        load_btn = QPushButton("📂 Load")
        load_btn.setStyleSheet(theme.get_button_style())
        load_btn.clicked.connect(lambda: self.load_statusline(scope))

        preview_btn = QPushButton("🔄 Update Preview")
        preview_btn.setStyleSheet(theme.get_button_style())
        preview_btn.clicked.connect(lambda: self.update_preview(scope))

        save_btn = QPushButton("💾 Save")
        save_btn.setStyleSheet(theme.get_button_style())
        save_btn.clicked.connect(lambda: self.save_statusline(scope))

        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.setStyleSheet(theme.get_button_style())
        clear_btn.clicked.connect(lambda: self.clear_statusline(scope))

        btn_layout.addWidget(load_btn)
        btn_layout.addWidget(preview_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(clear_btn)

        layout.addLayout(btn_layout)

        # Store references
        if not hasattr(self, 'editors'):
            self.editors = {}
        self.editors[scope] = {
            'command_input': command_input,
            'template_input': template_input,
            'json_preview': json_preview
        }

        return widget

    def on_project_changed(self, project_path: Path):
        """Handle project change"""
        self.load_all_statuslines()

    def load_all_statuslines(self):
        """Load statuslines for both scopes"""
        self.load_statusline("shared")
        self.load_statusline("local")

    def load_statusline(self, scope: str):
        """Load statusline for a specific scope"""
        if not self.project_context.has_project():
            return

        try:
            editor_data = self.editors[scope]

            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(self.project_context.get_project())
            else:
                settings = self.settings_manager.get_project_local_settings(self.project_context.get_project())

            statusline = settings.get("statusline", {})

            if isinstance(statusline, dict):
                editor_data['command_input'].setText(statusline.get("command", ""))
                editor_data['template_input'].setText(statusline.get("template", ""))
                self.update_preview(scope)
            else:
                editor_data['command_input'].clear()
                editor_data['template_input'].clear()
                editor_data['json_preview'].setPlainText("# No statusline configured")

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load {scope} statusline:\n{str(e)}")

    def update_preview(self, scope: str):
        """Update JSON preview"""
        try:
            editor_data = self.editors[scope]
            command = editor_data['command_input'].text().strip()
            template = editor_data['template_input'].text().strip()

            if command or template:
                config = {}
                if command:
                    config["command"] = command
                if template:
                    config["template"] = template

                formatted = json.dumps(config, indent=2)
                editor_data['json_preview'].setPlainText(formatted)
            else:
                editor_data['json_preview'].setPlainText("# No configuration")
        except Exception as e:
            editor_data['json_preview'].setPlainText(f"# Error: {str(e)}")

    def save_statusline(self, scope: str):
        """Save statusline configuration"""
        if not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        try:
            editor_data = self.editors[scope]
            command = editor_data['command_input'].text().strip()
            template = editor_data['template_input'].text().strip()

            if not command and not template:
                QMessageBox.warning(
                    self, "Empty Configuration",
                    "Please enter at least a command or template."
                )
                return

            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(self.project_context.get_project())
                settings_file = self.project_context.get_project() / ".claude" / "settings.json"
            else:
                settings = self.settings_manager.get_project_local_settings(self.project_context.get_project())
                settings_file = self.project_context.get_project() / ".claude" / "settings.local.json"

            statusline_config = {}
            if command:
                statusline_config["command"] = command
            if template:
                statusline_config["template"] = template

            settings["statusline"] = statusline_config
            self.settings_manager.save_settings(settings_file, settings)

            self.update_preview(scope)
            QMessageBox.information(self, "Success", f"{scope.capitalize()} statusline saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save statusline:\n{str(e)}")

    def clear_statusline(self, scope: str):
        """Clear statusline configuration"""
        if not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        reply = QMessageBox.question(
            self, "Confirm Clear",
            f"Clear {scope} statusline configuration?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if scope == "shared":
                    settings = self.settings_manager.get_project_shared_settings(self.project_context.get_project())
                    settings_file = self.project_context.get_project() / ".claude" / "settings.json"
                else:
                    settings = self.settings_manager.get_project_local_settings(self.project_context.get_project())
                    settings_file = self.project_context.get_project() / ".claude" / "settings.local.json"

                if "statusline" in settings:
                    del settings["statusline"]

                self.settings_manager.save_settings(settings_file, settings)

                editor_data = self.editors[scope]
                editor_data['command_input'].clear()
                editor_data['template_input'].clear()
                editor_data['json_preview'].setPlainText("# Statusline cleared")

                QMessageBox.information(self, "Success", f"{scope.capitalize()} statusline cleared!")
            except Exception as e:
                QMessageBox.critical(self, "Clear Error", f"Failed to clear statusline:\n{str(e)}")
