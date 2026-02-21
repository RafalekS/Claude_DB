"""
MCP Tools Dialog - Display tools available from an MCP server
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QFileDialog, QProgressBar,
    QTextEdit, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor
import asyncio
import json
from typing import List, Dict, Any
from pathlib import Path

from utils.mcp_inspector import inspect_server
from utils.theme import get_button_style


class MCPToolsFetchThread(QThread):
    """Background thread for fetching MCP tools"""
    finished = pyqtSignal(list)  # List of tools
    error = pyqtSignal(str)      # Error message

    def __init__(self, server_config: Dict[str, Any], server_name: str):
        super().__init__()
        self.server_config = server_config
        self.server_name = server_name

    def run(self):
        """Run the async tool fetching in a thread"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Fetch tools
            tools = loop.run_until_complete(
                inspect_server(self.server_config, self.server_name)
            )

            loop.close()
            self.finished.emit(tools)

        except Exception as e:
            self.error.emit(str(e))


class MCPToolsDialog(QDialog):
    """Dialog for displaying MCP server tools"""

    def __init__(self, server_name: str, server_config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.server_name = server_name
        self.server_config = server_config
        self.tools = []

        self.setWindowTitle(f"MCP Server Tools - {server_name}")
        self.resize(1000, 700)

        self.init_ui()
        self.fetch_tools()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel(f"<h2>Tools from MCP Server: {self.server_name}</h2>")
        layout.addWidget(header)

        # Progress bar (shown while loading)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Connecting to server and fetching tools...")
        layout.addWidget(self.status_label)

        # Splitter for table and details
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Tools table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Tool Name", "Description", "Parameters"])

        # Configure table
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

        splitter.addWidget(self.table)

        # Details panel
        details_layout = QVBoxLayout()
        details_label = QLabel("<b>Tool Details:</b>")
        details_layout.addWidget(details_label)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(200)
        details_layout.addWidget(self.details_text)

        details_widget = QLabel()  # Dummy widget to hold layout
        details_widget.setLayout(details_layout)
        splitter.addWidget(self.details_text)

        splitter.setSizes([500, 200])
        layout.addWidget(splitter)

        # Button row
        button_layout = QHBoxLayout()

        # Export button
        self.export_json_btn = QPushButton("📄 Export to JSON")
        self.export_json_btn.setStyleSheet(get_button_style())
        self.export_json_btn.clicked.connect(self.export_to_json)
        self.export_json_btn.setEnabled(False)
        button_layout.addWidget(self.export_json_btn)

        self.export_md_btn = QPushButton("📝 Export to Markdown")
        self.export_md_btn.setStyleSheet(get_button_style())
        self.export_md_btn.clicked.connect(self.export_to_markdown)
        self.export_md_btn.setEnabled(False)
        button_layout.addWidget(self.export_md_btn)

        button_layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(get_button_style())
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def fetch_tools(self):
        """Fetch tools from MCP server in background thread"""
        self.fetch_thread = MCPToolsFetchThread(self.server_config, self.server_name)
        self.fetch_thread.finished.connect(self.on_tools_fetched)
        self.fetch_thread.error.connect(self.on_fetch_error)
        self.fetch_thread.start()

    def on_tools_fetched(self, tools: List[Dict[str, Any]]):
        """Handle tools fetched successfully"""
        self.tools = tools
        self.progress_bar.hide()

        if not tools:
            self.status_label.setText(f"No tools found for server '{self.server_name}'")
            return

        self.status_label.setText(f"Found {len(tools)} tool(s)")
        self.populate_table()
        self.export_json_btn.setEnabled(True)
        self.export_md_btn.setEnabled(True)

    def on_fetch_error(self, error_msg: str):
        """Handle fetch error"""
        self.progress_bar.hide()
        self.status_label.setText(f"Error: {error_msg}")
        QMessageBox.critical(
            self,
            "Connection Error",
            f"Failed to connect to MCP server '{self.server_name}':\n\n{error_msg}"
        )

    def populate_table(self):
        """Populate the table with tools"""
        self.table.setRowCount(len(self.tools))

        for row, tool in enumerate(self.tools):
            # Tool name
            name_item = QTableWidgetItem(tool.get('name', 'Unknown'))
            name_item.setForeground(QColor("#667eea"))
            self.table.setItem(row, 0, name_item)

            # Description
            desc_item = QTableWidgetItem(tool.get('description', 'No description'))
            self.table.setItem(row, 1, desc_item)

            # Parameters count
            input_schema = tool.get('inputSchema', {})
            properties = input_schema.get('properties', {})
            required = input_schema.get('required', [])

            param_count = len(properties)
            required_count = len(required)

            if param_count > 0:
                param_text = f"{param_count} ({required_count} required)"
            else:
                param_text = "None"

            param_item = QTableWidgetItem(param_text)
            self.table.setItem(row, 2, param_item)

    def on_selection_changed(self):
        """Handle table selection change"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.details_text.clear()
            return

        row = selected_rows[0].row()
        tool = self.tools[row]

        # Build details text
        details = f"<h3>{tool.get('name', 'Unknown')}</h3>"
        details += f"<p><b>Description:</b> {tool.get('description', 'No description')}</p>"

        # Parameters
        input_schema = tool.get('inputSchema', {})
        properties = input_schema.get('properties', {})
        required = input_schema.get('required', [])

        if properties:
            details += "<p><b>Parameters:</b></p><ul>"
            for param_name, param_info in properties.items():
                param_type = param_info.get('type', 'unknown')
                param_desc = param_info.get('description', 'No description')
                is_required = param_name in required
                req_text = " <b>(required)</b>" if is_required else ""

                details += f"<li><code>{param_name}</code> ({param_type}){req_text}: {param_desc}</li>"
            details += "</ul>"
        else:
            details += "<p><b>Parameters:</b> None</p>"

        self.details_text.setHtml(details)

    def export_to_json(self):
        """Export tools to JSON file"""
        if not self.tools:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Tools to JSON",
            f"{self.server_name}_tools.json",
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'server_name': self.server_name,
                    'tool_count': len(self.tools),
                    'tools': self.tools
                }, f, indent=2)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Tools exported to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export tools:\n{str(e)}"
            )

    def export_to_markdown(self):
        """Export tools to Markdown file"""
        if not self.tools:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Tools to Markdown",
            f"{self.server_name}_tools.md",
            "Markdown Files (*.md)"
        )

        if not file_path:
            return

        try:
            from datetime import datetime

            md_content = f"# MCP Tools - {self.server_name}\n\n"
            md_content += f"**Generated:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            md_content += f"**Total Tools:** {len(self.tools)}\n\n"

            # Table of contents
            md_content += "## Table of Contents\n\n"
            for i, tool in enumerate(self.tools, 1):
                tool_name = tool.get('name', 'unknown')
                md_content += f"{i}. [{tool_name}](#{tool_name.lower().replace('_', '-')})\n"

            md_content += "\n## Tool Details\n\n"

            # Tool details
            for i, tool in enumerate(self.tools, 1):
                tool_name = tool.get('name', 'Unknown')
                tool_desc = tool.get('description', 'No description')

                md_content += f"### {i}. {tool_name}\n\n"
                md_content += f"**Description:** {tool_desc}\n\n"

                input_schema = tool.get('inputSchema', {})
                properties = input_schema.get('properties', {})
                required = input_schema.get('required', [])

                if properties:
                    md_content += "**Parameters:**\n\n"
                    md_content += "| Parameter | Type | Required | Description |\n"
                    md_content += "|-----------|------|----------|-------------|\n"

                    for param_name, param_info in properties.items():
                        param_type = param_info.get('type', 'unknown')
                        param_desc = param_info.get('description', 'No description')
                        is_required = "Yes" if param_name in required else "No"

                        md_content += f"| `{param_name}` | {param_type} | {is_required} | {param_desc} |\n"

                    md_content += "\n"
                else:
                    md_content += "**Parameters:** None\n\n"

                md_content += "---\n\n"

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Tools exported to:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export tools:\n{str(e)}"
            )
