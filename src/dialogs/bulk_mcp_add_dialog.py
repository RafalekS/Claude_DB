"""Bulk MCP Add Dialog"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QTextEdit
)
from pathlib import Path
import sys
import json
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme
from utils.template_manager import get_template_manager


class BulkMCPAddDialog(QDialog):
    """Dialog for bulk adding MCP server templates"""

    def __init__(self, templates_dir, parent=None):
        super().__init__(parent)
        self.templates_dir = templates_dir
        self.template_mgr = get_template_manager()
        self.setWindowTitle("Bulk Add MCP Servers")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("Bulk Add MCP Servers to Template Library")
        header.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY}; font-size: {theme.FONT_SIZE_LARGE}px;")
        layout.addWidget(header)

        instructions = QLabel(
            "Paste MCP server JSON configurations:\n\n"
            "<b>Format 1 - Full MCP config:</b>\n"
            '{"mcpServers": {"server-name": {"command": "npx", "args": [...], "env": {...}}}}\n\n'
            "<b>Format 2 - Single key-value pair:</b>\n"
            '"server-name": {"command": "npx", "args": [...], "env": {...}}\n\n'
            "<b>Format 3 - Individual servers (one per line or separated by ---MCP---):</b>\n"
            'server-name.json:\n{"command": "npx", "args": [...], "env": {...}}'
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet(f"color: {theme.FG_SECONDARY}; background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(instructions)

        input_label = QLabel("Paste MCP server configuration(s):")
        input_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY};")
        layout.addWidget(input_label)

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText(
            '{"mcpServers": {"github": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]}}}'
        )
        self.input_text.setStyleSheet(theme.get_text_edit_style())
        layout.addWidget(self.input_text)

        button_layout = QHBoxLayout()

        parse_btn = QPushButton("🔄 Parse & Preview")
        parse_btn.setStyleSheet(theme.get_button_style())
        parse_btn.clicked.connect(self.parse_and_preview)
        button_layout.addWidget(parse_btn)

        button_layout.addStretch()

        save_btn = QPushButton("💾 Save to Library")
        save_btn.setStyleSheet(theme.get_button_style())
        save_btn.clicked.connect(self.save_to_library)
        button_layout.addWidget(save_btn)

        close_btn = QPushButton("✗ Close")
        close_btn.setStyleSheet(theme.get_button_style())
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        preview_label = QLabel("Preview (will create these template files):")
        preview_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY};")
        layout.addWidget(preview_label)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet(theme.get_text_edit_style())
        layout.addWidget(self.preview_text)

    def preprocess_json_text(self, text):
        """Preprocess JSON text to fix common issues like unescaped backslashes in Windows paths"""
        import re

        # Fix missing quote after key name (e.g., "PLEX_USERNAME:"value" -> "PLEX_USERNAME":"value")
        # Pattern: "KEY:" where KEY has no quote or colon, followed by another quote
        text = re.sub(r'"([^":]+):"', r'"\1":"', text)

        # Fix brace imbalance
        text = self.fix_brace_balance(text)

        # Strategy: Find all quoted strings containing backslashes and escape them
        # This handles both "key":"value" pairs and array values ["item"]

        def escape_string_backslashes(match):
            """Escape backslashes in any quoted string"""
            content = match.group(1)
            # Escape backslashes (but don't double-escape already escaped ones)
            if '\\\\' not in content:  # Only if not already escaped
                content = content.replace('\\', '\\\\')
            return f'"{content}"'

        # Pattern to match any quoted string containing backslash
        # Matches "anything\with\backslashes"
        pattern = r'"([^"]*\\[^"]*)"'
        text = re.sub(pattern, escape_string_backslashes, text)

        return text

    def fix_brace_balance(self, text):
        """Attempt to fix unbalanced braces in JSON"""
        # Count braces (ignoring braces inside quoted strings)
        in_quotes = False
        escape_next = False
        open_count = 0
        close_count = 0

        for char in text:
            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"':
                in_quotes = not in_quotes
                continue

            if not in_quotes:
                if char == '{':
                    open_count += 1
                elif char == '}':
                    close_count += 1

        # Fix imbalance
        if open_count > close_count:
            # Missing closing braces - add at end
            text = text.rstrip() + ('}' * (open_count - close_count))
        elif close_count > open_count:
            # Extra closing braces - remove from end
            diff = close_count - open_count
            # Remove extra } from the end
            stripped = text.rstrip()
            while diff > 0 and stripped.endswith('}'):
                stripped = stripped[:-1].rstrip()
                diff -= 1
            text = stripped

        return text

    def auto_wrap_npx(self, config):
        """Auto-wrap npx commands with cmd /c for Windows compatibility"""
        if isinstance(config, dict) and "command" in config:
            command = config["command"]
            args = config.get("args", [])

            # Check if command is npx without wrapper
            if command == "npx":
                # Wrap with cmd /c
                config["command"] = "cmd"
                config["args"] = ["/c", "npx"] + args
                return True  # Wrapped

            # Check if already wrapped with cmd /k, convert to /c
            if command == "cmd" and len(args) >= 2 and args[0] == "/k" and args[1] == "npx":
                # Convert /k to /c
                config["args"] = ["/c"] + args[1:]
                return True  # Converted

        return False  # No changes

    def parse_and_preview(self):
        input_text = self.input_text.toPlainText().strip()
        if not input_text:
            QMessageBox.warning(self, "Empty Input", "Please paste MCP server configuration(s) first.")
            return

        try:
            self.parsed_mcps = {}
            preview_lines = []

            # Preprocess to fix common JSON issues
            input_text = self.preprocess_json_text(input_text)

            # Try parsing as full MCP config first
            try:
                data = json.loads(input_text)
                if "mcpServers" in data:
                    # Full config format
                    for name, config in data["mcpServers"].items():
                        # Auto-wrap npx commands
                        wrapped = self.auto_wrap_npx(config)
                        self.parsed_mcps[name] = json.dumps(config, indent=2)
                        preview_lines.append(f"✓ {name}.json" + (" (npx wrapped)" if wrapped else ""))
                else:
                    # Check if it's a single server with name as key (e.g., {"plex": {...}})
                    if isinstance(data, dict) and len(data) == 1:
                        server_name = list(data.keys())[0]
                        server_config = data[server_name]

                        # Special case: if the key is "mcpServers", extract servers from inside
                        if server_name.lower() == "mcpservers" and isinstance(server_config, dict):
                            # This is a wrapped format, extract all servers
                            for name, config in server_config.items():
                                wrapped = self.auto_wrap_npx(config)
                                self.parsed_mcps[name] = json.dumps(config, indent=2)
                                preview_lines.append(f"✓ {name}.json" + (" (npx wrapped)" if wrapped else ""))
                        # Check if the value looks like a server config (has command/args/env/url/type)
                        elif isinstance(server_config, dict) and any(k in server_config for k in ['command', 'args', 'env', 'url', 'type']):
                            # This is a named server config
                            wrapped = self.auto_wrap_npx(server_config)
                            self.parsed_mcps[server_name] = json.dumps(server_config, indent=2)
                            preview_lines.append(f"✓ {server_name}.json" + (" (npx wrapped)" if wrapped else ""))
                        else:
                            # Not a server config, treat whole thing as single server
                            wrapped = self.auto_wrap_npx(data)
                            self.parsed_mcps["mcp-server"] = json.dumps(data, indent=2)
                            preview_lines.append(f"✓ mcp-server.json" + (" (npx wrapped)" if wrapped else ""))
                    else:
                        # Single server object without name - use generic name
                        wrapped = self.auto_wrap_npx(data)
                        self.parsed_mcps["mcp-server"] = json.dumps(data, indent=2)
                        preview_lines.append(f"✓ mcp-server.json" + (" (npx wrapped)" if wrapped else ""))

            except json.JSONDecodeError:
                # Try wrapping with braces (handles single key-value pair format like "name": {...})
                wrapped_text = "{" + input_text.strip() + "}"
                try:
                    data = json.loads(wrapped_text)
                    # This is a single server in key-value format
                    if isinstance(data, dict) and len(data) == 1:
                        server_name = list(data.keys())[0]
                        server_config = data[server_name]
                        # Auto-wrap npx commands
                        wrapped = self.auto_wrap_npx(server_config)
                        self.parsed_mcps[server_name] = json.dumps(server_config, indent=2)
                        preview_lines.append(f"✓ {server_name}.json" + (" (npx wrapped)" if wrapped else ""))
                    else:
                        # Multiple keys - treat each as a separate server
                        for name, config in data.items():
                            # Auto-wrap npx commands
                            wrapped = self.auto_wrap_npx(config)
                            self.parsed_mcps[name] = json.dumps(config, indent=2)
                            preview_lines.append(f"✓ {name}.json" + (" (npx wrapped)" if wrapped else ""))
                except json.JSONDecodeError:
                    # Try splitting by ---MCP--- separator
                    mcp_texts = input_text.split('---MCP---')

                    for idx, mcp_text in enumerate(mcp_texts, 1):
                        mcp_text = mcp_text.strip()
                        if not mcp_text:
                            continue

                        # Try to extract name from "filename.json:" prefix
                        import re
                        name_match = re.match(r'^(.+?)\.json:\s*\n', mcp_text, re.MULTILINE)
                        if name_match:
                            name = name_match.group(1).strip()
                            json_text = mcp_text[len(name_match.group(0)):]
                        else:
                            name = f"mcp-server-{idx}"
                            json_text = mcp_text

                        # Validate JSON and auto-wrap npx
                        config = json.loads(json_text)
                        wrapped = self.auto_wrap_npx(config)
                        self.parsed_mcps[name] = json.dumps(config, indent=2)
                        preview_lines.append(f"✓ {name}.json" + (" (npx wrapped)" if wrapped else ""))

            if not self.parsed_mcps:
                QMessageBox.warning(self, "Parse Error", "No valid MCP servers found.")
                return

            preview = f"Found {len(self.parsed_mcps)} MCP server(s):\n\n" + "\n".join(preview_lines)
            self.preview_text.setPlainText(preview)

        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "JSON Error", f"Invalid JSON:\n{str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Parse Error", f"Failed to parse input:\n{str(e)}")

    def save_to_library(self):
        if not hasattr(self, 'parsed_mcps') or not self.parsed_mcps:
            QMessageBox.warning(self, "No Data", "Please parse MCP servers first using 'Parse & Preview'.")
            return

        try:
            added = 0
            skipped = 0

            for name, content in self.parsed_mcps.items():
                existing_templates = self.template_mgr.list_templates('mcp')
                if name in existing_templates:
                    skipped += 1
                    continue

                self.template_mgr.save_template('mcp', name, content)
                added += 1

            msg = f"Added {added} MCP server template(s) to library."
            if skipped > 0:
                msg += f"\nSkipped {skipped} (already exist)"

            QMessageBox.information(self, "Success", msg)
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save MCP servers:\n{str(e)}")
