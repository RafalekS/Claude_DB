"""
Skills Tab - managing Claude Code skills (directory-based with SKILL.md files)
"""

import os
import shutil
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QMessageBox, QListWidget, QSplitter, QLineEdit, QInputDialog,
    QListWidgetItem, QGroupBox, QFileDialog, QTabWidget, QDialog,
    QDialogButtonBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QAbstractItemView, QFormLayout, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import sys
import json
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme
from utils.template_manager import get_template_manager
from dialogs.skill_library_dialog import SkillLibraryDialog

# Load AVAILABLE_TOOLS from config, fall back to defaults
_config_file = Path(__file__).parent.parent.parent / "config" / "config.json"
try:
    with open(_config_file) as f:
        _app_config = json.load(f)
    AVAILABLE_TOOLS = _app_config.get("claude_tools", {}).get("available_tools", [
        "Read", "Write", "Edit", "MultiEdit", "Grep", "Glob", "Bash",
        "WebFetch", "WebSearch", "Task", "TodoWrite", "NotebookEdit",
        "AskUserQuestion", "Skill", "SlashCommand"
    ])
except Exception:
    AVAILABLE_TOOLS = [
        "Read", "Write", "Edit", "MultiEdit", "Grep", "Glob", "Bash",
        "WebFetch", "WebSearch", "Task", "TodoWrite", "NotebookEdit",
        "AskUserQuestion", "Skill", "SlashCommand"
    ]


class SkillsTab(QWidget):
    """Tab for managing Claude Code skills (directory-based)"""

    def __init__(self, config_manager, backup_manager, scope, project_context=None):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.scope = scope
        self.project_context = project_context
        self.current_skill = None

        # Validate parameters
        if scope == "project" and not project_context:
            raise ValueError("project_context is required when scope='project'")

        self.init_ui()

        # Connect to project changes if project scope
        if self.scope == "project" and self.project_context:
            self.project_context.project_changed.connect(self.on_project_changed)

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        scope_label = "User" if self.scope == "user" else "Project"
        header = QLabel(f"Skills Management ({scope_label})")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")

        header_layout.addWidget(header)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Single skills editor for current scope
        editor_widget = self.create_skills_editor()
        layout.addWidget(editor_widget, 1)

        # Info section at bottom
        info_group = QGroupBox("About Skills")
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
            "Skills are directory-based, NOT stored in JSON files.\n"
            "• User Skills: ~/.claude/skills/ - Personal skills available across all projects\n"
            "• Project Skills: ./.claude/skills/ - Shared with team via git\n"
            "• Each skill is a directory containing a SKILL.md file\n"
            "• Skills are automatically discovered when Claude Code runs"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px; padding: 5px;")
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

    def create_skills_editor(self):
        """Create skills editor for the current scope"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # File path label
        skills_dir = self.get_scope_skills_dir()
        self.path_label = QLabel(f"Directory: {skills_dir}")
        self.path_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_SMALL}px; color: {theme.FG_SECONDARY};")
        layout.addWidget(self.path_label)

        # Splitter for list and editor
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - skills list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        # Search
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search skills...")
        self.search_box.textChanged.connect(self.filter_skills)
        self.search_box.setStyleSheet(theme.get_line_edit_style())
        left_layout.addWidget(self.search_box)

        list_label = QLabel("Skills (directories with SKILL.md)")
        list_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_NORMAL}px; font-weight: bold; color: {theme.FG_PRIMARY};")
        left_layout.addWidget(list_label)

        self.skills_list = QListWidget()
        self.skills_list.itemClicked.connect(self.load_skill_content)
        self.skills_list.setStyleSheet(theme.get_list_widget_style())
        left_layout.addWidget(self.skills_list)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        new_btn = QPushButton("➕ New")
        new_btn.setToolTip("Create new skill")
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setToolTip("Load selected skill for editing")
        del_btn = QPushButton("🗑 Delete")
        del_btn.setToolTip("Delete selected skill")
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setToolTip("Reload skills list")
        library_btn = QPushButton("📚 Skill Library")
        library_btn.setToolTip("Browse and add skills from library templates")

        for btn in [new_btn, edit_btn, del_btn, refresh_btn, library_btn]:
            btn.setStyleSheet(theme.get_button_style())

        new_btn.clicked.connect(self.create_new_skill)
        edit_btn.clicked.connect(self.edit_skill)
        del_btn.clicked.connect(self.delete_skill)
        refresh_btn.clicked.connect(self.load_skills)
        library_btn.clicked.connect(self.open_skill_library)

        btn_layout.addWidget(new_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(library_btn)
        left_layout.addLayout(btn_layout)

        splitter.addWidget(left_panel)

        # Right panel - editor
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)

        # Editor header
        editor_btn_layout = QHBoxLayout()
        editor_btn_layout.setSpacing(5)

        self.skill_name_label = QLabel("No skill selected")
        self.skill_name_label.setStyleSheet(theme.get_label_style("normal", "secondary"))

        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip("Save SKILL.md file")
        backup_save_btn = QPushButton("📦 Backup & Save")
        backup_save_btn.setToolTip("Create backup and save SKILL.md")
        revert_btn = QPushButton("Revert")
        revert_btn.setToolTip("Revert to saved version")

        for btn in [save_btn, backup_save_btn, revert_btn]:
            btn.setStyleSheet(theme.get_button_style())

        save_btn.clicked.connect(self.save_skill)
        backup_save_btn.clicked.connect(self.backup_and_save_skill)
        revert_btn.clicked.connect(self.revert_skill)

        editor_btn_layout.addWidget(self.skill_name_label)
        editor_btn_layout.addStretch()
        editor_btn_layout.addWidget(save_btn)
        editor_btn_layout.addWidget(backup_save_btn)
        editor_btn_layout.addWidget(revert_btn)

        right_layout.addLayout(editor_btn_layout)

        # Editor
        self.editor = QTextEdit()
        self.editor.setStyleSheet(f"""
            QTextEdit {{
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: {theme.FONT_SIZE_NORMAL}px;
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                padding: 8px;
            }}
        """)
        self.editor.setPlaceholderText("Select a skill to edit its SKILL.md file, or create a new skill.")
        right_layout.addWidget(self.editor, 1)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter, 1)

        # Load initial data
        self.load_skills()

        return widget

    def on_project_changed(self, project_path: Path):
        """Handle project context change"""
        # Update path label
        skills_dir = self.get_scope_skills_dir()
        if skills_dir:
            self.path_label.setText(f"Directory: {skills_dir}")
        # Reload skills from new project
        self.load_skills()

    def get_scope_skills_dir(self):
        """Get skills directory for the current scope"""
        if self.scope == "user":
            return self.config_manager.claude_dir / "skills"
        else:  # project
            if not self.project_context or not self.project_context.has_project():
                return None
            return self.project_context.get_project() / ".claude" / "skills"


    def load_skills(self):
        """Load all skills from the scope's directory"""
        self.skills_list.clear()

        skills_dir = self.get_scope_skills_dir()

        if skills_dir and skills_dir.exists():
            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir():
                    skill_md = skill_dir / "SKILL.md"
                    if skill_md.exists():
                        item = QListWidgetItem(skill_dir.name)
                        item.setData(Qt.ItemDataRole.UserRole, skill_dir)
                        item.setForeground(QColor(theme.ACCENT_PRIMARY))
                        self.skills_list.addItem(item)

        # Show message if no skills found
        if self.skills_list.count() == 0:
            item = QListWidgetItem("No skills found. Click 'New' to create one.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(QColor(theme.FG_DIM))
            self.skills_list.addItem(item)

    def filter_skills(self, text):
        """Filter skills list based on search text"""
        for i in range(self.skills_list.count()):
            item = self.skills_list.item(i)
            if text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def load_skill_content(self, item):
        """Load selected skill's SKILL.md content"""
        skill_path = item.data(Qt.ItemDataRole.UserRole)
        if not skill_path:
            return

        skill_md = skill_path / "SKILL.md"

        if not skill_md.exists():
            QMessageBox.warning(
                self,
                "File Not Found",
                f"SKILL.md not found at:\n{skill_md}"
            )
            return

        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()

            self.editor.setPlainText(content)
            self.current_skill = skill_path
            self.skill_name_label.setText(f"Editing: {skill_path.name}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load SKILL.md:\n{str(e)}"
            )

    def edit_skill(self):
        """Edit selected skill with dialog"""
        current_item = self.skills_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a skill to edit.")
            return

        skill_name = current_item.text()
        skills_dir = self.get_scope_skills_dir()
        skill_dir = skills_dir / skill_name
        skill_md = skill_dir / "SKILL.md"

        if not skill_md.exists():
            QMessageBox.warning(self, "Error", "Skill file not found.")
            return

        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()

            dialog = EditSkillDialog(skill_name, content, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_data = dialog.get_skill_data()
                # Regenerate content with frontmatter
                new_content = f"""---
name: {skill_name}
description: {new_data['description']}
allowed-tools: {new_data['allowed_tools']}
---

# {new_data['display_name'] or skill_name}

{new_data['description']}

## Usage

Describe how to use this skill.

## Examples

Provide examples of using this skill.
"""
                with open(skill_md, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                self.load_skills()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit skill:\n{str(e)}")

    def create_new_skill(self):
        """Create a new skill directory and SKILL.md file"""
        dialog = NewSkillDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        skill_data = dialog.get_skill_data()
        skill_name = skill_data['name'].strip().lower().replace(' ', '-')

        skills_dir = self.get_scope_skills_dir()
        skill_dir = skills_dir / skill_name
        skill_md = skill_dir / "SKILL.md"

        # Check if already exists
        if skill_dir.exists():
            QMessageBox.warning(self, "Skill Exists", f"A skill named '{skill_name}' already exists")
            return

        try:
            # Create directory
            skill_dir.mkdir(parents=True, exist_ok=True)

            # Build YAML frontmatter
            content = f"""---
name: {skill_name}
description: {skill_data['description']}
allowed-tools: {skill_data['allowed_tools']}
---

# {skill_data['display_name'] or skill_name}

{skill_data['description']}

## Usage

Describe how to use this skill.

## Examples

Provide examples of using this skill.
"""

            with open(skill_md, 'w', encoding='utf-8') as f:
                f.write(content)

            # Reload skills list
            self.load_skills()

        except Exception as e:
            QMessageBox.critical(self, "Creation Error", f"Failed to create skill:\n{str(e)}")

    def delete_skill(self):
        """Delete the selected skill directory"""
        current_item = self.skills_list.currentItem()
        if not current_item:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a skill to delete."
            )
            return

        skill_path = current_item.data(Qt.ItemDataRole.UserRole)
        if not skill_path:
            return

        skill_name = skill_path.name

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the skill '{skill_name}'?\n\n"
            f"This will delete the entire directory:\n{skill_path}\n\n"
            f"This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Delete directory and all contents
                shutil.rmtree(skill_path)

                QMessageBox.information(
                    self,
                    "Deleted",
                    f"Skill '{skill_name}' has been deleted."
                )

                # Clear editor
                self.editor.clear()
                self.skill_name_label.setText("No skill selected")
                self.current_skill = None

                # Reload list
                self.load_skills()

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Deletion Error",
                    f"Failed to delete skill:\n{str(e)}"
                )

    def save_skill(self):
        """Save current SKILL.md content"""
        current_skill = self.current_skill
        if not current_skill:
            QMessageBox.warning(
                self,
                "No Skill Selected",
                "Please select a skill to save."
            )
            return

        skill_md = current_skill / "SKILL.md"

        try:
            # Save content
            content = self.editor.toPlainText()
            with open(skill_md, 'w', encoding='utf-8') as f:
                f.write(content)

            QMessageBox.information(
                self,
                "Saved",
                f"SKILL.md saved to:\n{skill_md}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save SKILL.md:\n{str(e)}"
            )

    def backup_and_save_skill(self):
        """Create backup and save current SKILL.md"""
        current_skill = self.current_skill
        if not current_skill:
            QMessageBox.warning(
                self,
                "No Skill Selected",
                "Please select a skill to save."
            )
            return

        skill_md = current_skill / "SKILL.md"

        try:
            # Create backup if file exists
            if skill_md.exists():
                self.backup_manager.create_file_backup(skill_md)

            # Save content
            content = self.editor.toPlainText()
            with open(skill_md, 'w', encoding='utf-8') as f:
                f.write(content)

            QMessageBox.information(
                self,
                "Saved",
                f"Backup created and SKILL.md saved to:\n{skill_md}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save SKILL.md:\n{str(e)}"
            )

    def revert_skill(self):
        """Revert to saved version"""
        current_skill = self.current_skill
        if not current_skill:
            return

        reply = QMessageBox.question(
            self,
            "Revert Changes",
            "Are you sure you want to revert to the saved version?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                skill_md = current_skill / "SKILL.md"
                with open(skill_md, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.editor.setPlainText(content)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to revert:\n{str(e)}"
                )

    def open_skill_library(self):
        """Open skill library to browse and manage templates"""
        template_mgr = get_template_manager()
        templates_dir = template_mgr.get_templates_dir('skills')

        dialog = SkillLibraryDialog(templates_dir, self.scope, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.get_selected_skills()
            if selected:
                self.deploy_skills(selected)
                self.load_skills()

    def deploy_skills(self, skills):
        """Deploy selected skills to the current scope"""
        skills_dir = self.get_scope_skills_dir()
        skills_dir.mkdir(parents=True, exist_ok=True)

        added_count = 0
        skipped_count = 0

        for skill_name, skill_content in skills:
            skill_dir = skills_dir / skill_name
            skill_md = skill_dir / "SKILL.md"

            if skill_md.exists():
                skipped_count += 1
                continue

            try:
                skill_dir.mkdir(parents=True, exist_ok=True)
                with open(skill_md, 'w', encoding='utf-8') as f:
                    f.write(skill_content)
                added_count += 1
            except Exception as e:
                QMessageBox.warning(self, "Deploy Error", f"Failed to deploy {skill_name}:\n{str(e)}")

        # Show summary
        msg = f"Deployed {added_count} skill(s)"
        if skipped_count > 0:
            msg += f"\nSkipped {skipped_count} (already exist)"
        QMessageBox.information(self, "Deploy Complete", msg)


class NewSkillDialog(QDialog):
    """Dialog for creating a new skill with proper YAML frontmatter"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Skill")
        self.setMinimumWidth(500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., my-awesome-skill")
        self.name_edit.setStyleSheet(theme.get_line_edit_style())
        form.addRow("Skill Name*:", self.name_edit)

        # Display Name field
        self.display_name_edit = QLineEdit()
        self.display_name_edit.setPlaceholderText("e.g., My Awesome Skill (optional)")
        self.display_name_edit.setStyleSheet(theme.get_line_edit_style())
        form.addRow("Display Name:", self.display_name_edit)

        # Description field
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("e.g., A skill that does awesome things")
        self.description_edit.setStyleSheet(theme.get_text_edit_style())
        self.description_edit.setMinimumHeight(100)
        self.description_edit.setMaximumHeight(150)
        form.addRow("Description*:", self.description_edit)

        layout.addLayout(form)

        # Tools checkboxes
        tools_label = QLabel("Allowed Tools (optional):")
        tools_label.setStyleSheet(f"color: {theme.FG_PRIMARY}; font-weight: bold;")
        layout.addWidget(tools_label)

        self.tool_checkboxes = {}
        tools_grid = QGridLayout()
        tools_grid.setSpacing(5)

        # Create checkboxes in a 3-column grid - default Read, Grep, Glob checked
        for idx, tool in enumerate(AVAILABLE_TOOLS):
            checkbox = QCheckBox(tool)
            checkbox.setStyleSheet(f"color: {theme.FG_PRIMARY};")
            # Default to Read, Grep, Glob checked
            if tool in ["Read", "Grep", "Glob"]:
                checkbox.setChecked(True)
            self.tool_checkboxes[tool] = checkbox
            row = idx // 3
            col = idx % 3
            tools_grid.addWidget(checkbox, row, col)

        tools_widget = QWidget()
        tools_widget.setLayout(tools_grid)
        tools_widget.setStyleSheet(f"background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px;")
        layout.addWidget(tools_widget)

        info_label = QLabel("* Required fields\n\nThe skill will be created with YAML frontmatter.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(info_label)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.setStyleSheet(theme.get_button_style())
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Skill name is required.")
            return
        if not self.description_edit.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Description is required.")
            return
        self.accept()

    def get_skill_data(self):
        # Collect checked tools
        selected_tools = [tool for tool, checkbox in self.tool_checkboxes.items() if checkbox.isChecked()]
        tools_str = ", ".join(selected_tools) if selected_tools else ""

        return {
            'name': self.name_edit.text().strip(),
            'display_name': self.display_name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'allowed_tools': tools_str
        }


class EditSkillDialog(QDialog):
    """Dialog for editing a skill with form fields"""

    def __init__(self, skill_name, content, parent=None):
        super().__init__(parent)
        self.skill_name = skill_name
        self.setWindowTitle(f"Edit Skill: {skill_name}")
        self.setMinimumWidth(500)
        self.init_ui(content)

    def init_ui(self, content):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Parse YAML frontmatter
        import re
        frontmatter_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            frontmatter_text = frontmatter_match.group(1)
            desc_match = re.search(r'description:\s*(.+)', frontmatter_text)
            tools_match = re.search(r'allowed-tools:\s*(.+)', frontmatter_text)

            parsed_desc = desc_match.group(1).strip() if desc_match else ""
            parsed_tools = tools_match.group(1).strip() if tools_match else "Read, Grep, Glob"
        else:
            parsed_desc = ""
            parsed_tools = "Read, Grep, Glob"

        # Parse display name from markdown title
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        parsed_display_name = title_match.group(1).strip() if title_match else self.skill_name

        form = QFormLayout()
        form.setSpacing(8)

        # Display Name field
        self.display_name_edit = QLineEdit()
        self.display_name_edit.setText(parsed_display_name)
        self.display_name_edit.setStyleSheet(theme.get_line_edit_style())
        form.addRow("Display Name:", self.display_name_edit)

        # Description field
        self.description_edit = QTextEdit()
        self.description_edit.setPlainText(parsed_desc)
        self.description_edit.setStyleSheet(theme.get_text_edit_style())
        self.description_edit.setMinimumHeight(100)
        self.description_edit.setMaximumHeight(150)
        form.addRow("Description*:", self.description_edit)

        layout.addLayout(form)

        # Tools checkboxes
        tools_label = QLabel("Allowed Tools (optional):")
        tools_label.setStyleSheet(f"color: {theme.FG_PRIMARY}; font-weight: bold;")
        layout.addWidget(tools_label)

        self.tool_checkboxes = {}
        tools_grid = QGridLayout()
        tools_grid.setSpacing(5)

        # Parse existing tools (comma-separated) and create set for lookup
        existing_tools = set()
        if parsed_tools:
            existing_tools = {tool.strip() for tool in parsed_tools.split(',')}

        # Create checkboxes in a 3-column grid
        for idx, tool in enumerate(AVAILABLE_TOOLS):
            checkbox = QCheckBox(tool)
            checkbox.setStyleSheet(f"color: {theme.FG_PRIMARY};")
            # Check if this tool was in the parsed list
            if tool in existing_tools:
                checkbox.setChecked(True)
            self.tool_checkboxes[tool] = checkbox
            row = idx // 3
            col = idx % 3
            tools_grid.addWidget(checkbox, row, col)

        tools_widget = QWidget()
        tools_widget.setLayout(tools_grid)
        tools_widget.setStyleSheet(f"background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px;")
        layout.addWidget(tools_widget)

        info_label = QLabel("* Required fields")
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(info_label)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.setStyleSheet(theme.get_button_style())
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def validate_and_accept(self):
        if not self.description_edit.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Description is required.")
            return
        self.accept()

    def get_skill_data(self):
        # Collect checked tools
        selected_tools = [tool for tool, checkbox in self.tool_checkboxes.items() if checkbox.isChecked()]
        tools_str = ", ".join(selected_tools) if selected_tools else ""

        return {
            'display_name': self.display_name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'allowed_tools': tools_str
        }
