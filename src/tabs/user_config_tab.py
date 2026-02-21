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

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget
)

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme
# Import subtabs (using OLD correct implementations)
from tabs.user_settings_subtab import UserSettingsSubTab
from tabs.user_model_info_subtab import UserModelInfoSubTab
from tabs.user_workflows_subtab import UserWorkflowsSubTab
from tabs.user_hooks_subtab import UserHooksSubTab
from tabs.user_permissions_subtab import UserPermissionsSubTab
from tabs.user_statusline_subtab import UserStatuslineSubTab
from tabs.agents_tab import AgentsTab
from tabs.commands_tab import CommandsTab
from tabs.mcp_tab import MCPTab
from tabs.skills_tab import SkillsTab


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
        layout.setContentsMargins(10, 10, 10, 10)
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

        # Tab widget for sub-tabs
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                background-color: {theme.BG_DARK};
            }}
            QTabBar::tab {{
                background-color: {theme.BG_MEDIUM};
                color: {theme.FG_PRIMARY};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {theme.ACCENT_PRIMARY};
                color: {theme.BG_DARK};
            }}
            QTabBar::tab:hover {{
                background-color: {theme.BG_LIGHT};
            }}
        """)

        # Add sub-tabs with actual implementations

        # Settings sub-tab (Model, Theme, Environment Variables)
        settings_tab = UserSettingsSubTab(self.config_manager, self.backup_manager, self.settings_manager)
        self.sub_tabs.addTab(settings_tab, "🎛️ Settings")

        # Model Information sub-tab
        model_info_tab = UserModelInfoSubTab(self.config_manager, self.backup_manager, self.settings_manager)
        self.sub_tabs.addTab(model_info_tab, "📚 Model Information")

        # Workflows sub-tab
        workflows_tab = UserWorkflowsSubTab(self.config_manager, self.backup_manager, self.settings_manager)
        self.sub_tabs.addTab(workflows_tab, "🔄 Workflows")

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

        layout.addWidget(self.sub_tabs, 1)

        # Info footer
        footer = QLabel(
            "💡 Tip: User settings apply globally to all projects. "
            "For project-specific settings, use the Project Configuration tab."
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
        layout.addWidget(footer)
