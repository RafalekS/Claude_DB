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

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QComboBox, QFileDialog, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem, QStandardItemModel

from utils.project_scanner import scan_projects

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
from tabs.rules_tab import RulesTab
from tabs.worktrees_tab import WorktreesTab
from tabs.project_conversations_subtab import ProjectConversationsSubTab
from tabs.project_file_history_subtab import ProjectFileHistorySubTab
from tabs.project_memories_subtab import ProjectMemoriesSubTab
from tabs.project_shell_snapshots_subtab import ProjectShellSnapshotsSubTab

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
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Header
        header_layout = QHBoxLayout()
        self.file_label = QLabel("CLAUDE.md")
        self.file_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")

        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self.save_content)
        self.save_btn.setEnabled(False)  # Disabled until project selected

        self.reload_btn = QPushButton("🔄 Reload")
        self.reload_btn.clicked.connect(self.load_content)
        self.reload_btn.setEnabled(False)

        header_layout.addWidget(self.file_label)
        header_layout.addStretch()
        header_layout.addWidget(self.reload_btn)
        header_layout.addWidget(self.save_btn)

        layout.addLayout(header_layout)

        # Editor
        self.editor = QTextEdit()
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

        if not isinstance(project_path, Path):
            self.editor.setPlaceholderText("CLAUDE.md editing is not available for remote projects.")
            self.editor.clear()
            self.save_btn.setEnabled(False)
            self.reload_btn.setEnabled(False)
            return

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
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        # Header
        header_layout = QHBoxLayout()
        self.file_label = QLabel("PROMPT.md")
        self.file_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")

        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self.save_content)
        self.save_btn.setEnabled(False)

        self.reload_btn = QPushButton("🔄 Reload")
        self.reload_btn.clicked.connect(self.load_content)
        self.reload_btn.setEnabled(False)

        header_layout.addWidget(self.file_label)
        header_layout.addStretch()
        header_layout.addWidget(self.reload_btn)
        header_layout.addWidget(self.save_btn)

        layout.addLayout(header_layout)

        # Editor
        self.editor = QTextEdit()
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

        if not isinstance(project_path, Path):
            self.editor.setPlaceholderText("PROMPT.md editing is not available for remote projects.")
            self.editor.clear()
            self.save_btn.setEnabled(False)
            self.reload_btn.setEnabled(False)
            return

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
        layout.setContentsMargins(6, 6, 6, 6)
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

        # Tracked custom (Browse-picked) paths not in the scanned list
        self._custom_paths: list[Path] = []

        self.project_combo = QComboBox()
        self.project_combo.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.project_combo.setMaxVisibleItems(15)
        self.project_combo.view().setStyleSheet("QListView { max-height: 350px; }")
        self.project_combo.currentIndexChanged.connect(self._on_combo_changed)

        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("Rescan projects")
        refresh_btn.clicked.connect(self.refresh_projects)

        browse_btn = QPushButton("📁 Browse")
        browse_btn.setToolTip("Select project folder manually")
        browse_btn.clicked.connect(self.browse_project_folder)

        clear_btn = QPushButton("✖ Clear")
        clear_btn.setToolTip("Clear current project")
        clear_btn.clicked.connect(self.clear_project)

        picker_layout.addWidget(self.project_combo, 1)
        picker_layout.addWidget(refresh_btn)
        picker_layout.addWidget(browse_btn)
        picker_layout.addWidget(clear_btn)

        picker_group_layout.addLayout(picker_layout)

        # Populate combo on init
        self._populate_combo()

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

        # Tab widget for sub-tabs — always enabled; each subtab handles "no project" state
        self.sub_tabs = QTabWidget()

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

        # Projects sub-tab (projects management - reads project from central project_context)
        projects_tab = ProjectsTab(self.config_manager, self.backup_manager, self.project_context)
        self.sub_tabs.addTab(projects_tab, "📂 Projects")

        # Conversations sub-tab (sessions for current project)
        conversations_tab = ProjectConversationsSubTab(self.project_context, config_manager=self.config_manager)
        self.sub_tabs.addTab(conversations_tab, "💬 Conversations")

        # File History sub-tab (pre-edit snapshots for current project)
        file_history_tab = ProjectFileHistorySubTab(self.project_context, config_manager=self.config_manager)
        self.sub_tabs.addTab(file_history_tab, "📋 File History")

        # Memories sub-tab (per-project memory .md files)
        memories_tab = ProjectMemoriesSubTab(self.project_context, config_manager=self.config_manager)
        self.sub_tabs.addTab(memories_tab, "🧠 Memories")

        # Shell Snapshots sub-tab (time-filtered shell environment snapshots)
        shell_snapshots_tab = ProjectShellSnapshotsSubTab(self.project_context, config_manager=self.config_manager)
        self.sub_tabs.addTab(shell_snapshots_tab, "🐚 Shell Snapshots")

        # Rules sub-tab (project-level rules)
        rules_tab = RulesTab(self.config_manager, self.backup_manager)
        self.sub_tabs.addTab(rules_tab, "📋 Rules")

        # Worktrees sub-tab (project git worktrees)
        worktrees_tab = WorktreesTab(self.config_manager, self.backup_manager)
        self.sub_tabs.addTab(worktrees_tab, "🌿 Worktrees")

        layout.addWidget(self.sub_tabs, 1)

    def apply_theme(self):
        """Propagate theme change to all subtabs."""
        for i in range(self.sub_tabs.count()):
            widget = self.sub_tabs.widget(i)
            if hasattr(widget, 'apply_theme'):
                widget.apply_theme()

        # Reflect current project selection in combo after theme reapply
        if self.project_context.has_project():
            self._sync_combo_to_context()

    # ------------------------------------------------------------------ #
    # Combo helpers
    # ------------------------------------------------------------------ #

    _SEPARATOR_DATA = "__separator__"

    def _get_fs_and_projects_dir(self):
        """Return (fs, projects_dir) for scan_projects(). None/None → local scan."""
        try:
            from modules.remote.filesystem import LocalFileSystem
            fs = self.config_manager.fs
            if isinstance(fs, LocalFileSystem):
                return None, None
            return fs, self.config_manager.claude_dir / "projects"
        except Exception:
            return None, None

    def _populate_combo(self, keep_selection=None):
        """Rebuild combo items from scanned + custom paths."""
        self.project_combo.blockSignals(True)
        self.project_combo.clear()

        fs, projects_dir = self._get_fs_and_projects_dir()
        if fs is not None:
            from modules.remote.remote_path import RemotePath
            raw_scanned = scan_projects(projects_dir=projects_dir, fs=fs)
            # Wrap path strings as RemotePath so project_context gets a proper path object
            scanned = [
                {**p, "path": RemotePath(str(p["path"])) if not isinstance(p["path"], RemotePath) else p["path"]}
                for p in raw_scanned
            ]
        else:
            scanned = scan_projects()

        scanned_paths = {str(p["path"]) for p in scanned}

        self.project_combo.addItem("-- Select Project --", None)

        for project in scanned:
            sessions = project["sessions"]
            label = f"{project['path']}  ({sessions} session{'s' if sessions != 1 else ''})"
            self.project_combo.addItem(label, project["path"])

        # Custom paths (Browse-picked) not already in scanned list
        custom = [p for p in self._custom_paths if str(p) not in scanned_paths]
        if custom:
            # Non-selectable separator
            model = self.project_combo.model()
            sep = QStandardItem("── Custom Folders ──")
            sep.setEnabled(False)
            sep.setData(self._SEPARATOR_DATA)
            model.appendRow(sep)

            for path in custom:
                self.project_combo.addItem(str(path), path)

        self.project_combo.blockSignals(False)

        # Re-select previous item if provided
        if keep_selection is not None:
            self._sync_combo_to_path(keep_selection)

    def _sync_combo_to_context(self):
        if self.project_context.has_project():
            self._sync_combo_to_path(self.project_context.get_project())

    def _sync_combo_to_path(self, path):
        self.project_combo.blockSignals(True)
        try:
            path_str = str(path)
            for i in range(self.project_combo.count()):
                item_data = self.project_combo.itemData(i)
                if item_data is not None and str(item_data) == path_str:
                    self.project_combo.setCurrentIndex(i)
                    return
        finally:
            self.project_combo.blockSignals(False)

    def _on_combo_changed(self, index: int):
        """Handle combo selection — update project_context."""
        path = self.project_combo.itemData(index)
        if path is None or path == self._SEPARATOR_DATA:
            return
        if self.project_context.set_project(path):
            self.update_status(path)
        else:
            QMessageBox.warning(self, "Invalid Path", f"Invalid project path:\n{path}")

    def refresh_projects(self):
        """Rescan ~/.claude/projects/ and rebuild combo."""
        current = self.project_context.get_project() if self.project_context.has_project() else None
        self._populate_combo(keep_selection=current)

    # ------------------------------------------------------------------ #
    # Browse / Clear
    # ------------------------------------------------------------------ #

    def browse_project_folder(self):
        """Open folder picker dialog"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Project Folder",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )

        if not folder:
            return

        project_path = Path(folder)

        if not self.project_context.set_project(project_path):
            QMessageBox.warning(self, "Invalid Path", f"Invalid project path:\n{project_path}")
            return

        # Add to custom list if not already in scanned projects
        scanned_paths = {str(p["path"]) for p in scan_projects()}
        if str(project_path) not in scanned_paths and project_path not in self._custom_paths:
            self._custom_paths.append(project_path)

        self._populate_combo(keep_selection=project_path)
        self.update_status(project_path)

    def clear_project(self):
        """Clear current project"""
        self.project_context.clear_project()
        self.project_combo.blockSignals(True)
        self.project_combo.setCurrentIndex(0)
        self.project_combo.blockSignals(False)
        self.status_label.setText("ℹ️ No project selected")
        self.status_label.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; "
            f"padding: 5px; "
            f"background-color: {theme.BG_MEDIUM}; "
            f"border-left: 3px solid {theme.ACCENT_SECONDARY}; "
            f"border-radius: 3px;"
        )

    def on_project_changed(self, new_project: Path):
        """Handle project context changes — sync combo selection and status label.

        Only syncs the visual state; does NOT repopulate the combo (which would
        re-trigger _on_combo_changed → set_project → this handler recursively).
        Browse-picked paths that need a repopulate are handled in browse_project_folder.
        """
        if new_project:
            self._sync_combo_to_path(new_project)
            self.update_status(new_project)
        else:
            self.project_combo.blockSignals(True)
            self.project_combo.setCurrentIndex(0)
            self.project_combo.blockSignals(False)
            self.status_label.setText("ℹ️ No project selected")
            self.status_label.setStyleSheet(
                f"color: {theme.FG_SECONDARY}; "
                f"font-size: {theme.FONT_SIZE_SMALL}px; "
                f"padding: 5px; "
                f"background-color: {theme.BG_MEDIUM}; "
                f"border-left: 3px solid {theme.ACCENT_SECONDARY}; "
                f"border-radius: 3px;"
            )

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
                f"border-left: 3px solid {theme.SUCCESS_COLOR}; "
                f"border-radius: 3px;"
            )
        else:
            self.status_label.setText(f"⚠️ Project loaded but .claude folder does not exist")
            self.status_label.setStyleSheet(
                f"color: {theme.FG_PRIMARY}; "
                f"font-size: {theme.FONT_SIZE_SMALL}px; "
                f"padding: 5px; "
                f"background-color: {theme.BG_MEDIUM}; "
                f"border-left: 3px solid {theme.WARNING_COLOR}; "
                f"border-radius: 3px;"
            )
