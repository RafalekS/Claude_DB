"""
Project Configuration Tab - Container for all project-level configuration
Includes centralized project folder picker and 8 sub-tabs:
1. Settings (Model, Theme - Shared/Local)
2. Hooks (Shared/Local)
3. Permissions (Shared/Local)
4. Statusline (Shared/Local)
5. Agents
6. Commands
7. MCP Servers
8. Skills
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QLineEdit, QFileDialog, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme
# Import subtabs (using OLD correct implementations)
from tabs.project_settings_subtab import ProjectSettingsSubTab
from tabs.project_hooks_subtab import ProjectHooksSubTab
from tabs.project_permissions_subtab import ProjectPermissionsSubTab
from tabs.project_statusline_subtab import ProjectStatuslineSubTab
from tabs.agents_tab import AgentsTab
from tabs.commands_tab import CommandsTab
from tabs.mcp_tab import MCPTab
from tabs.skills_tab import SkillsTab
from tabs.projects_tab import ProjectsTab


class ProjectClaudeMDSubTab(QWidget):
    """Simple CLAUDE.md viewer/editor for project context"""

    def __init__(self, project_context):
        super().__init__()
        self.project_context = project_context
        self.init_ui()
        self.project_context.project_changed.connect(self.load_content)
        self.load_content()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        self.file_label = QLabel("CLAUDE.md")
        self.file_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")

        self.save_btn = QPushButton("💾 Save")
        self.save_btn.setStyleSheet(theme.get_button_style())
        self.save_btn.clicked.connect(self.save_content)
        self.save_btn.setEnabled(False)  # Disabled until project selected

        self.reload_btn = QPushButton("🔄 Reload")
        self.reload_btn.setStyleSheet(theme.get_button_style())
        self.reload_btn.clicked.connect(self.load_content)
        self.reload_btn.setEnabled(False)

        header_layout.addWidget(self.file_label)
        header_layout.addStretch()
        header_layout.addWidget(self.reload_btn)
        header_layout.addWidget(self.save_btn)

        layout.addLayout(header_layout)

        # Editor
        self.editor = QTextEdit()
        self.editor.setStyleSheet(theme.get_text_edit_style())
        self.editor.setPlaceholderText("No project selected. CLAUDE.md will appear here when a project is selected.")
        layout.addWidget(self.editor, 1)

    def load_content(self):
        """Load CLAUDE.md from project folder"""
        if not self.project_context.has_project():
            self.editor.clear()
            self.editor.setPlaceholderText("No project selected. CLAUDE.md will appear here when a project is selected.")
            self.save_btn.setEnabled(False)
            self.reload_btn.setEnabled(False)
            return

        project_path = self.project_context.get_project()
        claude_md_path = project_path / "CLAUDE.md"

        if claude_md_path.exists():
            try:
                with open(claude_md_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.editor.setText(content)
                self.file_label.setText(f"CLAUDE.md - {project_path.name}")
                self.save_btn.setEnabled(True)
                self.reload_btn.setEnabled(True)
            except Exception as e:
                self.editor.setText(f"Error reading CLAUDE.md:\n{str(e)}")
                self.save_btn.setEnabled(False)
                self.reload_btn.setEnabled(False)
        else:
            self.editor.setText(f"No CLAUDE.md found in project folder:\n{project_path}")
            self.save_btn.setEnabled(False)
            self.reload_btn.setEnabled(False)

    def save_content(self):
        """Save CLAUDE.md to project folder"""
        if not self.project_context.has_project():
            return

        project_path = self.project_context.get_project()
        claude_md_path = project_path / "CLAUDE.md"

        try:
            with open(claude_md_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            QMessageBox.information(self, "Success", "CLAUDE.md saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save CLAUDE.md:\n{str(e)}")


class ProjectPromptSubTab(QWidget):
    """Simple PROMPT.md viewer/editor for project context"""

    def __init__(self, project_context):
        super().__init__()
        self.project_context = project_context
        self.init_ui()
        self.project_context.project_changed.connect(self.load_content)
        self.load_content()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        self.file_label = QLabel("PROMPT.md")
        self.file_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")

        self.save_btn = QPushButton("💾 Save")
        self.save_btn.setStyleSheet(theme.get_button_style())
        self.save_btn.clicked.connect(self.save_content)
        self.save_btn.setEnabled(False)

        self.reload_btn = QPushButton("🔄 Reload")
        self.reload_btn.setStyleSheet(theme.get_button_style())
        self.reload_btn.clicked.connect(self.load_content)
        self.reload_btn.setEnabled(False)

        header_layout.addWidget(self.file_label)
        header_layout.addStretch()
        header_layout.addWidget(self.reload_btn)
        header_layout.addWidget(self.save_btn)

        layout.addLayout(header_layout)

        # Editor
        self.editor = QTextEdit()
        self.editor.setStyleSheet(theme.get_text_edit_style())
        self.editor.setPlaceholderText("No project selected. PROMPT.md will appear here when a project is selected.")
        layout.addWidget(self.editor, 1)

    def load_content(self):
        """Load PROMPT.md from project help/ folder"""
        if not self.project_context.has_project():
            self.editor.clear()
            self.editor.setPlaceholderText("No project selected. PROMPT.md will appear here when a project is selected.")
            self.save_btn.setEnabled(False)
            self.reload_btn.setEnabled(False)
            return

        project_path = self.project_context.get_project()
        prompt_md_path = project_path / "help" / "PROMPT.md"

        if prompt_md_path.exists():
            try:
                with open(prompt_md_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.editor.setText(content)
                self.file_label.setText(f"PROMPT.md - {project_path.name}")
                self.save_btn.setEnabled(True)
                self.reload_btn.setEnabled(True)
            except Exception as e:
                self.editor.setText(f"Error reading PROMPT.md:\n{str(e)}")
                self.save_btn.setEnabled(False)
                self.reload_btn.setEnabled(False)
        else:
            self.editor.setText(f"No PROMPT.md found in help/ folder:\n{project_path / 'help'}")
            self.save_btn.setEnabled(False)
            self.reload_btn.setEnabled(False)

    def save_content(self):
        """Save PROMPT.md to project help/ folder"""
        if not self.project_context.has_project():
            return

        project_path = self.project_context.get_project()
        prompt_md_path = project_path / "help" / "PROMPT.md"

        # Create help folder if it doesn't exist
        prompt_md_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(prompt_md_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            QMessageBox.information(self, "Success", "PROMPT.md saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save PROMPT.md:\n{str(e)}")


class ProjectConfigTab(QWidget):
    """Container tab for all project-level configuration with centralized folder picker"""

    def __init__(self, config_manager, backup_manager, settings_manager, project_context):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.settings_manager = settings_manager
        self.project_context = project_context
        self.init_ui()

        # Connect to project context changes
        self.project_context.project_changed.connect(self.on_project_changed)

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        header = QLabel("Project Configuration")
        header.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; "
            f"font-weight: bold; "
            f"color: {theme.ACCENT_PRIMARY};"
        )

        header_layout.addWidget(header)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Description
        desc = QLabel(
            "Configure project-specific settings that apply only to the selected project. "
            "Select a project folder below - all sub-tabs will use this project."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; "
            f"padding: 5px; "
            f"margin-bottom: 10px;"
        )
        layout.addWidget(desc)

        # Project folder picker section
        picker_group_layout = QVBoxLayout()
        picker_group_layout.setSpacing(5)

        picker_label = QLabel("Current Project Folder:")
        picker_label.setStyleSheet(
            f"font-weight: bold; "
            f"color: {theme.FG_PRIMARY};"
        )
        picker_group_layout.addWidget(picker_label)

        picker_layout = QHBoxLayout()
        picker_layout.setSpacing(5)

        self.project_path_input = QLineEdit()
        self.project_path_input.setReadOnly(True)
        self.project_path_input.setPlaceholderText("No project selected - click Browse to select")
        self.project_path_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                padding: 8px;
                font-size: {theme.FONT_SIZE_SMALL}px;
            }}
        """)

        browse_btn = QPushButton("📁 Browse")
        browse_btn.setToolTip("Select project folder")
        browse_btn.setStyleSheet(theme.get_button_style())
        browse_btn.clicked.connect(self.browse_project_folder)

        clear_btn = QPushButton("✖ Clear")
        clear_btn.setToolTip("Clear current project")
        clear_btn.setStyleSheet(theme.get_button_style())
        clear_btn.clicked.connect(self.clear_project)

        picker_layout.addWidget(self.project_path_input)
        picker_layout.addWidget(browse_btn)
        picker_layout.addWidget(clear_btn)

        picker_group_layout.addLayout(picker_layout)

        # Project status label
        self.status_label = QLabel("ℹ️ No project selected")
        self.status_label.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; "
            f"padding: 5px; "
            f"background-color: {theme.BG_MEDIUM}; "
            f"border-left: 3px solid {theme.ACCENT_SECONDARY}; "
            f"border-radius: 3px;"
        )
        picker_group_layout.addWidget(self.status_label)

        layout.addLayout(picker_group_layout)

        # Separator
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {theme.BG_LIGHT};")
        layout.addWidget(separator)

        # Tab widget for sub-tabs
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setEnabled(False)  # Disabled until project is selected
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
            QTabBar::tab:disabled {{
                background-color: {theme.BG_MEDIUM};
                color: {theme.FG_SECONDARY};
            }}
        """)

        # Add sub-tabs with actual implementations

        # CLAUDE.md sub-tab (FIRST - moved from Projects sub-sub-tab)
        claude_md_tab = ProjectClaudeMDSubTab(self.project_context)
        self.sub_tabs.addTab(claude_md_tab, "📝 CLAUDE.md")

        # Settings sub-tab (Model, Theme, Environment Variables - Shared/Local)
        settings_tab = ProjectSettingsSubTab(self.config_manager, self.backup_manager, self.settings_manager, self.project_context)
        self.sub_tabs.addTab(settings_tab, "🎛️ Settings")

        # Hooks sub-tab (Project - uses settings.json)
        hooks_tab = ProjectHooksSubTab(self.config_manager, self.backup_manager, self.settings_manager, self.project_context)
        self.sub_tabs.addTab(hooks_tab, "🪝 Hooks")

        # Permissions sub-tab (Project - uses settings.json)
        permissions_tab = ProjectPermissionsSubTab(self.config_manager, self.backup_manager, self.settings_manager, self.project_context)
        self.sub_tabs.addTab(permissions_tab, "🔒 Permissions")

        # Statusline sub-tab (Project - uses settings.json)
        statusline_tab = ProjectStatuslineSubTab(self.config_manager, self.backup_manager, self.settings_manager, self.project_context)
        self.sub_tabs.addTab(statusline_tab, "📊 Statusline")

        # Agents sub-tab (Phase 3 - AgentsTab with project scope)
        agents_tab = AgentsTab(self.config_manager, self.backup_manager, "project", self.project_context)
        self.sub_tabs.addTab(agents_tab, "🤖 Agents")

        # Commands sub-tab (Phase 3 - CommandsTab with project scope)
        commands_tab = CommandsTab(self.config_manager, self.backup_manager, "project", self.project_context)
        self.sub_tabs.addTab(commands_tab, "⚡ Commands")

        # Skills sub-tab (Phase 3 - SkillsTab with project scope)
        skills_tab = SkillsTab(self.config_manager, self.backup_manager, "project", self.project_context)
        self.sub_tabs.addTab(skills_tab, "🎓 Skills")

        # Prompt sub-tab (AFTER Skills - moved from Projects sub-sub-tab)
        prompt_tab = ProjectPromptSubTab(self.project_context)
        self.sub_tabs.addTab(prompt_tab, "💬 Prompt")

        # MCP Servers sub-tab (Phase 3 - MCPTab with project scope)
        mcp_tab = MCPTab(self.config_manager, self.backup_manager, "project", self.project_context)
        self.sub_tabs.addTab(mcp_tab, "🔌 MCP Servers")

        # Projects sub-tab (projects management - simplified to only Project Info)
        projects_tab = ProjectsTab(self.config_manager, self.backup_manager)
        self.sub_tabs.addTab(projects_tab, "📂 Projects")

        layout.addWidget(self.sub_tabs, 1)

        # Load current project if set
        if self.project_context.has_project():
            current_project = self.project_context.get_project()
            self.project_path_input.setText(str(current_project))
            self.update_status(current_project)
            self.sub_tabs.setEnabled(True)

    def browse_project_folder(self):
        """Open folder picker dialog"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Project Folder",
            "C:\Scripts",
            QFileDialog.Option.ShowDirsOnly
        )

        if folder:
            project_path = Path(folder)

            # Set in project context
            if self.project_context.set_project(project_path):
                self.project_path_input.setText(str(project_path))
                self.update_status(project_path)
                self.sub_tabs.setEnabled(True)

                # Ensure .claude folder exists
                if not self.project_context.validate_claude_folder():
                    reply = QMessageBox.question(
                        self,
                        "Create .claude Folder?",
                        f"The selected project does not have a .claude folder.\n\n"
                        f"Create .claude folder in:\n{project_path}",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )

                    if reply == QMessageBox.StandardButton.Yes:
                        if self.project_context.ensure_claude_folder():
                            QMessageBox.information(
                                self,
                                "Created",
                                f"Created .claude folder in:\n{project_path}"
                            )
                        else:
                            QMessageBox.critical(
                                self,
                                "Error",
                                "Failed to create .claude folder"
                            )
            else:
                QMessageBox.warning(
                    self,
                    "Invalid Path",
                    f"Invalid project path:\n{project_path}"
                )

    def clear_project(self):
        """Clear current project"""
        self.project_context.clear_project()
        self.project_path_input.clear()
        self.project_path_input.setPlaceholderText("No project selected - click Browse to select")
        self.status_label.setText("ℹ️ No project selected")
        self.status_label.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; "
            f"padding: 5px; "
            f"background-color: {theme.BG_MEDIUM}; "
            f"border-left: 3px solid {theme.ACCENT_SECONDARY}; "
            f"border-radius: 3px;"
        )
        self.sub_tabs.setEnabled(False)

    def on_project_changed(self, new_project: Path):
        """Handle project context changes (from external sources)"""
        if new_project:
            self.project_path_input.setText(str(new_project))
            self.update_status(new_project)
            self.sub_tabs.setEnabled(True)
        else:
            self.clear_project()

    def update_status(self, project_path: Path):
        """Update status label with project info"""
        has_claude = self.project_context.validate_claude_folder()

        if has_claude:
            self.status_label.setText(f"✅ Project loaded: .claude folder exists")
            self.status_label.setStyleSheet(
                f"color: {theme.FG_PRIMARY}; "
                f"font-size: {theme.FONT_SIZE_SMALL}px; "
                f"padding: 5px; "
                f"background-color: {theme.BG_MEDIUM}; "
                f"border-left: 3px solid #4ade80; "
                f"border-radius: 3px;"
            )
        else:
            self.status_label.setText(f"⚠️ Project loaded but .claude folder does not exist")
            self.status_label.setStyleSheet(
                f"color: {theme.FG_PRIMARY}; "
                f"font-size: {theme.FONT_SIZE_SMALL}px; "
                f"padding: 5px; "
                f"background-color: {theme.BG_MEDIUM}; "
                f"border-left: 3px solid #f0ad4e; "
                f"border-radius: 3px;"
            )
