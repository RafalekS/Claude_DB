"""
Agents Tab - Manage Claude Code agents
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QMessageBox, QListWidget, QSplitter, QLineEdit, QInputDialog,
    QFileDialog, QTabWidget, QDialog, QComboBox, QFormLayout, QDialogButtonBox,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import sys
import json
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.theme import (
    BG_DARK, BG_MEDIUM, BG_LIGHT,
    FG_PRIMARY, FG_SECONDARY,
    ACCENT_PRIMARY,
    FONT_SIZE_SMALL, FONT_SIZE_LARGE,
    get_button_style, get_text_edit_style, get_line_edit_style
)
from utils.template_manager import get_template_manager

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


class NewAgentDialog(QDialog):
    """Dialog for creating a new agent with proper YAML frontmatter"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Agent")
        self.setMinimumWidth(500)
        self.init_ui()

    def init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Form layout
        form = QFormLayout()
        form.setSpacing(8)

        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., bill-organizer")
        self.name_edit.setStyleSheet(get_line_edit_style())
        form.addRow("Agent Name*:", self.name_edit)

        # Display Name field
        self.display_name_edit = QLineEdit()
        self.display_name_edit.setPlaceholderText("e.g., Bill Organizer (optional)")
        self.display_name_edit.setStyleSheet(get_line_edit_style())
        form.addRow("Display Name:", self.display_name_edit)

        # Description field
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("e.g., Extract and organize utility bills from Gmail")
        self.description_edit.setStyleSheet(get_text_edit_style())
        self.description_edit.setMinimumHeight(100)
        self.description_edit.setMaximumHeight(150)
        form.addRow("Description*:", self.description_edit)

        # Category field
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("e.g., automation, code-quality, documentation (optional)")
        self.category_edit.setStyleSheet(get_line_edit_style())
        form.addRow("Category:", self.category_edit)

        # Color field
        self.color_combo = QComboBox()
        self.color_combo.addItems([
            "blue", "green", "red", "yellow", "purple", "cyan", "magenta", "orange"
        ])
        self.color_combo.setStyleSheet(get_combo_box_style())
        form.addRow("Color:", self.color_combo)

        # Model dropdown
        self.model_combo = QComboBox()
        self.model_combo.addItems(["sonnet", "opus", "haiku"])
        self.model_combo.setStyleSheet(get_combo_box_style())
        form.addRow("Model*:", self.model_combo)

        # Subfolder field (optional)
        self.subfolder_edit = QLineEdit()
        self.subfolder_edit.setPlaceholderText("e.g., code-quality (optional)")
        self.subfolder_edit.setStyleSheet(get_line_edit_style())
        form.addRow("Subfolder:", self.subfolder_edit)

        layout.addLayout(form)

        # Tools checkboxes
        tools_label = QLabel("Tools (optional):")
        tools_label.setStyleSheet(f"color: {FG_PRIMARY}; font-weight: bold;")
        layout.addWidget(tools_label)

        self.tool_checkboxes = {}
        tools_grid = QGridLayout()
        tools_grid.setSpacing(5)

        # Create checkboxes in a 3-column grid
        for idx, tool in enumerate(AVAILABLE_TOOLS):
            checkbox = QCheckBox(tool)
            checkbox.setStyleSheet(f"color: {FG_PRIMARY};")
            self.tool_checkboxes[tool] = checkbox
            row = idx // 3
            col = idx % 3
            tools_grid.addWidget(checkbox, row, col)

        tools_widget = QWidget()
        tools_widget.setLayout(tools_grid)
        tools_widget.setStyleSheet(f"background: {BG_MEDIUM}; padding: 8px; border-radius: 3px;")
        layout.addWidget(tools_widget)

        # Info label
        info_label = QLabel(
            "* Required fields\n\n"
            "The agent will be created with YAML frontmatter containing all specified fields.\n"
            "You can add detailed instructions in the markdown content after creation."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {FG_SECONDARY}; background: {BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {FONT_SIZE_SMALL}px;")
        layout.addWidget(info_label)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.setStyleSheet(get_button_style())
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def validate_and_accept(self):
        """Validate inputs before accepting"""
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Agent name is required.")
            return
        if not self.description_edit.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Description is required.")
            return
        self.accept()

    def get_agent_data(self):
        """Return the agent data as a dictionary"""
        # Collect checked tools
        selected_tools = [tool for tool, checkbox in self.tool_checkboxes.items() if checkbox.isChecked()]
        tools_str = ", ".join(selected_tools) if selected_tools else ""

        return {
            'name': self.name_edit.text().strip(),
            'displayName': self.display_name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'category': self.category_edit.text().strip(),
            'color': self.color_combo.currentText(),
            'model': self.model_combo.currentText(),
            'subfolder': self.subfolder_edit.text().strip(),
            'tools': tools_str
        }


def get_combo_box_style():
    """Get combo box style"""
    return f"""
        QComboBox {{
            background: {BG_MEDIUM};
            color: {FG_PRIMARY};
            border: 1px solid {BG_LIGHT};
            border-radius: 3px;
            padding: 5px;
            min-height: 25px;
        }}
        QComboBox:hover {{
            border: 1px solid {ACCENT_PRIMARY};
        }}
        QComboBox::drop-down {{
            border: none;
            padding-right: 5px;
        }}
        QComboBox QAbstractItemView {{
            background: {BG_MEDIUM};
            color: {FG_PRIMARY};
            selection-background-color: {ACCENT_PRIMARY};
            selection-color: white;
            border: 1px solid {BG_LIGHT};
        }}
    """


class AgentsTab(QWidget):
    """Tab for managing Claude Code agents (single-scope)"""

    def __init__(self, config_manager, backup_manager, scope, project_context=None):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.scope = scope
        self.project_context = project_context

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
        header = QLabel(f"Agents ({scope_label})")
        header.setStyleSheet(f"font-size: {FONT_SIZE_LARGE}px; font-weight: bold; color: {ACCENT_PRIMARY};")

        header_layout.addWidget(header)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Single agents editor for current scope
        editor_widget = self.create_agents_editor()
        layout.addWidget(editor_widget, 1)

        # Info tip with best practices
        tip_label = QLabel(
            "💡 <b>Agent Design Best Practices:</b> "
            "Define ONE clear responsibility per agent • "
            "Minimize tool access per role (principle of least privilege) • "
            "Prefer read-only agents for analysis/review tasks • "
            "Limit write permissions to essential agents only"
            "<br><b>Example Agents:</b> "
            "Planner (read-only: convert features → tasks) • "
            "Codegen (edit: implement with path restrictions) • "
            "Tester (read-only: write failing tests) • "
            "Reviewer (read-only: structured comments) • "
            "Docs (edit: update documentation)"
            "<br><b>Usage:</b> "
            "Use <code>claude /agents</code> to invoke • "
            "User agents (~/.claude/agents/) are global • "
            "Project agents (./.claude/agents/) are shared with team via git"
        )
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet(f"color: {FG_SECONDARY}; background: {BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {FONT_SIZE_SMALL}px;")
        layout.addWidget(tip_label)

    def create_agents_editor(self):
        """Create agents editor for the current scope"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # File path label
        agents_dir = self.get_scope_agents_dir()
        path_label = QLabel(f"Directory: {agents_dir}")
        path_label.setStyleSheet(f"font-size: {FONT_SIZE_SMALL}px; color: {FG_SECONDARY};")
        layout.addWidget(path_label)

        # Store references
        self.path_label = path_label
        self.current_agent = None

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - agent list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        # Search
        search_box = QLineEdit()
        search_box.setPlaceholderText("Search...")
        search_box.textChanged.connect(self.filter_agents)
        search_box.setStyleSheet(get_line_edit_style())
        left_layout.addWidget(search_box)

        # Agent list
        agent_list = QListWidget()
        agent_list.itemClicked.connect(self.load_agent_content)
        agent_list.setStyleSheet(get_list_widget_style())
        left_layout.addWidget(agent_list)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        new_btn = QPushButton("➕ New")
        new_btn.setToolTip("Create a new agent")
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setToolTip("Edit agent metadata")
        del_btn = QPushButton("🗑️ Delete")
        del_btn.setToolTip("Delete the selected agent")
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setToolTip("Reload the agents list")
        library_btn = QPushButton("📚 Agent Library")
        library_btn.setToolTip("Browse and add agents from library templates")

        for btn in [new_btn, edit_btn, del_btn, refresh_btn, library_btn]:
            btn.setStyleSheet(get_button_style())

        new_btn.clicked.connect(self.create_new_agent)
        edit_btn.clicked.connect(self.edit_agent_metadata)
        del_btn.clicked.connect(self.delete_agent)
        refresh_btn.clicked.connect(self.load_agents)
        library_btn.clicked.connect(self.open_agent_library)

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

        # Editor buttons
        editor_btn_layout = QHBoxLayout()
        editor_btn_layout.setSpacing(5)

        agent_name_label = QLabel("No agent selected")
        agent_name_label.setStyleSheet(get_label_style("normal", "secondary"))

        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip("Save the current agent to file")
        backup_save_btn = QPushButton("📦 Backup & Save")
        backup_save_btn.setToolTip("Create timestamped backup before saving agent")
        revert_btn = QPushButton("Revert")
        revert_btn.setToolTip("Revert to saved version (discards unsaved changes)")

        for btn in [save_btn, backup_save_btn, revert_btn]:
            btn.setStyleSheet(get_button_style())

        save_btn.clicked.connect(self.save_agent)
        backup_save_btn.clicked.connect(self.backup_and_save_agent)
        revert_btn.clicked.connect(self.revert_agent)

        editor_btn_layout.addWidget(agent_name_label)
        editor_btn_layout.addStretch()
        editor_btn_layout.addWidget(save_btn)
        editor_btn_layout.addWidget(backup_save_btn)
        editor_btn_layout.addWidget(revert_btn)
        right_layout.addLayout(editor_btn_layout)

        # Editor
        agent_editor = QTextEdit()
        agent_editor.setStyleSheet(get_text_edit_style())
        right_layout.addWidget(agent_editor)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 1000])

        layout.addWidget(splitter, 1)

        # Store references
        self.search_box = search_box
        self.agent_list = agent_list
        self.agent_name_label = agent_name_label
        self.agent_editor = agent_editor

        # Load initial data
        self.load_agents()

        return widget

    def get_scope_agents_dir(self):
        """Get agents directory for the current scope"""
        if self.scope == "user":
            return self.config_manager.agents_dir
        else:  # project
            if not self.project_context.has_project():
                return None
            return self.project_context.get_project() / ".claude" / "agents"

    def on_project_changed(self, project_path: Path):
        """Handle project context change"""
        # Update path label
        agents_dir = self.get_scope_agents_dir()
        if agents_dir:
            self.path_label.setText(f"Directory: {agents_dir}")
        # Reload agents from new project
        self.load_agents()

    def load_agents(self):
        """Load all agents for the current scope"""
        try:
            self.agent_list.clear()

            agents_dir = self.get_scope_agents_dir()

            if not agents_dir or not agents_dir.exists():
                return

            # List all .md files in agents directory and subdirectories (recursive)
            agents = list(agents_dir.glob("**/*.md"))
            for agent_path in sorted(agents):
                # Show relative path from agents_dir
                rel_path = agent_path.relative_to(agents_dir)
                self.agent_list.addItem(str(rel_path))

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load agents:\n{str(e)}")

    def filter_agents(self, text):
        """Filter agents based on search text"""
        for i in range(self.agent_list.count()):
            item = self.agent_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def load_agent_content(self, item):
        """Load content of selected agent"""
        try:
            agent_name = item.text()
            agents_dir = self.get_scope_agents_dir()
            agent_path = agents_dir / agent_name

            if agent_path.exists():
                with open(agent_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.current_agent = agent_path
                self.agent_name_label.setText(f"Editing: {agent_name}")
                self.agent_editor.setPlainText(content)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load agent:\n{str(e)}")

    def save_agent(self):
        """Save current agent"""
        if not self.current_agent:
            QMessageBox.warning(self, "No Agent Selected", "Please select an agent to save.")
            return
        try:
            content = self.agent_editor.toPlainText()
            with open(self.current_agent, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(self, "Save Success", "Agent saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save agent:\n{str(e)}")

    def backup_and_save_agent(self):
        """Backup and save current agent"""
        if not self.current_agent:
            QMessageBox.warning(self, "No Agent Selected", "Please select an agent to save.")
            return
        try:
            self.backup_manager.create_file_backup(self.current_agent)
            content = self.agent_editor.toPlainText()
            with open(self.current_agent, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(self, "Backup & Save Success", "Backup created and agent saved!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to backup and save:\n{str(e)}")

    def revert_agent(self):
        """Revert agent to saved version"""
        if not self.current_agent:
            return
        reply = QMessageBox.question(
            self, "Revert Changes", "Are you sure you want to revert to the saved version?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with open(self.current_agent, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.agent_editor.setPlainText(content)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to revert:\n{str(e)}")

    def create_new_agent(self):
        """Create a new agent with proper YAML frontmatter"""
        # Show dialog to get agent data
        dialog = NewAgentDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        agent_data = dialog.get_agent_data()

        # Build agent path
        agents_dir = self.get_scope_agents_dir()

        # Handle subfolder
        if agent_data['subfolder']:
            agent_path = agents_dir / agent_data['subfolder'] / f"{agent_data['name']}.md"
        else:
            agent_path = agents_dir / f"{agent_data['name']}.md"

        if agent_path.exists():
            QMessageBox.warning(self, "Agent Exists", f"Agent '{agent_data['name']}' already exists.")
            return

        try:
            # Create parent directories if they don't exist
            agent_path.parent.mkdir(parents=True, exist_ok=True)

            # Build frontmatter
            frontmatter_lines = [
                "---",
                f"name: {agent_data['name']}"
            ]

            if agent_data['displayName']:
                frontmatter_lines.append(f"displayName: {agent_data['displayName']}")

            frontmatter_lines.append(f"description: {agent_data['description']}")

            if agent_data['category']:
                frontmatter_lines.append(f"category: {agent_data['category']}")

            frontmatter_lines.append(f"color: {agent_data['color']}")
            frontmatter_lines.append(f"model: {agent_data['model']}")

            if agent_data['tools']:
                frontmatter_lines.append(f"tools: {agent_data['tools']}")

            frontmatter_lines.append("---")
            frontmatter = "\n".join(frontmatter_lines)

            # Build full content
            content = f"""{frontmatter}

# {agent_data['displayName'] or agent_data['name']}

{agent_data['description']}

## Usage

Describe when and how to use this agent.

## Instructions

Add detailed instructions for this agent here.
"""

            with open(agent_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.load_agents()
            QMessageBox.information(
                self,
                "Agent Created",
                f"Agent '{agent_data['name']}' created successfully!\n\nLocation: {agent_path}"
            )

            # Auto-select the new agent
            rel_path = agent_path.relative_to(agents_dir)
            items = self.agent_list.findItems(str(rel_path), Qt.MatchFlag.MatchExactly)
            if items:
                self.agent_list.setCurrentItem(items[0])
                self.load_agent_content(items[0])

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create agent:\n{str(e)}")

    def delete_agent(self):
        """Delete selected agent"""
        if not self.current_agent:
            QMessageBox.warning(self, "No Agent Selected", "Please select an agent to delete.")
            return
        reply = QMessageBox.question(
            self, "Delete Agent", f"Are you sure you want to delete:\n{self.current_agent.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.current_agent.unlink()
                self.agent_editor.clear()
                self.agent_name_label.setText("No agent selected")
                self.current_agent = None
                self.load_agents()
                QMessageBox.information(self, "Delete Success", "Agent deleted successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete agent:\n{str(e)}")

    def edit_agent_metadata(self):
        """Edit agent metadata (frontmatter) in a GUI"""
        if not self.current_agent:
            QMessageBox.warning(self, "No Agent Selected", "Please select an agent to edit.")
            return

        try:
            # Read current content
            with open(self.current_agent, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse frontmatter
            frontmatter, body = self.parse_frontmatter(content)

            # Create dialog and pre-fill with current values
            dialog = NewAgentDialog(self)
            dialog.setWindowTitle("Edit Agent Metadata")
            dialog.name_edit.setText(frontmatter.get('name', ''))
            dialog.display_name_edit.setText(frontmatter.get('displayName', ''))
            dialog.description_edit.setPlainText(frontmatter.get('description', ''))
            dialog.category_edit.setText(frontmatter.get('category', ''))

            # Set color combo
            color = frontmatter.get('color', 'blue')
            color_index = dialog.color_combo.findText(color)
            if color_index >= 0:
                dialog.color_combo.setCurrentIndex(color_index)

            # Set model combo
            model = frontmatter.get('model', 'sonnet')
            model_index = dialog.model_combo.findText(model)
            if model_index >= 0:
                dialog.model_combo.setCurrentIndex(model_index)

            # Set tool checkboxes
            tools_str = frontmatter.get('tools', '')
            if tools_str:
                existing_tools = {tool.strip() for tool in tools_str.split(',')}
                for tool, checkbox in dialog.tool_checkboxes.items():
                    if tool in existing_tools:
                        checkbox.setChecked(True)

            # Don't show subfolder field for editing (can't move files)
            dialog.subfolder_edit.setVisible(False)
            dialog.findChild(QLabel).setVisible(False)  # Hide the label too

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            agent_data = dialog.get_agent_data()

            # Rebuild frontmatter
            frontmatter_lines = [
                "---",
                f"name: {agent_data['name']}"
            ]

            if agent_data['displayName']:
                frontmatter_lines.append(f"displayName: {agent_data['displayName']}")

            frontmatter_lines.append(f"description: {agent_data['description']}")

            if agent_data['category']:
                frontmatter_lines.append(f"category: {agent_data['category']}")

            frontmatter_lines.append(f"color: {agent_data['color']}")
            frontmatter_lines.append(f"model: {agent_data['model']}")

            if agent_data['tools']:
                frontmatter_lines.append(f"tools: {agent_data['tools']}")

            frontmatter_lines.append("---")
            new_frontmatter = "\n".join(frontmatter_lines)

            # Combine with existing body
            new_content = f"{new_frontmatter}\n\n{body}"

            # Update editor
            self.agent_editor.setPlainText(new_content)

            QMessageBox.information(
                self,
                "Metadata Updated",
                "Agent metadata has been updated. Click 'Save' to save changes to file."
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit metadata:\n{str(e)}")

    def parse_frontmatter(self, content):
        """Parse YAML frontmatter from content"""
        import re

        frontmatter = {}
        body = content

        # Check if content starts with ---
        if content.startswith('---'):
            # Find the closing ---
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
            if match:
                frontmatter_text = match.group(1)
                body = match.group(2)

                # Parse YAML-like frontmatter (simple key: value pairs)
                for line in frontmatter_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip()

        return frontmatter, body

    def open_agent_library(self):
        """Open agent library to browse and manage templates"""
        template_mgr = get_template_manager()
        templates_dir = template_mgr.get_templates_dir('agents')

        dialog = AgentLibraryDialog(templates_dir, self.scope, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.get_selected_agents()
            if selected:
                self.deploy_agents(selected)
                self.load_agents()

    def deploy_agents(self, agents):
        """Deploy selected agents to the current scope"""
        agents_dir = self.get_scope_agents_dir()
        agents_dir.mkdir(parents=True, exist_ok=True)

        added_count = 0
        skipped_count = 0

        for agent_name, agent_content in agents:
            agent_file = agents_dir / f"{agent_name}.md"
            if agent_file.exists():
                skipped_count += 1
                continue

            try:
                # Create parent directories if agent is in a subfolder
                agent_file.parent.mkdir(parents=True, exist_ok=True)

                with open(agent_file, 'w', encoding='utf-8') as f:
                    f.write(agent_content)
                added_count += 1
            except Exception as e:
                QMessageBox.critical(self, "Deploy Error", f"Failed to deploy '{agent_name}':\n{str(e)}")

        if added_count > 0 or skipped_count > 0:
            msg = f"Added {added_count} agent(s)"
            if skipped_count > 0:
                msg += f"\nSkipped {skipped_count} (already exist)"
            QMessageBox.information(self, "Deploy Complete", msg)


class AgentLibraryDialog(QDialog):
    """Dialog for managing agent templates in config/templates/agents/"""

    def __init__(self, templates_dir, scope, parent=None):
        super().__init__(parent)
        self.templates_dir = Path(templates_dir)
        self.scope = scope
        self.template_mgr = get_template_manager()
        self.current_folder = ""  # Empty = root, otherwise subfolder name
        self.setWindowTitle("Agent Library")
        self.setModal(True)
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Agent Library - Manage and deploy agent templates")
        header.setStyleSheet(f"font-weight: bold; color: {FG_PRIMARY}; font-size: {FONT_SIZE_LARGE}px;")
        layout.addWidget(header)

        # Navigation bar with back button and path
        nav_layout = QHBoxLayout()

        self.back_btn = QPushButton("⬅ Back")
        self.back_btn.setStyleSheet(get_button_style())
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setVisible(False)  # Hidden at root level
        nav_layout.addWidget(self.back_btn)

        self.path_label = QLabel(f"📁 {self.templates_dir}")
        self.path_label.setStyleSheet(f"color: {FG_SECONDARY}; font-size: {FONT_SIZE_SMALL}px;")
        nav_layout.addWidget(self.path_label)
        nav_layout.addStretch()

        layout.addLayout(nav_layout)

        # Load templates
        self.load_templates()

        # Table with checkboxes
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["", "Name", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 200)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        self.table.doubleClicked.connect(self.on_double_click)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {BG_DARK};
                color: {FG_PRIMARY};
                border: 1px solid {BG_LIGHT};
                border-radius: 3px;
            }}
            QHeaderView::section {{
                background-color: {BG_MEDIUM};
                color: {FG_PRIMARY};
                padding: 5px;
                border: 1px solid {BG_LIGHT};
            }}
            QHeaderView::section:hover {{
                background-color: {BG_LIGHT};
            }}
        """)

        self.populate_table()
        layout.addWidget(self.table)

        # Management buttons
        manage_layout = QHBoxLayout()

        add_btn = QPushButton("➕ Add Template")
        add_btn.setStyleSheet(get_button_style())
        add_btn.setToolTip("Create a new agent template with GUI form")
        add_btn.clicked.connect(self.add_template)
        manage_layout.addWidget(add_btn)

        edit_btn = QPushButton("✏️ Edit Selected")
        edit_btn.setStyleSheet(get_button_style())
        edit_btn.setToolTip("Edit selected template with GUI form")
        edit_btn.clicked.connect(self.edit_template)
        manage_layout.addWidget(edit_btn)

        bulk_add_btn = QPushButton("📋 Bulk Add")
        bulk_add_btn.setStyleSheet(get_button_style())
        bulk_add_btn.setToolTip("Add multiple agents at once by pasting")
        bulk_add_btn.clicked.connect(self.bulk_add_agents)
        manage_layout.addWidget(bulk_add_btn)

        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.setStyleSheet(get_button_style())
        delete_btn.setToolTip("Delete selected templates from library")
        delete_btn.clicked.connect(self.delete_selected)
        manage_layout.addWidget(delete_btn)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet(get_button_style())
        refresh_btn.setToolTip("Reload templates from folder")
        refresh_btn.clicked.connect(self.refresh_templates)
        manage_layout.addWidget(refresh_btn)

        open_folder_btn = QPushButton("📁 Open Folder")
        open_folder_btn.setStyleSheet(get_button_style())
        open_folder_btn.setToolTip("Open templates folder in file explorer")
        open_folder_btn.clicked.connect(self.open_folder)
        manage_layout.addWidget(open_folder_btn)

        manage_layout.addStretch()
        layout.addLayout(manage_layout)

        # Select All / Deselect All buttons
        select_layout = QHBoxLayout()
        select_all_btn = QPushButton("✓ Select All")
        select_all_btn.setStyleSheet(get_button_style())
        select_all_btn.clicked.connect(self.select_all)
        select_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("✗ Deselect All")
        deselect_all_btn.setStyleSheet(get_button_style())
        deselect_all_btn.clicked.connect(self.deselect_all)
        select_layout.addWidget(deselect_all_btn)

        select_layout.addStretch()
        layout.addLayout(select_layout)

        # Info label
        info = QLabel("Select agents to deploy, then click OK. You can also drop .md files directly into the templates folder.")
        info.setStyleSheet(f"color: {FG_SECONDARY}; font-size: {FONT_SIZE_SMALL}px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_templates(self):
        """Load templates from folder and organize by folder"""
        self.templates = {}
        self.folders = set()
        template_names = self.template_mgr.list_templates('agents')

        for name in template_names:
            try:
                content = self.template_mgr.read_template('agents', name)
                # Extract description from frontmatter
                info = self.template_mgr.get_template_info('agents', name)
                description = info.get('description', 'No description') if info else 'No description'
                self.templates[name] = {
                    'content': content,
                    'description': description
                }
                # Track folders
                if '/' in name:
                    folder = name.split('/')[0]
                    self.folders.add(folder)
            except Exception as e:
                print(f"Error loading template {name}: {e}")

    def populate_table(self):
        """Populate table based on current folder"""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        # Update path label and back button
        if self.current_folder:
            self.path_label.setText(f"📁 {self.templates_dir / self.current_folder}")
            self.back_btn.setVisible(True)
        else:
            self.path_label.setText(f"📁 {self.templates_dir}")
            self.back_btn.setVisible(False)

        items_to_show = []

        if not self.current_folder:
            # At root level - show folders first, then root-level templates
            for folder in sorted(self.folders):
                items_to_show.append(('folder', folder, ''))

            # Show templates that are at root level (no folder)
            for name in sorted(self.templates.keys()):
                if '/' not in name:
                    desc = self.templates[name].get('description', 'No description')
                    items_to_show.append(('template', name, desc))
        else:
            # Inside a folder - show templates in this folder
            prefix = self.current_folder + '/'
            for name in sorted(self.templates.keys()):
                if name.startswith(prefix):
                    template_name = name[len(prefix):]
                    if '/' not in template_name:
                        desc = self.templates[name].get('description', 'No description')
                        items_to_show.append(('template', name, desc))

        self.table.setRowCount(len(items_to_show))

        for row, (item_type, name, description) in enumerate(items_to_show):
            if item_type == 'folder':
                icon_item = QTableWidgetItem("📁")
                icon_item.setData(Qt.ItemDataRole.UserRole, 'folder')
                name_item = QTableWidgetItem(name)
                name_item.setForeground(QColor(ACCENT_PRIMARY))
                desc_item = QTableWidgetItem("")
            else:
                icon_item = QTableWidgetItem("📄")
                icon_item.setData(Qt.ItemDataRole.UserRole, 'template')
                display_name = name.split('/')[-1] if '/' in name else name
                name_item = QTableWidgetItem(display_name)
                name_item.setForeground(QColor(FG_PRIMARY))
                desc_item = QTableWidgetItem(description)
                desc_item.setForeground(QColor(FG_SECONDARY))

            name_item.setData(Qt.ItemDataRole.UserRole, name)
            icon_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(row, 0, icon_item)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, desc_item)

        self.table.setSortingEnabled(True)
        self.table.sortItems(1, Qt.SortOrder.AscendingOrder)

    def on_double_click(self, index):
        """Handle double-click on table row"""
        row = index.row()
        icon_item = self.table.item(row, 0)
        name_item = self.table.item(row, 1)

        if icon_item and icon_item.data(Qt.ItemDataRole.UserRole) == 'folder':
            folder_name = name_item.text()
            self.current_folder = folder_name
            self.populate_table()

    def go_back(self):
        """Navigate back to root folder"""
        self.current_folder = ""
        self.populate_table()

    def select_all(self):
        self.table.selectAll()

    def deselect_all(self):
        self.table.clearSelection()

    def get_selected_agents(self):
        """Get list of selected agent names and their content (not folders)"""
        selected = []
        for row in range(self.table.rowCount()):
            icon_item = self.table.item(row, 0)
            name_item = self.table.item(row, 1)
            if name_item and name_item.isSelected():
                if icon_item and icon_item.data(Qt.ItemDataRole.UserRole) == 'template':
                    full_name = name_item.data(Qt.ItemDataRole.UserRole)
                    if full_name in self.templates:
                        selected.append((full_name, self.templates[full_name]['content']))
        return selected

    def add_template(self):
        """Add a new template with GUI form"""
        dialog = NewAgentTemplateDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            template_data = dialog.get_template_data()
            try:
                # Build frontmatter
                frontmatter = f"""---
name: {template_data['name']}
description: {template_data['description']}"""

                if template_data.get('category'):
                    frontmatter += f"\ncategory: {template_data['category']}"
                if template_data.get('color'):
                    frontmatter += f"\ncolor: {template_data['color']}"
                if template_data.get('tools'):
                    frontmatter += f"\ntools: {template_data['tools']}"
                if template_data.get('model'):
                    frontmatter += f"\nmodel: {template_data['model']}"

                frontmatter += "\n---\n\n"

                # Build content
                content = frontmatter + f"# {template_data.get('displayName') or template_data['name']}\n\nAgent template content here.\n"

                # If in a folder, save to that folder
                if self.current_folder:
                    full_name = f"{self.current_folder}/{template_data['name']}"
                else:
                    full_name = template_data['name']
                self.template_mgr.save_template('agents', full_name, content)
                QMessageBox.information(self, "Success", f"Template '{full_name}' created!")
                self.refresh_templates()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save template:\n{str(e)}")

    def edit_template(self):
        """Edit selected template with GUI form"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a template to edit.")
            return

        # Edit the first selected template
        row = selected_rows[0].row()
        icon_item = self.table.item(row, 0)
        name_item = self.table.item(row, 1)

        # Check if it's a folder
        if icon_item and icon_item.data(Qt.ItemDataRole.UserRole) == 'folder':
            QMessageBox.warning(self, "Cannot Edit Folder", "Double-click on a folder to open it.")
            return

        # Get the full template name from UserRole
        agent_name = name_item.data(Qt.ItemDataRole.UserRole)
        if agent_name not in self.templates:
            QMessageBox.warning(self, "Error", f"Template '{agent_name}' not found.")
            return

        content = self.templates[agent_name]['content']

        # Get display name and folder prefix
        display_name = agent_name.split('/')[-1] if '/' in agent_name else agent_name
        folder_prefix = agent_name.rsplit('/', 1)[0] + '/' if '/' in agent_name else ""

        dialog = EditAgentTemplateDialog(display_name, content, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_content = dialog.get_content()
            try:
                self.template_mgr.save_template('agents', agent_name, new_content)
                QMessageBox.information(self, "Success", f"Template '{agent_name}' updated!")
                self.refresh_templates()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save template:\n{str(e)}")

    def bulk_add_agents(self):
        """Open bulk add dialog"""
        dialog = BulkAgentAddDialog(self.templates_dir, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_templates()

    def delete_selected(self):
        """Delete selected templates"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select templates to delete.")
            return

        # Get selected template names (skip folders)
        selected = []
        for row_index in selected_rows:
            row = row_index.row()
            icon_item = self.table.item(row, 0)
            name_item = self.table.item(row, 1)
            if icon_item and icon_item.data(Qt.ItemDataRole.UserRole) == 'template':
                full_name = name_item.data(Qt.ItemDataRole.UserRole)
                selected.append(full_name)

        if not selected:
            QMessageBox.warning(self, "No Templates Selected", "Please select templates to delete (folders cannot be deleted directly).")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete {len(selected)} template(s)?\n\n" + "\n".join(selected),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            for name in selected:
                try:
                    self.template_mgr.delete_template('agents', name)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to delete {name}:\n{str(e)}")

            QMessageBox.information(self, "Success", f"Deleted {len(selected)} template(s)!")
            self.refresh_templates()

    def refresh_templates(self):
        """Reload templates from folder"""
        self.load_templates()
        self.populate_table()

    def open_folder(self):
        """Open templates folder in file explorer"""
        import subprocess
        import platform
        if platform.system() == 'Windows':
            subprocess.Popen(['explorer', str(self.templates_dir)])
        elif platform.system() == 'Darwin':
            subprocess.Popen(['open', str(self.templates_dir)])
        else:
            subprocess.Popen(['xdg-open', str(self.templates_dir)])


class BulkAgentAddDialog(QDialog):
    """Dialog for bulk adding agent templates"""

    def __init__(self, templates_dir, parent=None):
        super().__init__(parent)
        self.templates_dir = templates_dir
        self.template_mgr = get_template_manager()
        self.setWindowTitle("Bulk Add Agents")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Bulk Add Agents to Template Library")
        header.setStyleSheet(f"font-weight: bold; color: {FG_PRIMARY}; font-size: {FONT_SIZE_LARGE}px;")
        layout.addWidget(header)

        # Instructions
        instructions = QLabel(
            "Paste agent template files (full markdown content with YAML frontmatter):\n\n"
            "Separate multiple agents with:\n"
            "<b>---AGENT---</b> on its own line\n\n"
            "Each agent should include YAML frontmatter with 'name:' field."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet(f"color: {FG_SECONDARY}; background: {BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {FONT_SIZE_SMALL}px;")
        layout.addWidget(instructions)

        # Text area for pasting
        input_label = QLabel("Paste agent template(s):")
        input_label.setStyleSheet(f"font-weight: bold; color: {FG_PRIMARY};")
        layout.addWidget(input_label)

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText(
            "---\nname: code-reviewer\ndescription: Reviews code for quality\n---\n\n# Code Reviewer\n...\n\n---AGENT---\n\n---\nname: test-generator\n..."
        )
        self.input_text.setStyleSheet(get_text_edit_style())
        layout.addWidget(self.input_text)

        # Buttons
        button_layout = QHBoxLayout()

        parse_btn = QPushButton("🔄 Parse & Preview")
        parse_btn.setStyleSheet(get_button_style())
        parse_btn.clicked.connect(self.parse_and_preview)
        button_layout.addWidget(parse_btn)

        button_layout.addStretch()

        save_btn = QPushButton("💾 Save to Library")
        save_btn.setStyleSheet(get_button_style())
        save_btn.clicked.connect(self.save_to_library)
        button_layout.addWidget(save_btn)

        close_btn = QPushButton("✗ Close")
        close_btn.setStyleSheet(get_button_style())
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        # Preview area
        preview_label = QLabel("Preview (will create these template files):")
        preview_label.setStyleSheet(f"font-weight: bold; color: {FG_PRIMARY};")
        layout.addWidget(preview_label)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet(get_text_edit_style())
        layout.addWidget(self.preview_text)

    def parse_and_preview(self):
        """Parse input and show preview"""
        input_text = self.input_text.toPlainText().strip()
        if not input_text:
            QMessageBox.warning(self, "Empty Input", "Please paste agent template(s) first.")
            return

        try:
            # Split by ---AGENT--- separator
            agent_texts = input_text.split('---AGENT---')

            self.parsed_agents = []
            preview_lines = []

            for agent_text in agent_texts:
                agent_text = agent_text.strip()
                if not agent_text:
                    continue

                # Extract name from frontmatter
                import re
                name_match = re.search(r'^name:\s*(.+?)$', agent_text, re.MULTILINE)
                if name_match:
                    name = name_match.group(1).strip()
                    self.parsed_agents.append((name, agent_text))
                    preview_lines.append(f"✓ {name}.md")
                else:
                    preview_lines.append(f"✗ Skipped (no 'name:' in frontmatter)")

            if not self.parsed_agents:
                QMessageBox.warning(self, "Parse Error", "No valid agents found. Make sure each agent has 'name:' in YAML frontmatter.")
                return

            # Show preview
            preview = f"Found {len(self.parsed_agents)} agent(s):\n\n" + "\n".join(preview_lines)
            self.preview_text.setPlainText(preview)

        except Exception as e:
            QMessageBox.critical(self, "Parse Error", f"Failed to parse input:\n{str(e)}")

    def save_to_library(self):
        """Save parsed agents to template library"""
        if not hasattr(self, 'parsed_agents') or not self.parsed_agents:
            QMessageBox.warning(self, "No Data", "Please parse agents first using 'Parse & Preview'.")
            return

        try:
            added = 0
            skipped = 0

            for name, content in self.parsed_agents:
                # Check if already exists
                existing_templates = self.template_mgr.list_templates('agents')
                if name in existing_templates:
                    skipped += 1
                    continue

                # Save template
                self.template_mgr.save_template('agents', name, content)
                added += 1

            msg = f"Added {added} agent template(s) to library."
            if skipped > 0:
                msg += f"\nSkipped {skipped} (already exist)"

            QMessageBox.information(self, "Success", msg)
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save agents:\n{str(e)}")


class NewAgentTemplateDialog(QDialog):
    """Dialog for creating a new agent template"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Agent Template")
        self.setMinimumWidth(500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., code-reviewer or code-quality/code-reviewer")
        self.name_edit.setStyleSheet(get_line_edit_style())
        form.addRow("Template Name*:", self.name_edit)

        # Display Name field
        self.display_name_edit = QLineEdit()
        self.display_name_edit.setPlaceholderText("e.g., Code Reviewer (optional)")
        self.display_name_edit.setStyleSheet(get_line_edit_style())
        form.addRow("Display Name:", self.display_name_edit)

        # Description field
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("e.g., Reviews code for quality, security, and best practices")
        self.description_edit.setStyleSheet(get_text_edit_style())
        self.description_edit.setMinimumHeight(100)
        self.description_edit.setMaximumHeight(150)
        form.addRow("Description*:", self.description_edit)

        # Category field
        self.category_edit = QLineEdit()
        self.category_edit.setPlaceholderText("e.g., code-quality, automation (optional)")
        self.category_edit.setStyleSheet(get_line_edit_style())
        form.addRow("Category:", self.category_edit)

        # Color field
        self.color_combo = QComboBox()
        self.color_combo.addItems(["blue", "green", "red", "yellow", "purple", "cyan", "magenta", "orange"])
        self.color_combo.setStyleSheet(get_combo_box_style())
        form.addRow("Color:", self.color_combo)

        # Model dropdown
        self.model_combo = QComboBox()
        self.model_combo.addItems(["inherit", "sonnet", "opus", "haiku"])
        self.model_combo.setStyleSheet(get_combo_box_style())
        form.addRow("Model:", self.model_combo)

        layout.addLayout(form)

        # Tools checkboxes
        tools_label = QLabel("Tools (optional):")
        tools_label.setStyleSheet(f"color: {FG_PRIMARY}; font-weight: bold;")
        layout.addWidget(tools_label)

        self.tool_checkboxes = {}
        tools_grid = QGridLayout()
        tools_grid.setSpacing(5)

        # Create checkboxes in a 3-column grid
        for idx, tool in enumerate(AVAILABLE_TOOLS):
            checkbox = QCheckBox(tool)
            checkbox.setStyleSheet(f"color: {FG_PRIMARY};")
            self.tool_checkboxes[tool] = checkbox
            row = idx // 3
            col = idx % 3
            tools_grid.addWidget(checkbox, row, col)

        tools_widget = QWidget()
        tools_widget.setLayout(tools_grid)
        tools_widget.setStyleSheet(f"background: {BG_MEDIUM}; padding: 8px; border-radius: 3px;")
        layout.addWidget(tools_widget)

        info_label = QLabel(
            "* Required fields\n\n"
            "Template name supports subfolders (e.g., 'code-quality/code-reviewer').\n"
            "The template will be created with YAML frontmatter."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {FG_SECONDARY}; background: {BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {FONT_SIZE_SMALL}px;")
        layout.addWidget(info_label)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.setStyleSheet(get_button_style())
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Template name is required.")
            return
        if not self.description_edit.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Description is required.")
            return
        self.accept()

    def get_template_data(self):
        # Collect checked tools
        selected_tools = [tool for tool, checkbox in self.tool_checkboxes.items() if checkbox.isChecked()]
        tools_str = ", ".join(selected_tools) if selected_tools else ""

        return {
            'name': self.name_edit.text().strip(),
            'displayName': self.display_name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'category': self.category_edit.text().strip(),
            'color': self.color_combo.currentText(),
            'model': self.model_combo.currentText(),
            'tools': tools_str
        }


class EditAgentTemplateDialog(QDialog):
    """Dialog for editing agent template with form fields"""

    def __init__(self, template_name, content, parent=None):
        super().__init__(parent)
        self.template_name = template_name
        self.setWindowTitle(f"Edit Agent Template: {template_name}")
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
            # Parse frontmatter fields
            name_match = re.search(r'name:\s*(.+)', frontmatter_text)
            display_match = re.search(r'displayName:\s*(.+)', frontmatter_text)
            desc_match = re.search(r'description:\s*(.+)', frontmatter_text)
            category_match = re.search(r'category:\s*(.+)', frontmatter_text)
            color_match = re.search(r'color:\s*(.+)', frontmatter_text)
            model_match = re.search(r'model:\s*(.+)', frontmatter_text)
            subfolder_match = re.search(r'subfolder:\s*(.+)', frontmatter_text)
            tools_match = re.search(r'tools:\s*(.+)', frontmatter_text)

            parsed_name = name_match.group(1).strip() if name_match else self.template_name
            parsed_display = display_match.group(1).strip() if display_match else ""
            parsed_desc = desc_match.group(1).strip() if desc_match else ""
            parsed_category = category_match.group(1).strip() if category_match else ""
            parsed_color = color_match.group(1).strip() if color_match else "blue"
            parsed_model = model_match.group(1).strip() if model_match else "sonnet"
            parsed_subfolder = subfolder_match.group(1).strip() if subfolder_match else ""
            parsed_tools = tools_match.group(1).strip() if tools_match else ""
        else:
            parsed_name = self.template_name
            parsed_display = ""
            parsed_desc = ""
            parsed_category = ""
            parsed_color = "blue"
            parsed_model = "sonnet"
            parsed_subfolder = ""
            parsed_tools = ""

        form = QFormLayout()
        form.setSpacing(8)

        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setText(parsed_name)
        self.name_edit.setStyleSheet(get_line_edit_style())
        form.addRow("Template Name*:", self.name_edit)

        # Display Name field
        self.display_name_edit = QLineEdit()
        self.display_name_edit.setText(parsed_display)
        self.display_name_edit.setStyleSheet(get_line_edit_style())
        form.addRow("Display Name:", self.display_name_edit)

        # Description field
        self.description_edit = QTextEdit()
        self.description_edit.setPlainText(parsed_desc)
        self.description_edit.setStyleSheet(get_text_edit_style())
        self.description_edit.setMinimumHeight(100)
        self.description_edit.setMaximumHeight(150)
        form.addRow("Description*:", self.description_edit)

        # Category field
        self.category_edit = QLineEdit()
        self.category_edit.setText(parsed_category)
        self.category_edit.setStyleSheet(get_line_edit_style())
        form.addRow("Category:", self.category_edit)

        # Color field
        self.color_combo = QComboBox()
        self.color_combo.addItems(["blue", "green", "red", "yellow", "purple", "cyan", "magenta", "orange"])
        self.color_combo.setCurrentText(parsed_color)
        self.color_combo.setStyleSheet(get_combo_box_style())
        form.addRow("Color:", self.color_combo)

        # Model field
        self.model_combo = QComboBox()
        self.model_combo.addItems(["sonnet", "opus", "haiku"])
        self.model_combo.setCurrentText(parsed_model)
        self.model_combo.setStyleSheet(get_combo_box_style())
        form.addRow("Model*:", self.model_combo)

        # Subfolder field
        self.subfolder_edit = QLineEdit()
        self.subfolder_edit.setText(parsed_subfolder)
        self.subfolder_edit.setPlaceholderText("e.g., code-quality (optional)")
        self.subfolder_edit.setStyleSheet(get_line_edit_style())
        form.addRow("Subfolder:", self.subfolder_edit)

        layout.addLayout(form)

        # Tools checkboxes
        tools_label = QLabel("Tools (optional):")
        tools_label.setStyleSheet(f"color: {FG_PRIMARY}; font-weight: bold;")
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
            checkbox.setStyleSheet(f"color: {FG_PRIMARY};")
            # Check if this tool was in the parsed list
            if tool in existing_tools:
                checkbox.setChecked(True)
            self.tool_checkboxes[tool] = checkbox
            row = idx // 3
            col = idx % 3
            tools_grid.addWidget(checkbox, row, col)

        tools_widget = QWidget()
        tools_widget.setLayout(tools_grid)
        tools_widget.setStyleSheet(f"background: {BG_MEDIUM}; padding: 8px; border-radius: 3px;")
        layout.addWidget(tools_widget)

        info_label = QLabel("* Required fields")
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {FG_SECONDARY}; background: {BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {FONT_SIZE_SMALL}px;")
        layout.addWidget(info_label)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.setStyleSheet(get_button_style())
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Template name is required.")
            return
        if not self.description_edit.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Description is required.")
            return
        self.accept()

    def get_content(self):
        """Return updated content with frontmatter"""
        data = self.get_template_data()
        content = f"""---
name: {data['name']}
displayName: {data['displayName']}
description: {data['description']}"""

        if data['category']:
            content += f"\ncategory: {data['category']}"
        if data['color']:
            content += f"\ncolor: {data['color']}"

        content += f"""
model: {data['model']}"""

        if data['subfolder']:
            content += f"\nsubfolder: {data['subfolder']}"

        if data['tools']:
            content += f"\ntools: {data['tools']}"

        content += f"""
---

# {data['displayName'] or data['name']}

{data['description']}

## Usage

Describe when and how to use this agent.
"""
        return content

    def get_template_data(self):
        # Collect checked tools
        selected_tools = [tool for tool, checkbox in self.tool_checkboxes.items() if checkbox.isChecked()]
        tools_str = ", ".join(selected_tools) if selected_tools else ""

        return {
            'name': self.name_edit.text().strip(),
            'displayName': self.display_name_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'category': self.category_edit.text().strip(),
            'color': self.color_combo.currentText(),
            'model': self.model_combo.currentText(),
            'subfolder': self.subfolder_edit.text().strip(),
            'tools': tools_str
        }


