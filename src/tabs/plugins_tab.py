"""
Plugins Tab - managing Claude Code plugins from both settings.json and ~/.claude/plugins/
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QMessageBox, QListWidget,
    QListWidgetItem, QGroupBox, QInputDialog, QTextBrowser, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from utils import theme
from utils.terminal_utils import run_in_terminal

class PluginsTab(QWidget):
    """Tab for managing Claude Code plugins from both settings.json and ~/.claude/plugins/"""

    def __init__(self, config_manager, backup_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager

        # Plugin file locations (may be RemotePath if connected to remote server)
        self.settings_file = self.config_manager.settings_file
        _claude_dir = self.config_manager.claude_dir
        self.plugins_dir = _claude_dir / "plugins"
        # Claude Code records installed plugins in installed_plugins.json
        # ({"version": 2, "plugins": {"name@marketplace": [ {scope, version, ...} ]}}).
        self.plugins_config_file = self.plugins_dir / "installed_plugins.json"
        self.plugins_marketplaces_file = self.plugins_dir / "known_marketplaces.json"

        self.init_ui()
        self.load_all_data()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        # Header
        header = QLabel("Plugins")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")
        layout.addWidget(header)

        # Compact file locations bar
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl

        info_label = QLabel(
            f"Settings: <code>{self.settings_file}</code> &nbsp;|&nbsp; "
            f"Plugins dir: <code>{self.plugins_dir}</code> &nbsp;|&nbsp; "
            f'<a href="https://claudemarketplaces.com/">Browse Marketplaces</a>'
        )
        info_label.setOpenExternalLinks(True)
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_SMALL}px; padding: 4px;")
        layout.addWidget(info_label)

        # Quick Actions Section
        quick_actions_group = QGroupBox("Quick Actions - Browse & Install Plugins")

        quick_actions_layout = QHBoxLayout()
        quick_actions_layout.setSpacing(10)

        # Marketplace management buttons (FIRST)
        self.add_known_marketplace_btn = QPushButton("➕ Add Marketplace")
        self.add_known_marketplace_btn.setToolTip("Add a new marketplace from GitHub/URL/path")
        self.add_known_marketplace_btn.clicked.connect(self.add_known_marketplace)

        self.remove_known_marketplace_btn = QPushButton("🗑 Remove Marketplace")
        self.remove_known_marketplace_btn.setToolTip("Remove selected marketplace")
        self.remove_known_marketplace_btn.clicked.connect(self.remove_known_marketplace)

        # Plugin browsing/installation buttons
        browse_marketplace_btn = QPushButton("🛒 Browse Marketplace (GUI)")
        browse_marketplace_btn.setToolTip("Browse and install plugins from marketplaces in GUI")
        browse_marketplace_btn.clicked.connect(self.open_marketplace_browser)

        browse_plugin_btn = QPushButton("📦 Browse in Terminal")
        browse_plugin_btn.setToolTip("Open Claude with /plugin command to browse available plugins")
        browse_plugin_btn.clicked.connect(self.browse_plugins)

        install_plugin_btn = QPushButton("⬇️ Install Plugin")
        install_plugin_btn.setToolTip("Install a plugin by name (e.g., formatter@your-org)")
        install_plugin_btn.clicked.connect(self.install_plugin_dialog)

        refresh_all_btn = QPushButton("🔄 Refresh All")
        refresh_all_btn.setToolTip("Reload all plugin data from files")
        refresh_all_btn.clicked.connect(self.load_all_data)

        quick_actions_layout.addWidget(self.add_known_marketplace_btn)
        quick_actions_layout.addWidget(self.remove_known_marketplace_btn)
        quick_actions_layout.addWidget(browse_marketplace_btn)
        quick_actions_layout.addWidget(browse_plugin_btn)
        quick_actions_layout.addWidget(install_plugin_btn)
        quick_actions_layout.addWidget(refresh_all_btn)
        quick_actions_layout.addStretch()

        quick_actions_group.setLayout(quick_actions_layout)
        layout.addWidget(quick_actions_group)

        # ── Splitter: left = plugins, right = marketplaces + reference ──────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(6)
        layout.addWidget(splitter, 1)

        # ── LEFT: Enabled + Installed Plugins ────────────────────────────────
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(5)

        # Enabled Plugins
        enabled_plugins_group = QGroupBox("Enabled Plugins (settings.json)")
        enabled_plugins_layout = QVBoxLayout(enabled_plugins_group)
        self.enabled_plugins_list = QListWidget()
        enabled_plugins_layout.addWidget(self.enabled_plugins_list)
        enabled_plugins_btn_layout = QHBoxLayout()
        enabled_plugins_btn_layout.setSpacing(4)
        self.add_enabled_plugin_btn = QPushButton("Add")
        self.add_enabled_plugin_btn.setToolTip("Add a plugin to enabledPlugins in settings.json")
        self.toggle_enabled_plugin_btn = QPushButton("Toggle")
        self.toggle_enabled_plugin_btn.setToolTip("Enable or disable the selected plugin")
        self.remove_enabled_plugin_btn = QPushButton("Remove")
        self.remove_enabled_plugin_btn.setToolTip("Remove plugin from enabledPlugins in settings.json")
        self.add_enabled_plugin_btn.clicked.connect(self.add_enabled_plugin)
        self.toggle_enabled_plugin_btn.clicked.connect(self.toggle_enabled_plugin)
        self.remove_enabled_plugin_btn.clicked.connect(self.remove_enabled_plugin)
        for b in (self.add_enabled_plugin_btn, self.toggle_enabled_plugin_btn, self.remove_enabled_plugin_btn):
            enabled_plugins_btn_layout.addWidget(b)
        enabled_plugins_btn_layout.addStretch()
        enabled_plugins_layout.addLayout(enabled_plugins_btn_layout)
        left_layout.addWidget(enabled_plugins_group)

        # Installed Plugins
        installed_plugins_group = QGroupBox("Installed Plugins (~/.claude/plugins/installed_plugins.json)")
        installed_plugins_layout = QVBoxLayout(installed_plugins_group)
        self.installed_plugins_list = QListWidget()
        installed_plugins_layout.addWidget(self.installed_plugins_list)
        left_layout.addWidget(installed_plugins_group)

        splitter.addWidget(left)

        # ── RIGHT: Marketplaces + Reference ──────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(4, 0, 0, 0)
        right_layout.setSpacing(5)

        # Known Marketplaces
        known_marketplaces_group = QGroupBox("Known Marketplaces (~/.claude/plugins/known_marketplaces.json)")
        known_marketplaces_layout = QVBoxLayout(known_marketplaces_group)
        self.known_marketplaces_list = QListWidget()
        known_marketplaces_layout.addWidget(self.known_marketplaces_list)
        right_layout.addWidget(known_marketplaces_group)

        # Extra Marketplaces
        extra_marketplaces_group = QGroupBox("Extra Known Marketplaces (settings.json)")
        extra_marketplaces_layout = QVBoxLayout(extra_marketplaces_group)
        self.extra_marketplaces_list = QListWidget()
        extra_marketplaces_layout.addWidget(self.extra_marketplaces_list)
        extra_marketplaces_btn_layout = QHBoxLayout()
        extra_marketplaces_btn_layout.setSpacing(4)
        self.add_extra_marketplace_btn = QPushButton("Add")
        self.add_extra_marketplace_btn.setToolTip("Add marketplace to extraKnownMarketplaces in settings.json")
        self.remove_extra_marketplace_btn = QPushButton("Remove")
        self.remove_extra_marketplace_btn.setToolTip("Remove marketplace from extraKnownMarketplaces in settings.json")
        self.add_extra_marketplace_btn.clicked.connect(self.add_extra_marketplace)
        self.remove_extra_marketplace_btn.clicked.connect(self.remove_extra_marketplace)
        extra_marketplaces_btn_layout.addWidget(self.add_extra_marketplace_btn)
        extra_marketplaces_btn_layout.addWidget(self.remove_extra_marketplace_btn)
        extra_marketplaces_btn_layout.addStretch()
        extra_marketplaces_layout.addLayout(extra_marketplaces_btn_layout)
        right_layout.addWidget(extra_marketplaces_group)

        # Plugin Capabilities reference
        plugin_ref_group = QGroupBox("Plugin Capabilities (plugin.json reference)")
        plugin_ref_layout = QVBoxLayout(plugin_ref_group)
        plugin_ref_layout.setSpacing(4)
        plugin_ref = QTextBrowser()
        plugin_ref.setOpenExternalLinks(False)
        _sz = theme.FONT_SIZE_SMALL
        plugin_ref.setHtml(
            f"<span style='font-size:{_sz}px; color:{theme.FG_SECONDARY};'>"
            "Directories at the plugin root (not inside <code>.claude-plugin/</code>): "
            "<code>skills/</code> <code>commands/</code> <code>agents/</code> "
            "<code>hooks/hooks.json</code> <code>.mcp.json</code> <code>.lsp.json</code> "
            "<code>monitors/monitors.json</code> <code>bin/</code><br>"
            "<b>.lsp.json</b> — keyed by language id: "
            "<code>{&quot;go&quot;: {&quot;command&quot;: &quot;gopls&quot;, "
            "&quot;extensionToLanguage&quot;: {&quot;.go&quot;: &quot;go&quot;}}}</code><br>"
            "<b>monitors/monitors.json</b> — array of watchers: "
            "<code>[{&quot;name&quot;: &quot;error-log&quot;, "
            "&quot;command&quot;: &quot;tail -F ./logs/error.log&quot;}]</code><br>"
            "<b>userConfig</b> — settings schema: "
            "<code>{&quot;apiKey&quot;: {&quot;type&quot;: &quot;string&quot;, "
            "&quot;title&quot;: &quot;API key&quot;, &quot;sensitive&quot;: true}}</code><br>"
            "<b>channels</b> — array of "
            "<code>{&quot;server&quot;: &quot;&lt;mcpServers key&gt;&quot;, &quot;userConfig&quot;: {…}}</code><br>"
            "<b>Vars:</b> <code>${CLAUDE_PLUGIN_ROOT}</code> install dir &nbsp; "
            "<code>${CLAUDE_PLUGIN_DATA}</code> persistent data dir"
            "</span>"
        )
        plugin_ref_layout.addWidget(plugin_ref)
        right_layout.addWidget(plugin_ref_group)
        self._plugin_ref = plugin_ref

        splitter.addWidget(right)
        splitter.setSizes([500, 500])

        # CLI reference footer
        cli_footer = QTextBrowser()
        cli_footer.setOpenExternalLinks(False)
        cli_footer.setMaximumHeight(50)
        cli_footer.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_SMALL}px; background: {theme.BG_MEDIUM}; "
            f"border-left: 3px solid {theme.ACCENT_SECONDARY}; border-radius: {theme.BORDER_RADIUS}px;"
        )
        cli_footer.setHtml(
            f"<span style='font-size:{theme.FONT_SIZE_SMALL}px;'>"
            "<b>CLI:</b> "
            "<code>claude plugin install &lt;id&gt;@&lt;marketplace&gt;</code> · "
            "<code>claude plugin uninstall &lt;id&gt; [--keep-data]</code> · "
            "<code>claude plugin enable/disable &lt;id&gt;</code> · "
            "<code>claude plugin update &lt;id&gt;</code> · "
            "<code>claude plugin validate</code> &nbsp;|&nbsp; "
            "<b>Cache:</b> <code>~/.claude/plugins/cache/</code>"
            "</span>"
        )
        layout.addWidget(cli_footer)
        self._cli_footer = cli_footer

        # Store data
        self.settings_data = {}
        self.plugins_config_data = {}
        self.plugins_marketplaces_data = {}

    def apply_theme(self):
        """Refresh HTML widgets with current theme colors."""
        self._plugin_ref.setHtml(
            f"<span style='font-size:{theme.FONT_SIZE_SMALL}px; color:{theme.FG_SECONDARY};'>"
            "<b>LSP Servers</b> — expose a Language Server Protocol server:<br>"
            f"<code style='font-size:{theme.FONT_SIZE_SMALL}px'>"
            "&nbsp;&nbsp;\"lsp\": {{\"command\": \"node\", \"args\": [\"server.js\"], \"languages\": [\"python\"]}}"
            "</code><br>"
            "<b>Monitors</b> — background watchers fired on file/event changes:<br>"
            f"<code style='font-size:{theme.FONT_SIZE_SMALL}px'>"
            "&nbsp;&nbsp;\"monitors\": [{{\"event\": \"FileChanged\", \"pattern\": \"*.py\", \"command\": \"lint.sh\"}}]"
            "</code><br>"
            "<b>userConfig</b> — user-configurable settings schema (shown in UI):<br>"
            f"<code style='font-size:{theme.FONT_SIZE_SMALL}px'>"
            "&nbsp;&nbsp;\"userConfig\": {{\"apiKey\": {{\"type\": \"string\", \"description\": \"API key\"}}}}"
            "</code><br>"
            "<b>channels</b> — communication channels: "
            "<code>\"channels\": [\"http\", \"stdio\"]</code><br>"
            "<b>Vars:</b> <code>${{CLAUDE_PLUGIN_ROOT}}</code> install dir &nbsp; "
            "<code>${{CLAUDE_PLUGIN_DATA}}</code> data dir"
            "</span>"
        )
        self._cli_footer.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_SMALL}px; background: {theme.BG_MEDIUM}; "
            f"border-left: 3px solid {theme.ACCENT_SECONDARY}; border-radius: {theme.BORDER_RADIUS}px;"
        )
        self._cli_footer.setHtml(
            f"<span style='font-size:{theme.FONT_SIZE_SMALL}px;'>"
            "<b>CLI:</b> "
            "<code>claude plugin install &lt;id&gt;@&lt;marketplace&gt;</code> · "
            "<code>claude plugin uninstall &lt;id&gt; [--keep-data]</code> · "
            "<code>claude plugin enable/disable &lt;id&gt;</code> · "
            "<code>claude plugin update &lt;id&gt;</code> · "
            "<code>claude plugin validate</code> &nbsp;|&nbsp; "
            "<b>Cache:</b> <code>~/.claude/plugins/cache/</code>"
            "</span>"
        )

    def load_all_data(self):
        """Load all plugin data from both locations"""
        self.load_enabled_plugins()
        self.load_installed_plugins()
        self.load_known_marketplaces()
        self.load_extra_marketplaces()

    def load_enabled_plugins(self):
        """Load enabledPlugins from settings.json"""
        self.enabled_plugins_list.clear()

        try:
            if isinstance(self.settings_file, Path) and self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings_data = json.load(f)

                enabled_plugins = self.settings_data.get('enabledPlugins', {})

                if len(enabled_plugins) == 0:
                    item = QListWidgetItem("No plugins enabled in settings.json")
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    item.setForeground(QColor(theme.FG_DIM))
                    self.enabled_plugins_list.addItem(item)
                else:
                    for plugin_name, is_enabled in enabled_plugins.items():
                        icon = "✓" if is_enabled else "✗"
                        item = QListWidgetItem(f"{icon} {plugin_name}")
                        item.setData(Qt.ItemDataRole.UserRole, {'name': plugin_name, 'enabled': is_enabled})

                        if is_enabled:
                            item.setForeground(QColor(theme.SUCCESS_COLOR))
                        else:
                            item.setForeground(QColor(theme.FG_DIM))

                        self.enabled_plugins_list.addItem(item)
            else:
                item = QListWidgetItem(f"settings.json not found")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                item.setForeground(QColor(theme.ERROR_COLOR))
                self.enabled_plugins_list.addItem(item)

        except Exception as e:
            logger.error("Failed to load enabled plugins from settings.json: %s", e)
            QMessageBox.critical(self, "Load Error", f"Failed to load settings.json:\n{str(e)}")

    def load_installed_plugins(self):
        """Load installed plugins from ~/.claude/plugins/installed_plugins.json"""
        self.installed_plugins_list.clear()

        try:
            if isinstance(self.plugins_config_file, Path) and self.plugins_config_file.exists():
                with open(self.plugins_config_file, 'r', encoding='utf-8') as f:
                    self.plugins_config_data = json.load(f)

                # Newer format: {"version": 2, "plugins": {"name@mkt": [ {scope, version, ...} ]}}
                # Older format: {"repositories": {...}}
                plugins = self.plugins_config_data.get('plugins') \
                    or self.plugins_config_data.get('repositories', {})

                if not plugins:
                    item = QListWidgetItem("No plugins installed")
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    item.setForeground(QColor(theme.FG_DIM))
                    self.installed_plugins_list.addItem(item)
                else:
                    for plugin_name, plugin_config in plugins.items():
                        detail = ""
                        entries = plugin_config if isinstance(plugin_config, list) else [plugin_config]
                        if entries and isinstance(entries[0], dict):
                            e0 = entries[0]
                            ver = e0.get('version', '')
                            scopes = ", ".join(sorted({e.get('scope', '') for e in entries if isinstance(e, dict)}))
                            detail = f"  ({ver}{' · ' + scopes if scopes else ''})"
                        item = QListWidgetItem(f"📦 {plugin_name}{detail}")
                        item.setData(Qt.ItemDataRole.UserRole, {'name': plugin_name, 'config': plugin_config})
                        item.setForeground(QColor(theme.SUCCESS_COLOR))
                        self.installed_plugins_list.addItem(item)
            else:
                item = QListWidgetItem("installed_plugins.json not found")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                item.setForeground(QColor(theme.ERROR_COLOR))
                self.installed_plugins_list.addItem(item)

        except Exception as e:
            logger.error("Failed to load installed plugins: %s", e)
            QMessageBox.critical(self, "Load Error", f"Failed to load config.json:\n{str(e)}")

    def load_known_marketplaces(self):
        """Load known marketplaces from ~/.claude/plugins/known_marketplaces.json"""
        self.known_marketplaces_list.clear()

        try:
            if isinstance(self.plugins_marketplaces_file, Path) and self.plugins_marketplaces_file.exists():
                with open(self.plugins_marketplaces_file, 'r', encoding='utf-8') as f:
                    self.plugins_marketplaces_data = json.load(f)

                if len(self.plugins_marketplaces_data) == 0:
                    item = QListWidgetItem("No marketplaces configured")
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    item.setForeground(QColor(theme.FG_DIM))
                    self.known_marketplaces_list.addItem(item)
                else:
                    for marketplace_name, marketplace_config in self.plugins_marketplaces_data.items():
                        source_info = marketplace_config.get('source', {})
                        source_type = source_info.get('source', 'unknown')
                        repo = source_info.get('repo', source_info.get('url', source_info.get('path', 'N/A')))

                        item = QListWidgetItem(f"📦 {marketplace_name} ({source_type}: {repo})")
                        item.setData(Qt.ItemDataRole.UserRole, {'name': marketplace_name, 'config': marketplace_config})
                        item.setForeground(QColor(theme.ACCENT_PRIMARY))
                        self.known_marketplaces_list.addItem(item)
            else:
                item = QListWidgetItem(f"known_marketplaces.json not found")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                item.setForeground(QColor(theme.ERROR_COLOR))
                self.known_marketplaces_list.addItem(item)

        except Exception as e:
            logger.error("Failed to load known_marketplaces.json: %s", e)
            QMessageBox.critical(self, "Load Error", f"Failed to load known_marketplaces.json:\n{str(e)}")

    def load_extra_marketplaces(self):
        """Load extraKnownMarketplaces from settings.json"""
        self.extra_marketplaces_list.clear()

        try:
            if isinstance(self.settings_file, Path) and self.settings_file.exists():
                extra_marketplaces = self.settings_data.get('extraKnownMarketplaces', {})

                if len(extra_marketplaces) == 0:
                    item = QListWidgetItem("No extra marketplaces in settings.json")
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    item.setForeground(QColor(theme.FG_DIM))
                    self.extra_marketplaces_list.addItem(item)
                else:
                    for marketplace_name, marketplace_config in extra_marketplaces.items():
                        source_info = marketplace_config.get('source', {})
                        source_type = source_info.get('source', 'unknown')
                        repo = source_info.get('repo', source_info.get('url', source_info.get('path', 'N/A')))

                        item = QListWidgetItem(f"📦 {marketplace_name} ({source_type}: {repo})")
                        item.setData(Qt.ItemDataRole.UserRole, {'name': marketplace_name, 'config': marketplace_config})
                        item.setForeground(QColor(theme.ACCENT_PRIMARY))
                        self.extra_marketplaces_list.addItem(item)
            else:
                item = QListWidgetItem(f"settings.json not found")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                item.setForeground(QColor(theme.ERROR_COLOR))
                self.extra_marketplaces_list.addItem(item)

        except Exception as e:
            logger.error("Failed to load extraKnownMarketplaces: %s", e)
            QMessageBox.critical(self, "Load Error", f"Failed to load extraKnownMarketplaces:\n{str(e)}")

    def add_enabled_plugin(self):
        """Add plugin to enabledPlugins in settings.json"""
        plugin_name, ok = QInputDialog.getText(
            self, "Add Enabled Plugin",
            "Enter plugin name (format: plugin-name@marketplace-name):"
        )

        if not ok or not plugin_name:
            return

        if '@' not in plugin_name:
            QMessageBox.warning(self, "Invalid Format",
                "Plugin name must be in format: plugin-name@marketplace-name")
            return

        if 'enabledPlugins' not in self.settings_data:
            self.settings_data['enabledPlugins'] = {}

        self.settings_data['enabledPlugins'][plugin_name] = True
        self.save_settings()
        self.load_enabled_plugins()

    def toggle_enabled_plugin(self):
        """Toggle plugin enabled/disabled in settings.json"""
        current_item = self.enabled_plugins_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a plugin to toggle.")
            return

        plugin_data = current_item.data(Qt.ItemDataRole.UserRole)
        if not plugin_data:
            return

        plugin_name = plugin_data['name']
        current_state = plugin_data['enabled']

        self.settings_data['enabledPlugins'][plugin_name] = not current_state
        self.save_settings()
        self.load_enabled_plugins()

    def remove_enabled_plugin(self):
        """Remove plugin from enabledPlugins in settings.json"""
        current_item = self.enabled_plugins_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a plugin to remove.")
            return

        plugin_data = current_item.data(Qt.ItemDataRole.UserRole)
        if not plugin_data:
            return

        plugin_name = plugin_data['name']

        reply = QMessageBox.question(self, "Confirm Removal",
            f"Remove plugin '{plugin_name}' from settings.json?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            del self.settings_data['enabledPlugins'][plugin_name]
            self.save_settings()
            self.load_enabled_plugins()

    def add_known_marketplace(self):
        """Add marketplace to known_marketplaces.json"""
        marketplace_name, ok = QInputDialog.getText(self, "Add Marketplace", "Enter marketplace name:")
        if not ok or not marketplace_name:
            return

        source_type, ok = QInputDialog.getItem(self, "Marketplace Source",
            "Select source type:", ["github", "git", "directory"], 0, False)
        if not ok:
            return

        if source_type == "github":
            param_name, param_prompt = "repo", "Enter GitHub repository (e.g., user-org/repo-name):"
        elif source_type == "git":
            param_name, param_prompt = "url", "Enter Git repository URL:"
        else:
            param_name, param_prompt = "path", "Enter local directory path:"

        param_value, ok = QInputDialog.getText(self, f"Marketplace {param_name.title()}", param_prompt)
        if not ok or not param_value:
            return

        from datetime import datetime
        marketplace_config = {
            "source": {"source": source_type, param_name: param_value},
            "installLocation": str(self.plugins_dir / "marketplaces" / marketplace_name),
            "lastUpdated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        }

        self.plugins_marketplaces_data[marketplace_name] = marketplace_config
        self.save_known_marketplaces()
        self.load_known_marketplaces()

    def remove_known_marketplace(self):
        """Remove marketplace from known_marketplaces.json"""
        current_item = self.known_marketplaces_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a marketplace to remove.")
            return

        marketplace_data = current_item.data(Qt.ItemDataRole.UserRole)
        if not marketplace_data:
            return

        marketplace_name = marketplace_data['name']

        reply = QMessageBox.question(self, "Confirm Removal",
            f"Remove marketplace '{marketplace_name}' from known_marketplaces.json?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            del self.plugins_marketplaces_data[marketplace_name]
            self.save_known_marketplaces()
            self.load_known_marketplaces()

    def add_extra_marketplace(self):
        """Add marketplace to extraKnownMarketplaces in settings.json"""
        marketplace_name, ok = QInputDialog.getText(self, "Add Extra Marketplace", "Enter marketplace name:")
        if not ok or not marketplace_name:
            return

        source_type, ok = QInputDialog.getItem(self, "Marketplace Source",
            "Select source type:", ["github", "git", "directory"], 0, False)
        if not ok:
            return

        if source_type == "github":
            param_name, param_prompt = "repo", "Enter GitHub repository (e.g., user-org/repo-name):"
        elif source_type == "git":
            param_name, param_prompt = "url", "Enter Git repository URL:"
        else:
            param_name, param_prompt = "path", "Enter local directory path:"

        param_value, ok = QInputDialog.getText(self, f"Marketplace {param_name.title()}", param_prompt)
        if not ok or not param_value:
            return

        if 'extraKnownMarketplaces' not in self.settings_data:
            self.settings_data['extraKnownMarketplaces'] = {}

        self.settings_data['extraKnownMarketplaces'][marketplace_name] = {
            "source": {"source": source_type, param_name: param_value}
        }

        self.save_settings()
        self.load_extra_marketplaces()

    def remove_extra_marketplace(self):
        """Remove marketplace from extraKnownMarketplaces in settings.json"""
        current_item = self.extra_marketplaces_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a marketplace to remove.")
            return

        marketplace_data = current_item.data(Qt.ItemDataRole.UserRole)
        if not marketplace_data:
            return

        marketplace_name = marketplace_data['name']

        reply = QMessageBox.question(self, "Confirm Removal",
            f"Remove marketplace '{marketplace_name}' from settings.json?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            del self.settings_data['extraKnownMarketplaces'][marketplace_name]
            self.save_settings()
            self.load_extra_marketplaces()

    def save_settings(self):
        """Save settings.json"""
        try:
            if not isinstance(self.settings_file, Path):
                QMessageBox.warning(self, "Not Supported", "Saving plugin settings is not supported for remote connections.")
                return

            if self.settings_file.exists():
                self.backup_manager.create_file_backup(self.settings_file)

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings_data, f, indent=2)

            QMessageBox.information(self, "Saved", "Changes saved to settings.json")
        except Exception as e:
            logger.error("Failed to save settings.json: %s", e)
            QMessageBox.critical(self, "Save Error", f"Failed to save settings.json:\n{str(e)}")

    def save_known_marketplaces(self):
        """Save known_marketplaces.json"""
        try:
            if not isinstance(self.plugins_marketplaces_file, Path):
                QMessageBox.warning(self, "Not Supported", "Saving marketplace config is not supported for remote connections.")
                return

            if self.plugins_marketplaces_file.exists():
                self.backup_manager.create_file_backup(self.plugins_marketplaces_file)

            self.plugins_marketplaces_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.plugins_marketplaces_file, 'w', encoding='utf-8') as f:
                json.dump(self.plugins_marketplaces_data, f, indent=2)

            QMessageBox.information(self, "Saved", "Changes saved to known_marketplaces.json")
        except Exception as e:
            logger.error("Failed to save known_marketplaces.json: %s", e)
            QMessageBox.critical(self, "Save Error", f"Failed to save known_marketplaces.json:\n{str(e)}")

    def open_marketplace_browser(self):
        """Open GUI marketplace browser"""
        from dialogs.plugin_marketplace_browser import PluginMarketplaceBrowserDialog

        # Get all marketplaces
        known_marketplaces = self.plugins_marketplaces_data if hasattr(self, 'plugins_marketplaces_data') else {}
        extra_marketplaces = self.settings_data.get('extraKnownMarketplaces', {}) if hasattr(self, 'settings_data') else {}

        if not known_marketplaces and not extra_marketplaces:
            QMessageBox.warning(
                self,
                "No Marketplaces",
                "No marketplaces configured.\n\n"
                "Please add marketplaces using the '➕ Add Marketplace' button first."
            )
            return

        # Open marketplace browser dialog
        dialog = PluginMarketplaceBrowserDialog(self, known_marketplaces, extra_marketplaces)
        dialog.exec()

        # Refresh plugin lists after dialog closes
        self.load_all_data()

    def browse_plugins(self):
        """Open terminal with claude /plugin command"""
        run_in_terminal('claude /plugin', 'Browse Plugins', self)

    def install_plugin_dialog(self):
        """Install a plugin by name via dialog"""
        from PyQt6.QtWidgets import QInputDialog

        plugin_name, ok = QInputDialog.getText(
            self,
            "Install Plugin",
            "Enter plugin name (e.g., formatter@your-org):\n\n" +
            "Format: plugin-name@marketplace-name"
        )

        if ok and plugin_name:
            self.install_plugin(plugin_name.strip())

    def install_plugin(self, plugin_name):
        """Install a plugin using claude plugin install command"""
        try:
            import subprocess

            # Run claude plugin install command
            result = subprocess.run(
                ["claude", "plugin", "install", plugin_name],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=60,
            )

            if result.returncode == 0:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Plugin '{plugin_name}' installed successfully!\n\n" +
                    result.stdout +
                    "\n\nRefreshing plugin data..."
                )
                # Reload all data to show the newly installed plugin
                self.load_all_data()
            else:
                QMessageBox.warning(
                    self,
                    "Installation Failed",
                    f"Failed to install plugin '{plugin_name}':\n\n{result.stderr}"
                )

        except subprocess.TimeoutExpired:
            logger.error("Plugin installation timed out")
            QMessageBox.critical(self, "Timeout", "Plugin installation timed out after 60 seconds")
        except Exception as e:
            logger.error("Failed to install plugin: %s", e)
            QMessageBox.critical(self, "Error", f"Failed to install plugin:\n{str(e)}")
