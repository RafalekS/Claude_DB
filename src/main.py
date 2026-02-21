#!/usr/bin/env python3
"""
Claude_DB - PyQt6 Application for Claude Code Configuration Management
Main application entry point
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QMessageBox, QStatusBar,
    QTabBar, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor, QIcon

# Import tab modules
from tabs.settings_tab import SettingsTab
from tabs.claude_md_tab import ClaudeMDTab
from tabs.agents_tab import AgentsTab  # Used by User/Project Config tabs
from tabs.commands_tab import CommandsTab  # Used by User/Project Config tabs
from tabs.skills_tab import SkillsTab  # Used by User/Project Config tabs
from tabs.prompts_tab import PromptsTab
from tabs.mcp_tab import MCPTab  # Used by User/Project Config tabs
from tabs.plugins_tab import PluginsTab
# from tabs.env_vars_tab import EnvVarsTab  # REMOVED - now integrated into Settings tab
from tabs.hooks_tab import HooksTab
from tabs.statusline_tab import StatuslineTab
from tabs.memory_tab import MemoryTab
# from tabs.permissions_tab import PermissionsTab  # DEPRECATED - Use User/Project Config tabs
from tabs.usage_tab import UsageTab
from tabs.cli_reference_tab import CLIReferenceTab
from tabs.model_config_tab import ModelConfigTab
from tabs.styles_workflows_tab import StylesWorkflowsTab
from tabs.claudekit_tab import ClaudeKitTab
from tabs.tools_tab import ToolsTab
from tabs.config_sync_tab import ConfigSyncTab
from tabs.projects_tab import ProjectsTab
from tabs.about_tab import AboutTab
from tabs.preferences_tab import PreferencesTab
# New refactored tabs (Phase 4)
from tabs.user_config_tab import UserConfigTab
from tabs.project_config_tab import ProjectConfigTab

from utils.config_manager import ConfigManager
from utils.backup_manager import BackupManager
from utils.settings_manager import SettingsManager
from utils.project_context import ProjectContext
from utils import theme


class ClaudeDBApp(QMainWindow):
    """Main application window for Claude_DB"""

    def __init__(self, app):
        super().__init__()
        self.app = app  # Store QApplication instance for dynamic theme switching
        self.config_manager = ConfigManager()
        self.backup_manager = BackupManager()

        # Initialize utilities for new refactored tabs
        user_settings_path = Path.home() / ".claude" / "settings.json"
        self.settings_manager = SettingsManager(user_settings_path)
        self.project_context = ProjectContext()

        # Auto-detect project folder from current working directory
        cwd = Path.cwd()
        if cwd.exists() and cwd.is_dir():
            # Set current directory as default project on startup
            self.project_context.set_project(cwd)
            print(f"Auto-detected project folder: {cwd}")

        # Set application icon BEFORE applying theme (to prevent theme override)
        self.set_app_icon()

        # Load saved preferences and apply theme before creating UI
        self.load_saved_preferences()

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Claude_DB - Claude Code Configuration Manager")
        self.setGeometry(100, 100, 1200, 800)

        # Theme is already applied in load_saved_preferences()
        # No need to override it here

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Add header
        header = self.create_header()
        main_layout.addWidget(header)

        # Tab bar style
        tab_bar_style = """
            QTabBar::tab {
                background: #3c3c3c;
                color: #ddd;
                padding: 8px 12px;
                margin-right: 2px;
                border: 1px solid #555;
            }
            QTabBar::tab:selected {
                background: #667eea;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #4c4c4c;
            }
        """

        # Create two tab bars (just the tab buttons, no content panes)
        self.tab_bar_row1 = QTabBar()
        self.tab_bar_row1.setStyleSheet(tab_bar_style)

        self.tab_bar_row2 = QTabBar()
        self.tab_bar_row2.setStyleSheet(tab_bar_style)

        # Create single content area (stacked widget)
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("QStackedWidget { border: 1px solid #444; background: #2b2b2b; }")

        # Define all tabs with their widgets - use keys for lookup
        # Key format: "tab_key" -> (default_display_name, widget)
        # Store as instance variable so preferences_tab can access it
        self.all_tabs = {
            # NEW REFACTORED TABS (Phase 4)
            "userconfig": ("👤 User Config", UserConfigTab(self.config_manager, self.backup_manager, self.settings_manager)),
            "projectconfig": ("📁 Project Config", ProjectConfigTab(self.config_manager, self.backup_manager, self.settings_manager, self.project_context)),
            # OLD TABS - DEPRECATED (moved to src/tabs/old/)
            "settings": ("⚙️ Settings", SettingsTab(self.config_manager, self.backup_manager)),
            "claudemd": ("📝 CLAUDE.md", ClaudeMDTab(self.config_manager, self.backup_manager)),
            # "agents": ("🤖 Agents [OLD]", AgentsTab(self.config_manager, self.backup_manager, "user", None)),  # DEPRECATED - Use User Config > Agents
            # "commands": ("⌨️ Commands [OLD]", CommandsTab(self.config_manager, self.backup_manager, "user", None)),  # DEPRECATED - Use User Config > Commands
            # "skills": ("💡 Skills [OLD]", SkillsTab(self.config_manager, self.backup_manager, "user", None)),  # DEPRECATED - Use User Config > Skills
            "prompts": ("💬 Prompts", PromptsTab(self.config_manager, self.backup_manager)),
            # "mcp": ("🔌 MCP [OLD]", MCPTab(self.config_manager, self.backup_manager, "user", None)),  # DEPRECATED - Use User Config > MCP
            "plugins": ("🧩 Plugins", PluginsTab(self.config_manager, self.backup_manager)),
            # "envvars" REMOVED - now integrated into Settings tab
            "hooks": ("🪝 Hooks", HooksTab(self.config_manager, self.backup_manager)),
            "statusline": ("📊 Statusline", StatuslineTab(self.config_manager, self.backup_manager)),
            "memory": ("💾 Memory", MemoryTab(self.config_manager, self.backup_manager)),
            # "permissions": ("🔐 Permissions", PermissionsTab(self.config_manager, self.backup_manager)),  # DEPRECATED - Use User/Project Config tabs
            "usage": ("📈 Usage & Analytics", UsageTab(self.config_manager, self.backup_manager)),
            "modelconfig": ("🧠 Model Config", ModelConfigTab(self.config_manager, self.backup_manager)),
            "clireference": ("📖 CLI Reference", CLIReferenceTab()),
            "styles": ("🔄 Workflows", StylesWorkflowsTab(self.config_manager, self.backup_manager)),
            "claudekit": ("🛠️ ClaudeKit", ClaudeKitTab()),
            "tools": ("🔧 Tools", ToolsTab()),
            # "configsync": Removed - now integrated into Preferences > Backup subtab
            "projects": ("📂 Projects", ProjectsTab(self.config_manager, self.backup_manager)),
            "about": ("ℹ️ About", AboutTab()),
            "preferences": ("🎨 Preferences", PreferencesTab(self.config_manager, self.backup_manager, self.app)),
        }

        # Default tab order (using keys)
        # NEW tabs at front, OLD tabs kept for comparison
        default_row1 = ["userconfig", "projectconfig", "settings", "claudemd", "agents", "commands",
                        "skills", "prompts", "mcp", "plugins", "hooks", "statusline"]
        default_row2 = ["memory", "permissions", "usage", "modelconfig", "clireference", "styles",
                        "claudekit", "tools", "projects", "about", "preferences"]

        # Load custom tab configuration from config
        row1_tabs, row2_tabs = self.load_tab_configuration(self.all_tabs, default_row1, default_row2)

        # Add tabs to row 1 bar and content stack
        for display_name, widget in row1_tabs:
            self.tab_bar_row1.addTab(display_name)
            self.content_stack.addWidget(widget)

        # Add tabs to row 2 bar and content stack (indices continue)
        self.row1_count = len(row1_tabs)
        for display_name, widget in row2_tabs:
            self.tab_bar_row2.addTab(display_name)
            self.content_stack.addWidget(widget)

        # Connect tab bars to content stack
        # Use tabBarClicked instead of currentChanged to handle re-clicking same tab
        self.tab_bar_row1.tabBarClicked.connect(self.switch_to_row1_tab)
        self.tab_bar_row2.tabBarClicked.connect(self.switch_to_row2_tab)

        # Add to layout
        main_layout.addWidget(self.tab_bar_row1)
        main_layout.addWidget(self.tab_bar_row2)
        main_layout.addWidget(self.content_stack)

        # Add toolbar
        toolbar = self.create_toolbar()
        main_layout.addLayout(toolbar)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def set_dark_theme(self):
        """Set dark theme for better visibility"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(43, 43, 43))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
        palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(102, 126, 234))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        self.setPalette(palette)

    def create_header(self):
        """Create application header"""
        header_widget = QWidget()
        header_widget.setMaximumHeight(60)
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 5, 10, 5)
        header_layout.setSpacing(2)

        title = QLabel("Claude Code Configuration Manager")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #667eea;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(f"Config: {self.config_manager.claude_dir}")
        subtitle.setStyleSheet("font-size: 11px; color: #999;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        return header_widget

    def create_toolbar(self):
        """Create bottom toolbar with global actions"""
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(10)

        # Backup buttons moved to Preferences tab
        toolbar_layout.addStretch()

        return toolbar_layout

    def create_backup(self):
        """Create backup of all configuration files"""
        try:
            self.status_bar.showMessage("Creating backup...")
            backup_path = self.backup_manager.create_full_backup()
            QMessageBox.information(
                self,
                "Backup Created",
                f"Configuration backup successfully created:\n{backup_path}"
            )
            self.status_bar.showMessage(f"Backup created: {backup_path}", 5000)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Backup Failed",
                f"Failed to create backup:\n{str(e)}"
            )
            self.status_bar.showMessage("Backup failed", 5000)

    def backup_program_files(self):
        """Run PowerShell script to backup program files"""
        import subprocess
        try:
            script_path = Path(__file__).parent.parent / "backup_program.ps1"
            subprocess.Popen(
                f'start pwsh -NoExit -Command "& \'{script_path}\'"',
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            self.status_bar.showMessage("Program backup script launched", 3000)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to launch backup script:\n{str(e)}"
            )

    def switch_to_row1_tab(self, index):
        """Switch to a tab from row 1"""
        if index >= 0:
            self.tab_bar_row1.setCurrentIndex(index)
            self.tab_bar_row2.blockSignals(True)
            self.tab_bar_row2.setCurrentIndex(-1)
            self.tab_bar_row2.blockSignals(False)
            self.content_stack.setCurrentIndex(index)

    def switch_to_row2_tab(self, index):
        """Switch to a tab from row 2"""
        if index >= 0:
            stack_index = self.row1_count + index
            self.tab_bar_row2.setCurrentIndex(index)
            self.tab_bar_row1.blockSignals(True)
            self.tab_bar_row1.setCurrentIndex(-1)
            self.tab_bar_row1.blockSignals(False)
            self.content_stack.setCurrentIndex(stack_index)

    def load_tab_configuration(self, all_tabs, default_row1, default_row2):
        """Load tab configuration from config file
        Returns: (row1_tabs, row2_tabs) where each is [(display_name, widget), ...]
        """
        try:
            config_file = Path(__file__).parent.parent / "config" / "config.json"

            if config_file.exists():
                with open(config_file, 'r') as f:
                    config_data = json.load(f)

                # Get tabs configuration
                tabs_config = config_data.get("tabs", {})
                row1_config = tabs_config.get("row1", [])
                row2_config = tabs_config.get("row2", [])

                # Build tab lists from config
                # Config format: [{"key": "settings", "name": "⚙️ Settings"}, ...]
                row1_tabs = []
                row2_tabs = []

                if row1_config:
                    for tab_info in row1_config:
                        key = tab_info.get("key")
                        custom_name = tab_info.get("name")
                        if key in all_tabs:
                            default_name, widget = all_tabs[key]
                            display_name = custom_name if custom_name else default_name
                            row1_tabs.append((display_name, widget))
                    print(f"Loaded {len(row1_tabs)} tabs for row 1 from config")

                if row2_config:
                    for tab_info in row2_config:
                        key = tab_info.get("key")
                        custom_name = tab_info.get("name")
                        if key in all_tabs:
                            default_name, widget = all_tabs[key]
                            display_name = custom_name if custom_name else default_name
                            row2_tabs.append((display_name, widget))
                    print(f"Loaded {len(row2_tabs)} tabs for row 2 from config")

                # If config exists but is empty, use defaults
                if not row1_tabs and not row2_tabs:
                    return self._build_default_tabs(all_tabs, default_row1, default_row2)

                return row1_tabs, row2_tabs
            else:
                print("No config file found, using default tab configuration")
                return self._build_default_tabs(all_tabs, default_row1, default_row2)

        except Exception as e:
            print(f"Failed to load tab configuration: {e}, using defaults")
            return self._build_default_tabs(all_tabs, default_row1, default_row2)

    def _build_default_tabs(self, all_tabs, default_row1, default_row2):
        """Build default tab lists"""
        row1_tabs = [(all_tabs[key][0], all_tabs[key][1]) for key in default_row1 if key in all_tabs]
        row2_tabs = [(all_tabs[key][0], all_tabs[key][1]) for key in default_row2 if key in all_tabs]
        return row1_tabs, row2_tabs

    def set_app_icon(self):
        """Set application icon from assets folder"""
        try:
            # Get the project root directory (parent of src/)
            project_root = Path(__file__).parent.parent

            # Try .ico first (preferred for Windows), then .png
            icon_paths = [
                project_root / "assets" / "claude_db_icon.ico",
                project_root / "assets" / "claude_db_icon.png"
            ]

            for icon_path in icon_paths:
                if icon_path.exists():
                    icon = QIcon(str(icon_path))
                    if not icon.isNull():
                        self.setWindowIcon(icon)
                        # Also set for the application (taskbar icon)
                        self.app.setWindowIcon(icon)
                        print(f"Application icon set: {icon_path}")
                        return

            print("No application icon found in assets/ folder")

        except Exception as e:
            print(f"Failed to set application icon: {e}")

    def load_saved_preferences(self):
        """Load saved preferences and apply theme on startup"""
        try:
            from utils import theme
            import json

            # Use project's config/config.json
            config_file = Path(__file__).parent.parent / "config" / "config.json"

            if config_file.exists():
                with open(config_file, 'r') as f:
                    config_data = json.load(f)

                # Get preferences section
                prefs = config_data.get("preferences", {})
                theme_name = prefs.get("theme", "Gruvbox Dark")
                font_size = prefs.get("font_size", 14)

                # Apply the saved theme
                theme.apply_theme(theme_name, font_size)

                # Apply stylesheet to the application
                app = QApplication.instance()
                if app:
                    app.setStyleSheet(theme.generate_app_stylesheet())

                print(f"Loaded preferences: {theme_name} theme with {font_size}px font")
            else:
                # No saved preferences - use default Gruvbox Dark
                print("No config file found, using default Gruvbox Dark")

                # Still apply default theme stylesheet
                app = QApplication.instance()
                if app:
                    app.setStyleSheet(theme.generate_app_stylesheet())
        except Exception as e:
            print(f"Failed to load preferences: {e}")
            # Continue with default theme
            app = QApplication.instance()
            if app:
                app.setStyleSheet(theme.generate_app_stylesheet())


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Set application metadata
    app.setApplicationName("Claude_DB")
    app.setOrganizationName("Claude Code Tools")
    app.setApplicationVersion("2.0.0")

    # Create and show main window (pass app instance for dynamic theme switching)
    window = ClaudeDBApp(app)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
