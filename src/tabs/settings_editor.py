"""
Master–detail settings.json editor.

Left  : every setting, grouped by category, filterable. A ● marks keys that are
        currently set in the file; ○ marks keys using their default.
Right : the control appropriate for whatever you selected on the left —
        a checkbox for a boolean, a dropdown for an enum, a number box, a text
        field, a one-per-line list, or a small JSON box for object values.

No raw-JSON blob, no "insert key" gimmick, no duplicated model/theme sections —
model, theme, effort, cleanupPeriodDays, etc. are all just rows in the list.

Used by UserSettingsSubTab (one scope) and ProjectSettingsSubTab (shared + local).
"""

import copy
import json
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QComboBox, QCheckBox, QSpinBox, QPlainTextEdit, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QSplitter, QStackedWidget, QFileDialog, QSizePolicy,
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QColor

from utils import theme

logger = logging.getLogger(__name__)

_DOCS = "https://code.claude.com/docs/en/settings-reference"
_MISSING = object()

# ── Schema ───────────────────────────────────────────────────────────────────
# type: bool | int | str | path | choice | list | json
#   choice → needs "options"; add "editable": True to allow a free value
#   int    → optional "min"/"max"/"suffix"
#   path   → optional "dir": True (pick a directory instead of a file)
#   list   → string list, edited one per line
#   json   → object value, edited as JSON
# path key uses dot notation for nested (e.g. "permissions.defaultMode").

SCHEMA: list[dict] = [
    # ── Model & reasoning ───────────────────────────────────────────────────
    dict(cat="Model & reasoning", key="model", type="choice", editable=True,
         options=["sonnet", "opus", "fable", "haiku", "opusplan",
                  "claude-sonnet-5", "claude-opus-5", "claude-fable-5",
                  "claude-haiku-4-5-20251001"],
         desc="Model each new session starts with. Alias or full id. "
              "--model / /model / ANTHROPIC_MODEL override this."),
    dict(cat="Model & reasoning", key="effortLevel", type="choice",
         options=["low", "medium", "high", "xhigh", "max", "ultracode"],
         desc="Reasoning depth / token spend. Claude Code defaults to xhigh. "
              "max and ultracode apply to the current session only."),
    dict(cat="Model & reasoning", key="fallbackModel", type="str",
         desc="Comma-separated backup model(s) used when the primary is overloaded."),
    dict(cat="Model & reasoning", key="availableModels", type="list",
         desc="Restrict which models /model, --model and the model key may pick "
              "(family name, prefix, or full id per line)."),
    dict(cat="Model & reasoning", key="enforceAvailableModels", type="bool",
         desc="Also restrict the Default option to the availableModels allowlist."),
    dict(cat="Model & reasoning", key="alwaysThinkingEnabled", type="bool",
         desc="Force extended thinking on for every turn."),
    dict(cat="Model & reasoning", key="showThinkingSummaries", type="bool",
         desc="Show readable summaries of the model's reasoning."),

    # ── Appearance & terminal ──────────────────────────────────────────────
    dict(cat="Appearance & terminal", key="theme", type="choice",
         options=["dark", "light", "dark-daltonized", "light-daltonized",
                  "dark-ansi", "light-ansi"],
         desc="Colour theme. Written here by /config."),
    dict(cat="Appearance & terminal", key="editorMode", type="choice", editable=True,
         options=["normal", "vim"], desc='"vim" for vim key bindings in the prompt.'),
    dict(cat="Appearance & terminal", key="verbose", type="bool",
         desc="Show full tool input/output instead of truncating it."),
    dict(cat="Appearance & terminal", key="spinnerTipsEnabled", type="bool",
         desc="Show the one-line tips under the working spinner."),
    dict(cat="Appearance & terminal", key="showTurnDuration", type="bool",
         desc='Show the "Cooked for …" duration after each turn.'),
    dict(cat="Appearance & terminal", key="prefersReducedMotion", type="bool",
         desc="Reduce or disable animations."),
    dict(cat="Appearance & terminal", key="emojiCompletionEnabled", type="bool",
         desc="Offer :shortcode: emoji completions."),
    dict(cat="Appearance & terminal", key="autoScrollEnabled", type="bool",
         desc="Auto-follow output in fullscreen mode."),
    dict(cat="Appearance & terminal", key="language", type="str",
         desc='Response language, e.g. "en", "es".'),

    # ── Notifications ──────────────────────────────────────────────────────
    dict(cat="Notifications", key="preferredNotifChannel", type="choice", editable=True,
         options=["terminal_bell", "iterm2", "iterm2_with_bell", "kitty",
                  "notifications_disabled"],
         desc="How Claude Code notifies you when it needs attention."),
    dict(cat="Notifications", key="inputNeededNotifEnabled", type="bool",
         desc="Push a notification to your phone when Claude is waiting on you."),
    dict(cat="Notifications", key="agentPushNotifEnabled", type="bool",
         desc="Push subagent notifications to your phone."),
    dict(cat="Notifications", key="awaySummaryEnabled", type="bool",
         desc="Show a session recap when you return."),

    # ── Context & memory ──────────────────────────────────────────────────
    dict(cat="Context & memory", key="autoCompactEnabled", type="bool",
         desc="Automatically compact the conversation as context fills."),
    dict(cat="Context & memory", key="autoCompactWindow", type="int", min=1, max=100,
         suffix=" %", desc="Context-fullness threshold that triggers auto-compaction."),
    dict(cat="Context & memory", key="promptCacheTtl", type="int", min=0, suffix=" s",
         desc="Prompt cache lifetime in seconds."),
    dict(cat="Context & memory", key="autoMemoryEnabled", type="bool",
         desc="Let Claude keep its own notes across sessions (on by default)."),
    dict(cat="Context & memory", key="autoMemoryDirectory", type="path", dir=True,
         desc="Override the auto-memory directory "
              "(default ~/.claude/projects/<project>/memory/). Absolute or ~/ path."),
    dict(cat="Context & memory", key="claudeMdExcludes", type="list",
         desc="Skip specific CLAUDE.md files / rules dirs — one glob per line, "
              "matched against absolute paths."),
    dict(cat="Context & memory", key="includeGitInstructions", type="bool",
         desc="Keep the built-in git instructions (set false to remove them)."),

    # ── Cleanup & updates ─────────────────────────────────────────────────
    dict(cat="Cleanup & updates", key="cleanupPeriodDays", type="int", min=0, suffix=" days",
         desc="How long to keep session transcripts before Claude Code deletes them. "
              "Memory files are excluded from this sweep."),
    dict(cat="Cleanup & updates", key="desktopSessionCleanupPeriodDays", type="int", min=0,
         suffix=" days", desc="Transcript retention for the desktop app."),
    dict(cat="Cleanup & updates", key="autoUpdatesChannel", type="choice",
         options=["latest", "stable"], desc="Which release channel auto-updates follow."),
    dict(cat="Cleanup & updates", key="minimumVersion", type="str",
         desc="Minimum version to auto-update to."),

    # ── Permissions & safety ──────────────────────────────────────────────
    dict(cat="Permissions & safety", key="permissions.defaultMode", type="choice",
         options=["default", "manual", "acceptEdits", "plan", "auto", "dontAsk",
                  "bypassPermissions"],
         desc="Permission mode sessions start in. Full allow/ask/deny rules are on "
              "the Permissions tab."),
    dict(cat="Permissions & safety", key="permissions.disableBypassPermissionsMode",
         type="choice", editable=True, options=["disable"],
         desc='Set to "disable" to prevent bypassPermissions mode.'),
    dict(cat="Permissions & safety", key="permissions.disableAutoMode",
         type="choice", editable=True, options=["disable"],
         desc='Set to "disable" to prevent auto mode.'),
    dict(cat="Permissions & safety", key="skipDangerousModePermissionPrompt", type="bool",
         desc="Skip the confirmation prompt when entering bypassPermissions mode."),

    # ── MCP ───────────────────────────────────────────────────────────────
    dict(cat="MCP", key="enableAllProjectMcpServers", type="bool",
         desc="Auto-approve every server in a project .mcp.json without prompting."),
    dict(cat="MCP", key="enabledMcpjsonServers", type="list",
         desc="Approve specific .mcp.json servers by name — one per line."),
    dict(cat="MCP", key="disabledMcpjsonServers", type="list",
         desc="Block specific .mcp.json servers by name — one per line."),

    # ── Skills, hooks, plugins ────────────────────────────────────────────
    dict(cat="Skills, hooks, plugins", key="disableBundledSkills", type="bool",
         desc="Turn off every bundled skill except /doctor."),
    dict(cat="Skills, hooks, plugins", key="disableAllHooks", type="bool",
         desc="Disable hooks, status line and @ suggestions (does not disable managed hooks)."),
    dict(cat="Skills, hooks, plugins", key="disableWorkflows", type="bool",
         desc="Turn off dynamic workflows."),
    dict(cat="Skills, hooks, plugins", key="disableSkillShellExecution", type="bool",
         desc="Stop skills from running inline shell commands."),
    dict(cat="Skills, hooks, plugins", key="outputStyle", type="choice", editable=True,
         options=["Default", "Proactive", "Concise", "Explanatory", "Learning"],
         desc="Output style name — built-in or one from .claude/output-styles/. "
              "Applies after /clear or a restart."),

    # ── Attribution ──────────────────────────────────────────────────────
    dict(cat="Attribution", key="attribution.commit", type="str",
         desc="Custom commit-message trailer."),
    dict(cat="Attribution", key="attribution.pr", type="str",
         desc="Custom PR-description attribution."),
    dict(cat="Attribution", key="attribution.sessionUrl", type="bool",
         desc="Include the claude.ai session link in commits/PRs (set false to omit)."),
    dict(cat="Attribution", key="includeCoAuthoredBy", type="bool",
         desc="DEPRECATED — use the attribution.* keys instead."),

    # ── Blocks (object values) ───────────────────────────────────────────
    dict(cat="Blocks (advanced)", key="env", type="json",
         desc="Environment variables for sessions. The Env Vars tab is the friendlier editor."),
    dict(cat="Blocks (advanced)", key="sandbox", type="json",
         desc='Bash sandboxing, e.g. {"enabled": true, "network": {"allowedDomains": [...]}}.'),
    dict(cat="Blocks (advanced)", key="hooks", type="json",
         desc="Hook commands keyed by event. Edit these on the Hooks tab."),
    dict(cat="Blocks (advanced)", key="statusLine", type="json",
         desc='{"type": "command", "command": "...", "padding": 0}. Edit on the Statusline tab.'),
    dict(cat="Blocks (advanced)", key="permissions", type="json",
         desc="Full allow/ask/deny object. Edit rules on the Permissions tab."),
    dict(cat="Blocks (advanced)", key="enabledPlugins", type="json",
         desc='Per-plugin enable state: {"name@marketplace": true}. Edit on the Plugins tab.'),
]

_SCHEMA_BY_KEY = {s["key"]: s for s in SCHEMA}
_SCHEMA_TOP_KEYS = {s["key"].split(".", 1)[0] for s in SCHEMA}


# ── nested get/set/del ───────────────────────────────────────────────────────

def _get(d: dict, path: str):
    cur = d
    for p in path.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return _MISSING
        cur = cur[p]
    return cur


def _set(d: dict, path: str, value):
    parts = path.split(".")
    cur = d
    for p in parts[:-1]:
        nxt = cur.get(p)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[p] = nxt
        cur = nxt
    cur[parts[-1]] = value


def _del(d: dict, path: str):
    parts = path.split(".")
    stack = [d]
    cur = d
    for p in parts[:-1]:
        if not isinstance(cur, dict) or p not in cur:
            return
        cur = cur[p]
        stack.append(cur)
    if isinstance(cur, dict):
        cur.pop(parts[-1], None)
    # prune now-empty parent dicts
    for p, parent in zip(reversed(parts[:-1]), reversed(stack[:-1])):
        child = parent.get(p)
        if isinstance(child, dict) and not child:
            parent.pop(p, None)
        else:
            break


# ── the editor ───────────────────────────────────────────────────────────────

class SettingsEditor(QWidget):
    """scopes: list of dicts, each:
        {"label": str,
         "load": () -> dict, "save": (dict) -> None,
         "path": () -> Path|str|None,
         "ready": () -> (bool, str)   # optional}
    """

    def __init__(self, scopes: list[dict], backup_manager=None, parent=None):
        super().__init__(parent)
        self._scopes = scopes
        self._backup = backup_manager
        self._working: dict = {}
        self._current_key: str | None = None
        self._editors: dict[str, QWidget] = {}
        self._build()
        self.reload()

    # -- construction --------------------------------------------------------

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(4)

        bar = QHBoxLayout()
        bar.setSpacing(6)
        self._scope_combo = QComboBox()
        for s in self._scopes:
            self._scope_combo.addItem(s["label"])
        self._scope_combo.currentIndexChanged.connect(self.reload)
        if len(self._scopes) > 1:
            bar.addWidget(QLabel("Scope:"))
            bar.addWidget(self._scope_combo)
        self._path_lbl = QLabel("")
        self._path_lbl.setStyleSheet(f"color:{theme.FG_SECONDARY};font-size:{theme.FONT_SIZE_SMALL}px;")
        bar.addWidget(self._path_lbl, 1)
        docs = QPushButton("📖 Reference")
        docs.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(_DOCS)))
        bar.addWidget(docs)
        outer.addLayout(bar)

        self._filter = QLineEdit()
        self._filter.setPlaceholderText("filter settings…")
        self._filter.setClearButtonEnabled(True)
        self._filter.textChanged.connect(self._apply_filter)
        outer.addWidget(self._filter)

        split = QSplitter(Qt.Orientation.Horizontal)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setColumnCount(1)
        self._tree.currentItemChanged.connect(self._on_select)
        split.addWidget(self._tree)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(8, 4, 4, 4)
        rl.setSpacing(6)
        self._key_lbl = QLabel("Select a setting")
        self._key_lbl.setStyleSheet(
            f"font-size:{theme.FONT_SIZE_LARGE}px;font-weight:bold;color:{theme.ACCENT_PRIMARY};")
        rl.addWidget(self._key_lbl)
        self._desc_lbl = QLabel("")
        self._desc_lbl.setWordWrap(True)
        self._desc_lbl.setStyleSheet(f"color:{theme.FG_SECONDARY};font-size:{theme.FONT_SIZE_SMALL}px;")
        rl.addWidget(self._desc_lbl)
        self._stack = QStackedWidget()
        self._stack.addWidget(QWidget())  # index 0 = blank
        rl.addWidget(self._stack)
        self._unset_btn = QPushButton("Unset (use default)")
        self._unset_btn.clicked.connect(self._unset_current)
        self._unset_btn.setEnabled(False)
        row = QHBoxLayout()
        row.addWidget(self._unset_btn)
        row.addStretch()
        rl.addLayout(row)
        rl.addStretch(1)
        split.addWidget(right)
        split.setSizes([300, 560])
        outer.addWidget(split, 1)

        bottom = QHBoxLayout()
        bottom.setSpacing(4)
        add_btn = QPushButton("＋ Add other key…")
        add_btn.setToolTip("Add a key that isn't in the list")
        add_btn.clicked.connect(self._add_custom_key)
        reload_btn = QPushButton("↻ Reload")
        reload_btn.clicked.connect(self.reload)
        bkp_btn = QPushButton("💾 Backup & Save")
        bkp_btn.clicked.connect(lambda: self._save(backup=True))
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(lambda: self._save(backup=False))
        bottom.addWidget(add_btn)
        bottom.addWidget(reload_btn)
        bottom.addStretch()
        bottom.addWidget(bkp_btn)
        bottom.addWidget(save_btn)
        outer.addLayout(bottom)

        self._status = QLabel("")
        self._status.setStyleSheet(f"color:{theme.FG_SECONDARY};font-size:{theme.FONT_SIZE_SMALL}px;")
        outer.addWidget(self._status)

    # -- data --------------------------------------------------------------

    def _scope(self) -> dict:
        return self._scopes[max(0, self._scope_combo.currentIndex())]

    def reload(self, *_):
        scope = self._scope()
        p = scope["path"]()
        self._path_lbl.setText(f"File: {p or '(no project selected)'}")
        ready = scope.get("ready")
        if ready:
            ok, why = ready()
            if not ok:
                self._working = {}
                self._tree.clear()
                self._status.setText(why)
                return
        try:
            self._working = copy.deepcopy(scope["load"]() or {})
        except Exception as e:
            logger.error("load settings failed: %s", e)
            self._working = {}
            self._status.setText(f"Load error: {e}")
        self._rebuild_tree()
        self._status.setText(f"{sum(1 for _ in self._iter_set_keys())} key(s) set in this file.")

    def _iter_set_keys(self):
        for s in SCHEMA:
            if _get(self._working, s["key"]) is not _MISSING:
                yield s["key"]

    def _custom_keys(self) -> list[str]:
        return sorted(k for k in self._working
                      if k not in _SCHEMA_TOP_KEYS)

    def _rebuild_tree(self):
        self._tree.blockSignals(True)
        self._tree.clear()
        cats: dict[str, QTreeWidgetItem] = {}
        for s in SCHEMA:
            parent = cats.get(s["cat"])
            if parent is None:
                parent = QTreeWidgetItem([s["cat"]])
                parent.setForeground(0, QColor(theme.ACCENT_SECONDARY))
                parent.setFlags(parent.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                self._tree.addTopLevelItem(parent)
                parent.setExpanded(True)
                cats[s["cat"]] = parent
            is_set = _get(self._working, s["key"]) is not _MISSING
            it = QTreeWidgetItem([f"{'●' if is_set else '○'} {s['key']}"])
            it.setData(0, Qt.ItemDataRole.UserRole, s["key"])
            if not is_set:
                it.setForeground(0, QColor(theme.FG_SECONDARY))
            parent.addChild(it)

        extra = self._custom_keys()
        if extra:
            p = QTreeWidgetItem(["Other keys in this file"])
            p.setForeground(0, QColor(theme.WARNING_COLOR))
            p.setFlags(p.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._tree.addTopLevelItem(p)
            p.setExpanded(True)
            for k in extra:
                it = QTreeWidgetItem([f"● {k}"])
                it.setData(0, Qt.ItemDataRole.UserRole, k)
                p.addChild(it)
        self._tree.blockSignals(False)
        self._apply_filter(self._filter.text())

    # -- selection / editors ---------------------------------------------

    def _on_select(self, cur: QTreeWidgetItem, _prev=None):
        if cur is None:
            return
        key = cur.data(0, Qt.ItemDataRole.UserRole)
        if not key:
            self._stack.setCurrentIndex(0)
            self._key_lbl.setText("Select a setting")
            self._desc_lbl.setText("")
            self._unset_btn.setEnabled(False)
            return
        self._current_key = key
        spec = _SCHEMA_BY_KEY.get(key) or dict(key=key, type="json",
                                               desc="Not a recognised Claude Code key — edited as JSON.")
        self._key_lbl.setText(key)
        self._desc_lbl.setText(spec.get("desc", ""))
        w = self._editors.get(key)
        if w is None:
            w = self._make_editor(spec)
            self._editors[key] = w
            self._stack.addWidget(w)
        self._populate_editor(spec, w)
        self._stack.setCurrentWidget(w)
        self._unset_btn.setEnabled(_get(self._working, key) is not _MISSING)

    def _make_editor(self, spec: dict) -> QWidget:
        t = spec["type"]
        if t == "bool":
            w = QCheckBox(spec.get("label") or "Enabled")
            w.toggled.connect(lambda v, k=spec["key"]: self._apply_value(k, bool(v)))
            return w
        if t == "int":
            w = QSpinBox()
            w.setRange(int(spec.get("min", 0)), int(spec.get("max", 2_147_483_647)))
            if spec.get("suffix"):
                w.setSuffix(spec["suffix"])
            w.valueChanged.connect(lambda v, k=spec["key"]: self._apply_value(k, int(v)))
            return w
        if t == "choice":
            w = QComboBox()
            w.setEditable(bool(spec.get("editable")))
            w.addItem("")  # blank = unset
            w.addItems([str(o) for o in spec.get("options", [])])
            handler = (lambda _i, k=spec["key"], c=w: self._apply_choice(k, c))
            w.currentIndexChanged.connect(handler)
            if w.isEditable():
                w.lineEdit().editingFinished.connect(lambda k=spec["key"], c=w: self._apply_choice(k, c))
            return w
        if t == "path":
            w = QWidget()
            h = QHBoxLayout(w)
            h.setContentsMargins(0, 0, 0, 0)
            le = QLineEdit()
            le.textChanged.connect(lambda s, k=spec["key"]: self._apply_str(k, s))
            btn = QPushButton("Browse…")
            btn.clicked.connect(lambda _c, le=le, spec=spec: self._browse(le, spec))
            h.addWidget(le, 1)
            h.addWidget(btn)
            w._line = le
            return w
        if t == "list":
            w = QPlainTextEdit()
            w.setPlaceholderText("one value per line")
            w.setMaximumHeight(160)
            w.textChanged.connect(lambda k=spec["key"], e=w: self._apply_list(k, e))
            return w
        if t == "json":
            w = QPlainTextEdit()
            w.setPlaceholderText("JSON value")
            w.setStyleSheet(f"font-family:{theme.FONT_FAMILY_MONO};font-size:{theme.FONT_SIZE_SMALL}px;")
            w.setMaximumHeight(220)
            w.textChanged.connect(lambda k=spec["key"], e=w: self._apply_json(k, e))
            return w
        # str
        w = QLineEdit()
        w.textChanged.connect(lambda s, k=spec["key"]: self._apply_str(k, s))
        return w

    def _populate_editor(self, spec: dict, w: QWidget):
        val = _get(self._working, spec["key"])
        has = val is not _MISSING
        t = spec["type"]
        self._suspend = True
        try:
            if t == "bool":
                w.setChecked(bool(val) if has else False)
            elif t == "int":
                w.setValue(int(val) if has and isinstance(val, (int, float)) else int(spec.get("min", 0)))
            elif t == "choice":
                text = str(val) if has else ""
                i = w.findText(text)
                if i >= 0:
                    w.setCurrentIndex(i)
                elif w.isEditable():
                    w.setCurrentText(text)
                else:
                    w.setCurrentIndex(0)
            elif t == "path":
                w._line.setText(str(val) if has else "")
            elif t == "list":
                w.setPlainText("\n".join(val) if has and isinstance(val, list) else "")
            elif t == "json":
                w.setPlainText(json.dumps(val, indent=2) if has else "")
            else:
                w.setText(str(val) if has else "")
        finally:
            self._suspend = False

    def _browse(self, le: QLineEdit, spec: dict):
        if spec.get("dir"):
            d = QFileDialog.getExistingDirectory(self, "Select directory", le.text() or str(Path.home()))
            if d:
                le.setText(d)
        else:
            f, _ = QFileDialog.getOpenFileName(self, "Select file", le.text() or str(Path.home()))
            if f:
                le.setText(f)

    # -- apply into _working ------------------------------------------------

    _suspend = False

    def _mark(self, key: str):
        """Refresh the ● / ○ marker for one leaf without rebuilding the tree."""
        it = self._tree.currentItem()
        if it and it.data(0, Qt.ItemDataRole.UserRole) == key:
            is_set = _get(self._working, key) is not _MISSING
            it.setText(0, f"{'●' if is_set else '○'} {key}")
            self._unset_btn.setEnabled(is_set)

    def _apply_value(self, key, value):
        if self._suspend:
            return
        _set(self._working, key, value)
        self._mark(key)

    def _apply_str(self, key, s):
        if self._suspend:
            return
        s = s.strip()
        if s:
            _set(self._working, key, s)
        else:
            _del(self._working, key)
        self._mark(key)

    def _apply_choice(self, key, combo: QComboBox):
        if self._suspend:
            return
        s = combo.currentText().strip()
        if s:
            _set(self._working, key, s)
        else:
            _del(self._working, key)
        self._mark(key)

    def _apply_list(self, key, edit: QPlainTextEdit):
        if self._suspend:
            return
        items = [ln.strip() for ln in edit.toPlainText().splitlines() if ln.strip()]
        if items:
            _set(self._working, key, items)
        else:
            _del(self._working, key)
        self._mark(key)

    def _apply_json(self, key, edit: QPlainTextEdit):
        if self._suspend:
            return
        txt = edit.toPlainText().strip()
        if not txt:
            _del(self._working, key)
            self._status.setText("")
            self._mark(key)
            return
        try:
            _set(self._working, key, json.loads(txt))
            self._status.setText("")
        except json.JSONDecodeError as e:
            self._status.setText(f"⚠ {key}: invalid JSON — {e}")
        self._mark(key)

    def _unset_current(self):
        if not self._current_key:
            return
        _del(self._working, self._current_key)
        spec = _SCHEMA_BY_KEY.get(self._current_key) or dict(key=self._current_key, type="json")
        w = self._editors.get(self._current_key)
        if w is not None:
            self._populate_editor(spec, w)
        self._mark(self._current_key)
        self._status.setText(f'"{self._current_key}" unset (will use the default).')

    def _add_custom_key(self):
        from PyQt6.QtWidgets import QInputDialog
        key, ok = QInputDialog.getText(self, "Add key", "Settings key (dot notation ok):")
        key = (key or "").strip()
        if not ok or not key:
            return
        if _get(self._working, key) is _MISSING:
            _set(self._working, key, "")
        self._rebuild_tree()
        # select it
        for i in range(self._tree.topLevelItemCount()):
            top = self._tree.topLevelItem(i)
            for j in range(top.childCount()):
                if top.child(j).data(0, Qt.ItemDataRole.UserRole) == key:
                    self._tree.setCurrentItem(top.child(j))
                    return

    # -- filter -----------------------------------------------------------

    def _apply_filter(self, text: str):
        t = text.lower().strip()
        for i in range(self._tree.topLevelItemCount()):
            top = self._tree.topLevelItem(i)
            visible = 0
            for j in range(top.childCount()):
                c = top.child(j)
                key = (c.data(0, Qt.ItemDataRole.UserRole) or "").lower()
                spec = _SCHEMA_BY_KEY.get(c.data(0, Qt.ItemDataRole.UserRole), {})
                hit = (not t) or t in key or t in spec.get("desc", "").lower() or t in spec.get("cat", "").lower()
                c.setHidden(not hit)
                visible += hit
            top.setHidden(visible == 0)

    # -- save -----------------------------------------------------------

    def _save(self, backup: bool):
        scope = self._scope()
        ready = scope.get("ready")
        if ready:
            ok, why = ready()
            if not ok:
                QMessageBox.warning(self, "Not available", why)
                return
        # surface any invalid JSON block before writing
        bad = [s["key"] for s in SCHEMA if s["type"] == "json"
               and isinstance(_get(self._working, s["key"]), str)]
        path = scope["path"]()
        try:
            if backup and self._backup and isinstance(path, Path) and path.exists():
                self._backup.create_file_backup(path)
            scope["save"](self._working)
        except Exception as e:
            logger.error("save settings failed: %s", e)
            QMessageBox.critical(self, "Save Error", str(e))
            return
        self._status.setText(f"Saved to {path}")
        QMessageBox.information(self, "Saved", f"Settings saved to:\n{path}")

    # -- host hooks ------------------------------------------------------

    def load_settings(self, *_):
        self.reload()

    def apply_theme(self):
        pass


# ── scope factories ─────────────────────────────────────────────────────────

def user_scope(config_manager) -> list[dict]:
    return [{
        "label": "User (~/.claude/settings.json)",
        "path": lambda: getattr(config_manager, "settings_file", None),
        "load": config_manager.get_settings,
        "save": lambda d: config_manager.save_settings(d),
    }]


def project_scopes(settings_manager, project_context) -> list[dict]:
    def _ready():
        if project_context and project_context.has_project():
            return True, ""
        return False, "Select a project first (Project Config → Projects)."

    def _p(name):
        if project_context and project_context.has_project():
            return Path(project_context.get_project()) / ".claude" / name
        return None

    return [
        {
            "label": "Shared (.claude/settings.json)", "ready": _ready,
            "path": lambda: _p("settings.json"),
            "load": lambda: settings_manager.get_project_shared_settings(project_context.get_project()),
            "save": lambda d: settings_manager.save_settings(_p("settings.json"), d),
        },
        {
            "label": "Local (.claude/settings.local.json)", "ready": _ready,
            "path": lambda: _p("settings.local.json"),
            "load": lambda: settings_manager.get_project_local_settings(project_context.get_project()),
            "save": lambda d: settings_manager.save_settings(_p("settings.local.json"), d),
        },
    ]
