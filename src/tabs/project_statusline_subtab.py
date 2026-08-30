"""
Project Statusline Sub-Tab - Manage project-level statusline configuration
Dedicated subtab for statusline in .claude/settings.json (Shared) and .claude/settings.local.json (Local)
"""

import json
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QTabWidget, QLineEdit, QFormLayout, QGroupBox,
    QSpinBox,
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont

from utils import theme

logger = logging.getLogger(__name__)

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
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        # Header
        header_layout = QHBoxLayout()

        header = QLabel("Project Statusline Configuration")
        header.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; "
            f"font-weight: bold; "
            f"color: {theme.ACCENT_PRIMARY};"
        )

        docs_btn = QPushButton("📖 Status Line Docs")
        docs_btn.setToolTip("Open official status line documentation")
        docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://code.claude.com/docs/en/statusline")
        ))

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(docs_btn)
        layout.addLayout(header_layout)

        # Nested tabs for Shared vs Local
        self.scope_tabs = QTabWidget()

        # Shared tab
        self.shared_editor = self.create_statusline_editor("shared")
        self.scope_tabs.addTab(self.shared_editor, "📤 Shared (.claude/settings.json)")

        # Local tab
        self.local_editor = self.create_statusline_editor("local")
        self.scope_tabs.addTab(self.local_editor, "🔒 Local (.claude/settings.local.json)")

        layout.addWidget(self.scope_tabs, 1)

        # Info footer
        footer = QLabel(
            "💡 <b>Shared:</b> committed to git • <b>Local:</b> your machine only • "
            "The <code>command</code> runs in a shell and receives a JSON blob on stdin "
            "(model.display_name, workspace.current_dir, cost.total_cost_usd, "
            "context_window.used_percentage, version, …). Parse it yourself — there are no "
            "<code>{{variables}}</code>."
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

        # File path label (stored as instance var so load_statusline can update it)
        path_label = QLabel("(no project selected)")
        path_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(path_label)
        if scope == "shared":
            self.shared_path_label = path_label
        else:
            self.local_path_label = path_label

        # Configuration section
        config_group = QGroupBox("Statusline Configuration")

        config_layout = QVBoxLayout()

        # Form inputs
        form_layout = QFormLayout()
        form_layout.setSpacing(8)

        command_input = QLineEdit()
        command_input.setPlaceholderText("script path (e.g. .claude/statusline.sh) or an inline shell command")
        form_layout.addRow("command:", command_input)

        padding_input = QSpinBox()
        padding_input.setRange(0, 40)
        padding_input.setToolTip("Extra left indentation in characters (default 0)")
        form_layout.addRow("padding:", padding_input)

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
                font-family: {theme.FONT_FAMILY_MONO};
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
        load_btn.clicked.connect(lambda: self.load_statusline(scope))

        preview_btn = QPushButton("🔄 Update Preview")
        preview_btn.clicked.connect(lambda: self.update_preview(scope))

        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(lambda: self.save_statusline(scope))

        clear_btn = QPushButton("🗑️ Clear")
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
            'padding_input': padding_input,
            'json_preview': json_preview
        }
        command_input.textChanged.connect(lambda _t, s=scope: self.update_preview(s))
        padding_input.valueChanged.connect(lambda _v, s=scope: self.update_preview(s))

        return widget

    @staticmethod
    def _build_config(command: str, padding: int) -> dict:
        cfg = {"type": "command", "command": command}
        if padding:
            cfg["padding"] = padding
        return cfg

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

        project_path = self.project_context.get_project()
        if scope == "shared":
            full_path = project_path / ".claude" / "settings.json"
            self.shared_path_label.setText(f"File: {full_path} (team-shared)")
        else:
            full_path = project_path / ".claude" / "settings.local.json"
            self.local_path_label.setText(f"File: {full_path} (user-specific)")

        try:
            editor_data = self.editors[scope]

            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(project_path)
            else:
                settings = self.settings_manager.get_project_local_settings(project_path)

            # Claude Code reads "statusLine" (camelCase); fall back to legacy lowercase for compat
            statusline = settings.get("statusLine", settings.get("statusline", {}))

            if isinstance(statusline, str):
                editor_data['command_input'].setText(statusline)
                editor_data['padding_input'].setValue(0)
                self.update_preview(scope)
            elif isinstance(statusline, dict):
                editor_data['command_input'].setText(statusline.get("command", ""))
                editor_data['padding_input'].setValue(int(statusline.get("padding", 0) or 0))
                self.update_preview(scope)
            else:
                editor_data['command_input'].clear()
                editor_data['padding_input'].setValue(0)
                editor_data['json_preview'].setPlainText("// no status line configured")

        except Exception as e:
            logger.error("Failed to load %s statusline: %s", scope, e)
            QMessageBox.critical(self, "Load Error", f"Failed to load {scope} statusline:\n{str(e)}")

    def update_preview(self, scope: str):
        """Update JSON preview"""
        editor_data = self.editors[scope]
        command = editor_data['command_input'].text().strip()
        if not command:
            editor_data['json_preview'].setPlainText("// no status line configured")
            return
        cfg = self._build_config(command, editor_data['padding_input'].value())
        editor_data['json_preview'].setPlainText(json.dumps({"statusLine": cfg}, indent=2))

    def save_statusline(self, scope: str):
        """Save statusline configuration"""
        if not self.project_context.has_project():
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        try:
            editor_data = self.editors[scope]
            command = editor_data['command_input'].text().strip()

            if not command:
                QMessageBox.warning(self, "Empty", "Enter a command before saving.")
                return

            if scope == "shared":
                settings = self.settings_manager.get_project_shared_settings(self.project_context.get_project())
                settings_file = self.project_context.get_project() / ".claude" / "settings.json"
            else:
                settings = self.settings_manager.get_project_local_settings(self.project_context.get_project())
                settings_file = self.project_context.get_project() / ".claude" / "settings.local.json"

            settings["statusLine"] = self._build_config(command, editor_data['padding_input'].value())
            settings.pop("statusline", None)  # drop a wrong-case key if present
            self.settings_manager.save_settings(settings_file, settings)

            self.update_preview(scope)
            QMessageBox.information(self, "Success", f"{scope.capitalize()} statusline saved successfully!")
        except Exception as e:
            logger.error("Failed to save %s statusline: %s", scope, e)
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

                settings.pop("statusLine", None)
                settings.pop("statusline", None)

                self.settings_manager.save_settings(settings_file, settings)

                editor_data = self.editors[scope]
                editor_data['command_input'].clear()
                editor_data['padding_input'].setValue(0)
                editor_data['json_preview'].setPlainText("// status line removed")

                QMessageBox.information(self, "Success", f"{scope.capitalize()} statusline cleared!")
            except Exception as e:
                logger.error("Failed to clear %s statusline: %s", scope, e)
                QMessageBox.critical(self, "Clear Error", f"Failed to clear statusline:\n{str(e)}")
