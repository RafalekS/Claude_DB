"""
Raw settings.json editor — full editor for every key, guided or not.

The other Settings sub-tabs only expose a handful of curated fields. This one
edits the whole file, so keys like `cleanupPeriodDays`, `spinnerTipsEnabled`,
`autoUpdatesChannel`, `fallbackModel`, the `sandbox.*` tree, etc. are reachable.

Used by:
  * User Config  → one scope (~/.claude/settings.json)
  * Project Config → two scopes (.claude/settings.json + .claude/settings.local.json)
"""

import json
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QComboBox, QMessageBox, QSplitter, QTreeWidget, QTreeWidgetItem, QLineEdit,
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QColor

from utils import theme

logger = logging.getLogger(__name__)

# ── Curated key reference (double-click inserts key: sample) ──────────────────
# (key, sample_value, one-line description). Grouped by the leading label.
COMMON_SETTINGS: list[tuple[str, str, object, str]] = [
    ("Model & effort", "model", "sonnet", "Default model (sonnet|opus|fable|haiku or full id)"),
    ("Model & effort", "effortLevel", "high", "low|medium|high|xhigh|max|ultracode"),
    ("Model & effort", "fallbackModel", "haiku", "Backup model(s) when the primary is overloaded"),
    ("Model & effort", "availableModels", ["sonnet", "haiku"], "Restrict which models /model may pick"),
    ("Model & effort", "enforceAvailableModels", True, "Also restrict the Default option to the allowlist"),
    ("Model & effort", "alwaysThinkingEnabled", True, "Force extended thinking on"),
    ("Model & effort", "showThinkingSummaries", True, "Show readable summaries of the reasoning"),

    ("Cleanup & updates", "cleanupPeriodDays", 30, "Days to keep session transcripts before deletion"),
    ("Cleanup & updates", "desktopSessionCleanupPeriodDays", 30, "Desktop transcript retention (days)"),
    ("Cleanup & updates", "autoUpdatesChannel", "stable", '"latest" or "stable"'),
    ("Cleanup & updates", "minimumVersion", "2.1.0", "Minimum version for auto-updates"),

    ("Context", "autoCompactEnabled", True, "Automatic context compaction"),
    ("Context", "autoCompactWindow", 90, "Context fullness threshold (%) that triggers auto-compact"),
    ("Context", "promptCacheTtl", 3600, "Prompt cache lifetime (seconds)"),

    ("UI & notifications", "preferredNotifChannel", "terminal_bell", "Notification channel"),
    ("UI & notifications", "theme", "dark", "dark|light|dark-daltonized|light-daltonized|dark-ansi|light-ansi"),
    ("UI & notifications", "editorMode", "vim", '"vim" for vim key bindings'),
    ("UI & notifications", "spinnerTipsEnabled", False, "Show the one-line tips under the spinner"),
    ("UI & notifications", "verbose", True, "Verbose tool output"),
    ("UI & notifications", "showTurnDuration", True, 'Show the "Cooked for …" duration'),
    ("UI & notifications", "language", "en", "Response language"),
    ("UI & notifications", "inputNeededNotifEnabled", True, "Push notification when waiting on you"),
    ("UI & notifications", "agentPushNotifEnabled", True, "Push subagent notifications to your phone"),

    ("Memory", "autoMemoryEnabled", False, "Auto memory on/off (default on)"),
    ("Memory", "autoMemoryDirectory", "~/my-memory", "Override the auto-memory directory"),
    ("Memory", "claudeMdExcludes", ["**/other-team/CLAUDE.md"], "Skip specific CLAUDE.md files (glob)"),

    ("Behaviour", "includeCoAuthoredBy", None, "DEPRECATED — use the attribution object"),
    ("Behaviour", "attribution", {"commit": "", "pr": ""}, "Customise commit / PR attribution"),
    ("Behaviour", "includeGitInstructions", False, "Remove the built-in git instructions"),
    ("Behaviour", "outputStyle", "Explanatory", "Output style name"),
    ("Behaviour", "disableBundledSkills", True, "Turn off every bundled skill except /doctor"),
    ("Behaviour", "enableAllProjectMcpServers", True, "Auto-approve all .mcp.json servers"),
    ("Behaviour", "enabledMcpjsonServers", ["server-a"], "Approve specific .mcp.json servers"),
    ("Behaviour", "disabledMcpjsonServers", ["server-b"], "Block specific .mcp.json servers"),

    ("Blocks", "env", {"KEY": "value"}, "Environment variables for sessions"),
    ("Blocks", "permissions", {"allow": [], "ask": [], "deny": [], "defaultMode": "default"},
     "allow / ask / deny rules and defaultMode"),
    ("Blocks", "hooks", {}, "Hook commands keyed by event name"),
    ("Blocks", "statusLine", {"type": "command", "command": ""}, "Status line command"),
    ("Blocks", "sandbox", {"enabled": True}, "Bash sandboxing configuration"),
]

_DOCS_URL = "https://code.claude.com/docs/en/settings-reference"


class RawSettingsSubTab(QWidget):
    """Full settings.json editor.

    scopes: list of dicts, each:
        {
          "label":  str,
          "path":   callable() -> Path | str | None,   # for the path label + backup
          "load":   callable() -> dict,                 # raises / returns {} if missing
          "save":   callable(dict) -> None,             # raises on failure
          "ready":  callable() -> (bool, str),          # optional: (can_edit, reason)
        }
    """

    def __init__(self, scopes: list[dict], backup_manager=None, parent=None,
                 on_saved=None, compact=False):
        """
        on_saved: optional callback() run after a successful save from this
                  editor — lets a host tab reload its own guided fields.
        compact:  hide the big header row (for embedding inside another tab).
        """
        super().__init__(parent)
        self._scopes = scopes
        self._backup_manager = backup_manager
        self._on_saved = on_saved
        self._compact = compact
        self._init_ui()
        self.reload()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        top = QHBoxLayout()
        top.setSpacing(6)
        if not self._compact:
            header = QLabel("settings.json — all keys")
            header.setStyleSheet(
                f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};"
            )
            top.addWidget(header)

        self._scope_combo = QComboBox()
        for s in self._scopes:
            self._scope_combo.addItem(s["label"])
        self._scope_combo.currentIndexChanged.connect(self.reload)
        if len(self._scopes) > 1:
            top.addWidget(QLabel("Scope:"))
            top.addWidget(self._scope_combo)

        top.addStretch()
        docs_btn = QPushButton("📖 Settings reference (all keys)")
        docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(_DOCS_URL)))
        top.addWidget(docs_btn)
        layout.addLayout(top)

        self._path_label = QLabel("")
        self._path_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(self._path_label)

        split = QSplitter(Qt.Orientation.Horizontal)

        # left: JSON editor
        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(0, 0, 4, 0)
        left_l.setSpacing(4)
        self._editor = QTextEdit()
        self._editor.setStyleSheet(
            f"QTextEdit {{ font-family: {theme.FONT_FAMILY_MONO}; font-size: {theme.FONT_SIZE_SMALL}px; "
            f"border-radius: 3px; padding: 6px; }}"
        )
        left_l.addWidget(self._editor, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        reload_btn = QPushButton("↻ Reload")
        reload_btn.clicked.connect(self.reload)
        fmt_btn = QPushButton("{ } Format")
        fmt_btn.clicked.connect(self._format)
        val_btn = QPushButton("✓ Validate")
        val_btn.clicked.connect(self._validate_dialog)
        backup_save_btn = QPushButton("💾 Backup & Save")
        backup_save_btn.clicked.connect(lambda: self._save(backup=True))
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(lambda: self._save(backup=False))
        for b in (reload_btn, fmt_btn, val_btn):
            btn_row.addWidget(b)
        btn_row.addStretch()
        btn_row.addWidget(backup_save_btn)
        btn_row.addWidget(save_btn)
        left_l.addLayout(btn_row)

        # right: key reference
        right = QWidget()
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(4, 0, 0, 0)
        right_l.setSpacing(4)
        right_l.addWidget(QLabel("Common keys — double-click to insert"))
        self._filter = QLineEdit()
        self._filter.setPlaceholderText("filter keys…")
        self._filter.setClearButtonEnabled(True)
        self._filter.textChanged.connect(self._apply_filter)
        right_l.addWidget(self._filter)

        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Key", "Description"])
        self._tree.setColumnWidth(0, 200)
        self._tree.setRootIsDecorated(True)
        self._tree.itemDoubleClicked.connect(self._insert_key)
        right_l.addWidget(self._tree, 1)
        self._populate_reference()

        split.addWidget(left)
        split.addWidget(right)
        split.setSizes([620, 380])
        layout.addWidget(split, 1)

        self._status = QLabel("")
        self._status.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(self._status)

    def _populate_reference(self):
        groups: dict[str, list] = {}
        for group, key, sample, desc in COMMON_SETTINGS:
            groups.setdefault(group.strip(), []).append((key, sample, desc))
        for group, rows in groups.items():
            parent = QTreeWidgetItem([group, ""])
            parent.setForeground(0, QColor(theme.ACCENT_SECONDARY))
            self._tree.addTopLevelItem(parent)
            for key, sample, desc in rows:
                child = QTreeWidgetItem([key, desc])
                child.setData(0, Qt.ItemDataRole.UserRole, (key, sample))
                child.setToolTip(1, desc)
                parent.addChild(child)
            parent.setExpanded(True)

    # ── data ─────────────────────────────────────────────────────────────────

    def _scope(self) -> dict:
        idx = max(0, self._scope_combo.currentIndex())
        return self._scopes[idx]

    def reload(self, *_):
        scope = self._scope()
        path = scope["path"]()
        self._path_label.setText(f"File: {path if path else '(no project selected)'}")

        ready_fn = scope.get("ready")
        if ready_fn:
            ok, reason = ready_fn()
            if not ok:
                self._editor.setReadOnly(True)
                self._editor.setPlainText(f"// {reason}")
                self._status.setText(reason)
                return
        self._editor.setReadOnly(False)

        try:
            data = scope["load"]() or {}
        except Exception as e:
            logger.error("Failed to load settings: %s", e)
            self._editor.setPlainText(f"// Error loading: {e}\n{{}}")
            self._status.setText(f"Load error: {e}")
            return
        self._editor.setPlainText(json.dumps(data, indent=2, ensure_ascii=False))
        self._status.setText(f"Loaded {len(data)} top-level key(s).")

    def _parsed(self):
        """Return the editor content parsed as a dict, or None (after showing an error)."""
        text = self._editor.toPlainText().strip()
        if not text:
            return {}
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            logger.error("Invalid settings JSON: %s", e)
            QMessageBox.critical(self, "Invalid JSON", f"{e}")
            return None
        if not isinstance(data, dict):
            QMessageBox.critical(self, "Invalid JSON", "settings.json must be a JSON object.")
            return None
        return data

    def _format(self):
        data = self._parsed()
        if data is not None:
            self._editor.setPlainText(json.dumps(data, indent=2, ensure_ascii=False))
            self._status.setText("Formatted.")

    def _validate_dialog(self):
        data = self._parsed()
        if data is not None:
            QMessageBox.information(self, "Valid", f"JSON is valid — {len(data)} top-level key(s).")

    def _save(self, backup: bool):
        if self._editor.isReadOnly():
            return
        data = self._parsed()
        if data is None:
            return
        scope = self._scope()
        path = scope["path"]()
        try:
            if backup and self._backup_manager and isinstance(path, Path) and path.exists():
                self._backup_manager.create_file_backup(path)
            scope["save"](data)
        except Exception as e:
            logger.error("Failed to save settings: %s", e)
            QMessageBox.critical(self, "Save Error", f"{e}")
            return
        self._status.setText(f"Saved to {path}")
        QMessageBox.information(self, "Saved", f"Settings saved to:\n{path}")
        if callable(self._on_saved):
            try:
                self._on_saved()
            except Exception as e:
                logger.warning("on_saved callback failed: %s", e)

    # ── key reference ────────────────────────────────────────────────────────

    def _apply_filter(self, text: str):
        t = text.lower()
        for i in range(self._tree.topLevelItemCount()):
            parent = self._tree.topLevelItem(i)
            any_visible = False
            for j in range(parent.childCount()):
                child = parent.child(j)
                match = t in child.text(0).lower() or t in child.text(1).lower()
                child.setHidden(not match)
                any_visible = any_visible or match
            parent.setHidden(not any_visible and bool(t))
            if any_visible:
                parent.setExpanded(True)

    def _insert_key(self, item: QTreeWidgetItem, _col: int = 0):
        payload = item.data(0, Qt.ItemDataRole.UserRole)
        if not payload:
            return
        key, sample = payload
        data = self._parsed()
        if data is None:
            return
        if key in data:
            self._status.setText(f'"{key}" is already set.')
            return
        data[key] = sample
        self._editor.setPlainText(json.dumps(data, indent=2, ensure_ascii=False))
        self._status.setText(f'Inserted "{key}" — review the value, then Save.')

    # ── external refresh hooks ───────────────────────────────────────────────

    def load_settings(self):
        self.reload()

    def apply_theme(self):
        pass


# ── factory helpers ─────────────────────────────────────────────────────────

def user_scope(config_manager) -> list[dict]:
    def _save(data):
        config_manager.save_settings(data)
    return [{
        "label": "User (~/.claude/settings.json)",
        "path": lambda: getattr(config_manager, "settings_file", None),
        "load": config_manager.get_settings,
        "save": _save,
    }]


def project_scopes(settings_manager, project_context) -> list[dict]:
    def _ready():
        if project_context and project_context.has_project():
            return True, ""
        return False, "Select a project first (Project Config → Projects)."

    def _shared_path():
        p = project_context.get_project() if project_context and project_context.has_project() else None
        return (Path(p) / ".claude" / "settings.json") if p else None

    def _local_path():
        p = project_context.get_project() if project_context and project_context.has_project() else None
        return (Path(p) / ".claude" / "settings.local.json") if p else None

    return [
        {
            "label": "Shared (.claude/settings.json)",
            "ready": _ready,
            "path": _shared_path,
            "load": lambda: settings_manager.get_project_shared_settings(project_context.get_project()),
            "save": lambda d: settings_manager.save_settings(_shared_path(), d),
        },
        {
            "label": "Local (.claude/settings.local.json)",
            "ready": _ready,
            "path": _local_path,
            "load": lambda: settings_manager.get_project_local_settings(project_context.get_project()),
            "save": lambda d: settings_manager.save_settings(_local_path(), d),
        },
    ]
