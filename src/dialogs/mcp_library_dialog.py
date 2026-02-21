"""MCP Library Dialog - manages MCP server templates"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QCheckBox, QWidget, QDialogButtonBox, QInputDialog,
    QLineEdit, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from pathlib import Path
import sys
import json
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.theme import (
    BG_DARK, BG_MEDIUM, BG_LIGHT,
    FG_PRIMARY, FG_SECONDARY,
    ACCENT_PRIMARY,
    FONT_SIZE_SMALL, FONT_SIZE_NORMAL, FONT_SIZE_LARGE,
    get_button_style, get_line_edit_style
)
from utils.template_manager import get_template_manager


class AddHTTPServerDialog(QDialog):
    """Simple dialog for adding HTTP MCP server templates"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add HTTP MCP Server Template")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Add HTTP MCP Server Template")
        header.setStyleSheet(f"font-weight: bold; color: {FG_PRIMARY}; font-size: {FONT_SIZE_NORMAL}px;")
        layout.addWidget(header)

        # Form layout
        form = QFormLayout()

        # Server Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., sap-docs")
        self.name_input.setStyleSheet(get_line_edit_style())
        form.addRow("Server Name*:", self.name_input)

        # URL
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("e.g., https://mcp-sap-docs.marianzeis.de/mcp")
        self.url_input.setStyleSheet(get_line_edit_style())
        self.url_input.textChanged.connect(self.on_url_changed)
        form.addRow("URL*:", self.url_input)

        # Server Type (HTTP or SSE)
        type_layout = QHBoxLayout()
        self.http_radio = QPushButton("HTTP")
        self.http_radio.setCheckable(True)
        self.http_radio.setChecked(True)
        self.http_radio.setStyleSheet(get_button_style())
        self.http_radio.clicked.connect(lambda: self.set_type("http"))

        self.sse_radio = QPushButton("SSE")
        self.sse_radio.setCheckable(True)
        self.sse_radio.setStyleSheet(get_button_style())
        self.sse_radio.clicked.connect(lambda: self.set_type("sse"))

        type_layout.addWidget(self.http_radio)
        type_layout.addWidget(self.sse_radio)
        type_layout.addStretch()
        form.addRow("Type*:", type_layout)

        self.server_type = "http"

        layout.addLayout(form)

        # Info
        info = QLabel("* Required fields. This creates a template for an HTTP-based MCP server.")
        info.setStyleSheet(f"color: {FG_SECONDARY}; font-size: {FONT_SIZE_SMALL}px;")
        layout.addWidget(info)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def set_type(self, server_type):
        """Set server type and update radio button states"""
        self.server_type = server_type
        self.http_radio.setChecked(server_type == "http")
        self.sse_radio.setChecked(server_type == "sse")

    def on_url_changed(self, text):
        """Auto-suggest server name from URL"""
        if not self.name_input.text():  # Only auto-fill if name is empty
            # Try to extract a meaningful name from URL
            # e.g., https://mcp-sap-docs.marianzeis.de/mcp -> sap-docs
            try:
                from urllib.parse import urlparse
                parsed = urlparse(text)
                hostname = parsed.hostname or ""
                # Try to extract from hostname
                if "mcp-" in hostname:
                    # Extract part after "mcp-"
                    parts = hostname.split("mcp-", 1)
                    if len(parts) > 1:
                        name_part = parts[1].split(".")[0]  # Get first part before domain
                        self.name_input.setText(name_part)
            except:
                pass

    def validate_and_accept(self):
        """Validate inputs before accepting"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Server name is required!")
            return

        if not self.url_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "URL is required!")
            return

        # Validate URL format
        url = self.url_input.text().strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            QMessageBox.warning(self, "Validation Error", "URL must start with http:// or https://")
            return

        self.accept()

    def get_server_config(self):
        """Get the server configuration"""
        server_name = self.name_input.text().strip()
        server_config = {
            "type": self.server_type,
            "url": self.url_input.text().strip()
        }
        return server_name, server_config


class MCPLibraryDialog(QDialog):
    """Dialog for managing MCP server templates in config/templates/mcp/"""

    def __init__(self, templates_dir, scope, parent=None):
        super().__init__(parent)
        self.templates_dir = Path(templates_dir)
        self.scope = scope
        self.template_mgr = get_template_manager()
        self.current_folder = ""  # Empty = root, otherwise subfolder name
        self.setWindowTitle("MCP Server Library")
        self.setModal(True)
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("MCP Server Library - Manage and deploy MCP server templates")
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

        self.load_templates()

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["", "Name", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 40)  # Wider for emoji icons
        self.table.setColumnWidth(1, 200)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSortingEnabled(True)
        # Sort by Name column by default, not the icon column
        self.table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        self.table.doubleClicked.connect(self.on_double_click)
        # Disable text elide mode to prevent "..." on narrow columns
        self.table.setTextElideMode(Qt.TextElideMode.ElideNone)
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

        manage_layout = QHBoxLayout()

        add_btn = QPushButton("➕ Add Template")
        add_btn.setStyleSheet(get_button_style())
        add_btn.setToolTip("Add stdio/command-based MCP server template")
        add_btn.clicked.connect(self.add_template)
        manage_layout.addWidget(add_btn)

        add_http_btn = QPushButton("🌐 Add HTTP Template")
        add_http_btn.setStyleSheet(get_button_style())
        add_http_btn.setToolTip("Add HTTP/SSE-based MCP server template")
        add_http_btn.clicked.connect(self.add_http_template)
        manage_layout.addWidget(add_http_btn)

        edit_btn = QPushButton("✏️ Edit Selected")
        edit_btn.setStyleSheet(get_button_style())
        edit_btn.clicked.connect(self.edit_template)
        manage_layout.addWidget(edit_btn)

        bulk_add_btn = QPushButton("📋 Bulk Add")
        bulk_add_btn.setStyleSheet(get_button_style())
        bulk_add_btn.clicked.connect(self.bulk_add_mcps)
        manage_layout.addWidget(bulk_add_btn)

        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.setStyleSheet(get_button_style())
        delete_btn.clicked.connect(self.delete_selected)
        manage_layout.addWidget(delete_btn)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet(get_button_style())
        refresh_btn.clicked.connect(self.refresh_templates)
        manage_layout.addWidget(refresh_btn)

        open_folder_btn = QPushButton("📁 Open Folder")
        open_folder_btn.setStyleSheet(get_button_style())
        open_folder_btn.clicked.connect(self.open_folder)
        manage_layout.addWidget(open_folder_btn)

        manage_layout.addStretch()
        layout.addLayout(manage_layout)

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

        info = QLabel("Select MCP servers to deploy, then click OK. You can also drop .json files directly into the templates folder.")
        info.setStyleSheet(f"color: {FG_SECONDARY}; font-size: {FONT_SIZE_SMALL}px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_templates(self):
        """Load all templates and organize by folder"""
        self.templates = {}
        self.folders = set()
        template_names = self.template_mgr.list_templates('mcp')

        for name in template_names:
            try:
                content = self.template_mgr.read_template('mcp', name)
                self.templates[name] = {
                    'content': content
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
                items_to_show.append(('folder', folder))

            # Show templates that are at root level (no folder)
            for name in sorted(self.templates.keys()):
                if '/' not in name:
                    items_to_show.append(('template', name))
        else:
            # Inside a folder - show templates in this folder
            prefix = self.current_folder + '/'
            for name in sorted(self.templates.keys()):
                if name.startswith(prefix):
                    # Get just the template name without folder prefix
                    template_name = name[len(prefix):]
                    # Only show if it's directly in this folder (no further subfolders)
                    if '/' not in template_name:
                        items_to_show.append(('template', name))

        self.table.setRowCount(len(items_to_show))

        for row, (item_type, name) in enumerate(items_to_show):
            if item_type == 'folder':
                icon_item = QTableWidgetItem("📁")
                icon_item.setData(Qt.ItemDataRole.UserRole, 'folder')
                name_item = QTableWidgetItem(name)
                name_item.setForeground(QColor(ACCENT_PRIMARY))
                desc_item = QTableWidgetItem("")  # No description for folders
            else:
                icon_item = QTableWidgetItem("📄")
                icon_item.setData(Qt.ItemDataRole.UserRole, 'template')
                # Show just the filename for display
                display_name = name.split('/')[-1] if '/' in name else name
                name_item = QTableWidgetItem(display_name)
                name_item.setForeground(QColor(FG_PRIMARY))

                # Extract description from _note field in JSON
                description = ""
                if name in self.templates:
                    try:
                        config = json.loads(self.templates[name]['content'])
                        description = config.get('_note', '')
                    except (json.JSONDecodeError, KeyError):
                        pass
                desc_item = QTableWidgetItem(description)
                desc_item.setForeground(QColor(FG_SECONDARY))

            # Store full name in UserRole for later retrieval
            name_item.setData(Qt.ItemDataRole.UserRole, name)
            icon_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Make icon column not sortable by setting empty sort role
            icon_item.setFlags(icon_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

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
            # Enter folder
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

    def get_selected_mcps(self):
        """Get selected templates (not folders)"""
        selected = []
        for row in range(self.table.rowCount()):
            icon_item = self.table.item(row, 0)
            name_item = self.table.item(row, 1)
            if name_item and name_item.isSelected():
                # Only include templates, not folders
                if icon_item and icon_item.data(Qt.ItemDataRole.UserRole) == 'template':
                    full_name = name_item.data(Qt.ItemDataRole.UserRole)
                    if full_name in self.templates:
                        selected.append((full_name, self.templates[full_name]['content']))
        return selected

    def add_template(self):
        """Add a new template using the same dialog as MCP tab"""
        # Import here to avoid circular import
        from tabs.mcp_tab import AddServerDialog

        # Use the same AddServerDialog from MCP tab
        dialog = AddServerDialog(self, edit_mode=False)
        # Show description field for templates
        dialog.description_label.setVisible(True)
        dialog.description_input.setVisible(True)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            server_name, server_config = dialog.get_server_config()

            try:
                # If in a folder, save to that folder
                if self.current_folder:
                    full_name = f"{self.current_folder}/{server_name}"
                else:
                    full_name = server_name

                # Convert server config to JSON template
                content = json.dumps(server_config, indent=2)
                self.template_mgr.save_template('mcp', full_name, content)
                self.refresh_templates()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save template:\n{str(e)}")

    def add_http_template(self):
        """Add a new HTTP server template using simplified dialog"""
        dialog = AddHTTPServerDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            server_name, server_config = dialog.get_server_config()

            try:
                # If in a folder, save to that folder
                if self.current_folder:
                    full_name = f"{self.current_folder}/{server_name}"
                else:
                    full_name = server_name

                # Convert server config to JSON template
                content = json.dumps(server_config, indent=2)
                self.template_mgr.save_template('mcp', full_name, content)
                self.refresh_templates()
                QMessageBox.information(
                    self,
                    "Template Added",
                    f"HTTP server template '{server_name}' added successfully!"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save template:\n{str(e)}")

    def edit_template(self):
        """Edit selected template using the same dialog as MCP tab"""
        # Import here to avoid circular import
        from tabs.mcp_tab import AddServerDialog

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
        mcp_name = name_item.data(Qt.ItemDataRole.UserRole)
        if mcp_name not in self.templates:
            QMessageBox.warning(self, "Error", f"Template '{mcp_name}' not found.")
            return

        content = self.templates[mcp_name]['content']

        try:
            # Parse JSON to get server config
            server_config = json.loads(content)

            # Extract and preserve metadata fields (but keep _note for description)
            metadata = {}
            metadata_fields = ['_creator', 'name', 'updated_at']
            for field in metadata_fields:
                if field in server_config:
                    metadata[field] = server_config.pop(field)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Invalid JSON", f"Template '{mcp_name}' contains invalid JSON.")
            return

        # Get just the template name (without folder) for display in dialog
        display_name = mcp_name.split('/')[-1] if '/' in mcp_name else mcp_name
        folder_prefix = mcp_name.rsplit('/', 1)[0] + '/' if '/' in mcp_name else ""

        # Use AddServerDialog in edit mode
        dialog = AddServerDialog(
            self,
            edit_mode=True,
            server_name=display_name,
            server_config=server_config
        )

        # Enable renaming for templates (unlike deployed servers)
        dialog.name_input.setReadOnly(False)
        dialog.name_input.setToolTip("You can rename this template")

        # Show description field for templates
        dialog.description_label.setVisible(True)
        dialog.description_input.setVisible(True)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_display_name, new_server_config = dialog.get_server_config()
            try:
                # Restore metadata fields
                final_config = {**metadata, **new_server_config}

                # Convert to JSON and save
                new_content = json.dumps(final_config, indent=2)

                # Construct new full name with folder prefix
                new_full_name = folder_prefix + new_display_name

                # Handle renaming: delete old template if name changed
                if new_full_name != mcp_name:
                    self.template_mgr.delete_template('mcp', mcp_name)

                # Save with new name
                self.template_mgr.save_template('mcp', new_full_name, new_content)
                self.refresh_templates()
                QMessageBox.information(
                    self,
                    "Template Updated",
                    f"Template '{new_display_name}' saved successfully!"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save template:\n{str(e)}")

    def bulk_add_mcps(self):
        """Open bulk add dialog"""
        from dialogs.bulk_mcp_add_dialog import BulkMCPAddDialog
        dialog = BulkMCPAddDialog(self.templates_dir, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_templates()

    def delete_selected(self):
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
                    self.template_mgr.delete_template('mcp', name)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to delete {name}:\n{str(e)}")

            QMessageBox.information(self, "Success", f"Deleted {len(selected)} template(s)!")
            self.refresh_templates()

    def refresh_templates(self):
        self.load_templates()
        self.populate_table()

    def open_folder(self):
        import subprocess
        import platform
        if platform.system() == 'Windows':
            subprocess.Popen(['explorer', str(self.templates_dir)])
        elif platform.system() == 'Darwin':
            subprocess.Popen(['open', str(self.templates_dir)])
        else:
            subprocess.Popen(['xdg-open', str(self.templates_dir)])
