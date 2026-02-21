"""
Environment Variables Tab - managing environment variables from settings.json
"""

import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QMessageBox, QListWidget, QInputDialog,
    QListWidgetItem, QGroupBox, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme


class EnvVarsTab(QWidget):
    """Tab for managing environment variables from settings.json"""

    def __init__(self, config_manager, backup_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.settings_file = self.config_manager.claude_dir / "settings.json"

        self.init_ui()
        self.load_env_vars()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header
        header = QLabel("Environment Variables")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")
        layout.addWidget(header)

        # Info label
        info_label = QLabel(
            f"Environment variables are stored in settings.json under the 'env' key.\n"
            f"File: {self.settings_file}"
        )
        info_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_SMALL}px; color: {theme.FG_SECONDARY}; padding: 5px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Environment Variables Section
        env_vars_group = QGroupBox("Environment Variables (from settings.json)")
        env_vars_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: {theme.FG_PRIMARY};
                background-color: {theme.BG_MEDIUM};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: {theme.BG_MEDIUM};
            }}
        """)

        env_vars_layout = QVBoxLayout()

        # Search box
        search_layout = QHBoxLayout()
        search_layout.setSpacing(5)

        search_label = QLabel("Search:")
        search_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_NORMAL}px; color: {theme.FG_PRIMARY};")

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Filter variables...")
        self.search_box.setMaximumWidth(200)
        self.search_box.textChanged.connect(self.filter_env_vars)
        self.search_box.setStyleSheet(theme.get_line_edit_style())

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_box)
        search_layout.addStretch()

        env_vars_layout.addLayout(search_layout)

        # Env vars list
        self.env_vars_list = QListWidget()
        self.env_vars_list.itemClicked.connect(self.on_env_var_selected)
        self.env_vars_list.setStyleSheet(theme.get_list_widget_style())
        env_vars_layout.addWidget(self.env_vars_list)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        self.add_btn = QPushButton("➕ Add Variable")
        self.add_btn.setToolTip("Add new environment variable")
        self.edit_btn = QPushButton("✏️ Edit Variable")
        self.edit_btn.setToolTip("Edit selected variable")
        self.remove_btn = QPushButton("🗑 Remove Variable")
        self.remove_btn.setToolTip("Remove selected variable")
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setToolTip("Reload from settings.json")

        for btn in [self.add_btn, self.edit_btn, self.remove_btn, self.refresh_btn]:
            btn.setStyleSheet(theme.get_button_style())

        self.add_btn.clicked.connect(self.add_env_var)
        self.edit_btn.clicked.connect(self.edit_env_var)
        self.remove_btn.clicked.connect(self.remove_env_var)
        self.refresh_btn.clicked.connect(self.load_env_vars)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()

        env_vars_layout.addLayout(btn_layout)
        env_vars_group.setLayout(env_vars_layout)
        layout.addWidget(env_vars_group)

        # Info section
        info_group = QGroupBox("About Environment Variables")
        info_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 10px;
                color: {theme.FG_PRIMARY};
                background-color: {theme.BG_MEDIUM};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: {theme.BG_MEDIUM};
            }}
        """)

        info_layout = QVBoxLayout()
        info_text = QLabel(
            "Environment variables are stored in settings.json under the 'env' key:\n"
            "• Format: {\"env\": {\"KEY\": \"value\"}}\n"
            "• Applied to every Claude Code session\n"
            "• Common variables: ANTHROPIC_API_KEY, ANTHROPIC_MODEL, HTTP_PROXY, etc.\n"
            "• Settings precedence: Enterprise > CLI args > Local > Shared > User\n"
            "• Keep sensitive variables in user settings (~/.claude/settings.json)"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px; padding: 5px;")
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Store data
        self.settings_data = {}

    def load_env_vars(self):
        """Load environment variables from settings.json"""
        self.env_vars_list.clear()

        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings_data = json.load(f)

                env_vars = self.settings_data.get('env', {})

                if len(env_vars) == 0:
                    item = QListWidgetItem("No environment variables configured in settings.json")
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    item.setForeground(QColor(theme.FG_DIM))
                    self.env_vars_list.addItem(item)
                else:
                    for key, value in sorted(env_vars.items()):
                        # Mask sensitive values
                        display_value = self.mask_sensitive_value(key, value)
                        item = QListWidgetItem(f"{key} = {display_value}")
                        item.setData(Qt.ItemDataRole.UserRole, {'key': key, 'value': value})
                        item.setForeground(QColor(theme.SUCCESS_COLOR))
                        self.env_vars_list.addItem(item)
            else:
                item = QListWidgetItem(f"settings.json not found at {self.settings_file}")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                item.setForeground(QColor(theme.ERROR_COLOR))
                self.env_vars_list.addItem(item)

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load settings.json:\n{str(e)}")

    def mask_sensitive_value(self, key, value):
        """Mask sensitive values like API keys"""
        sensitive_keys = ['KEY', 'TOKEN', 'PASSWORD', 'SECRET', 'AUTH']

        if any(sensitive in key.upper() for sensitive in sensitive_keys):
            if len(value) > 8:
                return f"{value[:4]}...{value[-4:]}"
            else:
                return "***"
        return value

    def filter_env_vars(self, text):
        """Filter environment variables list based on search text"""
        for i in range(self.env_vars_list.count()):
            item = self.env_vars_list.item(i)
            if text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def on_env_var_selected(self, item):
        """Handle env var selection"""
        pass  # Could show full value in future

    def add_env_var(self):
        """Add new environment variable"""
        # Get list of available env vars that are not already configured
        available_vars = self.get_available_env_vars()
        existing_vars = self.settings_data.get('env', {}).keys()

        # Filter out already configured variables
        available_choices = [var for var in available_vars if var not in existing_vars]

        if len(available_choices) == 0:
            QMessageBox.information(
                self, "All Variables Configured",
                "All known environment variables are already configured.\n\n"
                "You can still add a custom variable by typing the name."
            )
            # Fall back to text input for custom variables
            key, ok = QInputDialog.getText(
                self, "Add Custom Environment Variable",
                "Enter custom variable name (e.g., MY_CUSTOM_VAR):"
            )
            if not ok or not key:
                return
            key = key.strip().upper().replace(' ', '_')
        else:
            # Show dropdown with available variables + "Custom..." option
            available_choices.append("Custom...")

            key, ok = QInputDialog.getItem(
                self, "Add Environment Variable",
                "Select variable to add (or choose 'Custom...' for custom variable):",
                available_choices,
                0,
                False
            )

            if not ok:
                return

            if key == "Custom...":
                # Allow custom variable name
                key, ok = QInputDialog.getText(
                    self, "Add Custom Environment Variable",
                    "Enter custom variable name (e.g., MY_CUSTOM_VAR):"
                )
                if not ok or not key:
                    return
                key = key.strip().upper().replace(' ', '_')

        # Show description if available
        descriptions = self.get_env_var_descriptions()
        if key in descriptions:
            QMessageBox.information(
                self, f"About {key}",
                descriptions[key]
            )

        # Check if this is a boolean variable
        boolean_vars = self.get_boolean_env_vars()
        if key in boolean_vars:
            # Use dropdown for boolean values
            value, ok = QInputDialog.getItem(
                self, "Select Boolean Value",
                f"Select value for {key}:",
                ["true", "false"],
                0,
                False
            )
            if not ok:
                return
        else:
            # Use text input for other values
            value, ok = QInputDialog.getText(
                self, "Add Environment Variable",
                f"Enter value for {key}:"
            )
            if not ok:
                return

        # Add to env
        if 'env' not in self.settings_data:
            self.settings_data['env'] = {}

        self.settings_data['env'][key] = value
        self.save_settings()
        self.load_env_vars()

    def get_boolean_env_vars(self):
        """Return list of boolean environment variables"""
        return [
            "DISABLE_TELEMETRY",
            "DISABLE_PROMPT_CACHING",
            "DISABLE_PROMPT_CACHING_FOR_AGENTS",
            "ENABLE_EXPERIMENTAL_FEATURES",
            "DEBUG",
            "VERBOSE",
        ]

    def get_env_var_descriptions(self):
        """Return descriptions for environment variables"""
        return {
            # API Configuration
            "ANTHROPIC_API_KEY": "Your Anthropic API key for authentication with Claude API",
            "ANTHROPIC_AUTH_TOKEN": "Alternative authentication token for Anthropic services",
            "ANTHROPIC_BASE_URL": "Custom base URL for Anthropic API endpoint",
            "ANTHROPIC_API_URL": "Full API URL override for Anthropic services",

            # Model Selection
            "ANTHROPIC_MODEL": "Default model to use for Claude Code sessions",
            "ANTHROPIC_DEFAULT_SONNET_MODEL": "Specific Sonnet model version to use",
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": "Specific Haiku model version to use",
            "ANTHROPIC_DEFAULT_OPUS_MODEL": "Specific Opus model version to use",

            # Timeout Settings
            "BASH_DEFAULT_TIMEOUT_MS": "Default timeout in milliseconds for bash commands",
            "MCP_TIMEOUT": "Timeout in milliseconds for MCP server operations",
            "ANTHROPIC_TIMEOUT": "Timeout in milliseconds for Anthropic API requests",

            # Feature Flags
            "DISABLE_TELEMETRY": "Set to 'true' to disable usage telemetry collection",
            "DISABLE_PROMPT_CACHING": "Set to 'true' to disable prompt caching feature",
            "DISABLE_PROMPT_CACHING_FOR_AGENTS": "Set to 'true' to disable prompt caching for agents only",
            "ENABLE_EXPERIMENTAL_FEATURES": "Set to 'true' to enable experimental Claude Code features",

            # Proxy Settings
            "HTTP_PROXY": "HTTP proxy server URL (e.g., http://proxy.example.com:8080)",
            "HTTPS_PROXY": "HTTPS proxy server URL for secure connections",
            "NO_PROXY": "Comma-separated list of hosts to bypass proxy (e.g., localhost,127.0.0.1)",
            "ALL_PROXY": "Proxy server URL for all protocols",

            # Debug and Logging
            "DEBUG": "Set to 'true' to enable debug mode with verbose logging",
            "VERBOSE": "Set to 'true' to enable verbose output",
            "LOG_LEVEL": "Logging level (e.g., debug, info, warn, error)",

            # MCP Configuration
            "MCP_SERVER_PATH": "Custom path to MCP server executable",
            "MCP_SERVER_COMMAND": "Custom command to start MCP server",

            # Custom paths
            "CLAUDE_CONFIG_PATH": "Custom path to Claude Code configuration directory",
            "CLAUDE_CACHE_PATH": "Custom path to Claude Code cache directory",

            # Other common variables
            "NODE_ENV": "Node.js environment (development, production, test)",
            "PATH": "System PATH environment variable for executable lookup",
            "HOME": "User home directory path",
            "USER": "Current system username",
        }

    def get_available_env_vars(self):
        """Return list of known Claude Code environment variables"""
        return sorted([
            # API Configuration
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_AUTH_TOKEN",
            "ANTHROPIC_BASE_URL",
            "ANTHROPIC_API_URL",

            # Model Selection
            "ANTHROPIC_MODEL",
            "ANTHROPIC_DEFAULT_SONNET_MODEL",
            "ANTHROPIC_DEFAULT_HAIKU_MODEL",
            "ANTHROPIC_DEFAULT_OPUS_MODEL",

            # Timeout Settings
            "BASH_DEFAULT_TIMEOUT_MS",
            "MCP_TIMEOUT",
            "ANTHROPIC_TIMEOUT",

            # Feature Flags
            "DISABLE_TELEMETRY",
            "DISABLE_PROMPT_CACHING",
            "DISABLE_PROMPT_CACHING_FOR_AGENTS",
            "ENABLE_EXPERIMENTAL_FEATURES",

            # Proxy Settings
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "NO_PROXY",
            "ALL_PROXY",

            # Debug and Logging
            "DEBUG",
            "VERBOSE",
            "LOG_LEVEL",

            # MCP Configuration
            "MCP_SERVER_PATH",
            "MCP_SERVER_COMMAND",

            # Custom paths
            "CLAUDE_CONFIG_PATH",
            "CLAUDE_CACHE_PATH",

            # Other common variables
            "NODE_ENV",
            "PATH",
            "HOME",
            "USER",
        ])

    def edit_env_var(self):
        """Edit selected environment variable"""
        current_item = self.env_vars_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a variable to edit.")
            return

        var_data = current_item.data(Qt.ItemDataRole.UserRole)
        if not var_data:
            return

        key = var_data['key']
        old_value = var_data['value']

        value, ok = QInputDialog.getText(
            self, "Edit Environment Variable",
            f"Edit value for {key}:",
            text=old_value
        )

        if not ok:
            return

        self.settings_data['env'][key] = value
        self.save_settings()
        self.load_env_vars()

    def remove_env_var(self):
        """Remove selected environment variable"""
        current_item = self.env_vars_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a variable to remove.")
            return

        var_data = current_item.data(Qt.ItemDataRole.UserRole)
        if not var_data:
            return

        key = var_data['key']

        reply = QMessageBox.question(
            self, "Confirm Removal",
            f"Remove environment variable '{key}' from settings.json?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            del self.settings_data['env'][key]
            self.save_settings()
            self.load_env_vars()

    def save_settings(self):
        """Save settings.json"""
        try:
            # Create backup if file exists
            if self.settings_file.exists():
                self.backup_manager.create_file_backup(self.settings_file)

            # Save with proper formatting
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings_data, f, indent=2)

            QMessageBox.information(self, "Saved", "Environment variables saved to settings.json")

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save settings.json:\n{str(e)}")
