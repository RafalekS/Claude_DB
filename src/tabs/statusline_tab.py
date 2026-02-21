"""
Statusline Tab - Manage Claude Code statusline configuration
"""

import json
from pathlib import Path
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QTextBrowser, QLineEdit,
    QFormLayout, QGroupBox, QFileDialog, QTabWidget
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme


class StatuslineTab(QWidget):
    """Tab for managing Claude Code statusline"""

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

        header = QLabel("Statusline Configuration")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")

        docs_btn = QPushButton("📖 Statusline Docs")
        docs_btn.setStyleSheet(theme.get_button_style())
        docs_btn.setToolTip("Open official statusline documentation in browser")
        docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://docs.claude.com/en/docs/claude-code/statusline")
        ))

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(docs_btn)

        layout.addLayout(header_layout)

        # Main tab widget for User / Project
        self.main_tabs = QTabWidget()
        self.main_tabs.setStyleSheet(theme.get_tab_widget_style())

        # User tab
        self.user_tab = self.create_statusline_editor("user")
        self.main_tabs.addTab(self.user_tab, "User (~/.claude/settings.json)")

        # Project tab
        self.project_tab = self.create_project_statusline_editor()
        self.main_tabs.addTab(self.project_tab, "Project (./.claude/settings.json)")

        layout.addWidget(self.main_tabs)

        # Info tip
        tip_label = QLabel(
            "💡 The statusline displays contextual information at the bottom of Claude Code. "
            "Configure a custom script that receives session data as JSON and outputs formatted text."
        )
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; background: {theme.BG_MEDIUM}; font-size: {theme.FONT_SIZE_SMALL}px; padding: 8px; border-radius: 3px;")
        layout.addWidget(tip_label)

    def create_statusline_editor(self, scope):
        """Create statusline editor for user scope"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # File path label
        if scope == "user":
            file_path = self.config_manager.settings_file

        path_label = QLabel(f"File: {file_path}")
        path_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(path_label)

        # Configuration form
        config_group = QGroupBox("Statusline Settings")
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
        config_layout = QFormLayout()

        # Command input
        self.user_command_input = QLineEdit()
        self.user_command_input.setPlaceholderText("e.g., ~/.claude/statusline.sh or powershell -File ~/.claude/statusline.ps1")
        self.user_command_input.setStyleSheet(theme.get_line_edit_style())
        config_layout.addRow("Command:", self.user_command_input)

        # Padding input
        self.user_padding_input = QLineEdit()
        self.user_padding_input.setPlaceholderText("0")
        self.user_padding_input.setStyleSheet(theme.get_line_edit_style())
        config_layout.addRow("Padding:", self.user_padding_input)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Info browser
        info_label = QLabel("Statusline Info & Examples:")
        info_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY}; margin-top: 10px;")
        layout.addWidget(info_label)

        info_browser = QTextBrowser()
        info_browser.setOpenExternalLinks(True)
        info_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                padding: 10px;
                font-size: {theme.FONT_SIZE_SMALL}px;
            }}
        """)
        self.load_statusline_info(info_browser)
        layout.addWidget(info_browser, 1)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        enable_btn = QPushButton("✓ Enable Statusline")
        enable_btn.setToolTip("Enable statusline with current command and padding settings")
        disable_btn = QPushButton("✗ Disable Statusline")
        disable_btn.setToolTip("Disable statusline and clear configuration")
        reload_btn = QPushButton("🔄 Reload")
        reload_btn.setToolTip("Reload statusline configuration from settings file")
        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip("Save statusline configuration to settings file")
        backup_btn = QPushButton("📦 Backup & Save")
        backup_btn.setToolTip("Create backup of settings file before saving")

        for btn in [enable_btn, disable_btn, reload_btn, save_btn, backup_btn]:
            btn.setStyleSheet(theme.get_button_style())

        enable_btn.clicked.connect(lambda: self.enable_statusline(scope))
        disable_btn.clicked.connect(lambda: self.disable_statusline(scope))
        reload_btn.clicked.connect(lambda: self.load_statusline(scope))
        save_btn.clicked.connect(lambda: self.save_statusline(scope))
        backup_btn.clicked.connect(lambda: self.backup_and_save(scope))

        button_layout.addWidget(enable_btn)
        button_layout.addWidget(disable_btn)
        button_layout.addStretch()
        button_layout.addWidget(reload_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(backup_btn)

        layout.addLayout(button_layout)

        # Load initial data
        self.load_statusline(scope)

        return widget

    def create_project_statusline_editor(self):
        """Create project statusline editor with folder picker"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Project folder picker
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(5)

        folder_label = QLabel("Project Folder:")
        folder_label.setStyleSheet(f"color: {theme.FG_PRIMARY}; font-weight: bold;")

        self.project_folder_edit = QLineEdit()
        self.project_folder_edit.setText(str(Path.home()))
        self.project_folder_edit.setReadOnly(True)
        self.project_folder_edit.setStyleSheet(theme.get_line_edit_style())

        browse_folder_btn = QPushButton("Browse...")
        browse_folder_btn.setStyleSheet(theme.get_button_style())
        browse_folder_btn.setToolTip("Select a different project folder")
        browse_folder_btn.clicked.connect(self.browse_project_folder)

        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.project_folder_edit, 1)
        folder_layout.addWidget(browse_folder_btn)

        layout.addLayout(folder_layout)

        # File path label
        self.project_path_label = QLabel(f"File: {self.project_folder / '.claude' / 'settings.json'}")
        self.project_path_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(self.project_path_label)

        # Configuration form
        config_group = QGroupBox("Statusline Settings")
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
        config_layout = QFormLayout()

        # Command input
        self.project_command_input = QLineEdit()
        self.project_command_input.setPlaceholderText("e.g., ~/.claude/statusline.sh or powershell -File ~/.claude/statusline.ps1")
        self.project_command_input.setStyleSheet(theme.get_line_edit_style())
        config_layout.addRow("Command:", self.project_command_input)

        # Padding input
        self.project_padding_input = QLineEdit()
        self.project_padding_input.setPlaceholderText("0")
        self.project_padding_input.setStyleSheet(theme.get_line_edit_style())
        config_layout.addRow("Padding:", self.project_padding_input)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Info browser
        info_label = QLabel("Statusline Info & Examples:")
        info_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY}; margin-top: 10px;")
        layout.addWidget(info_label)

        info_browser = QTextBrowser()
        info_browser.setOpenExternalLinks(True)
        info_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                padding: 10px;
                font-size: {theme.FONT_SIZE_SMALL}px;
            }}
        """)
        self.load_statusline_info(info_browser)
        layout.addWidget(info_browser, 1)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        enable_btn = QPushButton("✓ Enable Statusline")
        enable_btn.setToolTip("Enable statusline with current command and padding settings")
        disable_btn = QPushButton("✗ Disable Statusline")
        disable_btn.setToolTip("Disable statusline and clear configuration")
        reload_btn = QPushButton("🔄 Reload")
        reload_btn.setToolTip("Reload statusline configuration from settings file")
        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip("Save statusline configuration to settings file")
        backup_btn = QPushButton("📦 Backup & Save")
        backup_btn.setToolTip("Create backup of settings file before saving")

        for btn in [enable_btn, disable_btn, reload_btn, save_btn, backup_btn]:
            btn.setStyleSheet(theme.get_button_style())

        enable_btn.clicked.connect(lambda: self.enable_statusline("project"))
        disable_btn.clicked.connect(lambda: self.disable_statusline("project"))
        reload_btn.clicked.connect(lambda: self.load_statusline("project"))
        save_btn.clicked.connect(lambda: self.save_statusline("project"))
        backup_btn.clicked.connect(lambda: self.backup_and_save("project"))

        button_layout.addWidget(enable_btn)
        button_layout.addWidget(disable_btn)
        button_layout.addStretch()
        button_layout.addWidget(reload_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(backup_btn)

        layout.addLayout(button_layout)

        # Load initial data
        self.load_statusline("project")

        return widget

    def browse_project_folder(self):
        """Browse for project folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Project Folder",
            str(Path.home())
        )
        if folder:
            self.project_folder = Path(folder)
            self.project_folder_edit.setText(str(Path.home()))
            self.project_path_label.setText(f"File: {self.project_folder / '.claude' / 'settings.json'}")
            # Reload settings from new folder
            self.load_statusline("project")

    def load_statusline(self, scope):
        """Load statusline from settings"""
        try:
            if scope == "user":
                file_path = self.config_manager.settings_file
                command_input = self.user_command_input
                padding_input = self.user_padding_input
            else:  # project
                file_path = self.project_folder / ".claude" / "settings.json"
                command_input = self.project_command_input
                padding_input = self.project_padding_input

            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                # Note: Claude Code uses "statusLine" with capital L
                statusline = settings.get("statusLine", {})
                command_input.setText(statusline.get("command", ""))
                padding_input.setText(str(statusline.get("padding", 0)))
            else:
                command_input.setText("")
                padding_input.setText("0")

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load statusline:\n{str(e)}")

    def save_statusline(self, scope):
        """Save statusline configuration"""
        try:
            if scope == "user":
                file_path = self.config_manager.settings_file
                command_input = self.user_command_input
                padding_input = self.user_padding_input
            else:  # project
                file_path = self.project_folder / ".claude" / "settings.json"
                command_input = self.project_command_input
                padding_input = self.project_padding_input

            # Load existing settings
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = {}
                file_path.parent.mkdir(parents=True, exist_ok=True)

            # Update statusline (note: Claude Code uses "statusLine" with capital L)
            settings["statusLine"] = {
                "type": "command",
                "command": command_input.text(),
                "padding": int(padding_input.text()) if padding_input.text() else 0
            }

            # Save
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)

            QMessageBox.information(self, "Saved", f"Statusline configuration saved to:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n{str(e)}")

    def backup_and_save(self, scope):
        """Backup and save"""
        try:
            if scope == "user":
                file_path = self.config_manager.settings_file
            else:  # project
                file_path = self.project_folder / ".claude" / "settings.json"

            if file_path.exists():
                self.backup_manager.create_file_backup(file_path)

            self.save_statusline(scope)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed:\n{str(e)}")

    def enable_statusline(self, scope):
        """Enable statusline"""
        try:
            if scope == "user":
                command_input = self.user_command_input
                padding_input = self.user_padding_input
            else:  # project
                command_input = self.project_command_input
                padding_input = self.project_padding_input

            if not command_input.text():
                QMessageBox.warning(self, "Missing Command", "Please enter a command for the statusline.")
                return

            self.save_statusline(scope)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to enable:\n{str(e)}")

    def disable_statusline(self, scope):
        """Disable statusline"""
        try:
            if scope == "user":
                file_path = self.config_manager.settings_file
                command_input = self.user_command_input
                padding_input = self.user_padding_input
            else:  # project
                file_path = self.project_folder / ".claude" / "settings.json"
                command_input = self.project_command_input
                padding_input = self.project_padding_input

            # Clear inputs
            command_input.setText("")
            padding_input.setText("0")

            # Remove from settings
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                # Note: Claude Code uses "statusLine" with capital L
                if "statusLine" in settings:
                    del settings["statusLine"]

                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(settings, f, indent=2)

            QMessageBox.information(self, "Disabled", "Statusline has been disabled.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to disable:\n{str(e)}")

    def load_statusline_info(self, browser):
        """Load statusline info and examples"""
        html = f"""
            <h3 style="color: {theme.ACCENT_PRIMARY};">What is the Statusline?</h3>
            <p>The statusline displays contextual information at the bottom of Claude Code sessions.</p>

            <h4 style="color: {theme.ACCENT_PRIMARY}; margin-top: 15px;">How It Works</h4>
            <ul style="line-height: 1.8;">
                <li>Configure a script/command that Claude Code will execute</li>
                <li>The script receives session data as JSON on stdin</li>
                <li>It outputs formatted text to stdout</li>
                <li>Claude Code displays this text in the statusline</li>
            </ul>

            <h4 style="color: {theme.ACCENT_PRIMARY}; margin-top: 15px;">Available Fields</h4>
            <ul style="line-height: 1.8;">
                <li><b>sessionId:</b> Current session ID</li>
                <li><b>model:</b> Model being used</li>
                <li><b>cost:</b> Estimated cost so far</li>
                <li><b>inputTokens:</b> Input tokens used</li>
                <li><b>outputTokens:</b> Output tokens generated</li>
                <li><b>cwd:</b> Current working directory</li>
                <li><b>timestamp:</b> Current timestamp</li>
            </ul>

            <h4 style="color: {theme.ACCENT_PRIMARY}; margin-top: 15px;">Example: PowerShell Script</h4>
            <pre style="background: {theme.BG_MEDIUM}; padding: 10px; border-radius: 3px;">
# Save as: ~/.claude/statusline.ps1
$input = $input | ConvertFrom-Json
"Session: $($input.sessionId) | Model: $($input.model) | Cost: $$($input.cost)"
            </pre>

            <h4 style="color: {theme.ACCENT_PRIMARY}; margin-top: 15px;">Example: Bash Script</h4>
            <pre style="background: {theme.BG_MEDIUM}; padding: 10px; border-radius: 3px;">
#!/bin/bash
# Save as: ~/.claude/statusline.sh (chmod +x)
data=$(cat)
session=$(echo "$data" | jq -r '.sessionId')
model=$(echo "$data" | jq -r '.model')
cost=$(echo "$data" | jq -r '.cost')
echo "Session: $session | Model: $model | Cost: $$cost"
            </pre>

            <h4 style="color: {theme.ACCENT_PRIMARY}; margin-top: 15px;">Configuration</h4>
            <ul style="line-height: 1.8;">
                <li><b>Command:</b> Path to your script (e.g., <code>~/.claude/statusline.sh</code> or <code>powershell -File ~/.claude/statusline.ps1</code>)</li>
                <li><b>Padding:</b> Number of blank lines to add before the statusline (default: 0)</li>
            </ul>

            <h4 style="color: {theme.ACCENT_PRIMARY}; margin-top: 15px;">Troubleshooting</h4>
            <ul style="line-height: 1.8;">
                <li>Make sure your script is executable (<code>chmod +x</code> on Unix)</li>
                <li>Use absolute paths for scripts and dependencies</li>
                <li>Test your script manually: <code>echo '{{"sessionId":"test"}}' | your-script.sh</code></li>
                <li>Check for syntax errors in your script</li>
                <li>Ensure jq is installed if using Bash example</li>
            </ul>
        """
        browser.setHtml(html)
