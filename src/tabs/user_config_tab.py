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

        info_label = QLabel("~/.claude/")
        info_label.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; "
            f"font-style: italic;"
        )

        header_layout.addWidget(header)
        header_layout.addWidget(info_label)
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
        settings_tab = UserSettingsSubTab(self.config_manager, self.backup_manager, self.settings_manager)
        self.sub_tabs.addTab(settings_tab, "🎛️ Settings")

        # Env Vars sub-tab
        env_vars_tab = EnvVarsTab(self.config_manager, self.backup_manager)
        self.sub_tabs.addTab(env_vars_tab, "🔑 Env Vars")

        # Hooks sub-tab (User - uses settings.json)
        hooks_tab = UserHooksSubTab(self.config_manager, self.backup_manager, self.settings_manager)
        self.sub_tabs.addTab(hooks_tab, "🪝 Hooks")

        # Permissions sub-tab (User - uses settings.json)
        permissions_tab = UserPermissionsSubTab(self.config_manager, self.backup_manager, self.settings_manager)
        self.sub_tabs.addTab(permissions_tab, "🔒 Permissions")

        # Statusline sub-tab (User - uses settings.json)
        statusline_tab = UserStatuslineSubTab(self.config_manager, self.backup_manager, self.settings_manager)
        self.sub_tabs.addTab(statusline_tab, "📊 Statusline")

        # Agents sub-tab (Phase 3 - AgentsTab with user scope)
        agents_tab = AgentsTab(self.config_manager, self.backup_manager, "user", None)
        self.sub_tabs.addTab(agents_tab, "🤖 Agents")

        # Commands sub-tab (Phase 3 - CommandsTab with user scope)
        commands_tab = CommandsTab(self.config_manager, self.backup_manager, "user", None)
        self.sub_tabs.addTab(commands_tab, "⚡ Commands")

        # MCP Servers sub-tab (Phase 3 - MCPTab with user scope)
        mcp_tab = MCPTab(self.config_manager, self.backup_manager, "user", None)
        self.sub_tabs.addTab(mcp_tab, "🔌 MCP Servers")

        # Skills sub-tab (Phase 3 - SkillsTab with user scope)
        skills_tab = SkillsTab(self.config_manager, self.backup_manager, "user", None)
        self.sub_tabs.addTab(skills_tab, "🎓 Skills")

        # Rules sub-tab
        rules_tab = RulesTab(self.config_manager, self.backup_manager)
        self.sub_tabs.addTab(rules_tab, "📋 Rules")

        # CLAUDE.md sub-tab (editor for ~/.claude/CLAUDE.md)
        claude_md_tab = ClaudeMDTab(self.config_manager, self.backup_manager)
        self.sub_tabs.addTab(claude_md_tab, "📝 CLAUDE.md")

        # CLAUDE.local.md sub-tab
        local_md_tab = ClaudeLocalMDTab(self.config_manager, self.backup_manager)
        self.sub_tabs.addTab(local_md_tab, "📝 CLAUDE.local.md")

        layout.addWidget(self.sub_tabs, 1)

    def apply_theme(self):
        """Propagate theme change to all subtabs."""
        for i in range(self.sub_tabs.count()):
            widget = self.sub_tabs.widget(i)
            if hasattr(widget, 'apply_theme'):
                widget.apply_theme()

