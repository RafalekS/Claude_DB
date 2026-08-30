"""
User Configuration Tab - Container for all user-level (global) configuration
Includes 8 sub-tabs:
1. Settings (Model, Theme)
2. Hooks
3. Permissions
4. Statusline
5. Agents
6. Commands
7. MCP Servers
8. Skills
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget
)

from utils import theme
# Import subtabs (using OLD correct implementations)
from tabs.user_settings_subtab import UserSettingsSubTab
from tabs.raw_settings_subtab import RawSettingsSubTab, user_scope
from tabs.user_hooks_subtab import UserHooksSubTab
from tabs.user_permissions_subtab import UserPermissionsSubTab
from tabs.user_statusline_subtab import UserStatuslineSubTab
from tabs.agents_tab import AgentsTab
from tabs.commands_tab import CommandsTab
from tabs.mcp_tab import MCPTab
from tabs.skills_tab import SkillsTab
from tabs.rules_tab import RulesTab
from tabs.claude_local_md_tab import ClaudeLocalMDTab
from tabs.claude_md_tab import ClaudeMDTab
from tabs.env_vars_tab import EnvVarsTab

class UserConfigTab(QWidget):
    """Container tab for all user-level configuration (~/. claude/)"""

    def __init__(self, config_manager, backup_manager, settings_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.settings_manager = settings_manager
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        header = QLabel("User (Global) Configuration")
        header.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; "
            f"font-weight: bold; "
            f"color: {theme.ACCENT_PRIMARY};"
        )

        self.info_label = QLabel(str(self.config_manager.claude_dir))
        self.info_label.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; "
            f"font-style: italic;"
        )

        header_layout.addWidget(header)
        header_layout.addWidget(self.info_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Description
        desc = QLabel(
            "Configure user-level settings that apply across all projects. "
            "These settings are stored in your home directory (~/.claude/)."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; "
            f"padding: 5px; "
            f"margin-bottom: 10px;"
        )
        layout.addWidget(desc)

        # Tab widget for sub-tabs — uses global app stylesheet, no per-widget override
        self.sub_tabs = QTabWidget()

        # Add sub-tabs with actual implementations

        # Settings sub-tab (Model, Theme, Environment Variables)
        self._settings_tab = UserSettingsSubTab(self.config_manager, self.backup_manager, self.settings_manager)
        self.sub_tabs.addTab(self._settings_tab, "🎛️ Settings")

        # Raw settings.json editor — every key, not just the curated fields
        self._raw_settings_tab = RawSettingsSubTab(user_scope(self.config_manager), self.backup_manager)
        self.sub_tabs.addTab(self._raw_settings_tab, "⚙️ settings.json")

        # Env Vars sub-tab
        self._env_vars_tab = EnvVarsTab(self.config_manager, self.backup_manager)
        self.sub_tabs.addTab(self._env_vars_tab, "🔑 Env Vars")

        # Hooks sub-tab (User - uses settings.json)
        self._hooks_tab = UserHooksSubTab(self.config_manager, self.backup_manager, self.settings_manager)
        self.sub_tabs.addTab(self._hooks_tab, "🪝 Hooks")

        # Permissions sub-tab (User - uses settings.json)
        self._permissions_tab = UserPermissionsSubTab(self.config_manager, self.backup_manager, self.settings_manager)
        self.sub_tabs.addTab(self._permissions_tab, "🔒 Permissions")

        # Statusline sub-tab (User - uses settings.json)
        self._statusline_tab = UserStatuslineSubTab(self.config_manager, self.backup_manager, self.settings_manager)
        self.sub_tabs.addTab(self._statusline_tab, "📊 Statusline")

        # Agents sub-tab (Phase 3 - AgentsTab with user scope)
        self._agents_tab = AgentsTab(self.config_manager, self.backup_manager, "user", None)
        self.sub_tabs.addTab(self._agents_tab, "🤖 Agents")

        # Commands sub-tab (Phase 3 - CommandsTab with user scope)
        self._commands_tab = CommandsTab(self.config_manager, self.backup_manager, "user", None)
        self.sub_tabs.addTab(self._commands_tab, "⚡ Commands")

        # MCP Servers sub-tab (Phase 3 - MCPTab with user scope)
        self._mcp_tab = MCPTab(self.config_manager, self.backup_manager, "user", None)
        self.sub_tabs.addTab(self._mcp_tab, "🔌 MCP Servers")

        # Skills sub-tab (Phase 3 - SkillsTab with user scope)
        self._skills_tab = SkillsTab(self.config_manager, self.backup_manager, "user", None)
        self.sub_tabs.addTab(self._skills_tab, "🎓 Skills")

        # Rules sub-tab
        rules_tab = RulesTab(self.config_manager, self.backup_manager)
        self.sub_tabs.addTab(rules_tab, "📋 Rules")

        # CLAUDE.md sub-tab (editor for ~/.claude/CLAUDE.md)
        self._claude_md_tab = ClaudeMDTab(self.config_manager, self.backup_manager)
        self.sub_tabs.addTab(self._claude_md_tab, "📝 CLAUDE.md")

        # CLAUDE.local.md sub-tab
        self._local_md_tab = ClaudeLocalMDTab(self.config_manager, self.backup_manager)
        self.sub_tabs.addTab(self._local_md_tab, "📝 CLAUDE.local.md")

        layout.addWidget(self.sub_tabs, 1)

    def refresh_all(self):
        """Reload all subtabs from the current config_manager source (local or remote)."""
        self._settings_tab.load_settings()
        self._raw_settings_tab.load_settings()
        self._env_vars_tab.load_env_vars()
        self._hooks_tab.load_hooks()
        self._permissions_tab.load_permissions()
        self._statusline_tab.load_statusline()
        self._agents_tab.load_agents()
        self._commands_tab.load_commands()
        self._mcp_tab.load_mcp_config()
        self._skills_tab.load_skills()
        self._claude_md_tab.load_content()
        self._local_md_tab.load_content()
        # Update header path label
        self.info_label.setText(str(self.config_manager.claude_dir))

    def apply_theme(self):
        """Propagate theme change to all subtabs."""
        for i in range(self.sub_tabs.count()):
            widget = self.sub_tabs.widget(i)
            if hasattr(widget, 'apply_theme'):
                widget.apply_theme()

