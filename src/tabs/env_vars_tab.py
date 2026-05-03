"""
Environment Variables Tab - split screen:
  Left:  current env vars from settings.json (editable)
  Right: reference table of all known Claude env vars with descriptions
"""

import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QMessageBox, QListWidget, QInputDialog,
    QListWidgetItem, QGroupBox, QLineEdit, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from utils import theme
import logging
logger = logging.getLogger(__name__)


# ── Reference data ────────────────────────────────────────────────────────────

_ENV_VARS = [
    # (name, category, default, description)
    ("ANTHROPIC_API_KEY", "API", "", "Anthropic API key for authentication"),
    ("ANTHROPIC_AUTH_TOKEN", "API", "", "Alternative auth token for Anthropic services"),
    ("ANTHROPIC_BASE_URL", "API", "https://api.anthropic.com", "Custom base URL for Anthropic API"),
    ("ANTHROPIC_API_URL", "API", "", "Full API URL override"),
    ("ANTHROPIC_MODEL", "Model", "claude-sonnet-4-5", "Default model for Claude Code sessions"),
    ("ANTHROPIC_SMALL_FAST_MODEL", "Model", "claude-haiku-4-5", "Fast model for lightweight tasks"),
    ("ANTHROPIC_DEFAULT_SONNET_MODEL", "Model", "", "Specific Sonnet version to use"),
    ("ANTHROPIC_DEFAULT_HAIKU_MODEL", "Model", "", "Specific Haiku version to use"),
    ("ANTHROPIC_DEFAULT_OPUS_MODEL", "Model", "", "Specific Opus version to use"),
    ("ANTHROPIC_TIMEOUT", "Timeout", "60000", "API request timeout in ms"),
    ("BASH_DEFAULT_TIMEOUT_MS", "Timeout", "120000", "Default bash command timeout in ms"),
    ("BASH_MAX_TIMEOUT_MS", "Timeout", "600000", "Max bash command timeout in ms"),
    ("MCP_TIMEOUT", "Timeout", "30000", "MCP server operation timeout in ms"),
    ("MCP_TOOL_TIMEOUT", "Timeout", "60000", "MCP tool call timeout in ms"),
    ("DISABLE_TELEMETRY", "Feature", "false", "Set true to disable usage telemetry"),
    ("DISABLE_PROMPT_CACHING", "Feature", "false", "Set true to disable prompt caching"),
    ("DISABLE_PROMPT_CACHING_FOR_AGENTS", "Feature", "false", "Disable prompt caching for agents only"),
    ("ENABLE_EXPERIMENTAL_FEATURES", "Feature", "false", "Enable experimental Claude Code features"),
    ("MAX_THINKING_TOKENS", "Feature", "31999", "Budget cap for extended thinking tokens"),
    ("HTTP_PROXY", "Proxy", "", "HTTP proxy URL (e.g. http://proxy:8080)"),
    ("HTTPS_PROXY", "Proxy", "", "HTTPS proxy URL for secure connections"),
    ("NO_PROXY", "Proxy", "", "Comma-separated hosts to bypass proxy"),
    ("ALL_PROXY", "Proxy", "", "Proxy URL for all protocols"),
    ("DEBUG", "Logging", "false", "Enable debug mode with verbose logging"),
    ("VERBOSE", "Logging", "false", "Enable verbose output"),
    ("LOG_LEVEL", "Logging", "warn", "Logging level: debug, info, warn, error"),
    ("OTEL_EXPORTER_OTLP_ENDPOINT", "Telemetry", "", "OpenTelemetry OTLP endpoint URL"),
    ("OTEL_EXPORTER_OTLP_HEADERS", "Telemetry", "", "OTLP export headers (key=value,key=value)"),
    ("CLAUDE_CODE_ENABLE_TELEMETRY", "Telemetry", "false", "Enable OpenTelemetry tracing"),
    ("MCP_SERVER_PATH", "MCP", "", "Custom path to MCP server executable"),
    ("MCP_SERVER_COMMAND", "MCP", "", "Custom command to start MCP server"),
    ("CLAUDE_CONFIG_PATH", "Paths", "~/.claude", "Custom path to Claude config directory"),
    ("CLAUDE_CACHE_PATH", "Paths", "", "Custom path to Claude cache directory"),
    ("CLAUDE_PROJECT_ROOT", "Paths", "", "Override project root detection"),
    ("NODE_ENV", "System", "production", "Node.js environment (development/production/test)"),
    ("PATH", "System", "", "System PATH for executable lookup"),
    ("HOME", "System", "", "User home directory path"),
]

_SENSITIVE_KEYS = {"KEY", "TOKEN", "PASSWORD", "SECRET", "AUTH"}


class EnvVarsTab(QWidget):
    """Split-screen env vars: left = current settings, right = reference."""

    def __init__(self, config_manager, backup_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.settings_data = {}
        self._init_ui()
        self.load_env_vars()

    @property
    def settings_file(self):
        return self.config_manager.settings_file

    # ── UI construction ───────────────────────────────────────────────────────

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        # Header
        hdr = QLabel("Environment Variables")
        hdr.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};"
        )
        layout.addWidget(hdr)

        self._info_label = QLabel(f"Stored in: {self.settings_file}")
        self._info_label.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_SMALL}px; color: {theme.FG_SECONDARY}; font-style: italic;"
        )
        layout.addWidget(self._info_label)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(6)
        layout.addWidget(splitter, 1)

        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setSizes([420, 580])

    def _build_left_panel(self):
        """Left: current env vars from settings.json."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 4, 0)
        layout.setSpacing(4)

        grp = QGroupBox("Current Variables (settings.json)")
        inner = QVBoxLayout(grp)
        inner.setSpacing(4)

        # Search
        row = QHBoxLayout()
        row.setSpacing(4)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter…")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._filter)
        row.addWidget(QLabel("Search:"))
        row.addWidget(self._search, 1)
        inner.addLayout(row)

        # List
        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self.edit_env_var)
        inner.addWidget(self._list, 1)

        # Buttons
        btns = QHBoxLayout()
        btns.setSpacing(4)
        self._add_btn    = QPushButton("Add")
        self._edit_btn   = QPushButton("Edit")
        self._remove_btn = QPushButton("Remove")
        self._refresh_btn = QPushButton("Refresh")
        for b in (self._add_btn, self._edit_btn, self._remove_btn, self._refresh_btn):
            btns.addWidget(b)
        btns.addStretch()
        self._add_btn.clicked.connect(self.add_env_var)
        self._edit_btn.clicked.connect(self.edit_env_var)
        self._remove_btn.clicked.connect(self.remove_env_var)
        self._refresh_btn.clicked.connect(self.load_env_vars)
        inner.addLayout(btns)

        layout.addWidget(grp)
        return panel

    def _build_right_panel(self):
        """Right: reference table of all known env vars."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(4, 0, 0, 0)
        layout.setSpacing(4)

        grp = QGroupBox("All Claude Code Environment Variables (reference)")
        inner = QVBoxLayout(grp)
        inner.setSpacing(4)

        # Search
        row = QHBoxLayout()
        row.setSpacing(4)
        self._ref_search = QLineEdit()
        self._ref_search.setPlaceholderText("Filter reference…")
        self._ref_search.setClearButtonEnabled(True)
        self._ref_search.textChanged.connect(self._filter_ref)
        row.addWidget(QLabel("Search:"))
        row.addWidget(self._ref_search, 1)
        inner.addLayout(row)

        # Table
        self._ref_table = QTableWidget(0, 4)
        self._ref_table.setHorizontalHeaderLabels(["Variable", "Category", "Default", "Description"])
        hdr = self._ref_table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hdr.resizeSection(0, 230)
        hdr.resizeSection(1, 80)
        hdr.resizeSection(2, 100)
        hdr.resizeSection(3, 300)
        self._ref_table.verticalHeader().setVisible(False)
        self._ref_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._ref_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._ref_table.setSortingEnabled(True)
        self._ref_table.doubleClicked.connect(self._add_from_reference)
        inner.addWidget(self._ref_table, 1)

        tip = QLabel("Double-click a row to add that variable to your settings.")
        tip.setStyleSheet(
            f"color: {theme.FG_DIM}; font-size: {theme.FONT_SIZE_SMALL}px; font-style: italic;"
        )
        inner.addWidget(tip)

        layout.addWidget(grp)

        self._populate_ref_table()
        return panel

    def _populate_ref_table(self):
        """Fill reference table with all known env vars."""
        self._ref_table.setSortingEnabled(False)
        self._ref_table.setRowCount(0)
        for name, cat, default, desc in _ENV_VARS:
            row = self._ref_table.rowCount()
            self._ref_table.insertRow(row)
            for col, val in enumerate((name, cat, default, desc)):
                item = QTableWidgetItem(val)
                item.setToolTip(val)
                self._ref_table.setItem(row, col, item)
        self._ref_table.setSortingEnabled(True)

    # ── Data loading / saving ────────────────────────────────────────────────

    def load_env_vars(self):
        self._list.clear()
        self._info_label.setText(f"Stored in: {self.settings_file}")
        try:
            self.settings_data = self.config_manager.get_settings()
            env_vars = self.settings_data.get('env', {})
            if not env_vars:
                item = QListWidgetItem("No environment variables configured")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                item.setForeground(QColor(theme.FG_DIM))
                self._list.addItem(item)
            else:
                for key, value in sorted(env_vars.items()):
                    display = self._mask(key, value)
                    item = QListWidgetItem(f"{key} = {display}")
                    item.setData(Qt.ItemDataRole.UserRole, {'key': key, 'value': value})
                    item.setForeground(QColor(theme.SUCCESS_COLOR))
                    self._list.addItem(item)
        except Exception as e:
            logger.error("Failed to load env vars: %s", e)
            QMessageBox.critical(self, "Load Error", f"Failed to load env vars:\n{e}")

    def _save(self):
        try:
            sf = self.settings_file
            if isinstance(sf, Path) and sf.exists():
                self.backup_manager.create_file_backup(sf)
            self.config_manager.save_settings(self.settings_data)
            self.load_env_vars()
        except Exception as e:
            logger.error("Failed to save settings.json: %s", e)
            QMessageBox.critical(self, "Save Error", f"Failed to save settings.json:\n{e}")

    # ── Actions ──────────────────────────────────────────────────────────────

    def add_env_var(self, key_preset=""):
        """Add a new env var, optionally pre-filled with key_preset."""
        existing = self.settings_data.get('env', {})
        available = [name for name, *_ in _ENV_VARS if name not in existing]
        available.append("Custom…")

        if key_preset and key_preset not in existing:
            key = key_preset
        else:
            key, ok = QInputDialog.getItem(
                self, "Add Environment Variable",
                "Select variable to add:",
                available, 0, False
            )
            if not ok:
                return
            if key == "Custom…":
                key, ok = QInputDialog.getText(
                    self, "Custom Variable", "Variable name:"
                )
                if not ok or not key:
                    return
                key = key.strip().upper().replace(' ', '_')

        # Show description hint if known
        descs = {name: desc for name, _, _, desc in _ENV_VARS}
        if key in descs:
            hint = descs[key]
        else:
            hint = key

        value, ok = QInputDialog.getText(
            self, f"Value for {key}", hint + "\n\nEnter value:"
        )
        if not ok:
            return

        if 'env' not in self.settings_data:
            self.settings_data['env'] = {}
        self.settings_data['env'][key] = value
        self._save()

    def edit_env_var(self, _item=None):
        item = self._list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Select a variable to edit.")
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        key, old_val = data['key'], data['value']
        value, ok = QInputDialog.getText(
            self, f"Edit {key}", f"New value for {key}:", text=old_val
        )
        if not ok:
            return
        self.settings_data['env'][key] = value
        self._save()

    def remove_env_var(self):
        item = self._list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Select a variable to remove.")
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        key = data['key']
        if QMessageBox.question(
            self, "Confirm", f"Remove '{key}' from settings.json?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            del self.settings_data['env'][key]
            self._save()

    def _add_from_reference(self, index):
        """Double-click on reference row → pre-fill key in add dialog."""
        key = self._ref_table.item(index.row(), 0).text()
        self.add_env_var(key_preset=key)

    # ── Filtering ────────────────────────────────────────────────────────────

    def _filter(self, text):
        for i in range(self._list.count()):
            item = self._list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def _filter_ref(self, text):
        t = text.lower()
        for row in range(self._ref_table.rowCount()):
            match = any(
                t in (self._ref_table.item(row, col).text() or "").lower()
                for col in range(self._ref_table.columnCount())
            )
            self._ref_table.setRowHidden(row, not match)

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _mask(key, value):
        if any(s in key.upper() for s in _SENSITIVE_KEYS):
            return f"{value[:4]}…{value[-4:]}" if len(value) > 8 else "***"
        return value
