#!/usr/bin/env python3
"""
Claude_DB - PyQt6 Application for Claude Code Configuration Management
Main application entry point
"""

import sys
import json
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QTabBar, QStackedWidget, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPalette, QColor, QIcon

# ── Logging setup ────────────────────────────────────────────────────────────
_LOG_DIR = Path(__file__).parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[
        TimedRotatingFileHandler(
            _LOG_DIR / "claude_db.log",
            when="midnight",
            backupCount=7,
            encoding="utf-8",
        ),
        logging.StreamHandler(),  # console: all levels
    ],
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── QTextBrowser HTML-source tracking ────────────────────────────────────────
# toHtml() destroys original tag structure (converts <code>, <h2>, etc. to
# <span> with baked-in inline styles).  We monkey-patch setHtml to store the
# CLEAN original source (with any injected <style> blocks stripped) so that
# _push_app_stylesheet() always re-injects from the clean base.
import re as _re
from PyQt6.QtWidgets import QTextBrowser as _QTextBrowser

_orig_setHtml = _QTextBrowser.setHtml


def _tracked_setHtml(self, html: str) -> None:  # type: ignore[override]
    import logging as _logging
    _log = _logging.getLogger("setHtml_patch")

    # Store the clean source so _reinject_html_css can call setHtml again later.
    self.setProperty("_html_source", html)

    # Apply stored document CSS via setDefaultStyleSheet BEFORE the HTML is
    # parsed — this is the only reliable way to get Qt's HTML renderer to
    # honour custom colors.  The QPalette color (from QSS) overrides inline CSS
    # in Qt's HTML renderer, but setDefaultStyleSheet is applied at parse time
    # before the palette override kicks in.
    stored_css = self.property("_doc_css") or ""
    if stored_css:
        self.document().setDefaultStyleSheet(stored_css)
        _log.debug("setHtml: applied _doc_css (%d chars) to browser %s", len(stored_css), id(self))

    _orig_setHtml(self, html)
    _log.debug("setHtml done on browser %s, html len=%d", id(self), len(html))


_QTextBrowser.setHtml = _tracked_setHtml  # type: ignore[method-assign]

# Import tab modules
from tabs.prompts_tab import PromptsTab
from tabs.plugins_tab import PluginsTab
from tabs.memory_tab import MemoryTab
from tabs.usage_tab import UsageTab
from tabs.documentation_tab import DocumentationTab
from tabs.claudekit_tab import ClaudeKitTab
from tabs.tools_tab import ToolsTab
from tabs.about_tab import AboutTab
from tabs.preferences_tab import PreferencesTab
from tabs.user_config_tab import UserConfigTab
from tabs.project_config_tab import ProjectConfigTab
from tabs.remote_servers_tab import RemoteServersTab

from utils.config_manager import ConfigManager, ConfigManagerProxy
from utils.backup_manager import BackupManager
from utils.settings_manager import SettingsManager
from utils.project_context import ProjectContext
from utils import theme
from modules.remote import ServerRegistry, ServerContext, ConnectionManager

class ClaudeDBApp(QMainWindow):
    """Main application window for Claude_DB"""

    def __init__(self, app):
        super().__init__()
        self.app = app  # Store QApplication instance for dynamic theme switching

        # Local config manager (always available as the local baseline)
        self._local_config_manager = ConfigManager()
        # Proxy wraps the local CM at startup; swapped to remote CM on connect
        self.config_manager = ConfigManagerProxy(self._local_config_manager)

        self.backup_manager = BackupManager()

        # Remote infrastructure
        self.server_registry = ServerRegistry()
        self.server_context = ServerContext()
        self.connection_manager = ConnectionManager()

        # Initialize utilities for new refactored tabs
        user_settings_path = Path.home() / ".claude" / "settings.json"
        self.settings_manager = SettingsManager(user_settings_path)
        self.project_context = ProjectContext()

        # Auto-detect project folder from current working directory
        cwd = Path.cwd()
        if cwd.exists() and cwd.is_dir():
            self.project_context.set_project(cwd)
            logger.info(f"Auto-detected project folder: {cwd}")

        # Set application icon BEFORE applying theme (to prevent theme override)
        self.set_app_icon()

        # Load saved preferences and apply theme before creating UI
        self.load_saved_preferences()

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Claude_DB - Claude Code Configuration Manager")
        self.resize(1200, 800)

        # Theme is already applied in load_saved_preferences()
        # No need to override it here

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Tab bar style — built from theme variables so it updates on theme change
        tab_bar_style = f"""
            QTabBar::tab {{
                background: {theme.BG_MEDIUM};
                color: {theme.FG_SECONDARY};
                padding: 8px 12px;
                margin-right: 2px;
                border: 1px solid {theme.BG_LIGHT};
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                font-weight: bold;
                border-bottom: 2px solid {theme.ACCENT_PRIMARY};
            }}
            QTabBar::tab:hover:!selected {{
                background: {theme.BG_LIGHT};
                color: {theme.FG_PRIMARY};
            }}
        """

        # Create two tab bars (just the tab buttons, no content panes)
        self.tab_bar_row1 = QTabBar()
        self.tab_bar_row1.setStyleSheet(tab_bar_style)

        self.tab_bar_row2 = QTabBar()
        self.tab_bar_row2.setStyleSheet(tab_bar_style)

        # Create single content area (stacked widget)
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet(
            f"QStackedWidget {{ border: 1px solid {theme.BG_LIGHT}; background: {theme.BG_DARK}; }}"
        )

        # Define all tabs with their widgets - use keys for lookup
        # Key format: "tab_key" -> (default_display_name, widget)
        # Store as instance variable so preferences_tab can access it
        self.all_tabs = {
            "userconfig": ("👤 User Config", UserConfigTab(self.config_manager, self.backup_manager, self.settings_manager)),
            "projectconfig": ("📁 Project Config", ProjectConfigTab(self.config_manager, self.backup_manager, self.settings_manager, self.project_context)),
            "prompts": ("💬 Prompts", PromptsTab(self.config_manager, self.backup_manager)),
            "plugins": ("🧩 Plugins", PluginsTab(self.config_manager, self.backup_manager)),
            "memory": ("📁 Files", MemoryTab(self.config_manager, self.backup_manager)),
            "usage": ("📈 Usage & Analytics", UsageTab(self.config_manager, self.backup_manager)),
            "docs": ("📚 Documentation", DocumentationTab()),
            "claudekit": ("🛠️ ClaudeKit", ClaudeKitTab()),
            "tools": ("🔧 Tools", ToolsTab()),
            "about": ("ℹ️ About", AboutTab()),
            "preferences": ("🎨 Preferences", PreferencesTab(self.config_manager, self.backup_manager, self.app)),
            "remote_servers": ("🌐 Remote", RemoteServersTab(self.server_registry, self.connection_manager, self.server_context)),
        }

        # Default tab order (using keys)
        default_row1 = ["userconfig", "projectconfig", "prompts", "plugins", "memory"]
        default_row2 = ["usage", "docs", "claudekit", "tools", "about", "preferences", "remote_servers"]

        # Load custom tab configuration from config
        row1_tabs, row2_tabs = self.load_tab_configuration(self.all_tabs, default_row1, default_row2)

        # Add tabs to row 1 bar and content stack
        for display_name, widget in row1_tabs:
            self.tab_bar_row1.addTab(display_name)
            self.content_stack.addWidget(widget)

        # Add tabs to row 2 bar and content stack (indices continue)
        self.row1_count = len(row1_tabs)
        for display_name, widget in row2_tabs:
            self.tab_bar_row2.addTab(display_name)
            self.content_stack.addWidget(widget)

        # Connect tab bars to content stack
        # Use tabBarClicked instead of currentChanged to handle re-clicking same tab
        self.tab_bar_row1.tabBarClicked.connect(self.switch_to_row1_tab)
        self.tab_bar_row2.tabBarClicked.connect(self.switch_to_row2_tab)

        # ── Amber remote banner (hidden when local) ───────────────────────────
        self._remote_banner = QFrame()
        self._remote_banner.setVisible(False)
        self._remote_banner.setStyleSheet(
            "QFrame { background: #E8A000; border-radius: 3px; }"
        )
        banner_row = QHBoxLayout(self._remote_banner)
        banner_row.setContentsMargins(10, 4, 10, 4)
        self._remote_banner_lbl = QLabel("Remote: —")
        self._remote_banner_lbl.setStyleSheet(
            "color: #000; font-weight: bold; background: transparent;"
        )
        self._remote_discon_btn = QPushButton("Disconnect")
        self._remote_discon_btn.setStyleSheet(
            "QPushButton { background: rgba(0,0,0,0.15); color: #000;"
            " border: 1px solid rgba(0,0,0,0.3); border-radius: 3px; padding: 2px 8px; }"
            "QPushButton:hover { background: rgba(0,0,0,0.25); }"
        )
        self._remote_discon_btn.clicked.connect(self._on_remote_disconnect)
        banner_row.addWidget(self._remote_banner_lbl, 1)
        banner_row.addWidget(self._remote_discon_btn)

        # ── Add to layout ─────────────────────────────────────────────────────
        main_layout.addWidget(self._remote_banner)
        main_layout.addWidget(self.tab_bar_row1)
        main_layout.addWidget(self.tab_bar_row2)
        main_layout.addWidget(self.content_stack)

        # Add toolbar
        toolbar = self.create_toolbar()
        main_layout.addLayout(toolbar)

        # GitHub rate-limit indicator shown in window title when active
        self._github_label = QLabel("")
        self._github_label.hide()  # kept for API compatibility but not displayed

        # Connect server_changed → rebuild ConfigManager proxy delegate
        self.server_context.server_changed.connect(self._on_server_changed)

        # Health-check timer: poll connection every 30 s while remote is active
        self._health_timer = QTimer(self)
        self._health_timer.setInterval(30_000)
        self._health_timer.timeout.connect(self._check_connection_health)

        # Auto-reconnect to last-used server (deferred so all tabs are ready)
        QTimer.singleShot(500, self._try_reconnect_last_server)

        # Connect preferences signals → MainWindow handlers
        prefs_widget = self.all_tabs.get("preferences")
        if prefs_widget:
            _, prefs_tab = prefs_widget
            if hasattr(prefs_tab, "theme_changed"):
                prefs_tab.theme_changed.connect(self.apply_theme_change)
            if hasattr(prefs_tab, "navigate_to"):
                prefs_tab.navigate_to.connect(self.navigate_to_class)

    # ── Remote mode ───────────────────────────────────────────────────────────

    def _on_server_changed(self, server_cfg) -> None:
        """Called when ServerContext fires server_changed (None = local)."""
        if server_cfg is None:
            # Back to local
            self._health_timer.stop()
            self._remote_banner.setVisible(False)
            self.config_manager.set_delegate(self._local_config_manager)
            self._save_last_server(None)
            self.project_context.clear_project()
            logger.info("Switched to local mode")
        else:
            # Switched to a remote server
            label = self.server_context.get_label()
            self._remote_banner_lbl.setText(f"  Remote: {label}")
            self._remote_banner.setVisible(True)

            # Build a ConfigManager backed by the remote filesystem
            try:
                from utils.config_manager import ConfigManager as _CM
                from modules.remote.remote_path import RemotePath
                claude_dir = self.connection_manager.get_claude_dir()
                remote_cm = _CM(
                    fs=self.connection_manager.fs,
                    claude_dir=RemotePath(claude_dir) if claude_dir else None,
                )
                self.config_manager.set_delegate(remote_cm)
                logger.info("Switched to remote mode: %s (claude_dir=%s)", label, claude_dir)
            except Exception as exc:
                logger.error("Failed to build remote ConfigManager: %s", exc)
                self._remote_banner_lbl.setText(f"  Remote: {label}  ⚠ config error")

            self._save_last_server(server_cfg.get("id"))
            self.project_context.clear_project()
            self._health_timer.start()

        # Refresh tabs that show server-dependent data (deferred so CM proxy is ready)
        QTimer.singleShot(0, self._refresh_server_dependent_tabs)

    def _on_remote_disconnect(self) -> None:
        """Disconnect button in amber banner clicked."""
        self.connection_manager.disconnect()
        self.server_context.set_active(None)

    def _check_connection_health(self) -> None:
        """Called every 30 s while connected; reverts to local if connection dropped."""
        if not self._remote_banner.isVisible():
            self._health_timer.stop()
            return
        if not self.connection_manager.is_connected():
            logger.warning("Health check: remote connection lost — reverting to local")
            self._remote_banner_lbl.setText(
                self._remote_banner_lbl.text() + "  ⚠ connection lost"
            )
            self._on_remote_disconnect()

    def _refresh_server_dependent_tabs(self) -> None:
        """Refresh memory and project-config tabs after a server switch."""
        memory_entry = self.all_tabs.get("memory")
        if memory_entry:
            _, memory_tab = memory_entry
            if hasattr(memory_tab, "refresh_all"):
                try:
                    memory_tab.refresh_all()
                except Exception as exc:
                    logger.warning("memory_tab.refresh_all failed: %s", exc)

        proj_entry = self.all_tabs.get("projectconfig")
        if proj_entry:
            _, proj_tab = proj_entry
            if hasattr(proj_tab, "refresh_projects"):
                try:
                    proj_tab.refresh_projects()
                except Exception as exc:
                    logger.warning("project_config_tab.refresh_projects failed: %s", exc)

        user_entry = self.all_tabs.get("userconfig")
        if user_entry:
            _, user_tab = user_entry
            if hasattr(user_tab, "refresh_all"):
                try:
                    user_tab.refresh_all()
                except Exception as exc:
                    logger.warning("user_config_tab.refresh_all failed: %s", exc)

    # ── Last-server persistence ────────────────────────────────────────────────

    def _config_file_path(self) -> Path:
        return Path(__file__).parent.parent / "config" / "config.json"

    def _save_last_server(self, server_id: str | None) -> None:
        from utils import app_config

        def _mut(d: dict):
            if server_id:
                d["last_server_id"] = server_id
            else:
                d.pop("last_server_id", None)
        try:
            app_config.update(_mut, self._config_file_path())
        except Exception as exc:
            logger.warning("Could not save last_server_id: %s", exc)

    def _try_reconnect_last_server(self) -> None:
        """On startup, silently reconnect to the last used remote server if available."""
        try:
            cfg_path = self._config_file_path()
            if not cfg_path.exists():
                return
            with open(cfg_path, encoding="utf-8") as f:
                data = json.load(f)
            last_id = data.get("last_server_id")
            if not last_id:
                return
            server = self.server_registry.get_server(last_id)
            if not server:
                return
            logger.info("Auto-reconnecting to last server: %s", last_id)
            remote_entry = self.all_tabs.get("remote_servers")
            if remote_entry:
                _, remote_tab = remote_entry
                if hasattr(remote_tab, "_connect"):
                    # Select the server in the table then trigger connect
                    self._auto_connect_server(remote_tab, server)
        except Exception as exc:
            logger.warning("Auto-reconnect skipped: %s", exc)

    def _auto_connect_server(self, remote_tab, server_cfg: dict) -> None:
        """Select server in the table and trigger the connect flow."""
        try:
            from PyQt6.QtCore import QThread
            from modules.remote.ssh_client import SSHConnectionError

            # Find the row matching this server id in the table
            table = remote_tab._table
            sid = server_cfg.get("id", "")
            for row in range(table.rowCount()):
                item = table.item(row, 0)
                if item and item.data(Qt.ItemDataRole.UserRole) == sid:
                    table.selectRow(row)
                    break
            remote_tab._connect()
        except Exception as exc:
            logger.warning("_auto_connect_server failed: %s", exc)

    def set_dark_theme(self):
        """Set dark theme for better visibility"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(43, 43, 43))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
        palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(102, 126, 234))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        self.setPalette(palette)

    def create_header(self):
        """Create application header"""
        header_widget = QWidget()
        header_widget.setMaximumHeight(60)
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 5, 10, 5)
        header_layout.setSpacing(2)

        title = QLabel("Claude Code Configuration Manager")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel(f"Config: {self.config_manager.claude_dir}")
        subtitle.setStyleSheet(f"font-size: 11px; color: {theme.FG_SECONDARY};")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        return header_widget

    def create_toolbar(self):
        """Create bottom toolbar with global actions"""
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(10)

        # Backup buttons moved to Preferences tab
        toolbar_layout.addStretch()

        return toolbar_layout

    # ── Status bar helpers ────────────────────────────────────────────────

    def set_status(self, message: str, is_error: bool = False, timeout: int = 5000) -> None:
        """Log a status message (status bar removed — kept for tab API compatibility)."""
        logger.debug(f"Status: {message}")

    def update_github_status(self, remaining: int) -> None:
        """No-op — status bar removed."""
        pass

    # ── Theme switching ───────────────────────────────────────────────────

    def apply_theme_change(self, theme_name: str, font_size: int) -> None:
        """Apply a new theme instantly across the whole application.

        Connected to PreferencesTab.theme_changed signal.
        Applies the app-level stylesheet and rebuilds the two tab-bar stylesheets
        from current theme variables so hardcoded colours stay correct.
        """
        _theme = theme
        _theme.apply_theme(theme_name, font_size)
        self.app.setStyleSheet(_theme.generate_app_stylesheet())

        # Rebuild tab bar stylesheets from theme variables (they were set with
        # hardcoded colours in init_ui; refresh them here so they match the new theme)
        tab_bar_style = f"""
            QTabBar::tab {{
                background: {_theme.BG_MEDIUM};
                color: {_theme.FG_SECONDARY};
                padding: 8px 12px;
                margin-right: 2px;
                border: 1px solid {_theme.BG_LIGHT};
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background: {_theme.BG_DARK};
                color: {_theme.FG_PRIMARY};
                font-weight: bold;
                border-bottom: 2px solid {_theme.ACCENT_PRIMARY};
            }}
            QTabBar::tab:hover:!selected {{
                background: {_theme.BG_LIGHT};
                color: {_theme.FG_PRIMARY};
            }}
        """
        self.tab_bar_row1.setStyleSheet(tab_bar_style)
        self.tab_bar_row2.setStyleSheet(tab_bar_style)

        # Refresh header subtitle colour
        self.content_stack.setStyleSheet(
            f"QStackedWidget {{ border: 1px solid {_theme.BG_LIGHT}; background: {_theme.BG_DARK}; }}"
        )

        # Call apply_theme() on any tab that has custom per-widget theme styling
        for _tab_widget in self.all_tabs.values():
            widget = _tab_widget[1] if isinstance(_tab_widget, tuple) else _tab_widget
            if hasattr(widget, 'apply_theme'):
                widget.apply_theme()

        logger.info(f"Theme changed to '{theme_name}' {font_size}px")

    # ── Navigation ────────────────────────────────────────────────────────────

    def navigate_to_class(self, class_name: str) -> bool:
        """Switch to the tab/subtab that contains the given class name.

        Checks:
          1. Is this a main-tab widget? Switch to it directly.
          2. Does any main tab have a sub_tabs (QTabWidget) containing this class?
             If so, switch to the main tab and select the subtab.
          3. If it looks like a Dialog, try to find the main tab from which the
             dialog's file is referenced and switch to that tab.

        Returns True if navigation succeeded.
        """
        from PyQt6.QtWidgets import QTabWidget as _QTW

        # ── Pass 1: direct main-tab match ─────────────────────────────────────
        for tab_key, (_, widget) in self.all_tabs.items():
            if type(widget).__name__ == class_name:
                self._switch_to_tab_key(tab_key)
                logger.debug(f"Navigated to main tab '{tab_key}' for class '{class_name}'")
                return True

        # ── Pass 2: subtab match ───────────────────────────────────────────────
        # Look for a QTabWidget attribute called 'sub_tabs' on any main tab
        for tab_key, (_, widget) in self.all_tabs.items():
            sub_tw = getattr(widget, 'sub_tabs', None)
            if not isinstance(sub_tw, _QTW):
                continue
            for i in range(sub_tw.count()):
                subtab = sub_tw.widget(i)
                if type(subtab).__name__ == class_name:
                    self._switch_to_tab_key(tab_key)
                    sub_tw.setCurrentIndex(i)
                    logger.debug(
                        f"Navigated to '{tab_key}' subtab {i} ('{class_name}')"
                    )
                    return True

        # ── Pass 3: dialog — find which main tab its source file belongs to ───
        # For dialogs we can only navigate to the parent tab, not open the dialog.
        # We map dialog class → the main tab it's associated with by source file.
        # Fall back to a best-guess based on class name keywords.
        if class_name.endswith("Dialog"):
            hints = {
                "Agent":       "userconfig",
                "Server":      "userconfig",
                "Permission":  "userconfig",
                "Mcp":         "userconfig",
                "MCP":         "userconfig",
                "Skill":       "userconfig",
                "Command":     "userconfig",
                "Prompt":      "prompts",
                "Tab":         "preferences",
                "Backup":      "preferences",
                "Theme":       "preferences",
                "Import":      "prompts",
                "Rule":        "userconfig",
            }
            for keyword, tab_key in hints.items():
                if keyword in class_name and tab_key in self.all_tabs:
                    self._switch_to_tab_key(tab_key)
                    logger.debug(
                        f"Navigated to '{tab_key}' (dialog hint for '{class_name}')"
                    )
                    return True

        logger.warning(f"navigate_to_class: could not find '{class_name}'")
        return False

    def _switch_to_tab_key(self, tab_key: str):
        """Switch the content stack to the tab identified by key.

        Finds the widget in the content stack by identity (safe regardless of
        which order tabs were added) and dispatches to row1/row2 switch.
        """
        entry = self.all_tabs.get(tab_key)
        if not entry:
            return
        target_widget = entry[1]

        # Find the stack index by scanning for widget identity
        for stack_idx in range(self.content_stack.count()):
            if self.content_stack.widget(stack_idx) is target_widget:
                if stack_idx < self.row1_count:
                    self.switch_to_row1_tab(stack_idx)
                else:
                    self.switch_to_row2_tab(stack_idx - self.row1_count)
                return

    def create_backup(self):
        """Create backup of all configuration files"""
        try:
            backup_path = self.backup_manager.create_full_backup()
            QMessageBox.information(
                self,
                "Backup Created",
                f"Configuration backup successfully created:\n{backup_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Backup Failed",
                f"Failed to create backup:\n{str(e)}"
            )

    def backup_program_files(self):
        """Launch backup script in a terminal (cross-platform)."""
        from utils.terminal_utils import run_in_terminal
        script_path = Path(__file__).parent.parent / "backup_program.sh"
        if not script_path.exists():
            self.set_status("Backup script not found", is_error=True)
            return
        run_in_terminal(f'bash "{script_path}"', title="Backup", parent_widget=self)
        self.set_status("Backup script launched", timeout=3000)

    def switch_to_row1_tab(self, index):
        """Switch to a tab from row 1"""
        if index >= 0:
            self.tab_bar_row1.setCurrentIndex(index)
            self.tab_bar_row2.blockSignals(True)
            self.tab_bar_row2.setCurrentIndex(-1)
            self.tab_bar_row2.blockSignals(False)
            self.content_stack.setCurrentIndex(index)

    def switch_to_row2_tab(self, index):
        """Switch to a tab from row 2"""
        if index >= 0:
            stack_index = self.row1_count + index
            self.tab_bar_row2.setCurrentIndex(index)
            self.tab_bar_row1.blockSignals(True)
            self.tab_bar_row1.setCurrentIndex(-1)
            self.tab_bar_row1.blockSignals(False)
            self.content_stack.setCurrentIndex(stack_index)

    def load_tab_configuration(self, all_tabs, default_row1, default_row2):
        """Load tab configuration from config file
        Returns: (row1_tabs, row2_tabs) where each is [(display_name, widget), ...]
        """
        try:
            config_file = Path(__file__).parent.parent / "config" / "config.json"

            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                # Get tabs configuration
                tabs_config = config_data.get("tabs", {})
                row1_config = tabs_config.get("row1", [])
                row2_config = tabs_config.get("row2", [])

                # Build tab lists from config
                # Config format: [{"key": "settings", "name": "⚙️ Settings"}, ...]
                row1_tabs = []
                row2_tabs = []

                if row1_config:
                    for tab_info in row1_config:
                        key = tab_info.get("key")
                        custom_name = tab_info.get("name")
                        if key in all_tabs:
                            default_name, widget = all_tabs[key]
                            display_name = custom_name if custom_name else default_name
                            row1_tabs.append((display_name, widget))
                    logger.debug(f"Loaded {len(row1_tabs)} tabs for row 1 from config")

                if row2_config:
                    for tab_info in row2_config:
                        key = tab_info.get("key")
                        custom_name = tab_info.get("name")
                        if key in all_tabs:
                            default_name, widget = all_tabs[key]
                            display_name = custom_name if custom_name else default_name
                            row2_tabs.append((display_name, widget))
                    logger.debug(f"Loaded {len(row2_tabs)} tabs for row 2 from config")

                # If config exists but is empty, use defaults
                if not row1_tabs and not row2_tabs:
                    return self._build_default_tabs(all_tabs, default_row1, default_row2)

                # Auto-add any newly registered tabs that aren't in the saved config
                configured_keys = set()
                for tab_info in row1_config + row2_config:
                    configured_keys.add(tab_info.get("key"))
                for key in default_row1 + default_row2:
                    if key not in configured_keys and key in all_tabs:
                        default_name, widget = all_tabs[key]
                        row2_tabs.append((default_name, widget))
                        logger.info("Auto-added new tab to row 2: %s", key)

                return row1_tabs, row2_tabs
            else:
                logger.info("No config file found, using default tab configuration")
                return self._build_default_tabs(all_tabs, default_row1, default_row2)

        except Exception as e:
            logger.warning(f"Failed to load tab configuration: {e}, using defaults")
            return self._build_default_tabs(all_tabs, default_row1, default_row2)

    def _build_default_tabs(self, all_tabs, default_row1, default_row2):
        """Build default tab lists"""
        row1_tabs = [(all_tabs[key][0], all_tabs[key][1]) for key in default_row1 if key in all_tabs]
        row2_tabs = [(all_tabs[key][0], all_tabs[key][1]) for key in default_row2 if key in all_tabs]
        return row1_tabs, row2_tabs

    def set_app_icon(self):
        """Set application icon from assets folder"""
        try:
            # Get the project root directory (parent of src/)
            project_root = Path(__file__).parent.parent

            # Try .ico first (preferred for Windows), then .png
            icon_paths = [
                project_root / "assets" / "claude_db_icon.ico",
                project_root / "assets" / "claude_db_icon.png"
            ]

            for icon_path in icon_paths:
                if icon_path.exists():
                    icon = QIcon(str(icon_path))
                    if not icon.isNull():
                        self.setWindowIcon(icon)
                        self.app.setWindowIcon(icon)
                        logger.debug(f"Application icon set: {icon_path}")
                        return

            logger.debug("No application icon found in assets/ folder")

        except Exception as e:
            logger.warning(f"Failed to set application icon: {e}")

    def load_saved_preferences(self):
        """Load saved preferences and apply theme on startup"""
        try:
            from utils import theme

            # Read active theme name and per-theme settings from themes.json
            theme_name = theme.get_active_theme_name()
            all_themes = theme.load_themes()
            entry = all_themes.get(theme_name, all_themes.get("Gruvbox Dark", {}))
            font_size = entry.get("font_size", 14)
            font_family = entry.get("font_family", "Segoe UI")

            theme.apply_theme(theme_name, font_size, font_family)

            app = QApplication.instance()
            if app:
                app.setStyleSheet(theme.generate_app_stylesheet())

            logger.info(f"Loaded preferences: {theme_name} theme with {font_size}px font")
        except Exception as e:
            logger.warning(f"Failed to load preferences: {e}")
            app = QApplication.instance()
            if app:
                app.setStyleSheet(theme.generate_app_stylesheet())

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Set application metadata
    app.setApplicationName("Claude_DB")
    app.setOrganizationName("Claude Code Tools")
    app.setApplicationVersion("2.0.0")

    # Create and show main window (pass app instance for dynamic theme switching)
    window = ClaudeDBApp(app)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
