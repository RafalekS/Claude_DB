"""
CLAUDE.md Tab - Edit the CLAUDE.md file
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QMessageBox
)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.theme import *


class ClaudeMDTab(QWidget):
    """Tab for editing CLAUDE.md"""

    def __init__(self, config_manager, backup_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.init_ui()
        self.load_content()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # Header with buttons
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        self.file_label = QLabel(f"{self.config_manager.claude_md}")
        self.file_label.setStyleSheet(f"color: {FG_DIM}; font-size: {FONT_SIZE_SMALL}px;")

        self.save_btn = QPushButton("Save")
        self.save_btn.setToolTip("Save CLAUDE.md to file")
        self.backup_save_btn = QPushButton("Backup & Save")
        self.backup_save_btn.setToolTip("Create timestamped backup before saving CLAUDE.md")
        self.revert_btn = QPushButton("Revert")
        self.revert_btn.setToolTip("Reload CLAUDE.md from file (discards unsaved changes)")

        for btn in [self.save_btn, self.backup_save_btn, self.revert_btn]:
            btn.setStyleSheet(get_button_style())

        self.save_btn.clicked.connect(self.save_content)
        self.backup_save_btn.clicked.connect(self.backup_and_save)
        self.revert_btn.clicked.connect(self.load_content)

        header_layout.addWidget(self.file_label)
        header_layout.addStretch()
        header_layout.addWidget(self.save_btn)
        header_layout.addWidget(self.backup_save_btn)
        header_layout.addWidget(self.revert_btn)

        layout.addLayout(header_layout)

        # Statistics panel
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet(f"""
            background-color: {BG_MEDIUM};
            color: {FG_SECONDARY};
            padding: 8px;
            border: 1px solid {BG_LIGHT};
            border-radius: 3px;
            font-size: {FONT_SIZE_SMALL}px;
        """)
        layout.addWidget(self.stats_label)

        # Editor - FILLS ALL SPACE
        self.editor = QTextEdit()
        self.editor.setStyleSheet(get_text_edit_style())
        self.editor.textChanged.connect(self.update_statistics)  # Update stats on text change
        layout.addWidget(self.editor, 1)  # Stretch factor

        # Best Practices Tip
        tip_label = QLabel(
            "💡 <b>CLAUDE.md Best Practices:</b> "
            "Keep concise and human-readable • "
            "Refine iteratively like any prompt • "
            "Add emphasis keywords (IMPORTANT, YOU MUST) • "
            "Use # key in conversations to auto-add instructions • "
            "Document custom tools, code style, and project-specific warnings"
        )
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet(f"color: {FG_SECONDARY}; background: {BG_MEDIUM}; padding: 8px; border-radius: 3px; font-size: {FONT_SIZE_SMALL}px;")
        layout.addWidget(tip_label)

    def update_statistics(self):
        """Update statistics display"""
        content = self.editor.toPlainText()

        # Calculate statistics
        char_count = len(content)
        line_count = content.count('\n') + 1 if content else 0
        word_count = len(content.split()) if content else 0

        # Estimate token count (rough approximation: ~4 chars per token for English)
        # This is a heuristic - actual tokenization varies by model
        estimated_tokens = char_count // 4

        # Get file size if it exists
        file_size = "N/A"
        if self.config_manager.claude_md.exists():
            size_bytes = self.config_manager.claude_md.stat().st_size
            if size_bytes < 1024:
                file_size = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                file_size = f"{size_bytes / 1024:.1f} KB"
            else:
                file_size = f"{size_bytes / (1024 * 1024):.1f} MB"

        # Format statistics display
        stats_text = (
            f"📊 <b>Statistics:</b> "
            f"Characters: {char_count:,} • "
            f"Words: {word_count:,} • "
            f"Lines: {line_count:,} • "
            f"Estimated Tokens: ~{estimated_tokens:,} • "
            f"File Size: {file_size}"
        )

        self.stats_label.setText(stats_text)

    def load_content(self):
        """Load CLAUDE.md content"""
        try:
            content = self.config_manager.get_claude_md()
            self.editor.setPlainText(content)
            self.update_statistics()  # Update stats after loading
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CLAUDE.md:\n{str(e)}")

    def save_content(self):
        """Save CLAUDE.md content"""
        try:
            content = self.editor.toPlainText()
            self.config_manager.save_claude_md(content)
            QMessageBox.information(self, "Saved", "CLAUDE.md saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save:\n{str(e)}")

    def backup_and_save(self):
        """Backup and save"""
        try:
            self.backup_manager.create_file_backup(self.config_manager.claude_md)
            content = self.editor.toPlainText()
            self.config_manager.save_claude_md(content)
            QMessageBox.information(self, "Saved", "Backup created and CLAUDE.md saved!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed:\n{str(e)}")
