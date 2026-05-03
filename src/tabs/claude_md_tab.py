"""
CLAUDE.md Tab - Editor for ~/.claude/CLAUDE.md (User memory / instructions for all projects)
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from utils import theme
import logging
logger = logging.getLogger(__name__)


class ClaudeMDTab(QWidget):
    """Subtab editor for ~/.claude/CLAUDE.md"""

    def __init__(self, config_manager, backup_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self._modified = False
        self.init_ui()
        self.load_content()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # ── Title row ────────────────────────────────────────────────────
        title_layout = QHBoxLayout()

        title = QLabel("Edit CLAUDE.md  —  User Instructions for All Projects")
        title.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};"
        )
        title_layout.addWidget(title)
        title_layout.addStretch()

        # Unsaved-changes indicator (hidden by default)
        self.unsaved_label = QLabel("● UNSAVED CHANGES")
        self.unsaved_label.setStyleSheet(
            f"color: {theme.WARNING_COLOR}; font-weight: bold; font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        self.unsaved_label.setVisible(False)
        title_layout.addWidget(self.unsaved_label)

        layout.addLayout(title_layout)

        # ── File path ────────────────────────────────────────────────────
        self.file_label = QLabel()
        self.file_label.setStyleSheet(
            f"color: {theme.FG_DIM}; font-size: {theme.FONT_SIZE_SMALL}px; font-family: {theme.FONT_FAMILY_MONO};"
        )
        layout.addWidget(self.file_label)

        # ── Action buttons ───────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        self.save_btn = QPushButton("💾 Save")
        self.save_btn.setToolTip("Save CLAUDE.md  (Ctrl+S)")
        self.save_btn.setMinimumWidth(90)
        self.save_btn.clicked.connect(self.save_content)

        self.backup_save_btn = QPushButton("🗂 Backup & Save")
        self.backup_save_btn.setToolTip("Create a timestamped backup, then save")
        self.backup_save_btn.setMinimumWidth(130)
        self.backup_save_btn.clicked.connect(self.backup_and_save)

        self.revert_btn = QPushButton("↩ Revert")
        self.revert_btn.setToolTip("Reload from file — discards unsaved changes")
        self.revert_btn.setMinimumWidth(90)
        self.revert_btn.clicked.connect(self.load_content)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.backup_save_btn)
        btn_layout.addWidget(self.revert_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # ── Statistics bar ───────────────────────────────────────────────
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet(
            f"padding: 4px 6px; border-radius: 3px; font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(self.stats_label)

        # ── Separator ────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        # ── Editor ───────────────────────────────────────────────────────
        self.editor = QTextEdit()
        self.editor.setPlaceholderText(
            "# CLAUDE.md\n\n"
            "Write instructions here that Claude will follow in every session.\n"
            "Example:\n"
            "  - Always use 2-space indentation\n"
            "  - Run 'npm test' before committing\n"
            "  - Keep functions under 50 lines\n"
        )
        self.editor.setStyleSheet(
            f"QTextEdit {{ font-family: {theme.FONT_FAMILY_MONO}; font-size: {theme.FONT_SIZE_NORMAL}px; }}"
        )
        self.editor.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.editor, 1)

        # ── Tip bar ──────────────────────────────────────────────────────
        tip_label = QLabel(
            "💡 <b>Tips:</b> "
            "Keep under 200 lines for best adherence · "
            "Use # in Claude Code conversations to auto-add instructions · "
            "Use /memory in Claude Code to view active instructions · "
            "Path-scoped rules go in .claude/rules/*.md"
        )
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; padding: 6px; border-radius: 3px; font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(tip_label)

    # ── Internal helpers ──────────────────────────────────────────────────

    def _on_text_changed(self):
        """Mark as modified and update stats."""
        if not self._modified:
            self._modified = True
            self.unsaved_label.setVisible(True)
        self._update_statistics()

    def _update_statistics(self):
        """Refresh the statistics bar."""
        content = self.editor.toPlainText()
        char_count = len(content)
        line_count = content.count('\n') + 1 if content else 0
        word_count = len(content.split()) if content else 0
        estimated_tokens = char_count // 4

        file_size = "N/A"
        claude_md = self.config_manager.claude_md
        if isinstance(claude_md, Path) and claude_md.exists():
            size_bytes = claude_md.stat().st_size
            if size_bytes < 1024:
                file_size = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                file_size = f"{size_bytes / 1024:.1f} KB"
            else:
                file_size = f"{size_bytes / (1024 * 1024):.1f} MB"

        color = theme.WARNING_COLOR if line_count > 200 else theme.FG_SECONDARY
        self.stats_label.setText(
            f"<span style='color:{color}'>"
            f"Lines: {line_count:,}"
            f"{'  ⚠ &gt;200 lines may reduce adherence' if line_count > 200 else ''}"
            f"</span>  "
            f"Words: {word_count:,}  •  "
            f"Chars: {char_count:,}  •  "
            f"~{estimated_tokens:,} tokens  •  "
            f"File: {file_size}"
        )

    # ── Public methods ────────────────────────────────────────────────────

    def load_content(self):
        """Load CLAUDE.md content from disk."""
        self.file_label.setText(f"File: {self.config_manager.claude_md}")
        try:
            content = self.config_manager.get_claude_md()
            self.editor.blockSignals(True)
            self.editor.setPlainText(content)
            self.editor.blockSignals(False)
            self._modified = False
            self.unsaved_label.setVisible(False)
            self._update_statistics()
        except Exception as e:
            logger.error("Failed to load CLAUDE.md: %s", e)
            QMessageBox.critical(self, "Load Error", f"Failed to load CLAUDE.md:\n{str(e)}")

    def save_content(self):
        """Save CLAUDE.md to disk."""
        try:
            content = self.editor.toPlainText()
            self.config_manager.save_claude_md(content)
            self._modified = False
            self.unsaved_label.setVisible(False)
            self._update_statistics()
            QMessageBox.information(self, "Saved", "CLAUDE.md saved successfully!")
        except Exception as e:
            logger.error("Failed to save CLAUDE.md: %s", e)
            QMessageBox.critical(self, "Save Error", f"Failed to save CLAUDE.md:\n{str(e)}")

    def backup_and_save(self):
        """Create a backup then save."""
        try:
            cm = self.config_manager.claude_md
            if isinstance(cm, Path) and cm.exists():
                self.backup_manager.create_file_backup(cm)
            content = self.editor.toPlainText()
            self.config_manager.save_claude_md(content)
            self._modified = False
            self.unsaved_label.setVisible(False)
            self._update_statistics()
            QMessageBox.information(self, "Saved", "Backup created and CLAUDE.md saved!")
        except Exception as e:
            logger.error("Failed to backup and save CLAUDE.md: %s", e)
            QMessageBox.critical(self, "Error", f"Failed:\n{str(e)}")
