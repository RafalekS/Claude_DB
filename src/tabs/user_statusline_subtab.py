"""
User Statusline Sub-Tab - manage the user-level statusLine in ~/.claude/settings.json.

Claude Code's status line runs a shell command that reads a JSON blob on stdin
and prints the line to stdout. The setting is:

    "statusLine": { "type": "command", "command": "<script or inline>", "padding": 0 }

There is no template / {{variable}} mechanism — the script does the formatting.
"""

import json
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QGroupBox, QLineEdit, QFormLayout, QSpinBox,
    QComboBox,
)
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices

from utils import theme

logger = logging.getLogger(__name__)

# Ready-to-paste inline commands (need `jq` on PATH).
_EXAMPLES = {
    "Model + context %":
        "jq -r '\"[\\(.model.display_name)] \\(.context_window.used_percentage // 0 | floor)% ctx\"'",
    "Dir + git branch + cost":
        "jq -r '\"📁 \\(.workspace.current_dir | split(\"/\") | last)"
        "  \\(.workspace.git_worktree // \"\")  $\\(.cost.total_cost_usd // 0 | . * 100 | round / 100)\"'",
    "Model + dir + version":
        "jq -r '\"\\(.model.display_name) — \\(.workspace.current_dir) (v\\(.version))\"'",
}

_STDIN_FIELDS = (
    "model.id · model.display_name · cwd · workspace.current_dir · workspace.project_dir · "
    "workspace.added_dirs · workspace.git_worktree · workspace.repo.{host,owner,name} · "
    "cost.total_cost_usd · cost.total_duration_ms · cost.total_lines_added/removed · "
    "context_window.context_window_size · context_window.used_percentage · "
    "context_window.remaining_percentage · exceeds_200k_tokens · session_id · "
    "transcript_path · version · output_style.name"
)


class UserStatuslineSubTab(QWidget):
    """Editor for the user-level statusLine setting."""

    SCOPE_DESC = "~/.claude/settings.json"

    def __init__(self, config_manager, backup_manager, settings_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.settings_manager = settings_manager
        self.init_ui()
        self.load_statusline()

    # ── UI ───────────────────────────────────────────────────────────────────

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        header_layout = QHBoxLayout()
        header = QLabel("User Status Line")
        header.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};"
        )
        docs_btn = QPushButton("📖 Status Line Docs")
        docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://code.claude.com/docs/en/statusline")
        ))
        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(docs_btn)
        layout.addLayout(header_layout)

        self._path_label = QLabel(f"File: {self.config_manager.settings_file}")
        self._path_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(self._path_label)

        config_group = QGroupBox('statusLine  ("type": "command")')
        config_layout = QVBoxLayout(config_group)

        form = QFormLayout()
        form.setSpacing(8)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText(
            "script path (e.g. ~/.claude/statusline.sh) or an inline shell command"
        )
        form.addRow("command:", self.command_input)

        self.padding_input = QSpinBox()
        self.padding_input.setRange(0, 40)
        self.padding_input.setToolTip("Extra left indentation in characters (default 0)")
        form.addRow("padding:", self.padding_input)

        ex_row = QHBoxLayout()
        self.example_combo = QComboBox()
        self.example_combo.addItem("— insert an example inline command —")
        for name in _EXAMPLES:
            self.example_combo.addItem(name)
        insert_btn = QPushButton("Insert")
        insert_btn.clicked.connect(self._insert_example)
        ex_row.addWidget(self.example_combo, 1)
        ex_row.addWidget(insert_btn)
        form.addRow("examples:", ex_row)

        config_layout.addLayout(form)

        preview_label = QLabel("settings.json fragment:")
        preview_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY}; margin-top: 8px;")
        config_layout.addWidget(preview_label)

        self.json_preview = QTextEdit()
        self.json_preview.setReadOnly(True)
        self.json_preview.setMaximumHeight(130)
        self.json_preview.setStyleSheet(
            f"QTextEdit {{ font-family: {theme.FONT_FAMILY_MONO}; border-radius: 3px; padding: 5px; }}"
        )
        config_layout.addWidget(self.json_preview)

        self.command_input.textChanged.connect(self.update_preview)
        self.padding_input.valueChanged.connect(self.update_preview)

        layout.addWidget(config_group)

        btn_layout = QHBoxLayout()
        load_btn = QPushButton("📂 Reload")
        load_btn.clicked.connect(self.load_statusline)
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save_statusline)
        clear_btn = QPushButton("🗑️ Remove")
        clear_btn.clicked.connect(self.clear_statusline)
        btn_layout.addWidget(load_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)

        footer = QLabel(
            "💡 The command runs in a shell and gets a JSON blob on <b>stdin</b>; its stdout is the "
            "status line (first line only, unless it prints multiple lines). No <code>{{variables}}</code> — "
            "parse the JSON yourself (e.g. with <code>jq</code>).<br>"
            f"<b>stdin fields:</b> <code style='font-size:{theme.FONT_SIZE_SMALL}px'>{_STDIN_FIELDS}</code>"
        )
        footer.setWordWrap(True)
        footer.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px; padding: 8px; "
            f"background-color: {theme.BG_MEDIUM}; border-radius: 3px;"
        )
        layout.addWidget(footer)
        layout.addStretch()

    # ── behaviour ────────────────────────────────────────────────────────────

    def _insert_example(self):
        name = self.example_combo.currentText()
        if name in _EXAMPLES:
            self.command_input.setText(_EXAMPLES[name])

    def _build_config(self) -> dict:
        cfg = {"type": "command", "command": self.command_input.text().strip()}
        if self.padding_input.value():
            cfg["padding"] = self.padding_input.value()
        return cfg

    def update_preview(self):
        if not self.command_input.text().strip():
            self.json_preview.setPlainText("// no status line configured")
            return
        self.json_preview.setPlainText(json.dumps({"statusLine": self._build_config()}, indent=2))

    def load_statusline(self):
        self._path_label.setText(f"File: {self.config_manager.settings_file}")
        try:
            settings = self.config_manager.get_settings()
            sl = settings.get("statusLine", settings.get("statusline", {}))
            if isinstance(sl, str):
                self.command_input.setText(sl)
                self.padding_input.setValue(0)
            elif isinstance(sl, dict):
                self.command_input.setText(sl.get("command", ""))
                self.padding_input.setValue(int(sl.get("padding", 0) or 0))
            else:
                self.command_input.clear()
                self.padding_input.setValue(0)
            self.update_preview()
        except Exception as e:
            logger.error("Failed to load statusLine: %s", e)
            QMessageBox.critical(self, "Load Error", f"Failed to load statusLine:\n{e}")

    def save_statusline(self):
        if not self.command_input.text().strip():
            QMessageBox.warning(self, "Empty", "Enter a command before saving.")
            return
        try:
            settings = self.config_manager.get_settings()
            settings.pop("statusline", None)  # drop a wrong-case key if present
            settings["statusLine"] = self._build_config()
            self.config_manager.save_settings(settings)
            self.update_preview()
            QMessageBox.information(self, "Saved", "Status line saved.")
        except Exception as e:
            logger.error("Failed to save statusLine: %s", e)
            QMessageBox.critical(self, "Save Error", f"Failed to save statusLine:\n{e}")

    def clear_statusline(self):
        if QMessageBox.question(
            self, "Confirm", "Remove the statusLine setting?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            settings = self.config_manager.get_settings()
            settings.pop("statusLine", None)
            settings.pop("statusline", None)
            self.config_manager.save_settings(settings)
            self.command_input.clear()
            self.padding_input.setValue(0)
            self.update_preview()
            QMessageBox.information(self, "Removed", "Status line removed.")
        except Exception as e:
            logger.error("Failed to clear statusLine: %s", e)
            QMessageBox.critical(self, "Clear Error", f"Failed to clear statusLine:\n{e}")
