"""
MCP Tab - Manage Claude Code MCP server configuration
"""

import json
import re
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QMessageBox, QListWidget, QSplitter, QComboBox, QListWidgetItem,
    QDialog, QFormLayout, QLineEdit, QTextEdit as QTextEditWidget, QDialogButtonBox,
    QFileDialog, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QColor
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme
from utils.terminal_utils import run_command_silent
from utils.mcp_validator import MCPValidator
from utils.template_manager import get_template_manager
from dialogs.mcp_tools_dialog import MCPToolsDialog
from dialogs.mcp_library_dialog import MCPLibraryDialog


class KeyValueTableWidget(QWidget):
    """Reusable widget for editing key-value pairs"""

    def __init__(self, title="Key-Value Pairs", parent=None):
        super().__init__(parent)
        self.title = title
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Header with add/remove buttons
        header_layout = QHBoxLayout()
        label = QLabel(self.title)
        label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY};")
        header_layout.addWidget(label)
        header_layout.addStretch()

        add_btn = QPushButton("➕ Add Row")
        add_btn.setStyleSheet(theme.get_button_style())
        add_btn.clicked.connect(self.add_row)
        header_layout.addWidget(add_btn)

        remove_btn = QPushButton("➖ Remove Row")
        remove_btn.setStyleSheet(theme.get_button_style())
        remove_btn.clicked.connect(self.remove_row)
        header_layout.addWidget(remove_btn)

        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Key", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
            }}
            QHeaderView::section {{
                background-color: {theme.BG_MEDIUM};
                color: {theme.FG_PRIMARY};
                padding: 5px;
                border: 1px solid {theme.BG_LIGHT};
            }}
        """)
        layout.addWidget(self.table)

    def add_row(self, key="", value=""):
        """Add a new row to the table"""
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        self.table.setItem(row_position, 0, QTableWidgetItem(key))
        self.table.setItem(row_position, 1, QTableWidgetItem(value))

    def remove_row(self):
        """Remove selected row"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)

    def set_data(self, data_dict):
        """Load data from dictionary"""
        self.table.setRowCount(0)
        for key, value in data_dict.items():
            self.add_row(key, str(value))

    def get_data(self):
        """Get data as dictionary"""
        data = {}
        for row in range(self.table.rowCount()):
            key_item = self.table.item(row, 0)
            value_item = self.table.item(row, 1)
            if key_item and value_item:
                key = key_item.text().strip()
                value = value_item.text().strip()
                if key:  # Only add non-empty keys
                    data[key] = value
        return data


class AddServerDialog(QDialog):
    """Dialog for adding/editing MCP servers"""

    def __init__(self, parent=None, edit_mode=False, server_name=None, server_config=None):
        super().__init__(parent)
        self.edit_mode = edit_mode
        self.original_server_name = server_name
        self.setWindowTitle("Edit MCP Server" if edit_mode else "Add MCP Server")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.init_ui(server_config)

    def init_ui(self, server_config=None):
        layout = QVBoxLayout(self)

        # Form layout
        form = QFormLayout()

        # Server Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., my-server")
        self.name_input.setStyleSheet(theme.get_line_edit_style())
        if self.edit_mode:
            self.name_input.setText(self.original_server_name)
            self.name_input.setReadOnly(True)
            self.name_input.setToolTip("Server name cannot be changed when editing")
        form.addRow("Server Name*:", self.name_input)

        # Description (optional - used for templates)
        self.description_label = QLabel("Description:")
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("e.g., Clone from https://github.com/..., run 'npm install'")
        self.description_input.setStyleSheet(theme.get_line_edit_style())
        self.description_input.setVisible(False)  # Hidden by default, shown for templates
        self.description_label.setVisible(False)
        form.addRow(self.description_label, self.description_input)

        # Server Type (http vs command/stdio)
        type_layout = QHBoxLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Command (stdio)", "HTTP", "SSE"])
        self.type_combo.setStyleSheet(theme.get_combo_style())
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        type_layout.addWidget(self.type_combo)

        type_info = QLabel("💡 Command = local process, HTTP/SSE = remote server")
        type_info.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        type_layout.addWidget(type_info)
        type_layout.addStretch()
        form.addRow("Server Type*:", type_layout)

        # Command Template (for stdio type) - NEW
        self.template_label = QLabel("Command Template:")
        template_layout = QHBoxLayout()
        self.template_combo = QComboBox()
        self.template_combo.addItems(["Custom", "npx", "uvx"])
        self.template_combo.setStyleSheet(theme.get_combo_style())
        self.template_combo.currentTextChanged.connect(self.on_template_changed)
        template_layout.addWidget(self.template_combo)

        template_info = QLabel("💡 npx = cmd /c npx -y • uvx = uvx -y")
        template_info.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        template_layout.addWidget(template_info)
        template_layout.addStretch()
        form.addRow(self.template_label, template_layout)

        # Command (for stdio type)
        self.command_label = QLabel("Command*:")
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("e.g., npx @example/server or C:\\path\\to\\python.exe")
        self.command_input.setStyleSheet(theme.get_line_edit_style())
        form.addRow(self.command_label, self.command_input)

        # Arguments (for stdio type)
        self.args_label = QLabel("Arguments:")
        self.args_input = QTextEdit()
        self.args_input.setPlaceholderText("One argument per line, e.g.:\nC:\\path\\to\\script.py\n--verbose\n--port 3000")
        self.args_input.setStyleSheet(theme.get_text_edit_style())
        self.args_input.setMaximumHeight(80)
        form.addRow(self.args_label, self.args_input)

        # Windows cmd wrapper checkbox
        self.wrap_cmd_checkbox = QCheckBox("Wrap with cmd /c (Windows)")
        self.wrap_cmd_checkbox.setToolTip("Windows requires 'cmd /c' wrapper to execute npx commands")
        self.wrap_cmd_checkbox.setStyleSheet(f"color: {theme.FG_PRIMARY};")
        self.wrap_cmd_checkbox.stateChanged.connect(self.on_wrap_cmd_changed)
        form.addRow("", self.wrap_cmd_checkbox)

        # URL (for HTTP/SSE type)
        self.url_label = QLabel("URL*:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("e.g., http://localhost:3000/mcp or https://api.example.com/mcp")
        self.url_input.setStyleSheet(theme.get_line_edit_style())
        form.addRow(self.url_label, self.url_input)

        layout.addLayout(form)

        # Environment Variables (key-value table)
        self.env_table = KeyValueTableWidget("Environment Variables", self)
        layout.addWidget(self.env_table)

        # Headers (key-value table, HTTP only)
        self.headers_table = KeyValueTableWidget("Headers (HTTP/SSE only)", self)
        layout.addWidget(self.headers_table)

        # Info label
        info = QLabel("* Required fields. Environment and Headers are optional.")
        info.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(info)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Load existing config if editing
        if server_config:
            self.load_config(server_config)
        else:
            # Default to Command type
            self.on_type_changed("Command (stdio)")

    def load_config(self, config):
        """Load existing server configuration into form"""
        # Block signals to prevent template changes from overwriting loaded data
        self.template_combo.blockSignals(True)

        # Determine server type
        if "type" in config:
            server_type = config["type"]
            if server_type == "http":
                self.type_combo.setCurrentText("HTTP")
            elif server_type == "sse":
                self.type_combo.setCurrentText("SSE")
        else:
            # No type = command/stdio
            self.type_combo.setCurrentText("Command (stdio)")

        # Load command
        command_val = ""
        if "command" in config:
            command_val = config["command"]
            self.command_input.setText(command_val)

        # Load args
        args_text = ""
        if "args" in config:
            args_list = config["args"]
            if isinstance(args_list, list):
                args_text = "\n".join(args_list)
                self.args_input.setPlainText(args_text)

        # Detect if npx command needs wrapping or is already wrapped
        args_lines = [line.strip() for line in args_text.split('\n') if line.strip()] if args_text else []

        # Check if npx without wrapper - auto-wrap it
        if command_val == "npx":
            # Wrap with cmd /c
            self.command_input.setText("cmd")
            new_args = ["/c", "npx"] + args_lines
            self.args_input.setPlainText('\n'.join(new_args))
            self.wrap_cmd_checkbox.setChecked(True)
            self.template_combo.setCurrentText("Custom")
        # Check if already wrapped with cmd
        elif command_val == "cmd" and len(args_lines) >= 2 and args_lines[0] in ['/c', '/k'] and args_lines[1] == 'npx':
            # Already wrapped
            self.wrap_cmd_checkbox.setChecked(True)
            # Detect template type
            if args_lines[0] == '/c' and len(args_lines) > 2 and args_lines[2] == '-y':
                self.template_combo.setCurrentText("npx")
            else:
                self.template_combo.setCurrentText("Custom")
        elif command_val == "uvx" and args_text.startswith("-y"):
            self.template_combo.setCurrentText("uvx")
            self.wrap_cmd_checkbox.setChecked(False)
        else:
            self.template_combo.setCurrentText("Custom")
            self.wrap_cmd_checkbox.setChecked(False)

        # Re-enable signals
        self.template_combo.blockSignals(False)

        # Load URL
        if "url" in config:
            self.url_input.setText(config["url"])

        # Load environment
        if "env" in config and isinstance(config["env"], dict):
            self.env_table.set_data(config["env"])

        # Load headers
        if "headers" in config and isinstance(config["headers"], dict):
            self.headers_table.set_data(config["headers"])

        # Load description (_note field for templates)
        if "_note" in config:
            self.description_input.setText(config["_note"])

    def on_type_changed(self, server_type):
        """Update UI based on server type"""
        is_command = "Command" in server_type
        is_http = "HTTP" in server_type or "SSE" in server_type

        # Show/hide fields based on type
        self.template_label.setVisible(is_command)
        self.template_combo.setVisible(is_command)
        self.command_label.setVisible(is_command)
        self.command_input.setVisible(is_command)
        self.args_label.setVisible(is_command)
        self.args_input.setVisible(is_command)
        self.wrap_cmd_checkbox.setVisible(is_command)

        self.url_label.setVisible(is_http)
        self.url_input.setVisible(is_http)

        self.headers_table.setVisible(is_http)

    def on_template_changed(self, template):
        """Update command and args based on template selection"""
        if template == "npx":
            # npx template: cmd /c npx -y <package>
            self.command_input.setText("cmd")
            self.command_input.setPlaceholderText("Command is set to 'cmd'")
            # Pre-fill args with /c npx -y
            self.args_input.setPlaceholderText("Template pre-filled. Add package name on next line:\n/c\nnpx\n-y\n@modelcontextprotocol/server-filesystem")
            self.args_input.setPlainText("/c\nnpx\n-y\n")
            # Move cursor to end for user to add package name
            self.args_input.moveCursor(self.args_input.textCursor().MoveOperation.End)
            # Check the wrapper checkbox
            self.wrap_cmd_checkbox.setChecked(True)
        elif template == "uvx":
            # uvx template: uvx -y <package> (no cmd wrapper)
            self.command_input.setText("uvx")
            self.command_input.setPlaceholderText("Command is set to 'uvx'")
            # Pre-fill args with -y
            self.args_input.setPlaceholderText("Template pre-filled. Add package name on next line:\n-y\nmcp-server-package")
            self.args_input.setPlainText("-y\n")
            # Move cursor to end for user to add package name
            self.args_input.moveCursor(self.args_input.textCursor().MoveOperation.End)
            # Uncheck wrapper (uvx doesn't need it)
            self.wrap_cmd_checkbox.setChecked(False)
        else:  # Custom
            # Reset to custom mode
            self.command_input.setPlaceholderText("e.g., npx @example/server or C:\\path\\to\\python.exe")
            self.args_input.setPlaceholderText("One argument per line, e.g.:\nC:\\path\\to\\script.py\n--verbose\n--port 3000")
            # Don't clear fields when switching to custom

    def on_wrap_cmd_changed(self, state):
        """Handle cmd wrapper checkbox changes"""
        command = self.command_input.text().strip()
        args_text = self.args_input.toPlainText().strip()

        if state == Qt.CheckState.Checked.value:
            # Apply wrapper: wrap npx command with cmd /c
            if command == "npx" or (command and "npx" in args_text and "cmd" not in command):
                # User has npx without wrapper, apply it
                if command == "npx":
                    # Command is npx, wrap it
                    self.command_input.setText("cmd")
                    # Prepend /c and npx to args
                    args_lines = args_text.split('\n') if args_text else []
                    new_args = ["/c", "npx"] + args_lines
                    self.args_input.setPlainText('\n'.join(new_args))
        else:
            # Remove wrapper: unwrap cmd /c from npx
            if command == "cmd" and args_text:
                args_lines = [line.strip() for line in args_text.split('\n') if line.strip()]
                # Check if it's wrapped npx (starts with /c or /k followed by npx)
                if len(args_lines) >= 2 and args_lines[0] in ['/c', '/k'] and args_lines[1] == 'npx':
                    # Remove /c and set npx as command
                    self.command_input.setText("npx")
                    self.args_input.setPlainText('\n'.join(args_lines[2:]))

    def validate_and_accept(self):
        """Validate inputs before accepting"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Server name is required!")
            return

        server_type = self.type_combo.currentText()
        is_command = "Command" in server_type
        is_http = "HTTP" in server_type or "SSE" in server_type

        if is_command and not self.command_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Command is required for Command type servers!")
            return

        if is_http and not self.url_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "URL is required for HTTP/SSE type servers!")
            return

        self.accept()

    def get_server_config(self):
        """Get the server configuration from form inputs"""
        config = {}
        server_type = self.type_combo.currentText()

        if "Command" in server_type:
            # Command/stdio type - no "type" field in config
            config["command"] = self.command_input.text().strip()

            # Parse args (one per line)
            args_text = self.args_input.toPlainText().strip()
            if args_text:
                config["args"] = [arg.strip() for arg in args_text.split('\n') if arg.strip()]
        else:
            # HTTP or SSE type
            if "HTTP" in server_type:
                config["type"] = "http"
            elif "SSE" in server_type:
                config["type"] = "sse"

            config["url"] = self.url_input.text().strip()

            # Add headers if any
            headers = self.headers_table.get_data()
            if headers:
                config["headers"] = headers

        # Add environment if any
        env = self.env_table.get_data()
        if env:
            config["env"] = env

        # Add description (_note) if provided and visible
        if self.description_input.isVisible():
            description = self.description_input.text().strip()
            if description:
                config["_note"] = description

        return self.name_input.text().strip(), config


class CustomRenameDialog(QDialog):
    """Dialog for custom renaming of conflicting servers"""

    def __init__(self, conflicts, existing_names, parent=None):
        super().__init__(parent)
        self.conflicts = conflicts  # List of conflicting server names
        self.existing_names = existing_names  # Set of all existing names to avoid
        self.rename_map = {}  # Maps old_name -> new_name
        self.setWindowTitle("Rename Conflicting Servers")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("The following servers conflict with existing names.\nPlease provide new names:")
        header.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY}; font-size: {theme.FONT_SIZE_NORMAL}px;")
        layout.addWidget(header)

        # Table for conflicts
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Conflicting Name", "New Name"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
            }}
            QHeaderView::section {{
                background-color: {theme.BG_MEDIUM};
                color: {theme.FG_PRIMARY};
                padding: 5px;
                border: 1px solid {theme.BG_LIGHT};
            }}
        """)

        # Populate table
        self.name_inputs = {}
        self.table.setRowCount(len(self.conflicts))
        for row, conflict_name in enumerate(self.conflicts):
            # Conflicting name (read-only)
            name_item = QTableWidgetItem(conflict_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, name_item)

            # New name input
            new_name_input = QLineEdit()
            new_name_input.setPlaceholderText(f"{conflict_name}-renamed")
            new_name_input.setStyleSheet(theme.get_line_edit_style())
            self.table.setCellWidget(row, 1, new_name_input)
            self.name_inputs[conflict_name] = new_name_input

        layout.addWidget(self.table)

        # Info label
        info = QLabel("New names must be unique and not conflict with existing servers.")
        info.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(info)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def validate_and_accept(self):
        """Validate new names and accept"""
        self.rename_map = {}
        new_names_used = set()

        for conflict_name, input_widget in self.name_inputs.items():
            new_name = input_widget.text().strip()

            if not new_name:
                QMessageBox.warning(self, "Empty Name", f"Please provide a new name for '{conflict_name}'")
                return

            if new_name in self.existing_names:
                QMessageBox.warning(self, "Name Exists", f"Name '{new_name}' already exists. Please choose a different name.")
                return

            if new_name in new_names_used:
                QMessageBox.warning(self, "Duplicate Name", f"Name '{new_name}' is used multiple times. Each new name must be unique.")
                return

            new_names_used.add(new_name)
            self.rename_map[conflict_name] = new_name

        self.accept()

    def get_rename_map(self):
        """Get the rename mapping"""
        return self.rename_map


class MCPSearchWorker(QThread):
    """Background worker for MCP server search."""

    results_ready = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, query: str, sources: list, parent=None):
        super().__init__(parent)
        self._query = query
        self._sources = sources

    def run(self):
        try:
            from utils.mcp_search_client import MCPSearchClient
            client = MCPSearchClient()
            results = client.search(self._query, self._sources)
            self.results_ready.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class MCPTab(QWidget):
    """Tab for managing MCP servers"""

    def __init__(self, config_manager, backup_manager, scope, project_context=None):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.scope = scope
        self.project_context = project_context
        self.server_health = {}  # Store health status from claude mcp list

        # Validate parameters
        if scope in ("project", "local") and not project_context:
            raise ValueError("project_context is required when scope='project' or 'local'")

        self.init_ui()

        # Connect to project changes if project or local scope
        if self.scope in ("project", "local") and self.project_context:
            self.project_context.project_changed.connect(self.on_project_changed)

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        scope_label = "User" if self.scope == "user" else "Local" if self.scope == "local" else "Project"
        header = QLabel(f"MCP Servers ({scope_label})")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")

        header_layout.addWidget(header)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Sub-tabs: Configure | Discover
        self._sub_tabs = QTabWidget()
        self._sub_tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {theme.BG_LIGHT}; border-radius: 3px; }}
            QTabBar::tab {{ padding: 5px 14px; background: {theme.BG_MEDIUM}; color: {theme.FG_SECONDARY}; }}
            QTabBar::tab:selected {{ background: {theme.BG_DARK}; color: {theme.FG_PRIMARY}; border-bottom: 2px solid {theme.ACCENT_PRIMARY}; }}
        """)

        editor_widget = self.create_mcp_editor()
        self._sub_tabs.addTab(editor_widget, "Configure")
        self._sub_tabs.addTab(self.create_discover_tab(), "Discover")

        layout.addWidget(self._sub_tabs, 1)

        # Info section with recommended servers
        info_label = QLabel(
            "💡 <b>MCP Quick Commands:</b> "
            "<code>claude mcp list</code> (view servers) • "
            "<code>claude mcp add &lt;name&gt; &lt;cmd&gt;</code> (add) • "
            "<code>claude mcp remove &lt;name&gt;</code> (remove) • "
            "<code>claude mcp add-from-claude-desktop</code> (import)"
            "<br><b>Recommended Servers:</b> "
            "Filesystem: <code>npx @modelcontextprotocol/server-filesystem</code> • "
            "GitHub: <code>npx @modelcontextprotocol/server-github</code> (needs GITHUB_TOKEN) • "
            "Puppeteer: <code>npx @modelcontextprotocol/server-puppeteer</code> • "
            "Memory: <code>npx @modelcontextprotocol/server-memory</code>"
            "<br><b>Scopes:</b> "
            "User (~/.claude.json) affects all projects • "
            "Local (~/.claude/.mcp.json) affects current user • "
            "Project (./.mcp.json) is shared with team • "
            "Use <code>-s user/project</code> flag to specify scope • "
            "Use <code>claude mcp list</code> to check server status"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(info_label)

    def create_mcp_editor(self):
        """Create MCP editor for the current scope"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # File path label
        file_path = self.get_scope_file_path()
        self.path_label = QLabel(f"File: {file_path}")
        self.path_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_SMALL}px; color: {theme.FG_SECONDARY};")
        layout.addWidget(self.path_label)

        # Store config data
        self.config = {"mcpServers": {}}

        # Track which source we're currently editing (for project scope)
        self.current_editing_source = "mcp"  # "mcp" or "claude"

        # Splitter with server list and editor
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side - Server list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search servers...")
        self.search_box.textChanged.connect(self.filter_servers)
        self.search_box.setStyleSheet(theme.get_line_edit_style())
        left_layout.addWidget(self.search_box)

        list_label = QLabel("Servers:")
        list_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY};")
        left_layout.addWidget(list_label)

        self.server_list = QListWidget()
        self.server_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                padding: 5px;
                font-size: {theme.FONT_SIZE_NORMAL}px;
            }}
            QListWidget::item {{
                padding: 5px;
            }}
            QListWidget::item:selected {{
                background-color: {theme.ACCENT_PRIMARY};
                color: {theme.BG_DARK};
            }}
        """)
        self.server_list.itemClicked.connect(self.on_server_selected)
        left_layout.addWidget(self.server_list)

        # Buttons - matching pattern from other tabs
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        add_btn = QPushButton("➕ Add")
        add_btn.setToolTip("Add a new MCP server")
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setToolTip("Edit selected MCP server")
        remove_btn = QPushButton("🗑️ Delete")
        remove_btn.setToolTip("Remove selected MCP server")
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setToolTip("Reload MCP configuration")
        library_btn = QPushButton("📚 MCP Library")
        library_btn.setToolTip("Browse and deploy servers from library")
        tools_btn = QPushButton("🔧 Tools")
        tools_btn.setToolTip("List tools from selected server")
        validate_btn = QPushButton("✅ Validate")
        validate_btn.setToolTip("Validate MCP configuration for Windows compatibility")
        autofix_btn = QPushButton("🔧 Auto-Fix")
        autofix_btn.setToolTip("Auto-fix MCP configuration for Windows (adds cmd /c wrapper)")

        for btn in [add_btn, edit_btn, refresh_btn, library_btn, tools_btn, validate_btn, autofix_btn]:
            btn.setStyleSheet(theme.get_button_style())
        remove_btn.setStyleSheet(theme.get_button_danger_style())

        add_btn.clicked.connect(self.add_server)
        edit_btn.clicked.connect(self.edit_server)
        remove_btn.clicked.connect(self.remove_server)
        refresh_btn.clicked.connect(self.load_mcp_config)
        library_btn.clicked.connect(self.open_mcp_sources)
        tools_btn.clicked.connect(self.list_server_tools)
        validate_btn.clicked.connect(self.validate_mcp_config)
        autofix_btn.clicked.connect(self.autofix_mcp_config)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(library_btn)
        btn_layout.addWidget(tools_btn)
        btn_layout.addWidget(validate_btn)
        btn_layout.addWidget(autofix_btn)
        left_layout.addLayout(btn_layout)

        splitter.addWidget(left_panel)

        # Right side - JSON editor
        editor_panel = QWidget()
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(5)

        # Info label for .claude.json servers (project scope only)
        self.claude_json_info_label = QLabel()
        self.claude_json_info_label.setWordWrap(True)
        self.claude_json_info_label.setStyleSheet(f"color: {theme.WARNING_COLOR}; background: {theme.BG_MEDIUM}; padding: 6px; border-radius: 3px; font-size: {theme.FONT_SIZE_SMALL}px; border-left: 3px solid {theme.WARNING_COLOR};")
        self.claude_json_info_label.setVisible(False)  # Hidden by default
        editor_layout.addWidget(self.claude_json_info_label)

        # Editor header with buttons
        editor_header = QHBoxLayout()
        editor_header.setSpacing(5)

        self.server_name_label = QLabel("No server selected")
        self.server_name_label.setStyleSheet(theme.get_label_style("normal", "secondary"))

        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip("Save MCP configuration")
        backup_btn = QPushButton("📦 Backup & Save")
        backup_btn.setToolTip("Create backup and save")
        revert_btn = QPushButton("Revert")
        revert_btn.setToolTip("Revert to saved version")

        for btn in [save_btn, backup_btn, revert_btn]:
            btn.setStyleSheet(theme.get_button_style())

        save_btn.clicked.connect(self.save_mcp_config)
        backup_btn.clicked.connect(self.backup_and_save)
        revert_btn.clicked.connect(self.revert_mcp_config)

        editor_header.addWidget(self.server_name_label)
        editor_header.addStretch()
        editor_header.addWidget(save_btn)
        editor_header.addWidget(backup_btn)
        editor_header.addWidget(revert_btn)

        editor_layout.addLayout(editor_header)

        self.editor = QTextEdit()
        self.editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: {theme.FONT_SIZE_NORMAL}px;
            }}
        """)
        editor_layout.addWidget(self.editor)

        splitter.addWidget(editor_panel)
        splitter.setSizes([300, 700])
        layout.addWidget(splitter, 1)

        # Load initial data
        self.load_mcp_config()

        return widget

    # ── Discover sub-tab ────────────────────────────────────────────────────

    def create_discover_tab(self) -> QWidget:
        """Build the Discover sub-tab UI."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Search bar
        search_layout = QHBoxLayout()
        self._discover_search = QLineEdit()
        self._discover_search.setPlaceholderText("Search MCP servers... (e.g. filesystem, github, slack)")
        self._discover_search.setStyleSheet(theme.get_line_edit_style())
        self._discover_search.returnPressed.connect(self._do_discover_search)
        search_layout.addWidget(self._discover_search)

        self._discover_search_btn = QPushButton("Search")
        self._discover_search_btn.setStyleSheet(theme.get_button_style())
        self._discover_search_btn.clicked.connect(self._do_discover_search)
        search_layout.addWidget(self._discover_search_btn)
        layout.addLayout(search_layout)

        # Source checkboxes
        sources_layout = QHBoxLayout()
        sources_label = QLabel("Sources:")
        sources_label.setStyleSheet(f"color: {theme.FG_SECONDARY};")
        sources_layout.addWidget(sources_label)

        self._source_checks = {}
        for key, label in [
            ("mcp.so", "mcp.so"),
            ("mcpservers.org", "mcpservers.org"),
            ("pulsemcp.com", "PulseMCP"),
            ("github", "GitHub"),
        ]:
            cb = QCheckBox(label)
            cb.setChecked(True)
            cb.setStyleSheet(f"color: {theme.FG_PRIMARY};")
            self._source_checks[key] = cb
            sources_layout.addWidget(cb)
        sources_layout.addStretch()
        layout.addLayout(sources_layout)

        # Results table
        self._discover_table = QTableWidget()
        self._discover_table.setColumnCount(5)
        self._discover_table.setHorizontalHeaderLabels(
            ["Name", "Description", "Source", "Stars", "Install Command"]
        )
        hdr = self._discover_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self._discover_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._discover_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._discover_table.verticalHeader().hide()
        self._discover_table.setSortingEnabled(True)
        self._discover_table.setStyleSheet(theme.get_table_style())
        layout.addWidget(self._discover_table, 1)

        # Restore saved column widths
        from utils.ui_state_manager import UIStateManager
        UIStateManager.instance().connect_table("mcp.discover_table", self._discover_table)

        # Bottom row: status | rate limit | Add button
        bottom_layout = QHBoxLayout()
        self._discover_status = QLabel("Enter a search term above.")
        self._discover_status.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        bottom_layout.addWidget(self._discover_status)
        bottom_layout.addStretch()

        self._discover_rate_label = QLabel("")
        self._discover_rate_label.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        bottom_layout.addWidget(self._discover_rate_label)

        add_btn = QPushButton("Add to Config")
        add_btn.setStyleSheet(theme.get_button_style())
        add_btn.clicked.connect(self._add_discover_to_config)
        bottom_layout.addWidget(add_btn)
        layout.addLayout(bottom_layout)

        return widget

    def _do_discover_search(self):
        """Start a background MCP server search."""
        query = self._discover_search.text().strip()
        if not query:
            return
        sources = [k for k, cb in self._source_checks.items() if cb.isChecked()]
        if not sources:
            self._discover_status.setText("Select at least one source.")
            return

        self._discover_search_btn.setEnabled(False)
        self._discover_status.setText("Searching…")
        self._discover_table.setRowCount(0)

        self._search_worker = MCPSearchWorker(query, sources, parent=self)
        self._search_worker.results_ready.connect(self._on_discover_results)
        self._search_worker.error.connect(self._on_discover_error)
        self._search_worker.finished.connect(
            lambda: self._discover_search_btn.setEnabled(True)
        )
        self._search_worker.start()

    def _on_discover_results(self, results):
        """Populate the results table."""
        self._discover_table.setSortingEnabled(False)
        self._discover_table.setRowCount(0)
        for result in results:
            row = self._discover_table.rowCount()
            self._discover_table.insertRow(row)
            self._discover_table.setItem(row, 0, QTableWidgetItem(result.name))
            self._discover_table.setItem(row, 1, QTableWidgetItem(result.description))
            self._discover_table.setItem(row, 2, QTableWidgetItem(result.source))
            stars_item = QTableWidgetItem(str(result.stars) if result.stars else "")
            stars_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._discover_table.setItem(row, 3, stars_item)
            self._discover_table.setItem(row, 4, QTableWidgetItem(result.install_command))
            # Store full result for later use
            self._discover_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, result)
        self._discover_table.setSortingEnabled(True)

        count = len(results)
        self._discover_status.setText(
            f"{count} result{'s' if count != 1 else ''} found."
        )

        # Update GitHub rate limit display
        try:
            from utils.github_client import GitHubClient
            rl = GitHubClient().get_rate_limit()
            remaining = rl.get("rate", {}).get("remaining", rl.get("remaining", "?"))
            self._discover_rate_label.setText(f"GitHub API: {remaining} remaining")
            win = self.window()
            if hasattr(win, "update_github_status"):
                win.update_github_status(remaining)
        except Exception:
            pass

    def _on_discover_error(self, msg: str):
        self._discover_status.setText(f"Search error: {msg}")

    def _add_discover_to_config(self):
        """Pre-fill AddServerDialog from the selected search result."""
        row = self._discover_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Select a server from the results first.")
            return

        result = self._discover_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if result is None:
            return

        # Build a server_config dict from the install_command
        parts = (result.install_command or "").split()
        server_config = {}
        if parts:
            server_config["command"] = parts[0]
            if len(parts) > 1:
                server_config["args"] = parts[1:]

        dialog = AddServerDialog(self, server_config=server_config)
        safe_name = result.name.lower().replace(" ", "-")
        dialog.name_input.setText(safe_name)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            server_name, srv_cfg = dialog.get_server_config()
            config = self.config
            if "mcpServers" not in config:
                config["mcpServers"] = {}

            if server_name in config["mcpServers"]:
                reply = QMessageBox.question(
                    self,
                    "Server Exists",
                    f"Server '{server_name}' already exists. Overwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.No:
                    return

            config["mcpServers"][server_name] = srv_cfg
            self.config = config
            self.editor.setPlainText(json.dumps(config, indent=2))
            self.update_server_list()
            # Switch to Configure tab so user can save
            self._sub_tabs.setCurrentIndex(0)
            win = self.window()
            if hasattr(win, "set_status"):
                win.set_status(f"Server '{server_name}' added — remember to save.")
            else:
                QMessageBox.information(
                    self, "Server Added",
                    f"Server '{server_name}' added.\n\nDon't forget to save the configuration."
                )

    def get_scope_file_path(self):
        """Get file path for the current scope"""
        if self.scope == "user":
            return self.config_manager.get_mcp_file_path("user")
        elif self.scope == "local":
            if not self.project_context or not self.project_context.has_project():
                return Path.home() / ".claude" / ".mcp.json"
            return self.project_context.get_project() / ".claude" / ".mcp.json"
        else:  # project
            if not self.project_context or not self.project_context.has_project():
                return None
            return self.project_context.get_project() / ".mcp.json"

    def on_project_changed(self, project_path: Path):
        """Handle project context change"""
        # Update path label
        file_path = self.get_scope_file_path()
        if file_path:
            self.path_label.setText(f"File: {file_path}")
        # Reload MCP config from new project
        self.load_mcp_config()

    def get_scope_display_name(self):
        """Get display name for current scope"""
        return {
            "user": "User",
            "local": "Local",
            "project": "Project"
        }.get(self.scope, "Unknown")

    def update_server_list(self):
        """Update the server list from config with health status icons - shows BOTH sources merged"""
        self.server_list.clear()

        # For project scope, merge both sources for display in the server list
        if self.scope == "project" and hasattr(self, 'mcp_json_servers') and hasattr(self, 'claude_json_servers'):
            merged_servers = {**self.mcp_json_servers, **self.claude_json_servers}
        else:
            # For user/local scope, just use self.config
            merged_servers = self.config.get("mcpServers", {})

        for server_name, server_config in merged_servers.items():
            # Get server type
            server_type = server_config.get("type", "stdio")

            # Determine source for project scope
            source_label = ""
            if self.scope == "project" and hasattr(self, 'mcp_json_servers') and hasattr(self, 'claude_json_servers'):
                if server_name in self.claude_json_servers:
                    source_label = " [.claude.json]"
                elif server_name in self.mcp_json_servers:
                    source_label = " [.mcp.json]"

            # Create list item with type and source
            item_text = f"{server_name} ({server_type}){source_label}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, server_name)  # Store server name
            self.server_list.addItem(item)

    def filter_servers(self, text):
        """Filter server list based on search text"""
        for i in range(self.server_list.count()):
            item = self.server_list.item(i)
            if text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def switch_editor_source(self, source):
        """Switch the editor to show a different source config"""
        if source == "mcp":
            # Show .mcp.json content
            self.current_editing_source = "mcp"
            self.config = {"mcpServers": self.mcp_json_servers}
            self.path_label.setText(f"File: {self.get_scope_file_path()}")
        elif source == "claude":
            # Show project settings from .claude.json
            self.current_editing_source = "claude"
            self.config = {"mcpServers": self.claude_json_servers}
            claude_path = Path.home() / ".claude.json"
            project_dir = str(self.get_scope_file_path().parent)
            self.path_label.setText(f"File: {claude_path} (project: {project_dir})")

        # Update editor with new config
        formatted_json = json.dumps(self.config, indent=2)
        self.editor.setPlainText(formatted_json)

    def on_server_selected(self, item):
        """Handle server selection - switch editor to appropriate source and highlight server"""
        server_name = item.data(Qt.ItemDataRole.UserRole)

        # Determine which source this server belongs to
        if self.scope == "project" and hasattr(self, 'mcp_json_servers') and hasattr(self, 'claude_json_servers'):
            # Check if server is in .claude.json
            if server_name in self.claude_json_servers:
                # Switch editor to .claude.json source
                if self.current_editing_source != "claude":
                    self.switch_editor_source("claude")
            # Check if server is in .mcp.json
            elif server_name in self.mcp_json_servers:
                # Switch editor to .mcp.json source
                if self.current_editing_source != "mcp":
                    self.switch_editor_source("mcp")

        # Update label to show selected server and source
        source_indicator = ""
        if self.scope == "project" and hasattr(self, 'current_editing_source'):
            if self.current_editing_source == "claude":
                source_indicator = " [~/.claude.json]"
            else:
                source_indicator = " [.mcp.json]"

        self.server_name_label.setText(f"Editing: {server_name}{source_indicator}")

        # Find and highlight the server name in the editor
        text = self.editor.toPlainText()
        search_text = f'"{server_name}"'

        # Find the position of the server name
        cursor = self.editor.textCursor()
        doc = self.editor.document()
        cursor = doc.find(search_text)

        if not cursor.isNull():
            # Select the entire server block (approximate by selecting multiple lines)
            cursor.movePosition(cursor.MoveOperation.StartOfLine)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 10)
            self.editor.setTextCursor(cursor)
            self.editor.ensureCursorVisible()

    def load_mcp_config(self):
        """Load MCP configuration from current scope and auto-check health"""
        try:
            if self.scope == "user":
                # User scope: load from config manager
                full_config = self.config_manager.get_mcp_config(self.scope)
                if "mcpServers" in full_config:
                    self.config = {"mcpServers": full_config["mcpServers"]}
                else:
                    self.config = {"mcpServers": {}}
                # No .claude.json info label for user scope
                if hasattr(self, 'claude_json_info_label'):
                    self.claude_json_info_label.setVisible(False)
            else:
                # For local/project, keep separate configs from two sources:
                # 1. .mcp.json in project folder
                # 2. Project-specific settings in ~/.claude.json
                self.mcp_json_servers = {}
                self.claude_json_servers = {}

                # Source 1: Read from .mcp.json
                file_path = self.get_scope_file_path()
                if file_path and file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        mcp_json_config = json.load(f)
                        if "mcpServers" in mcp_json_config:
                            self.mcp_json_servers = mcp_json_config["mcpServers"]

                # Source 2: Read project-specific settings from ~/.claude.json (only for project scope)
                if self.scope == "project":
                    try:
                        claude_json_path = Path.home() / ".claude.json"
                        if claude_json_path.exists():
                            with open(claude_json_path, 'r', encoding='utf-8') as f:
                                claude_config = json.load(f)
                                # Get current project path
                                current_project = self.get_scope_file_path()
                                if current_project:
                                    project_dir = str(current_project.parent)

                                    # Project settings are under the "projects" key
                                    if "projects" in claude_config and isinstance(claude_config["projects"], dict):
                                        # Try multiple path formats to match
                                        possible_keys = [
                                            project_dir,  # As-is
                                            project_dir.replace('\\', '/'),  # Forward slashes
                                            project_dir.replace('/', '\\'),  # Backslashes
                                        ]

                                        for key in possible_keys:
                                            if key in claude_config["projects"]:
                                                project_settings = claude_config["projects"][key]
                                                if "mcpServers" in project_settings:
                                                    self.claude_json_servers = project_settings["mcpServers"]
                                                break
                    except Exception as e:
                        # If reading .claude.json fails, just use .mcp.json servers
                        pass

                # For project scope: start with .mcp.json in the editor
                if self.scope == "project":
                    # Default to editing .mcp.json
                    self.current_editing_source = "mcp"
                    self.config = {"mcpServers": self.mcp_json_servers}

                    # Update info label if there are .claude.json servers
                    if self.claude_json_servers:
                        claude_server_names = list(self.claude_json_servers.keys())
                        claude_count = len(claude_server_names)
                        server_list_text = ", ".join(claude_server_names)
                        self.claude_json_info_label.setText(
                            f"ℹ️ <b>{claude_count} server(s) from ~/.claude.json:</b> {server_list_text}<br>"
                            f"Click on a [.claude.json] server in the list to edit it. Changes will be saved to ~/.claude.json."
                        )
                        self.claude_json_info_label.setVisible(True)
                    else:
                        self.claude_json_info_label.setVisible(False)
                else:
                    # For local scope: show all servers normally (no special handling)
                    self.config = {"mcpServers": self.mcp_json_servers}
                    if hasattr(self, 'claude_json_info_label'):
                        self.claude_json_info_label.setVisible(False)

            formatted_json = json.dumps(self.config, indent=2)
            self.editor.setPlainText(formatted_json)
            self.update_server_list()

            # Reset label when loading fresh config
            self.server_name_label.setText("No server selected")


        except FileNotFoundError:
            # File doesn't exist yet - create empty config
            self.config = {"mcpServers": {}}
            self.editor.setPlainText('{\n  "mcpServers": {\n  }\n}')
            self.update_server_list()
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load MCP configuration:\n{str(e)}")

    def add_server(self):
        """Add a new MCP server via dialog"""
        dialog = AddServerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            server_name, server_config = dialog.get_server_config()

            config = self.config

            # Check if server already exists
            if "mcpServers" in config and server_name in config["mcpServers"]:
                reply = QMessageBox.question(
                    self,
                    "Server Exists",
                    f"Server '{server_name}' already exists. Overwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return

            # Add server to config
            if "mcpServers" not in config:
                config["mcpServers"] = {}

            config["mcpServers"][server_name] = server_config
            self.config = config

            # Update editor and list
            formatted_json = json.dumps(config, indent=2)
            self.editor.setPlainText(formatted_json)
            self.update_server_list()

            QMessageBox.information(
                self,
                "Server Added",
                f"Server '{server_name}' added successfully!\n\nDon't forget to save the configuration."
            )

    def remove_server(self):
        """Remove selected MCP server"""
        server_list = self.server_list
        selected_items = server_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a server to remove.")
            return

        server_name = selected_items[0].data(Qt.ItemDataRole.UserRole)

        # Determine source and provide appropriate warning
        source_info = ""
        if self.scope == "project" and hasattr(self, 'claude_json_servers') and server_name in self.claude_json_servers:
            source_info = " from ~/.claude.json"

        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove server '{server_name}'{source_info}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Determine which source and switch editor if needed
                if self.scope == "project" and hasattr(self, 'claude_json_servers') and server_name in self.claude_json_servers:
                    # Switch to claude source to delete
                    if self.current_editing_source != "claude":
                        self.switch_editor_source("claude")

                config = self.config
                # Remove from config
                if "mcpServers" in config and server_name in config["mcpServers"]:
                    del config["mcpServers"][server_name]
                    # Update editor
                    formatted_json = json.dumps(config, indent=2)
                    self.editor.setPlainText(formatted_json)
                    # Save
                    self.save_mcp_config_internal(config)
                    self.update_server_list()
                    QMessageBox.information(self, "Removed", f"Server '{server_name}' removed successfully{source_info}!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to remove server:\n{str(e)}")

    def edit_server(self):
        """Edit selected MCP server via dialog"""
        server_list = self.server_list
        selected_items = server_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a server to edit.")
            return

        server_name = selected_items[0].data(Qt.ItemDataRole.UserRole)

        # Determine which source and switch editor if needed
        if self.scope == "project" and hasattr(self, 'claude_json_servers') and server_name in self.claude_json_servers:
            # Switch to claude source to edit
            if self.current_editing_source != "claude":
                self.switch_editor_source("claude")

        config = self.config

        if "mcpServers" not in config or server_name not in config["mcpServers"]:
            QMessageBox.warning(self, "Error", f"Server '{server_name}' not found in configuration.")
            return

        # Get existing server config
        server_config = config["mcpServers"][server_name]

        # Open dialog in edit mode
        dialog = AddServerDialog(
            self,
            edit_mode=True,
            server_name=server_name,
            server_config=server_config
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get updated config (name should be the same since we disabled the name field)
            _, updated_config = dialog.get_server_config()

            # Update config
            config["mcpServers"][server_name] = updated_config
            self.config = config

            # Update editor and list
            formatted_json = json.dumps(config, indent=2)
            self.editor.setPlainText(formatted_json)
            self.update_server_list()

            QMessageBox.information(
                self,
                "Server Updated",
                f"Server '{server_name}' updated successfully!\n\nDon't forget to save the configuration."
            )

    def list_server_tools(self):
        """List all tools available from the selected MCP server"""
        server_list = self.server_list
        selected_items = server_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a server to inspect.")
            return

        server_name = selected_items[0].data(Qt.ItemDataRole.UserRole)

        # Get server config from merged sources
        server_config = None
        if self.scope == "project" and hasattr(self, 'mcp_json_servers') and hasattr(self, 'claude_json_servers'):
            # Check both sources
            if server_name in self.mcp_json_servers:
                server_config = self.mcp_json_servers[server_name]
            elif server_name in self.claude_json_servers:
                server_config = self.claude_json_servers[server_name]
        else:
            # Use current config
            if "mcpServers" in self.config and server_name in self.config["mcpServers"]:
                server_config = self.config["mcpServers"][server_name]

        if not server_config:
            QMessageBox.warning(self, "Error", f"Server '{server_name}' not found in configuration.")
            return

        # Open the MCP Tools Dialog
        dialog = MCPToolsDialog(server_name, server_config, self)
        dialog.exec()

    def validate_json(self):
        """Validate the JSON in the editor"""
        try:
            editor = self.editor
            json.loads(editor.toPlainText())
            QMessageBox.information(self, "Valid", "JSON is valid!")
            return True
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Invalid JSON", f"Invalid JSON:\n{str(e)}")
            return False

    def save_mcp_config(self):
        """Save MCP configuration"""
        if not self.validate_json():
            return
        try:
            editor = self.editor
            content = editor.toPlainText()
            config = json.loads(content)
            self.save_mcp_config_internal(config)
            self.config = config
            self.update_server_list()

            # Show which file was saved
            if self.scope == "project" and hasattr(self, 'current_editing_source'):
                if self.current_editing_source == "claude":
                    save_location = "~/.claude.json (project settings)"
                else:
                    save_location = ".mcp.json"
            else:
                save_location = f"{self.get_scope_display_name()} scope"

            QMessageBox.information(self, "Saved", f"MCP configuration saved to {save_location}!")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n{str(e)}")

    def save_mcp_config_internal(self, config):
        """Internal method to save config without validation"""
        if self.scope == "user":
            self.config_manager.save_mcp_config(config, self.scope)
        else:
            # For local/project, determine which file to save to
            if self.scope == "project" and hasattr(self, 'current_editing_source') and self.current_editing_source == "claude":
                # Save to ~/.claude.json under the projects key
                claude_json_path = Path.home() / ".claude.json"
                project_dir = str(self.get_scope_file_path().parent)

                # Read existing .claude.json
                if claude_json_path.exists():
                    with open(claude_json_path, 'r', encoding='utf-8') as f:
                        claude_config = json.load(f)
                else:
                    claude_config = {}

                # Ensure projects key exists
                if "projects" not in claude_config:
                    claude_config["projects"] = {}

                # Find the correct project key (try different path formats)
                project_key = None
                possible_keys = [
                    project_dir,
                    project_dir.replace('\\', '/'),
                    project_dir.replace('/', '\\'),
                ]
                for key in possible_keys:
                    if key in claude_config["projects"]:
                        project_key = key
                        break

                # Use the first format if no match found
                if not project_key:
                    project_key = project_dir

                # Update project's mcpServers
                if project_key not in claude_config["projects"]:
                    claude_config["projects"][project_key] = {}

                claude_config["projects"][project_key]["mcpServers"] = config.get("mcpServers", {})

                # Save back to .claude.json
                with open(claude_json_path, 'w', encoding='utf-8') as f:
                    json.dump(claude_config, f, indent=2)

                # Update our cached copy
                self.claude_json_servers = config.get("mcpServers", {})
            else:
                # Save to .mcp.json
                file_path = self.get_scope_file_path()
                if file_path:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2)

                    # Update our cached copy
                    if hasattr(self, 'mcp_json_servers'):
                        self.mcp_json_servers = config.get("mcpServers", {})

    def backup_and_save(self):
        """Create backup before saving"""
        try:
            file_path = self.get_scope_file_path()
            if file_path.exists():
                self.backup_manager.create_file_backup(file_path)
            if self.validate_json():
                editor = self.editor
                content = editor.toPlainText()
                config = json.loads(content)
                self.save_mcp_config_internal(config)
                self.config = config
                self.update_server_list()
                QMessageBox.information(self, "Saved", "Backup created and MCP configuration saved!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed:\n{str(e)}")

    def revert_mcp_config(self):
        """Revert to saved version"""
        reply = QMessageBox.question(
            self,
            "Revert Changes",
            "Are you sure you want to revert to the saved version?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.load_mcp_config()

    def open_mcp_sources(self):
        """Open MCP library to browse and manage templates"""
        template_mgr = get_template_manager()
        templates_dir = template_mgr.get_templates_dir('mcp')

        dialog = MCPLibraryDialog(templates_dir, self.scope, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.get_selected_mcps()
            if selected:
                self.deploy_mcps(selected)
                self.load_mcp_config()

    def deploy_mcps(self, mcps):
        """Deploy selected MCP servers to the current scope"""
        # Load existing config
        mcp_file = self.get_scope_file_path()
        if not mcp_file:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        try:
            if mcp_file.exists():
                with open(mcp_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {"mcpServers": {}}

            added_count = 0
            skipped_count = 0

            for mcp_name, mcp_content in mcps:
                # Parse the JSON content
                mcp_data = json.loads(mcp_content)

                # Strip metadata fields (used by mcp_linker and other tools)
                metadata_fields = ['_creator', 'name', 'updated_at']
                for field in metadata_fields:
                    mcp_data.pop(field, None)

                # Check if server already exists
                if mcp_name in config.get("mcpServers", {}):
                    skipped_count += 1
                    continue

                # Add to config
                if "mcpServers" not in config:
                    config["mcpServers"] = {}

                config["mcpServers"][mcp_name] = mcp_data
                added_count += 1

            # Save config
            mcp_file.parent.mkdir(parents=True, exist_ok=True)
            with open(mcp_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)

            # Show summary
            msg = f"Deployed {added_count} MCP server(s)"
            if skipped_count > 0:
                msg += f"\nSkipped {skipped_count} (already exist)"
            QMessageBox.information(self, "Deploy Complete", msg)

        except Exception as e:
            QMessageBox.critical(self, "Deploy Error", f"Failed to deploy MCP servers:\n{str(e)}")

    def reset_project_choices(self):
        """Reset MCP project choices"""
        # Confirm action
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            "Are you sure you want to reset all MCP project choices?\n\n"
            "This will clear your project-specific MCP server selections.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        success, stdout, stderr = run_command_silent(
            ["claude", "mcp", "reset-project-choices"],
            timeout=30,
            shell=True
        )

        if success:
            QMessageBox.information(
                self,
                "Success",
                "MCP project choices have been reset!\n\n" + stdout
            )
            # Reload configuration
            self.load_mcp_config()
        else:
            if "timed out" in stderr.lower():
                QMessageBox.critical(self, "Timeout", "Command timed out after 30 seconds")
            elif "not found" in stderr.lower() or "no such file" in stderr.lower():
                QMessageBox.critical(
                    self,
                    "Command Not Found",
                    "claude command not found in PATH.\n\n"
                    "Make sure Claude Code is installed and the claude CLI is in your system PATH."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Command Failed",
                    f"Failed to reset project choices:\n\n{stderr}"
                )

    def validate_mcp_config(self):
        """Validate MCP configuration for Windows compatibility"""
        try:
            # Save current editor content to temp file for validation
            file_path = self.get_scope_file_path()
            if not file_path:
                QMessageBox.warning(self, "No Project", "Please select a project first.")
                return

            # If file doesn't exist, create it temporarily from editor content
            temp_validation = False
            if not file_path.exists():
                # Save editor content to temp location for validation
                try:
                    content = self.editor.toPlainText()
                    config = json.loads(content)
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2)
                    temp_validation = True
                except json.JSONDecodeError as e:
                    QMessageBox.critical(self, "Invalid JSON", f"Cannot validate: Invalid JSON in editor\n{str(e)}")
                    return

            # Run validation
            validator = MCPValidator()
            report = validator.get_validation_report(file_path)

            # Clean up temp file if created
            if temp_validation and file_path.exists():
                file_path.unlink()

            # Show validation report
            msg = QMessageBox(self)
            msg.setWindowTitle("MCP Validation Report")
            msg.setText(report)
            msg.setIcon(QMessageBox.Icon.Information)

            # Add detailed info
            is_valid, errors, warnings = validator.validate_mcp_json(file_path) if file_path.exists() else (True, [], [])

            if errors:
                msg.setIcon(QMessageBox.Icon.Critical)
            elif warnings:
                msg.setIcon(QMessageBox.Icon.Warning)
            else:
                msg.setIcon(QMessageBox.Icon.Information)

            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()

        except Exception as e:
            QMessageBox.critical(self, "Validation Error", f"Failed to validate:\n{str(e)}")

    def autofix_mcp_config(self):
        """Auto-fix MCP configuration for Windows compatibility"""
        try:
            # Get current file path
            file_path = self.get_scope_file_path()
            if not file_path:
                QMessageBox.warning(self, "No Project", "Please select a project first.")
                return

            # If file doesn't exist, create it from editor content
            temp_fix = False
            if not file_path.exists():
                try:
                    content = self.editor.toPlainText()
                    config = json.loads(content)
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2)
                    temp_fix = True
                except json.JSONDecodeError as e:
                    QMessageBox.critical(self, "Invalid JSON", f"Cannot auto-fix: Invalid JSON in editor\n{str(e)}")
                    return

            # Run auto-fix
            validator = MCPValidator()
            success, fixed_json, fixes_applied = validator.auto_fix_windows(file_path)

            # Clean up temp file
            if temp_fix and file_path.exists():
                file_path.unlink()

            if not success:
                QMessageBox.critical(self, "Auto-Fix Failed", "Failed to auto-fix configuration:\n" + "\n".join(fixes_applied))
                return

            if not fixes_applied:
                QMessageBox.information(
                    self,
                    "No Fixes Needed",
                    "Configuration is already Windows-compatible!\n\nNo changes were needed."
                )
                return

            # Show fixes applied
            fixes_msg = "\n".join([f"• {fix}" for fix in fixes_applied])
            reply = QMessageBox.question(
                self,
                "Auto-Fix Complete",
                f"The following fixes were applied:\n\n{fixes_msg}\n\nApply these changes to the editor?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Update editor with fixed JSON
                self.editor.setPlainText(fixed_json)

                # Parse and update config
                self.config = json.loads(fixed_json)
                self.update_server_list()

                QMessageBox.information(
                    self,
                    "Applied",
                    f"Auto-fix applied successfully!\n\n{len(fixes_applied)} fix(es) applied.\n\nDon't forget to save the configuration."
                )

        except Exception as e:
            QMessageBox.critical(self, "Auto-Fix Error", f"Failed to auto-fix:\n{str(e)}")
