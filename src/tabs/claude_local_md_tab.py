"""
CLAUDE.local.md Tab - Edit the local (gitignored) CLAUDE.md override file
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QMessageBox
)
from utils import theme


class ClaudeLocalMDTab(QWidget):
    """Tab for editing CLAUDE.local.md — the gitignored local instructions override"""

    def __init__(self, config_manager, backup_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.init_ui()
        self.load_content()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # Header row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        self.file_label = QLabel(str(self.config_manager.claude_local_md))
        self.file_label.setStyleSheet(f"color: {theme.FG_DIM}; font-size: {theme.FONT_SIZE_SMALL}px;")

        self.save_btn = QPushButton("Save")
        self.save_btn.setToolTip("Save CLAUDE.local.md to file (creates it if missing)")
        self.backup_save_btn = QPushButton("Backup & Save")
        self.backup_save_btn.setToolTip("Create timestamped backup before saving")
        self.revert_btn = QPushButton("Revert")
        self.revert_btn.setToolTip("Reload from disk (discards unsaved changes)")
        self.delete_btn = QPushButton("Delete File")
        self.delete_btn.setToolTip("Delete CLAUDE.local.md from disk")
        self.delete_btn.setStyleSheet(theme.get_button_danger_style())

        for btn in [self.save_btn, self.backup_save_btn, self.revert_btn]:
            btn.setStyleSheet(theme.get_button_style())

        self.save_btn.clicked.connect(self.save_content)
        self.backup_save_btn.clicked.connect(self.backup_and_save)
        self.revert_btn.clicked.connect(self.load_content)
        self.delete_btn.clicked.connect(self.delete_file)

        header_layout.addWidget(self.file_label)
        header_layout.addStretch()
        header_layout.addWidget(self.save_btn)
        header_layout.addWidget(self.backup_save_btn)
        header_layout.addWidget(self.revert_btn)
        header_layout.addWidget(self.delete_btn)
        layout.addLayout(header_layout)

        # Status bar
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet(f"""
            background-color: {theme.BG_MEDIUM};
            color: {theme.FG_SECONDARY};
            padding: 6px 8px;
            border: 1px solid {theme.BG_LIGHT};
            border-radius: 3px;
            font-size: {theme.FONT_SIZE_SMALL}px;
        """)
        layout.addWidget(self.stats_label)

        # Editor
        self.editor = QTextEdit()
        self.editor.setStyleSheet(theme.get_text_edit_style())
        self.editor.textChanged.connect(self._update_stats)
        layout.addWidget(self.editor, 1)

        # Info footer
        tip_label = QLabel(
            "💡 <b>CLAUDE.local.md</b> is loaded after CLAUDE.md and overrides or extends it. "
            "It is <b>gitignored by default</b> — use it for personal instructions, local paths, "
            "machine-specific config, or anything you don't want in the shared repository. "
            "Claude Code loads both files; local settings take precedence where they conflict."
        )
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; background: {theme.BG_MEDIUM}; "
            f"padding: 8px; border-radius: 3px; font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(tip_label)

    def _update_stats(self):
        content = self.editor.toPlainText()
        chars = len(content)
        lines = content.count('\n') + 1 if content else 0
        words = len(content.split()) if content else 0
        tokens = chars // 4

        exists = self.config_manager.claude_local_md.exists()
        file_info = ""
        if exists:
            size = self.config_manager.claude_local_md.stat().st_size
            file_info = f" • File: {size:,} B"
        else:
            file_info = " • File: not yet created"

        self.stats_label.setText(
            f"📊 Characters: {chars:,} • Words: {words:,} • "
            f"Lines: {lines:,} • Tokens: ~{tokens:,}{file_info}"
        )

    def load_content(self):
        try:
            content = self.config_manager.get_claude_local_md()
            self.editor.setPlainText(content)
            self._update_stats()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CLAUDE.local.md:\n{e}")

    def save_content(self):
        try:
            self.config_manager.save_claude_local_md(self.editor.toPlainText())
            self._update_stats()
            QMessageBox.information(self, "Saved", "CLAUDE.local.md saved.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")

    def backup_and_save(self):
        try:
            if self.config_manager.claude_local_md.exists():
                self.backup_manager.create_file_backup(self.config_manager.claude_local_md)
            self.config_manager.save_claude_local_md(self.editor.toPlainText())
            self._update_stats()
            QMessageBox.information(self, "Saved", "Backup created and CLAUDE.local.md saved.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed:\n{e}")

    def delete_file(self):
        if not self.config_manager.claude_local_md.exists():
            QMessageBox.information(self, "Not Found", "CLAUDE.local.md does not exist.")
            return
        reply = QMessageBox.question(
            self, "Delete CLAUDE.local.md",
            "Delete CLAUDE.local.md from disk? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.config_manager.claude_local_md.unlink()
                self.editor.clear()
                self._update_stats()
                QMessageBox.information(self, "Deleted", "CLAUDE.local.md deleted.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete:\n{e}")
