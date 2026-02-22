"""Bulk Skill Add Dialog"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QTextEdit
)
from pathlib import Path
import sys
import re
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme
from utils.template_manager import get_template_manager


class BulkSkillAddDialog(QDialog):
    """Dialog for bulk adding skill templates"""

    def __init__(self, templates_dir, parent=None):
        super().__init__(parent)
        self.templates_dir = templates_dir
        self.template_mgr = get_template_manager()
        self.setWindowTitle("Bulk Add Skills")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("Bulk Add Skills to Template Library")
        header.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY}; font-size: {theme.FONT_SIZE_LARGE}px;")
        layout.addWidget(header)

        instructions = QLabel(
            "Paste skill template files (full markdown content with YAML frontmatter):\n\n"
            "Separate multiple skills with:\n"
            "<b>---SKILL---</b> on its own line\n\n"
            "Each skill should include YAML frontmatter with 'name:' field."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet(f"color: {theme.FG_SECONDARY}; background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(instructions)

        input_label = QLabel("Paste skill template(s):")
        input_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY};")
        layout.addWidget(input_label)

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText(
            "---\nname: example-skill\ndescription: Example skill\n---\n\n# Example Skill\n...\n\n---SKILL---\n\n---\nname: another-skill\n..."
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

    def parse_and_preview(self):
        input_text = self.input_text.toPlainText().strip()
        if not input_text:
            QMessageBox.warning(self, "Empty Input", "Please paste skill template(s) first.")
            return

        try:
            skill_texts = input_text.split('---SKILL---')
            self.parsed_skills = []
            preview_lines = []

            for skill_text in skill_texts:
                skill_text = skill_text.strip()
                if not skill_text:
                    continue

                name_match = re.search(r'^name:\s*(.+?)$', skill_text, re.MULTILINE)
                if name_match:
                    name = name_match.group(1).strip()
                    self.parsed_skills.append((name, skill_text))
                    preview_lines.append(f"✓ {name}.md")
                else:
                    preview_lines.append(f"✗ Skipped (no 'name:' in frontmatter)")

            if not self.parsed_skills:
                QMessageBox.warning(self, "Parse Error", "No valid skills found. Make sure each skill has 'name:' in YAML frontmatter.")
                return

            preview = f"Found {len(self.parsed_skills)} skill(s):\n\n" + "\n".join(preview_lines)
            self.preview_text.setPlainText(preview)

        except Exception as e:
            QMessageBox.critical(self, "Parse Error", f"Failed to parse input:\n{str(e)}")

    def save_to_library(self):
        if not hasattr(self, 'parsed_skills') or not self.parsed_skills:
            QMessageBox.warning(self, "No Data", "Please parse skills first using 'Parse & Preview'.")
            return

        try:
            added = 0
            skipped = 0

            for name, content in self.parsed_skills:
                existing_templates = self.template_mgr.list_templates('skills')
                if name in existing_templates:
                    skipped += 1
                    continue

                self.template_mgr.save_template('skills', name, content)
                added += 1

            msg = f"Added {added} skill template(s) to library."
            if skipped > 0:
                msg += f"\nSkipped {skipped} (already exist)"

            QMessageBox.information(self, "Success", msg)
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save skills:\n{str(e)}")
