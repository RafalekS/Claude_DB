"""Bulk Command Add Dialog"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QTextEdit
)
from pathlib import Path
import sys
import re
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.theme import *
from utils.template_manager import get_template_manager


class BulkCommandAddDialog(QDialog):
    """Dialog for bulk adding command templates"""

    def __init__(self, templates_dir, parent=None):
        super().__init__(parent)
        self.templates_dir = templates_dir
        self.template_mgr = get_template_manager()
        self.setWindowTitle("Bulk Add Commands")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("Bulk Add Commands to Template Library")
        header.setStyleSheet(f"font-weight: bold; color: {FG_PRIMARY}; font-size: {FONT_SIZE_LARGE}px;")
        layout.addWidget(header)

        instructions = QLabel(
            "Paste command template files (full markdown content):\n\n"
            "Separate multiple commands with:\n"
            "<b>---COMMAND---</b> on its own line\n\n"
            "Commands are simple markdown files (no YAML frontmatter required). Filenames will be used as command names."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet(f"color: {FG_SECONDARY}; background: {BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {FONT_SIZE_SMALL}px;")
        layout.addWidget(instructions)

        input_label = QLabel("Paste command template(s):")
        input_label.setStyleSheet(f"font-weight: bold; color: {FG_PRIMARY};")
        layout.addWidget(input_label)

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText(
            "example-command.md:\n# Example Command\nCommand description...\n\n---COMMAND---\n\nanother-command.md:\n# Another Command\n..."
        )
        self.input_text.setStyleSheet(get_text_edit_style())
        layout.addWidget(self.input_text)

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

        preview_label = QLabel("Preview (will create these template files):")
        preview_label.setStyleSheet(f"font-weight: bold; color: {FG_PRIMARY};")
        layout.addWidget(preview_label)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet(get_text_edit_style())
        layout.addWidget(self.preview_text)

    def parse_and_preview(self):
        input_text = self.input_text.toPlainText().strip()
        if not input_text:
            QMessageBox.warning(self, "Empty Input", "Please paste command template(s) first.")
            return

        try:
            # Split by ---COMMAND--- separator
            command_texts = input_text.split('---COMMAND---')
            self.parsed_commands = []
            preview_lines = []

            for idx, command_text in enumerate(command_texts, 1):
                command_text = command_text.strip()
                if not command_text:
                    continue

                # Try to extract name from first line if it looks like "filename.md:"
                name_match = re.match(r'^(.+?)\.md:\s*\n', command_text, re.MULTILINE)
                if name_match:
                    name = name_match.group(1).strip()
                    # Remove the filename line from content
                    content = command_text[len(name_match.group(0)):]
                else:
                    # Use generic name
                    name = f"command-{idx}"
                    content = command_text

                self.parsed_commands.append((name, content.strip()))
                preview_lines.append(f"✓ {name}.md")

            if not self.parsed_commands:
                QMessageBox.warning(self, "Parse Error", "No valid commands found.")
                return

            preview = f"Found {len(self.parsed_commands)} command(s):\n\n" + "\n".join(preview_lines)
            self.preview_text.setPlainText(preview)

        except Exception as e:
            QMessageBox.critical(self, "Parse Error", f"Failed to parse input:\n{str(e)}")

    def save_to_library(self):
        if not hasattr(self, 'parsed_commands') or not self.parsed_commands:
            QMessageBox.warning(self, "No Data", "Please parse commands first using 'Parse & Preview'.")
            return

        try:
            added = 0
            skipped = 0

            for name, content in self.parsed_commands:
                existing_templates = self.template_mgr.list_templates('commands')
                if name in existing_templates:
                    skipped += 1
                    continue

                self.template_mgr.save_template('commands', name, content)
                added += 1

            msg = f"Added {added} command template(s) to library."
            if skipped > 0:
                msg += f"\nSkipped {skipped} (already exist)"

            QMessageBox.information(self, "Success", msg)
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save commands:\n{str(e)}")
