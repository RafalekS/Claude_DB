"""
Rules Tab - Manage Claude Code rules files in ~/.claude/rules/ and .claude/rules/
Rules are markdown files with optional YAML frontmatter that provide path-scoped instructions.
"""

import re
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QMessageBox, QListWidget, QSplitter, QListWidgetItem,
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QComboBox,
    QInputDialog, QTabWidget
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

from utils import theme


_FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)


def _parse_frontmatter(content: str) -> dict:
    """Extract frontmatter keys from a rule file."""
    m = _FRONTMATTER_RE.match(content)
    if not m:
        return {}
    result = {}
    for line in m.group(1).splitlines():
        if ':' in line:
            k, _, v = line.partition(':')
            result[k.strip()] = v.strip().strip('"').strip("'")
    return result


def _strip_frontmatter(content: str) -> str:
    """Return body text after frontmatter."""
    m = _FRONTMATTER_RE.match(content)
    return content[m.end():] if m else content


class NewRuleDialog(QDialog):
    """Dialog for creating a new rule file."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Rule")
        self.setMinimumWidth(460)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(8)
        lbl = f"color: {theme.FG_PRIMARY}; font-weight: bold;"

        name_lbl = QLabel("File name:")
        name_lbl.setStyleSheet(lbl)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. coding-style  (saved as coding-style.md)")
        self.name_edit.setStyleSheet(theme.get_input_style() if hasattr(theme, 'get_input_style') else "")
        form.addRow(name_lbl, self.name_edit)

        desc_lbl = QLabel("Description:")
        desc_lbl.setStyleSheet(lbl)
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("One-line summary shown in info panel")
        form.addRow(desc_lbl, self.desc_edit)

        paths_lbl = QLabel("Paths (optional):")
        paths_lbl.setStyleSheet(lbl)
        self.paths_edit = QLineEdit()
        self.paths_edit.setPlaceholderText("e.g. src/**, tests/** (comma-separated globs)")
        self.paths_edit.setToolTip(
            "If set, this rule only applies when Claude is working inside matching paths.\n"
            "Leave empty for a global rule."
        )
        form.addRow(paths_lbl, self.paths_edit)

        layout.addLayout(form)

        # Info
        info = QLabel(
            "Rules are markdown files with optional YAML frontmatter.\n"
            "Use the <b>paths</b> field to scope a rule to specific directories."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(info)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self) -> dict:
        name = self.name_edit.text().strip().removesuffix(".md")
        desc = self.desc_edit.text().strip()
        paths_text = self.paths_edit.text().strip()
        paths = [p.strip() for p in paths_text.split(",") if p.strip()] if paths_text else []
        return {"name": name, "description": desc, "paths": paths}


class RuleEditorWidget(QWidget):
    """Editor panel for a single scope (user or project)."""

    def __init__(self, scope: str, rules_dir_fn, parent=None):
        super().__init__(parent)
        self._scope = scope
        self._get_rules_dir = rules_dir_fn
        self._current_path: Path | None = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Left: file list ──────────────────────────────────────────────────
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(4)

        dir_lbl = QLabel("Rules directory:")
        dir_lbl.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        left_layout.addWidget(dir_lbl)

        self._dir_label = QLabel("(no directory)")
        self._dir_label.setStyleSheet(
            f"color: {theme.ACCENT_PRIMARY}; font-size: {theme.FONT_SIZE_SMALL}px; "
            f"font-family: 'Consolas', monospace;"
        )
        self._dir_label.setWordWrap(True)
        left_layout.addWidget(self._dir_label)

        list_lbl = QLabel("Rule files:")
        list_lbl.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY};")
        left_layout.addWidget(list_lbl)

        self._file_list = QListWidget()
        self._file_list.itemClicked.connect(self._on_file_selected)
        left_layout.addWidget(self._file_list)

        # File action buttons
        btn_row = QHBoxLayout()
        new_btn = QPushButton("➕ New")
        new_btn.setStyleSheet(theme.get_button_style())
        new_btn.clicked.connect(self._new_rule)
        delete_btn = QPushButton("🗑 Delete")
        delete_btn.setStyleSheet(theme.get_button_style())
        delete_btn.clicked.connect(self._delete_rule)
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedWidth(30)
        refresh_btn.setStyleSheet(theme.get_button_style())
        refresh_btn.clicked.connect(self.refresh)
        btn_row.addWidget(new_btn)
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()
        btn_row.addWidget(refresh_btn)
        left_layout.addLayout(btn_row)

        left.setMinimumWidth(180)
        splitter.addWidget(left)

        # ── Right: editor ────────────────────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        self._file_label = QLabel("Select a rule file to edit")
        self._file_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        right_layout.addWidget(self._file_label)

        # Frontmatter info strip
        self._fm_label = QLabel()
        self._fm_label.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px; "
            f"background: {theme.BG_MEDIUM}; padding: 4px 6px; border-radius: 3px;"
        )
        self._fm_label.setWordWrap(True)
        self._fm_label.hide()
        right_layout.addWidget(self._fm_label)

        self._editor = QTextEdit()
        self._editor.setStyleSheet(f"""
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
        self._editor.setPlaceholderText(
            "# Rule content\n\nWrite your rule here in Markdown.\n\n"
            "You can add YAML frontmatter at the top:\n"
            "---\n"
            "description: Brief description\n"
            "paths:\n"
            "  - src/**\n"
            "---\n"
        )
        right_layout.addWidget(self._editor, 1)

        save_row = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.setStyleSheet(theme.get_button_style())
        save_btn.clicked.connect(self._save_rule)
        save_row.addStretch()
        save_row.addWidget(save_btn)
        right_layout.addLayout(save_row)

        splitter.addWidget(right)
        splitter.setSizes([220, 580])
        layout.addWidget(splitter, 1)

    # ── Public ──────────────────────────────────────────────────────────────

    def refresh(self):
        """Reload file list from disk."""
        rules_dir = self._get_rules_dir()
        if rules_dir:
            self._dir_label.setText(str(rules_dir))
        else:
            self._dir_label.setText("(not configured)")

        self._file_list.clear()
        if not rules_dir or not rules_dir.exists():
            item = QListWidgetItem("No rules directory found")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self._file_list.addItem(item)
            return

        md_files = sorted(rules_dir.glob("**/*.md"))
        if not md_files:
            item = QListWidgetItem("No rule files yet — click ➕ New")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self._file_list.addItem(item)
            return

        for f in md_files:
            rel = f.relative_to(rules_dir)
            fm = _parse_frontmatter(f.read_text(encoding="utf-8", errors="replace"))
            desc = fm.get("description", "")
            paths = fm.get("paths", "")
            scope_icon = "📍" if paths else "📄"
            display = f"{scope_icon} {rel}"
            if desc:
                display += f"  — {desc[:50]}"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, f)
            self._file_list.addItem(item)

    # ── Private ─────────────────────────────────────────────────────────────

    def _on_file_selected(self, item: QListWidgetItem):
        path: Path = item.data(Qt.ItemDataRole.UserRole)
        if not path:
            return
        self._current_path = path
        content = path.read_text(encoding="utf-8", errors="replace")
        self._editor.setPlainText(content)
        self._file_label.setText(str(path))

        fm = _parse_frontmatter(content)
        if fm:
            parts = []
            if "description" in fm:
                parts.append(f"description: {fm['description']}")
            if "paths" in fm:
                parts.append(f"paths: {fm['paths']}")
            self._fm_label.setText("Frontmatter: " + " | ".join(parts))
            self._fm_label.show()
        else:
            self._fm_label.hide()

    def _new_rule(self):
        rules_dir = self._get_rules_dir()
        if not rules_dir:
            QMessageBox.warning(self, "No Directory", "Cannot determine rules directory for this scope.")
            return

        dlg = NewRuleDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        data = dlg.get_data()
        if not data["name"]:
            QMessageBox.warning(self, "Name Required", "Please enter a file name.")
            return

        rule_path = rules_dir / f"{data['name']}.md"
        if rule_path.exists():
            QMessageBox.warning(self, "Exists", f"{rule_path.name} already exists.")
            return

        # Build frontmatter
        fm_lines = ["---"]
        if data["description"]:
            fm_lines.append(f'description: "{data["description"]}"')
        if data["paths"]:
            fm_lines.append("paths:")
            for p in data["paths"]:
                fm_lines.append(f"  - {p}")
        fm_lines.append("---")
        fm_lines.append("")
        fm_lines.append(f"# {data['name'].replace('-', ' ').title()}")
        fm_lines.append("")
        fm_lines.append("<!-- Write your rule here -->")

        rules_dir.mkdir(parents=True, exist_ok=True)
        rule_path.write_text("\n".join(fm_lines), encoding="utf-8")
        self.refresh()

        # Select newly created file
        for i in range(self._file_list.count()):
            item = self._file_list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == rule_path:
                self._file_list.setCurrentItem(item)
                self._on_file_selected(item)
                break

    def _save_rule(self):
        if not self._current_path:
            QMessageBox.warning(self, "Nothing Selected", "Select a rule file first.")
            return
        content = self._editor.toPlainText()
        self._current_path.write_text(content, encoding="utf-8")
        QMessageBox.information(self, "Saved", f"Saved {self._current_path.name}")
        self.refresh()

    def _delete_rule(self):
        if not self._current_path:
            QMessageBox.warning(self, "Nothing Selected", "Select a rule file to delete.")
            return
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete {self._current_path.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._current_path.unlink()
            self._current_path = None
            self._editor.clear()
            self._fm_label.hide()
            self._file_label.setText("Select a rule file to edit")
            self.refresh()


class RulesTab(QWidget):
    """Tab for managing Claude Code rules files."""

    def __init__(self, config_manager, backup_manager):
        super().__init__()
        self._config_manager = config_manager
        self._backup_manager = backup_manager
        self._init_ui()

    def _get_user_rules_dir(self) -> Path | None:
        base = getattr(self._config_manager, 'claude_dir', None)
        if base:
            return Path(base) / "rules"
        return Path.home() / ".claude" / "rules"

    def _get_project_rules_dir(self) -> Path | None:
        cwd = Path.cwd()
        return cwd / ".claude" / "rules"

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        # Header
        header_row = QHBoxLayout()
        header = QLabel("Rules Manager")
        header.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};"
        )
        docs_btn = QPushButton("📖 Rules Docs")
        docs_btn.setStyleSheet(theme.get_button_style())
        docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://code.claude.com/en/docs/claude-code/memory#rules-directory")
        ))
        header_row.addWidget(header)
        header_row.addStretch()
        header_row.addWidget(docs_btn)
        layout.addLayout(header_row)

        # Scope tabs
        scope_tabs = QTabWidget()
        scope_tabs.setStyleSheet(theme.get_tab_widget_style())

        self._user_editor = RuleEditorWidget("user", self._get_user_rules_dir)
        scope_tabs.addTab(self._user_editor, "👤 User (~/.claude/rules/)")

        self._project_editor = RuleEditorWidget("project", self._get_project_rules_dir)
        scope_tabs.addTab(self._project_editor, "📁 Project (.claude/rules/)")

        scope_tabs.currentChanged.connect(self._on_scope_changed)
        layout.addWidget(scope_tabs, 1)

        # Footer
        footer = QLabel(
            "💡 <b>Rules</b> are Markdown files that provide reusable instructions to Claude. "
            "Use <b>paths:</b> frontmatter to scope a rule to specific directories. "
            "Rules in <code>~/.claude/rules/</code> apply globally; "
            "rules in <code>.claude/rules/</code> apply to the current project. "
            "Use <code>claudeMdExcludes</code> in settings to prevent loading rules from certain paths."
        )
        footer.setWordWrap(True)
        footer.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px; "
            f"padding: 8px; background-color: {theme.BG_MEDIUM}; border-radius: 3px;"
        )
        layout.addWidget(footer)

        # Initial load
        self._user_editor.refresh()

    def _on_scope_changed(self, index: int):
        if index == 0:
            self._user_editor.refresh()
        else:
            self._project_editor.refresh()
