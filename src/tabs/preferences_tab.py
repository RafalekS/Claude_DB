"""
Preferences Tab - Application settings and theme management
"""

import json
import logging
import shutil
import sys
import tempfile
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QPushButton, QMessageBox, QGroupBox, QFormLayout,
    QDialog, QListWidget, QLineEdit, QTextEdit, QListWidgetItem, QInputDialog,
    QApplication, QTabWidget, QCheckBox, QAbstractItemView, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QTextBrowser,
    QScrollArea, QGridLayout
)
from PyQt6.QtCore import pyqtSignal, QProcess, Qt
from utils import theme
from utils.ui_state_manager import UIStateManager
from tabs.config_sync_tab import ConfigSyncTab
from tabs.widget_theme_editor import WidgetThemeEditor, ColorSwatch, WIDGET_DEFS
from utils.widget_indexer import load_navigation_tree, get_widgets_for_nav_entry

logger = logging.getLogger(__name__)

def _atomic_json_write(path: Path, data: dict) -> None:
    """Write *data* as JSON to *path* atomically (temp-file + rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.json', delete=False,
        dir=path.parent, encoding='utf-8'
    ) as tmp:
        json.dump(data, tmp, indent=2)
        tmp_path = tmp.name
    shutil.move(tmp_path, path)

# Load themes from config file
THEMES = theme.AVAILABLE_THEMES


class IntLineEdit(QLineEdit):
    """A compact numeric input that exposes .value() / .setValue() like QSpinBox,
    but looks like a plain text field — no arrow buttons."""
    from PyQt6.QtCore import pyqtSignal as _sig
    valueChanged = _sig(int)

    def __init__(self, lo: int, hi: int, val: int, parent=None):
        super().__init__(str(val), parent)
        from PyQt6.QtGui import QIntValidator
        self.setValidator(QIntValidator(lo, hi, self))
        self.textChanged.connect(self._on_text)

    def _on_text(self, text: str):
        try:
            self.valueChanged.emit(int(text))
        except ValueError:
            pass

    def value(self) -> int:
        try:
            return int(self.text())
        except ValueError:
            return 0

    def setValue(self, v: int):
        self.blockSignals(True)
        self.setText(str(v))
        self.blockSignals(False)


class TabEditorDialog(QDialog):
    """Unified dialog for reordering and renaming tabs"""

    def __init__(self, parent, tabs_row1, tabs_row2):
        super().__init__(parent)
        self.setWindowTitle("Edit Tabs - Reorder & Rename")
        self.setModal(True)
        self.resize(900, 800)

        # Store original names for rename tracking
        self.original_names = {}
        self.rename_map = {}

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Info label
        info = QLabel("Reorder tabs with Up/Down/Move buttons, or double-click a tab to rename it")
        info.setStyleSheet(f"font-size: {theme.FONT_SIZE_SMALL}px; color: {theme.FG_SECONDARY}; font-style: italic;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Row 1 tabs
        row1_label = QLabel("Row 1 Tabs:")
        row1_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_NORMAL}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")
        layout.addWidget(row1_label)

        self.row1_list = QListWidget()
        self.row1_list.setStyleSheet(f"""
            QListWidget {{
                font-size: {theme.FONT_SIZE_NORMAL}px;
                padding: 5px;
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
            }}
            QListWidget::item {{
                padding: 8px;
                color: {theme.FG_PRIMARY};
                background-color: {theme.BG_DARK};
            }}
            QListWidget::item:selected {{
                background-color: {theme.ACCENT_PRIMARY};
                color: {theme.BG_DARK};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {theme.BG_MEDIUM};
            }}
        """)
        for tab_name in tabs_row1:
            self.row1_list.addItem(tab_name)
            self.original_names[tab_name] = tab_name

        self.row1_list.itemDoubleClicked.connect(self.rename_tab_item)
        layout.addWidget(self.row1_list)

        row1_buttons = QHBoxLayout()
        up1_btn = QPushButton("▲ Move Up")
        down1_btn = QPushButton("▼ Move Down")
        to_row2_btn = QPushButton("➡️ Move to Row 2")
        rename1_btn = QPushButton("✏️ Rename Selected")

        to_row2_btn.setMinimumWidth(150)

        up1_btn.clicked.connect(lambda: self.move_item_up(self.row1_list))
        down1_btn.clicked.connect(lambda: self.move_item_down(self.row1_list))
        to_row2_btn.clicked.connect(self.move_to_row2)
        rename1_btn.clicked.connect(lambda: self.rename_selected_tab(self.row1_list))

        row1_buttons.addWidget(up1_btn)
        row1_buttons.addWidget(down1_btn)
        row1_buttons.addWidget(rename1_btn)
        row1_buttons.addWidget(to_row2_btn)
        row1_buttons.addStretch()
        layout.addLayout(row1_buttons)

        # Row 2 tabs
        row2_label = QLabel("Row 2 Tabs:")
        row2_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_NORMAL}px; font-weight: bold; color: {theme.ACCENT_PRIMARY}; margin-top: 10px;")
        layout.addWidget(row2_label)

        self.row2_list = QListWidget()
        self.row2_list.setStyleSheet(f"""
            QListWidget {{
                font-size: {theme.FONT_SIZE_NORMAL}px;
                padding: 5px;
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
            }}
            QListWidget::item {{
                padding: 8px;
                color: {theme.FG_PRIMARY};
                background-color: {theme.BG_DARK};
            }}
            QListWidget::item:selected {{
                background-color: {theme.ACCENT_PRIMARY};
                color: {theme.BG_DARK};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {theme.BG_MEDIUM};
            }}
        """)
        for tab_name in tabs_row2:
            self.row2_list.addItem(tab_name)
            self.original_names[tab_name] = tab_name

        self.row2_list.itemDoubleClicked.connect(self.rename_tab_item)
        layout.addWidget(self.row2_list)

        row2_buttons = QHBoxLayout()
        up2_btn = QPushButton("▲ Move Up")
        down2_btn = QPushButton("▼ Move Down")
        to_row1_btn = QPushButton("⬅️ Move to Row 1")
        rename2_btn = QPushButton("✏️ Rename Selected")

        to_row1_btn.setMinimumWidth(150)

        up2_btn.clicked.connect(lambda: self.move_item_up(self.row2_list))
        down2_btn.clicked.connect(lambda: self.move_item_down(self.row2_list))
        to_row1_btn.clicked.connect(self.move_to_row1)
        rename2_btn.clicked.connect(lambda: self.rename_selected_tab(self.row2_list))

        row2_buttons.addWidget(up2_btn)
        row2_buttons.addWidget(down2_btn)
        row2_buttons.addWidget(rename2_btn)
        row2_buttons.addWidget(to_row1_btn)
        row2_buttons.addStretch()
        layout.addLayout(row2_buttons)

        # Dialog buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def rename_tab_item(self, item):
        """Rename a tab via double-click"""
        self.rename_selected_tab(item.listWidget())

    def rename_selected_tab(self, list_widget):
        """Rename the selected tab in the given list"""
        current_item = list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a tab to rename")
            return

        current_text = current_item.text()

        # Find the original name
        original_name = current_text
        for orig, renamed in self.rename_map.items():
            if renamed == current_text:
                original_name = orig
                break

        new_name, ok = QInputDialog.getText(
            self,
            "Rename Tab",
            f"Enter new name for '{current_text}':",
            QLineEdit.EchoMode.Normal,
            current_text
        )

        if ok and new_name and new_name != current_text:
            current_item.setText(new_name)
            self.rename_map[original_name] = new_name

    def move_item_up(self, list_widget):
        """Move selected item up in the list"""
        current_row = list_widget.currentRow()
        if current_row > 0:
            item = list_widget.takeItem(current_row)
            list_widget.insertItem(current_row - 1, item)
            list_widget.setCurrentRow(current_row - 1)

    def move_item_down(self, list_widget):
        """Move selected item down in the list"""
        current_row = list_widget.currentRow()
        if current_row < list_widget.count() - 1 and current_row >= 0:
            item = list_widget.takeItem(current_row)
            list_widget.insertItem(current_row + 1, item)
            list_widget.setCurrentRow(current_row + 1)

    def move_to_row2(self):
        """Move selected item from Row 1 to Row 2"""
        current_row = self.row1_list.currentRow()
        if current_row >= 0:
            item = self.row1_list.takeItem(current_row)
            self.row2_list.addItem(item.text())
            if self.row1_list.count() > 0:
                new_row = min(current_row, self.row1_list.count() - 1)
                self.row1_list.setCurrentRow(new_row)

    def move_to_row1(self):
        """Move selected item from Row 2 to Row 1"""
        current_row = self.row2_list.currentRow()
        if current_row >= 0:
            item = self.row2_list.takeItem(current_row)
            self.row1_list.addItem(item.text())
            if self.row2_list.count() > 0:
                new_row = min(current_row, self.row2_list.count() - 1)
                self.row2_list.setCurrentRow(new_row)

    def get_ordered_tabs(self):
        """Get the new tab order"""
        row1 = [self.row1_list.item(i).text() for i in range(self.row1_list.count())]
        row2 = [self.row2_list.item(i).text() for i in range(self.row2_list.count())]
        return row1, row2

    def get_rename_map(self):
        """Get the rename mapping"""
        return self.rename_map

class AddNewTabDialog(QDialog):
    """Dialog for adding a new empty tab"""

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Add New Tab")
        self.setModal(True)
        self.resize(700, 400)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        info = QLabel("Create a new empty tab with fundamental structure")
        info.setStyleSheet(f"font-weight: bold; color: {theme.ACCENT_PRIMARY};")
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(10)

        # Tab name input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Custom Tab, My Settings, etc.")
        self.name_input.setMinimumWidth(500)
        form.addRow("Tab Name:", self.name_input)

        # Tab icon input
        self.icon_input = QLineEdit()
        self.icon_input.setPlaceholderText("e.g., 🔧, 📝, ⚙️, 🎯, etc.")
        self.icon_input.setMinimumWidth(500)
        form.addRow("Tab Icon (emoji):", self.icon_input)

        # Row selection
        self.row_combo = QComboBox()
        self.row_combo.addItems(["Row 1", "Row 2"])
        form.addRow("Add to:", self.row_combo)

        # Content input
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("Optional: Enter initial content for the tab (leave empty for blank tab)")
        self.content_input.setMaximumHeight(150)
        form.addRow("Initial Content:", self.content_input)

        layout.addLayout(form)

        # Dialog buttons
        button_layout = QHBoxLayout()
        create_btn = QPushButton("Create Tab")
        cancel_btn = QPushButton("Cancel")
        create_btn.clicked.connect(self.validate_and_accept)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(create_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def validate_and_accept(self):
        """Validate inputs before accepting"""
        tab_name = self.name_input.text().strip()
        if not tab_name:
            QMessageBox.warning(self, "Missing Name", "Please enter a tab name")
            return
        self.accept()

    def get_tab_data(self):
        """Get the new tab data"""
        icon = self.icon_input.text().strip() or "📄"
        name = self.name_input.text().strip()
        full_name = f"{icon} {name}"
        row = 1 if self.row_combo.currentText() == "Row 1" else 2
        content = self.content_input.toPlainText().strip()

        return {
            "name": full_name,
            "row": row,
            "content": content
        }

class PreferencesTab(QWidget):
    """Tab for application preferences and theme management"""

    # Signal emitted when theme changes
    theme_changed = pyqtSignal(str, int)  # theme_name, font_size
    # Signal to navigate to a tab/subtab/dialog by class name
    navigate_to   = pyqtSignal(str)

    def __init__(self, config_manager, backup_manager, app=None):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.app = app  # QApplication instance for dynamic theme switching
        # Use project's config/config.json instead of ~/.claude/
        self.config_file = Path(__file__).parent.parent.parent / "config" / "config.json"
        self.init_ui()
        self.load_preferences()

    def init_ui(self):
        """Initialize the UI with subtabs"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(10)

        # Header — store reference for apply_theme()
        self._pref_header = QLabel("Application Preferences")
        self._pref_header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY}; margin-bottom: 10px;")
        layout.addWidget(self._pref_header)

        # Create subtabs — uses global app stylesheet, no per-widget override
        self.subtabs = QTabWidget()

        # Create subtabs
        self.create_appearance_subtab()
        self.create_backup_subtab()
        self.create_search_subtab()
        self.create_skills_subtab()

        layout.addWidget(self.subtabs)

    # ── Theme editor variable definitions ───────────────────────────────────────

    # (label, var_name, usage_description)
    _THEME_COLOR_VARS = [
        ("Background",     "BG_DARK",           "main window bg, code blocks, text editors"),
        ("Surface",        "BG_MEDIUM",          "panels, footers, inputs, header bg"),
        ("Surface Light",  "BG_LIGHT",           "borders, dividers, scrollbars"),
        ("Text Primary",   "FG_PRIMARY",         "headings, labels, primary text"),
        ("Text Secondary", "FG_SECONDARY",       "descriptions, subtitles, dim labels"),
        ("Text Dim",       "FG_DIM",             "disabled text, placeholders"),
        ("Accent",         "ACCENT_PRIMARY",     "buttons, active tabs, links, key actions"),
        ("Accent Alt",     "ACCENT_SECONDARY",   "footer borders, section markers, hover state"),
        ("Error",          "ERROR_COLOR",        "error messages, destructive actions"),
        ("Warning",        "WARNING_COLOR",      "warnings, caution indicators"),
        ("Success",        "SUCCESS_COLOR",      "success messages, OK states"),
    ]

    # (label, var_name, min, max, default)
    _THEME_TYPO_VARS = [
        ("Normal",   "FONT_SIZE_NORMAL", 8,  24, 14),
        ("Large",    "FONT_SIZE_LARGE",  10, 28, 16),
        ("Small",    "FONT_SIZE_SMALL",  7,  20, 12),
        ("Tiny",     "FONT_SIZE_TINY",   6,  18, 11),
        ("Tab",      "FONT_SIZE_TAB",    8,  20, 13),
    ]

    _THEME_SPACING_VARS = [
        ("Border Radius",  "BORDER_RADIUS", 0, 20, 4),
        ("Margin SM",      "MARGIN_SM",     0, 20, 3),
        ("Margin MD",      "MARGIN_MD",     0, 30, 6),
        ("Margin LG",      "MARGIN_LG",     0, 40, 10),
        ("Padding SM",     "PADDING_SM",    0, 20, 4),
        ("Padding MD",     "PADDING_MD",    0, 30, 8),
    ]

    def create_appearance_subtab(self):
        """Create Appearance subtab — widget theme editor + elements browser."""
        # Initialize backward-compat state (read from / written to config.json)
        self._custom_colors  = {}
        self._custom_numbers = {}
        appearance_widget = QWidget()
        main_layout = QVBoxLayout(appearance_widget)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # ── Top row: Theme selector + Tab Management ─────────────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        theme_group = QGroupBox("Color Theme")
        theme_form = QFormLayout(theme_group)
        theme_form.setSpacing(6)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(THEMES.keys())
        self.theme_combo.currentTextChanged.connect(self.preview_theme)
        theme_form.addRow("Theme:", self.theme_combo)
        top_row.addWidget(theme_group, 1)

        tab_mgmt_group = QGroupBox("Tab Management")
        tab_mgmt_layout = QHBoxLayout(tab_mgmt_group)
        tab_mgmt_layout.setSpacing(8)
        self.edit_tabs_btn = QPushButton("Edit Tabs")
        self.edit_tabs_btn.setToolTip("Reorder and rename tabs")
        self.edit_tabs_btn.clicked.connect(self.open_tab_editor_dialog)
        self.add_tab_btn = QPushButton("Add New Tab")
        self.add_tab_btn.setToolTip("Create a new empty tab")
        self.add_tab_btn.clicked.connect(self.open_add_tab_dialog)
        tab_mgmt_layout.addWidget(self.edit_tabs_btn)
        tab_mgmt_layout.addWidget(self.add_tab_btn)
        tab_mgmt_layout.addStretch()
        top_row.addWidget(tab_mgmt_group, 1)

        main_layout.addLayout(top_row)

        # ── Inner tabs: Widget Editor | Elements ─────────────────────────
        self._inner_tabs = QTabWidget()
        self._inner_tabs.setDocumentMode(True)
        self._inner_tabs.addTab(self._build_widget_preview(), "🧩 Widget Editor")
        self._inner_tabs.addTab(self._build_elements_tab(), "🔍 Elements")
        main_layout.addWidget(self._inner_tabs, 1)

        # ── Action buttons ────────────────────────────────────────────────
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.save_theme_btn = QPushButton("Save Theme")
        self.save_theme_btn.setToolTip(
            "Save changes back into the currently selected theme.\n"
            "Overwrites its entry in config/themes/themes.json in-place."
        )
        self.save_theme_btn.clicked.connect(self._save_current_theme)

        self.save_as_theme_btn = QPushButton("Save as New Theme...")
        self.save_as_theme_btn.setToolTip(
            "Save current colors + widget styles as a brand-new named theme.\n"
            "Prompts for a name, then adds it to the dropdown."
        )
        self.save_as_theme_btn.clicked.connect(self._save_as_theme)

        self.delete_theme_btn = QPushButton("Delete Theme")
        self.delete_theme_btn.setToolTip("Remove selected theme from themes.json")
        self.delete_theme_btn.clicked.connect(self._delete_theme)

        self.apply_btn = QPushButton("Save Session")
        self.apply_btn.setToolTip(
            "Changes are already live. This writes them to config/config.json\n"
            "so the same theme, font and widget styles are restored on next startup."
        )
        self.apply_btn.clicked.connect(self.apply_preferences)

        self.reset_btn = QPushButton("Reset to Gruvbox Dark")
        self.reset_btn.setToolTip(
            "Hard-reset everything back to the Gruvbox Dark defaults:\n"
            "colors, font size, font family, widget styles."
        )
        self.reset_btn.clicked.connect(self.reset_to_default)

        self.restart_btn = QPushButton("Restart App")
        self.restart_btn.setToolTip("Restart application")
        self.restart_btn.clicked.connect(self.restart_application)

        button_layout.addWidget(self.save_theme_btn)
        button_layout.addWidget(self.save_as_theme_btn)
        button_layout.addWidget(self.delete_theme_btn)
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.restart_btn)
        main_layout.addLayout(button_layout)

        self.subtabs.addTab(appearance_widget, "🎨 Appearance")

    def _build_widget_preview(self):
        """Build the interactive widget theme editor (real Qt widgets, click to edit)."""
        self._widget_theme_editor = WidgetThemeEditor(
            on_change_callback=self._push_app_stylesheet
        )
        # Forward navigation requests up to MainWindow
        self._widget_theme_editor.navigate_to.connect(self.navigate_to)
        return self._widget_theme_editor

    def _build_elements_tab(self) -> QWidget:
        """Elements tab — browse widget usage per Tab/SubTab/Dialog/Window."""
        from PyQt6.QtGui import QColor, QFont

        # Load nav tree (addTab-based, proper labels + parent info)
        try:
            nav_tree = load_navigation_tree()
        except Exception:
            nav_tree = []

        # qt_class → wdef_name for Widget Editor navigation
        qt_class_to_wdef: dict[str, str] = {}
        for wname, wdef in WIDGET_DEFS.items():
            qc = wdef.get("qt_class", wdef["selector"].split("::")[0].split(" ")[0])
            qt_class_to_wdef.setdefault(qc, wname)

        # Organize tree: top-level entries + children by parent
        top_level   = [e for e in nav_tree if not e.get("parent_id")]
        by_parent: dict[str, list] = {}
        for e in nav_tree:
            if e.get("parent_id"):
                by_parent.setdefault(e["parent_id"], []).append(e)

        # ── UI ────────────────────────────────────────────────────────────────
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)

        # ── Left: navigation tree list ────────────────────────────────────────
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(4, 4, 4, 4)
        left_layout.setSpacing(2)

        lbl = QLabel("Navigation")
        lbl.setStyleSheet(f"color: {theme.FG_DIM}; font-style: italic; padding: 2px 0;")
        left_layout.addWidget(lbl)

        self._elements_nav_list = QListWidget()
        self._elements_nav_list.setAlternatingRowColors(False)
        _list_style = (
            f"QListWidget {{ background: {theme.BG_MEDIUM}; border: 1px solid {theme.BG_LIGHT}; "
            f"border-radius: 4px; color: {theme.FG_PRIMARY}; }}"
            f"QListWidget::item:selected {{ background: {theme.ACCENT_PRIMARY}; color: {theme.BG_DARK}; }}"
            f"QListWidget::item:hover {{ background: {theme.BG_LIGHT}; }}"
        )
        self._elements_nav_list.setStyleSheet(_list_style)

        def _add_header(text: str):
            item = QListWidgetItem(text)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(QColor(theme.FG_DIM))
            f = item.font(); f.setItalic(True); item.setFont(f)
            self._elements_nav_list.addItem(item)

        def _add_entry(entry: dict, indent: int = 0):
            prefix = "    " * indent
            icon = "📋" if entry["type"] == "Tab" else "  ·"
            item = QListWidgetItem(f"{prefix}{icon} {entry['label']}")
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self._elements_nav_list.addItem(item)

        # Tabs + their subtabs (nested)
        _add_header("── Tabs ──")
        for tab in sorted(top_level, key=lambda e: e["label"]):
            _add_entry(tab, indent=0)
            for sub in sorted(by_parent.get(tab["id"], []), key=lambda e: e["label"]):
                _add_entry(sub, indent=1)

        # Dialogs (no parent in nav tree)
        dialogs = [e for e in nav_tree if e.get("type") == "Dialog"]
        if dialogs:
            _add_header("── Dialogs ──")
            for d in sorted(dialogs, key=lambda e: e["label"]):
                _add_entry(d, indent=0)

        left_layout.addWidget(self._elements_nav_list, 1)
        splitter.addWidget(left)

        # ── Right: widget list ────────────────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(4, 4, 4, 4)
        right_layout.setSpacing(2)

        self._elements_detail_lbl = QLabel("Select a location")
        self._elements_detail_lbl.setStyleSheet(
            f"color: {theme.FG_DIM}; font-style: italic; padding: 2px 0;"
        )
        right_layout.addWidget(self._elements_detail_lbl)

        self._elements_widget_list = QListWidget()
        self._elements_widget_list.setAlternatingRowColors(False)
        self._elements_widget_list.setStyleSheet(_list_style)
        right_layout.addWidget(self._elements_widget_list, 1)
        splitter.addWidget(right)

        splitter.setSizes([230, 400])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        layout.addWidget(splitter, 1)

        # ── Signals ───────────────────────────────────────────────────────────
        def _on_nav_clicked(item: QListWidgetItem):
            entry = item.data(Qt.ItemDataRole.UserRole)
            if not entry:
                return
            parent_lbl = entry.get("parent_label")
            if parent_lbl:
                detail = f"{entry['label']}  (sub of {parent_lbl})"
            else:
                detail = f"{entry['label']}  ({entry['type']})"
            self._elements_detail_lbl.setText(
                f"Widgets in: {detail}  — click to open in Widget Editor"
            )
            try:
                qt_classes = get_widgets_for_nav_entry(entry)
            except Exception:
                qt_classes = []
            self._elements_widget_list.clear()
            for qc in sorted(qt_classes):
                wname = qt_class_to_wdef.get(qc)
                if wname:
                    wdef = WIDGET_DEFS[wname]
                    text = f"{wdef.get('icon', '•')}  ·  {qc}"
                else:
                    text = f"•  {qc}"
                    wname = None
                wi = QListWidgetItem(text)
                wi.setData(Qt.ItemDataRole.UserRole, wname)
                self._elements_widget_list.addItem(wi)
            # If this entry uses QTextBrowser, also list the virtual HTML_Content widget
            if 'QTextBrowser' in qt_classes and 'HTML_Content' in WIDGET_DEFS:
                html_wdef = WIDGET_DEFS['HTML_Content']
                wi = QListWidgetItem(f"{html_wdef.get('icon', '🌐')}  ·  HTML Content (inline styles)")
                wi.setData(Qt.ItemDataRole.UserRole, 'HTML_Content')
                self._elements_widget_list.addItem(wi)

        def _on_widget_clicked(item: QListWidgetItem):
            wname = item.data(Qt.ItemDataRole.UserRole)
            if not wname:
                return
            self._inner_tabs.setCurrentIndex(0)
            if hasattr(self, "_widget_theme_editor"):
                self._widget_theme_editor._preview_panel._select(wname)
                self._widget_theme_editor._prop_panel.load_widget(wname)

        self._elements_nav_list.itemClicked.connect(_on_nav_clicked)
        self._elements_widget_list.itemClicked.connect(_on_widget_clicked)

        return container

    def _update_preview_html(self):
        """No-op: preview is now real live Qt widgets in WidgetThemeEditor."""

    # ── Live-apply helpers ───────────────────────────────────────────────────

    @staticmethod
    def _inject_css_into_html(html: str, css: str) -> str:
        """Inject a marked <style> block into HTML.

        The marker attribute (data-claudedb="1") lets the monkey-patched
        setHtml() in main.py strip the block before saving _html_source, so
        the stored original is always clean and re-injection is idempotent.
        """
        import re
        style_block = f'<style data-claudedb="1">{css}</style>'
        if '</head>' in html:
            return html.replace('</head>', style_block + '</head>', 1)
        if re.search(r'<body[^>]*>', html):
            return re.sub(r'(<body[^>]*>)', r'\1' + style_block, html, count=1)
        return style_block + html

    def _push_app_stylesheet(self):
        """Regenerate and push the full app stylesheet from current theme globals + widget overrides."""
        from PyQt6.QtWidgets import QTextBrowser
        app = QApplication.instance()
        if app:
            base_qss = theme.generate_app_stylesheet()
            widget_qss = self._widget_theme_editor.get_overrides_qss() if hasattr(self, '_widget_theme_editor') else ''
            app.setStyleSheet(base_qss + '\n' + widget_qss)

        if not hasattr(self, '_widget_theme_editor'):
            return

        # Build the full HTML CSS including body color/bg.
        # Injecting it as a <style> block inside the HTML is the only approach
        # that reliably overrides Qt's QSS cascade for HTML-rendered content.
        doc_css = self._widget_theme_editor.get_document_css()

        main_win = self.window()
        for browser in main_win.findChildren(QTextBrowser):
            orig_html = browser.property("_html_source")
            if orig_html is None:
                continue  # browser not set via setHtml; skip

            scroll = browser.verticalScrollBar().value()
            styled_html = self._inject_css_into_html(orig_html, doc_css)
            browser.setHtml(styled_html)   # monkey-patch strips marker → _html_source stays clean
            browser.verticalScrollBar().setValue(scroll)

    def apply_theme(self):
        """Re-apply inline styles that were baked at widget-creation time so they match the current theme."""
        # Header
        if hasattr(self, '_pref_header'):
            self._pref_header.setStyleSheet(
                f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY}; margin-bottom: 10px;"
            )
        # Widget theme editor left panel
        if hasattr(self, '_widget_theme_editor'):
            self._widget_theme_editor.apply_theme()

    def _reset_custom_colors(self):
        """Re-apply the base theme colors, discarding any unsaved palette changes."""
        self._custom_colors.clear()
        theme.apply_theme(self.theme_combo.currentText(), theme.FONT_SIZE_NORMAL, theme.FONT_FAMILY_UI)
        self._push_app_stylesheet()
        self._refresh_color_buttons()

    def _refresh_color_buttons(self):
        """Palette colors are now in the Widget Theme Editor — refresh it instead."""
        if hasattr(self, '_widget_theme_editor'):
            self._widget_theme_editor.apply_theme()

    # ── Theme management ─────────────────────────────────────────────────────

    def _save_current_theme(self):
        """Overwrite the currently selected theme in themes.json with current settings."""
        name = self.theme_combo.currentText()
        if not name:
            return
        widget_overrides = self._widget_theme_editor.get_overrides_dict() if hasattr(self, '_widget_theme_editor') else {}
        ok = theme.save_theme_to_file(
            name=name,
            widgets=widget_overrides or None,
            font_size=theme.FONT_SIZE_NORMAL,
            font_family=theme.FONT_FAMILY_UI,
            font_mono=theme.FONT_MONOSPACE,
            custom_colors=self._custom_colors,
            custom_numbers=self._custom_numbers,
            set_active=True,
        )
        if ok:
            self._custom_colors.clear()
            main_win = self.window()
            if hasattr(main_win, "set_status"):
                main_win.set_status(f"Theme '{name}' saved to themes.json")
            else:
                QMessageBox.information(self, "Saved", f"Theme '{name}' saved.")
        else:
            QMessageBox.critical(self, "Error", "Failed to write themes.json")

    def _save_as_theme(self):
        """Snapshot current colors and save as a named theme in config/themes.json."""
        name, ok = QInputDialog.getText(
            self, "Save as Theme",
            "Enter a name for this theme:\n"
            "(saves current colors to config/themes.json\nand adds it to the dropdown)"
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        widget_overrides = self._widget_theme_editor.get_overrides_dict() if hasattr(self, '_widget_theme_editor') else {}
        if theme.save_theme_to_file(
            name=name,
            widgets=widget_overrides or None,
            font_size=theme.FONT_SIZE_NORMAL,
            font_family=theme.FONT_FAMILY_UI,
            font_mono=theme.FONT_MONOSPACE,
            custom_colors=self._custom_colors,
            custom_numbers=self._custom_numbers,
            set_active=True,
        ):
            global THEMES
            THEMES = theme.AVAILABLE_THEMES
            self.theme_combo.blockSignals(True)
            self.theme_combo.clear()
            self.theme_combo.addItems(THEMES.keys())
            idx = self.theme_combo.findText(name)
            if idx >= 0:
                self.theme_combo.setCurrentIndex(idx)
            self.theme_combo.blockSignals(False)
            # Colors are now part of the named theme; clear the "unsaved" tracking dict
            self._custom_colors.clear()
            main_win = self.window()
            if hasattr(main_win, "set_status"):
                main_win.set_status(f"Theme '{name}' saved to config/themes.json")
            else:
                QMessageBox.information(self, "Saved", f"Theme '{name}' saved to config/themes.json")
        else:
            QMessageBox.critical(self, "Error", "Failed to write config/themes.json")

    def _delete_theme(self):
        """Delete the selected theme from config/themes.json."""
        name = self.theme_combo.currentText()
        reply = QMessageBox.question(
            self, "Delete Theme",
            f"Delete theme '{name}' from themes.json?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        if theme.delete_theme_from_file(name):
            global THEMES
            THEMES = theme.AVAILABLE_THEMES
            self.theme_combo.blockSignals(True)
            self.theme_combo.clear()
            self.theme_combo.addItems(THEMES.keys())
            if self.theme_combo.count() > 0:
                self.theme_combo.setCurrentIndex(0)
            self.theme_combo.blockSignals(False)
            self.preview_theme(self.theme_combo.currentText())
        else:
            QMessageBox.critical(
                self, "Error",
                f"Could not delete '{name}'.\nIt may be the last remaining theme or the file is read-only."
            )

    def create_backup_subtab(self):
        """Create Backup subtab"""
        backup_widget = QWidget()
        layout = QVBoxLayout(backup_widget)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        # Backup Management Group
        backup_group = QGroupBox("Backup Management")
        backup_layout = QHBoxLayout()
        backup_layout.setSpacing(10)

        self.full_backup_btn = QPushButton("📦 Create Full Backup")
        self.full_backup_btn.setToolTip("Create backup of all Claude Code configuration files")
        self.full_backup_btn.clicked.connect(self.create_full_backup)

        self.program_backup_btn = QPushButton("💾 Backup Program Files")
        self.program_backup_btn.setToolTip("Create backup of Claude_DB program files")
        self.program_backup_btn.clicked.connect(self.backup_program_files)

        backup_layout.addWidget(self.full_backup_btn)
        backup_layout.addWidget(self.program_backup_btn)
        backup_layout.addStretch()

        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)

        # Config Sync section
        config_sync_label = QLabel("Configuration Sync")
        config_sync_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_NORMAL}px; font-weight: bold; color: {theme.ACCENT_PRIMARY}; margin-top: 15px;")
        layout.addWidget(config_sync_label)

        config_sync_widget = ConfigSyncTab(self.config_manager, self.backup_manager)
        # Remove height restriction to show all content properly
        layout.addWidget(config_sync_widget, 1)  # Give it stretch factor for proper sizing

        layout.addStretch()
        self.subtabs.addTab(backup_widget, "💾 Backup")

    def create_search_subtab(self):
        """Create Search Settings subtab (GitHub token, MCP sources, cache)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        # ── GitHub ──────────────────────────────────────────────────────
        github_group = QGroupBox("GitHub API")
        github_layout = QFormLayout(github_group)
        github_layout.setSpacing(8)

        token_row = QHBoxLayout()
        self._github_token_input = QLineEdit()
        self._github_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._github_token_input.setPlaceholderText("ghp_xxxxxxxxxxxxxxxxxxxx (optional)")
        token_row.addWidget(self._github_token_input)

        show_btn = QPushButton("👁")
        show_btn.setMaximumWidth(40)
        show_btn.setCheckable(True)
        show_btn.toggled.connect(
            lambda on: self._github_token_input.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
            )
        )
        token_row.addWidget(show_btn)

        test_btn = QPushButton("Test")
        test_btn.clicked.connect(self._test_github_token)
        token_row.addWidget(test_btn)
        github_layout.addRow("Token:", token_row)

        timeout_row = QHBoxLayout()
        self._github_timeout_spin = QSpinBox()
        self._github_timeout_spin.setRange(5, 120)
        self._github_timeout_spin.setValue(30)
        self._github_timeout_spin.setSuffix(" s")
        timeout_row.addWidget(self._github_timeout_spin)
        timeout_row.addStretch()
        github_layout.addRow("Timeout:", timeout_row)

        cache_row = QHBoxLayout()
        self._github_cache_spin = QSpinBox()
        self._github_cache_spin.setRange(0, 168)
        self._github_cache_spin.setValue(24)
        self._github_cache_spin.setSuffix(" h")
        cache_row.addWidget(self._github_cache_spin)
        cache_row.addStretch()
        github_layout.addRow("Cache TTL:", cache_row)
        layout.addWidget(github_group)

        # ── MCP Search sources ───────────────────────────────────────────
        mcp_group = QGroupBox("MCP Server Search")
        mcp_layout = QVBoxLayout(mcp_group)
        mcp_layout.setSpacing(6)

        src_label = QLabel("Enabled sources:")
        src_label.setStyleSheet(f"color: {theme.FG_SECONDARY};")
        mcp_layout.addWidget(src_label)

        self._mcp_source_checks = {}
        for key, label in [
            ("mcp.so", "mcp.so"),
            ("mcpservers.org", "mcpservers.org"),
            ("pulsemcp.com", "PulseMCP"),
            ("github", "GitHub"),
        ]:
            cb = QCheckBox(label)
            cb.setChecked(True)
            self._mcp_source_checks[key] = cb
            mcp_layout.addWidget(cb)

        mcp_cache_row = QHBoxLayout()
        mcp_cache_label = QLabel("MCP cache TTL:")
        mcp_cache_label.setStyleSheet(f"color: {theme.FG_SECONDARY};")
        mcp_cache_row.addWidget(mcp_cache_label)
        self._mcp_cache_spin = QSpinBox()
        self._mcp_cache_spin.setRange(0, 168)
        self._mcp_cache_spin.setValue(24)
        self._mcp_cache_spin.setSuffix(" h")
        mcp_cache_row.addWidget(self._mcp_cache_spin)
        clear_btn = QPushButton("Clear MCP Cache")
        clear_btn.clicked.connect(self._clear_mcp_cache)
        mcp_cache_row.addWidget(clear_btn)
        mcp_cache_row.addStretch()
        mcp_layout.addLayout(mcp_cache_row)
        layout.addWidget(mcp_group)

        # Save button
        save_btn = QPushButton("Save Search Settings")
        save_btn.clicked.connect(self._save_search_settings)
        layout.addWidget(save_btn)
        layout.addStretch()

        self.subtabs.addTab(widget, "🔍 Search")

    def _test_github_token(self):
        """Test the GitHub token by fetching rate limit."""
        token = self._github_token_input.text().strip()
        try:
            from utils.github_client import GitHubClient
            # Temporarily patch the token
            client = GitHubClient.__new__(GitHubClient)
            client._token = token
            client._timeout = self._github_timeout_spin.value()
            client._cache_hours = 0
            client._db_path = None

            import urllib.request, json as _json
            req = urllib.request.Request("https://api.github.com/rate_limit")
            req.add_header("User-Agent", "Claude_DB/2.0")
            req.add_header("Accept", "application/vnd.github+json")
            if token:
                req.add_header("Authorization", f"Bearer {token}")
            with urllib.request.urlopen(req, timeout=self._github_timeout_spin.value()) as resp:
                data = _json.loads(resp.read().decode())
            remaining = data.get("rate", {}).get("remaining", "?")
            limit = data.get("rate", {}).get("limit", "?")
            QMessageBox.information(
                self, "GitHub Token OK",
                f"Rate limit: {remaining} / {limit} requests remaining."
            )
        except Exception as e:
            QMessageBox.critical(self, "GitHub Token Error", f"Failed: {e}")

    def _clear_mcp_cache(self):
        """Clear the MCP search cache."""
        try:
            from utils.mcp_search_client import MCPSearchClient
            n = MCPSearchClient().clear_cache()
            QMessageBox.information(self, "Cache Cleared", f"Cleared {n} cached MCP search entries.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to clear cache:\n{e}")

    def _save_search_settings(self):
        """Save GitHub + MCP search settings to config.json."""
        try:
            config_data = {}
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    config_data = json.load(f)

            config_data.setdefault("github", {})
            config_data["github"]["token"] = self._github_token_input.text().strip()
            config_data["github"]["request_timeout"] = self._github_timeout_spin.value()
            config_data["github"]["cache_hours"] = self._github_cache_spin.value()

            config_data.setdefault("mcp_search", {})
            config_data["mcp_search"]["enabled_sources"] = [
                k for k, cb in self._mcp_source_checks.items() if cb.isChecked()
            ]
            config_data["mcp_search"]["cache_hours"] = self._mcp_cache_spin.value()

            _atomic_json_write(self.config_file, config_data)

            win = self.window()
            if hasattr(win, "set_status"):
                win.set_status("Search settings saved.")
            else:
                QMessageBox.information(self, "Saved", "Search settings saved.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings:\n{e}")

    def create_skills_subtab(self):
        """Create Skills settings subtab (dirs + curated skill sources)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        # ── Skill directories ────────────────────────────────────────────
        dir_group = QGroupBox("Skill Directories")
        dir_layout = QFormLayout(dir_group)
        dir_layout.setSpacing(8)

        user_row = QHBoxLayout()
        self._skills_user_dir = QLineEdit()
        self._skills_user_dir.setPlaceholderText("Leave blank for ~/.claude/skills/")
        user_row.addWidget(self._skills_user_dir)
        user_browse = QPushButton("Browse")
        user_browse.clicked.connect(lambda: self._browse_skills_dir(self._skills_user_dir))
        user_row.addWidget(user_browse)
        dir_layout.addRow("User skills dir:", user_row)

        proj_row = QHBoxLayout()
        self._skills_proj_dir = QLineEdit()
        self._skills_proj_dir.setPlaceholderText("Leave blank for .claude/skills/ in current project")
        proj_row.addWidget(self._skills_proj_dir)
        proj_browse = QPushButton("Browse")
        proj_browse.clicked.connect(lambda: self._browse_skills_dir(self._skills_proj_dir))
        proj_row.addWidget(proj_browse)
        dir_layout.addRow("Project skills dir:", proj_row)
        layout.addWidget(dir_group)

        # ── Skill sources (resizable via splitter) ───────────────────────
        src_group = QGroupBox("Skill Sources (config/skill_sources.json)")
        src_layout = QVBoxLayout(src_group)
        src_layout.setContentsMargins(4, 4, 4, 4)
        src_layout.setSpacing(4)

        self._skill_sources_table = QTableWidget()
        self._skill_sources_table.setColumnCount(4)
        self._skill_sources_table.setHorizontalHeaderLabels(["Owner/Repo", "Description", "Type", "Skills Prefix"])
        hdr = self._skill_sources_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self._skill_sources_table.setMinimumHeight(80)
        UIStateManager.instance().restore_table_state("prefs.skill_sources", self._skill_sources_table)
        UIStateManager.instance().connect_table("prefs.skill_sources", self._skill_sources_table)
        self._skill_sources_table.verticalHeader().hide()
        self._skill_sources_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        # Buttons live INSIDE the group, below the table — no splitter between them
        src_layout.addWidget(self._skill_sources_table, 1)

        src_btns = QHBoxLayout()
        src_btns.setContentsMargins(0, 0, 0, 0)
        src_btns.setSpacing(5)
        for label, slot in [
            ("Add", self._add_skill_source),
            ("Remove", self._remove_skill_source),
            ("Reset to Defaults", self._reset_skill_sources),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(slot)
            src_btns.addWidget(btn)
        src_btns.addStretch()
        src_layout.addLayout(src_btns)

        # Save button
        save_btn = QPushButton("Save Skills Settings")
        save_btn.clicked.connect(self._save_skills_settings)

        # Outer splitter: dirs group on top, [src_group + save] on bottom — draggable
        outer_splitter = QSplitter(Qt.Orientation.Vertical)
        outer_splitter.setChildrenCollapsible(False)
        outer_splitter.addWidget(dir_group)

        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(4)
        bottom_layout.addWidget(src_group, 1)
        bottom_layout.addWidget(save_btn)
        outer_splitter.addWidget(bottom)
        outer_splitter.setSizes([140, 400])

        layout.addWidget(outer_splitter, 1)

        self.subtabs.addTab(widget, "🛠 Skills")

    def _browse_skills_dir(self, line_edit: QLineEdit):
        path = QFileDialog.getExistingDirectory(self, "Select Skills Directory")
        if path:
            line_edit.setText(path)

    def _populate_skill_sources_table(self, sources: list):
        self._skill_sources_table.setRowCount(0)
        for src in sources:
            row = self._skill_sources_table.rowCount()
            self._skill_sources_table.insertRow(row)
            self._skill_sources_table.setItem(row, 0, QTableWidgetItem(f"{src.get('owner','')}/{src.get('repo','')}"))
            self._skill_sources_table.setItem(row, 1, QTableWidgetItem(src.get("description", "")))
            self._skill_sources_table.setItem(row, 2, QTableWidgetItem(src.get("type", "direct")))
            self._skill_sources_table.setItem(row, 3, QTableWidgetItem(src.get("skills_prefix", "")))

    def _add_skill_source(self):
        text, ok = QInputDialog.getText(
            self, "Add Skill Source",
            "Enter owner/repo (e.g. anthropics/skills):"
        )
        if not ok or not text.strip():
            return
        parts = text.strip().split("/", 1)
        if len(parts) != 2:
            QMessageBox.warning(self, "Invalid", "Enter as owner/repo")
            return
        row = self._skill_sources_table.rowCount()
        self._skill_sources_table.insertRow(row)
        from PyQt6.QtWidgets import QTableWidgetItem
        self._skill_sources_table.setItem(row, 0, QTableWidgetItem(text.strip()))
        self._skill_sources_table.setItem(row, 1, QTableWidgetItem(""))
        self._skill_sources_table.setItem(row, 2, QTableWidgetItem("direct"))
        self._skill_sources_table.setItem(row, 3, QTableWidgetItem("skills/"))

    def _remove_skill_source(self):
        row = self._skill_sources_table.currentRow()
        if row >= 0:
            self._skill_sources_table.removeRow(row)

    def _reset_skill_sources(self):
        from utils.skill_search_client import load_skill_sources
        self._populate_skill_sources_table(load_skill_sources())

    def _save_skills_settings(self):
        try:
            config_data = {}
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    config_data = json.load(f)

            config_data.setdefault("paths", {})
            config_data["paths"]["user_skills_dir"] = self._skills_user_dir.text().strip()
            config_data["paths"]["project_skills_dir"] = self._skills_proj_dir.text().strip()

            _atomic_json_write(self.config_file, config_data)

            # Save skill sources JSON
            _sources_file = Path(__file__).parent.parent.parent / "config" / "skill_sources.json"
            sources = []
            for row in range(self._skill_sources_table.rowCount()):
                owner_repo = (self._skill_sources_table.item(row, 0) or QTableWidgetItem("")).text().strip()
                if not owner_repo:
                    continue
                parts = owner_repo.split("/", 1)
                sources.append({
                    "owner": parts[0] if len(parts) > 0 else "",
                    "repo": parts[1] if len(parts) > 1 else "",
                    "description": (self._skill_sources_table.item(row, 1) or QTableWidgetItem("")).text(),
                    "type": (self._skill_sources_table.item(row, 2) or QTableWidgetItem("direct")).text() or "direct",
                    "skills_prefix": (self._skill_sources_table.item(row, 3) or QTableWidgetItem("")).text(),
                })
            _atomic_json_write(_sources_file, sources)

            win = self.window()
            if hasattr(win, "set_status"):
                win.set_status("Skills settings saved.")
            else:
                QMessageBox.information(self, "Saved", "Skills settings saved.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")

    def _load_skills_settings(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    config_data = json.load(f)
                paths = config_data.get("paths", {})
                self._skills_user_dir.setText(paths.get("user_skills_dir", ""))
                self._skills_proj_dir.setText(paths.get("project_skills_dir", ""))

            from utils.skill_search_client import load_skill_sources
            self._populate_skill_sources_table(load_skill_sources())
        except Exception as e:
            logger.warning("Failed to load skills settings: %s", e)

    def _load_search_settings(self):
        """Load GitHub + MCP search settings into the Search subtab."""
        try:
            if not self.config_file.exists():
                return
            with open(self.config_file, "r") as f:
                config_data = json.load(f)

            gh = config_data.get("github", {})
            self._github_token_input.setText(gh.get("token", ""))
            self._github_timeout_spin.setValue(gh.get("request_timeout", 30))
            self._github_cache_spin.setValue(gh.get("cache_hours", 24))

            mcp = config_data.get("mcp_search", {})
            enabled = mcp.get("enabled_sources", list(self._mcp_source_checks.keys()))
            for key, cb in self._mcp_source_checks.items():
                cb.setChecked(key in enabled)
            self._mcp_cache_spin.setValue(mcp.get("cache_hours", 24))
        except Exception as e:
            logger.warning("Failed to load search settings: %s", e)

    def open_tab_editor_dialog(self):
        """Open unified dialog for editing tabs (reorder and rename)"""
        # Get current tab configuration from main window
        main_window = self.get_main_window()
        if not main_window:
            QMessageBox.warning(self, "Error", "Cannot access main window")
            return

        # Read tab names from CONFIG FILE, not from UI
        # This ensures we always have the latest saved names, even if UI hasn't been updated
        tabs_row1 = []
        tabs_row2 = []

        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)

                tabs_config = config_data.get("tabs", {})

                # Read row1 tabs from config
                for tab_info in tabs_config.get("row1", []):
                    tabs_row1.append(tab_info.get("name", ""))

                # Read row2 tabs from config
                for tab_info in tabs_config.get("row2", []):
                    tabs_row2.append(tab_info.get("name", ""))

            # Fallback: If no config exists, read from UI
            if not tabs_row1 and not tabs_row2:
                for i in range(main_window.tab_bar_row1.count()):
                    tabs_row1.append(main_window.tab_bar_row1.tabText(i))
                for i in range(main_window.tab_bar_row2.count()):
                    tabs_row2.append(main_window.tab_bar_row2.tabText(i))
        except Exception as e:
            # On error, fallback to reading from UI
            logger.warning("Error reading config, using UI: %s", e)
            for i in range(main_window.tab_bar_row1.count()):
                tabs_row1.append(main_window.tab_bar_row1.tabText(i))
            for i in range(main_window.tab_bar_row2.count()):
                tabs_row2.append(main_window.tab_bar_row2.tabText(i))

        dialog = TabEditorDialog(self, tabs_row1, tabs_row2)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_row1, new_row2 = dialog.get_ordered_tabs()
            rename_map = dialog.get_rename_map()

            # Build display name to key mapping from CONFIG FILE, not from UI
            # This ensures we map based on the saved config, not the potentially stale UI
            display_to_key = {}

            try:
                if self.config_file.exists():
                    with open(self.config_file, 'r') as f:
                        config_data = json.load(f)

                    tabs_config = config_data.get("tabs", {})

                    # Map names from config to their keys
                    for tab_info in tabs_config.get("row1", []):
                        key = tab_info.get("key")
                        name = tab_info.get("name")
                        if key and name:
                            display_to_key[name] = key

                    for tab_info in tabs_config.get("row2", []):
                        key = tab_info.get("key")
                        name = tab_info.get("name")
                        if key and name:
                            display_to_key[name] = key

            except Exception as e:
                logger.warning("Error reading config for mapping: %s", e)

            # Also add default names as fallback
            for key, (default_name, widget) in main_window.all_tabs.items():
                if default_name not in display_to_key:
                    display_to_key[default_name] = key

            # CRITICAL: Apply rename_map to display_to_key
            # When user renames "User" -> "CC Config" in the dialog, we need to map "CC Config" to the correct key
            # rename_map format: {"📝 User": "📝 CC Config"}  (original_name -> new_name)
            for original_name, new_name in rename_map.items():
                # Find the key for original_name
                key = display_to_key.get(original_name)
                if key:
                    # Now map the new_name to the same key
                    display_to_key[new_name] = key

            # Save unified configuration
            self.save_tab_configuration(new_row1, new_row2, display_to_key)

            changes = []
            if new_row1 != tabs_row1 or new_row2 != tabs_row2:
                changes.append("tab order")
            if rename_map:
                changes.append(f"{len(rename_map)} tab(s) renamed")

            if changes:
                QMessageBox.information(
                    self,
                    "Changes Saved",
                    f"Saved: {', '.join(changes)}\n\n"
                    "Please restart the application to see the changes."
                )

    def open_add_tab_dialog(self):
        """Open dialog to add new tab"""
        dialog = AddNewTabDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tab_data = dialog.get_tab_data()
            self.create_new_tab(tab_data)
            QMessageBox.information(
                self,
                "Tab Created",
                f"New tab '{tab_data['name']}' has been created.\n\n"
                "Please restart the application to see the new tab."
            )

    def get_main_window(self):
        """Get reference to main application window"""
        widget = self.parent()
        while widget is not None:
            if hasattr(widget, 'tab_bar_row1') and hasattr(widget, 'tab_bar_row2'):
                return widget
            widget = widget.parent()
        return None

    def save_tab_configuration(self, row1_names, row2_names, display_to_key):
        """Save unified tab configuration (order and names) to config

        Args:
            row1_names: List of display names for row 1 tabs
            row2_names: List of display names for row 2 tabs
            display_to_key: Dict mapping display names to stable keys
        """
        try:
            config_data = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)

            # Build new format: [{"key": "...", "name": "..."}, ...]
            row1_config = []
            for display_name in row1_names:
                key = display_to_key.get(display_name)
                if key:
                    row1_config.append({"key": key, "name": display_name})

            row2_config = []
            for display_name in row2_names:
                key = display_to_key.get(display_name)
                if key:
                    row2_config.append({"key": key, "name": display_name})

            # Save in new unified format
            config_data["tabs"] = {
                "row1": row1_config,
                "row2": row2_config
            }

            # Remove old format entries if they exist
            config_data.pop("tab_order", None)
            config_data.pop("tab_renames", None)

            _atomic_json_write(self.config_file, config_data)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save tab configuration:\n{str(e)}")

    def create_new_tab(self, tab_data):
        """Create new tab file and save to config"""
        try:
            # Create new tab file
            tab_filename = tab_data["name"].replace(" ", "_").replace(":", "").lower() + "_tab.py"
            tab_path = Path(__file__).parent / tab_filename

            # Generate tab content based on CLI reference template
            tab_content = self.generate_tab_template(tab_data)

            with open(tab_path, 'w', encoding='utf-8') as f:
                f.write(tab_content)

            # Save to config
            config_data = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)

            if "custom_tabs" not in config_data:
                config_data["custom_tabs"] = []

            config_data["custom_tabs"].append({
                "name": tab_data["name"],
                "row": tab_data["row"],
                "file": tab_filename,
                "content": tab_data["content"]
            })

            _atomic_json_write(self.config_file, config_data)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create new tab:\n{str(e)}")

    def generate_tab_template(self, tab_data):
        """Generate Python code for new tab based on CLI reference template"""
        class_name = ''.join(word.capitalize() for word in tab_data["name"].replace(":", "").split() if word not in ['📄', '🔧', '📝', '⚙️', '🎯'])

        content_html = f"""
        <html>
        <body>
            <h2>{tab_data["name"]}</h2>
            <p>{tab_data.get("content", "This is a custom tab. Add your content here.")}</p>
        </body>
        </html>
        """

        return f'''"""
{tab_data["name"]} Tab - Custom tab
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextBrowser, QLabel
)
from PyQt6.QtCore import Qt

from utils import theme

class {class_name}Tab(QWidget):
    """Custom tab: {tab_data["name"]}"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        # Header
        header = QLabel("{tab_data["name"]}")
        header.setStyleSheet(f"font-size: {{theme.FONT_SIZE_LARGE}}px; font-weight: bold; color: {{theme.ACCENT_PRIMARY}};")

        layout.addWidget(header)

        # Content browser
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet(f"""
            QTextBrowser {{
                border-radius: 3px;
                padding: 15px;
                font-family: {theme.FONT_FAMILY_MONO};
                font-size: {{theme.FONT_SIZE_NORMAL}}px;
            }}
        """)

        self.load_content()
        layout.addWidget(self.browser, 1)

    def load_content(self):
        """Load tab content"""
        html_content = f"""{content_html}"""

        self.browser.setHtml(html_content)
'''

    def preview_theme(self, theme_name):
        """Switch to a different theme — clears all custom overrides and applies live."""
        if theme_name not in THEMES:
            return
        # Switching themes discards any unsaved customizations
        self._custom_colors.clear()
        self._custom_numbers.clear()
        font_size   = theme.FONT_SIZE_NORMAL
        font_family = theme.FONT_FAMILY_UI
        font_mono   = theme.FONT_MONOSPACE
        theme.apply_theme(theme_name, font_size, font_family)
        theme.FONT_MONOSPACE = font_mono
        theme.FONT_FAMILY_MONO = f"'{font_mono}', 'Courier New', monospace"
        # Load widget definitions stored in this theme
        if hasattr(self, '_widget_theme_editor'):
            saved_widgets = theme.get_theme_widgets(theme_name)
            self._widget_theme_editor.load_widgets_dict(saved_widgets)
        # Apply live to the running app (includes widget overrides)
        app = QApplication.instance()
        if app:
            from PyQt6.QtGui import QFont
            app.setFont(QFont(font_family, font_size))
        self._push_app_stylesheet()
        # Tell the main window to refresh its tab bars and any inline-styled widgets
        self.theme_changed.emit(theme_name, font_size)
        # Sync editor controls to the new theme's values
        self._refresh_color_buttons()
        self._update_preview_html()

    def _collect_number_overrides(self) -> dict:
        """Read current theme globals and build the custom_numbers dict.
        Only keeps values that differ from theme defaults."""
        all_vars = [
            ("FONT_SIZE_NORMAL", 14), ("FONT_SIZE_LARGE", 16), ("FONT_SIZE_SMALL", 12),
            ("FONT_SIZE_TINY", 11), ("FONT_SIZE_TAB", 13),
            ("BORDER_RADIUS", 4), ("MARGIN_SM", 3), ("MARGIN_MD", 6),
            ("MARGIN_LG", 10), ("PADDING_SM", 4), ("PADDING_MD", 8),
        ]
        return {vn: getattr(theme, vn) for vn, _default in all_vars}

    def apply_preferences(self):
        """Save current session state to config/config.json so it restores on next startup.
        Changes are already applied live — this just persists them.
        """
        theme_name  = self.theme_combo.currentText()
        font_size   = theme.FONT_SIZE_NORMAL
        font_family = theme.FONT_FAMILY_UI
        font_mono   = theme.FONT_MONOSPACE

        # Re-apply to make sure the running app state is fully consistent
        theme.apply_theme(theme_name, font_size, font_family)
        if self._custom_colors:
            theme.apply_color_overrides(self._custom_colors)
        theme.FONT_MONOSPACE = font_mono
        theme.FONT_FAMILY_MONO = f"'{font_mono}', 'Courier New', monospace"
        self._custom_numbers = self._collect_number_overrides()
        theme.apply_number_overrides(self._custom_numbers)

        app = QApplication.instance()
        if app:
            from PyQt6.QtGui import QFont
            app.setFont(QFont(font_family, font_size))
            self._push_app_stylesheet()

        self._refresh_color_buttons()
        self.theme_changed.emit(theme_name, font_size)
        self.save_preferences_silently()

        main_win = self.window()
        if hasattr(main_win, "set_status"):
            main_win.set_status(
                f"Session saved — theme '{theme_name}', {font_family} {font_size}px  →  config/themes/themes.json"
            )

    def _save_to_themes_json(self, set_active: bool = False) -> None:
        """Write current theme state (fonts, overrides, widgets) to themes.json."""
        theme_name = self.theme_combo.currentText()
        widget_overrides = (
            self._widget_theme_editor.get_overrides_dict()
            if hasattr(self, '_widget_theme_editor') else {}
        )
        theme.save_theme_to_file(
            name=theme_name,
            widgets=widget_overrides,
            font_size=theme.FONT_SIZE_NORMAL,
            font_family=theme.FONT_FAMILY_UI,
            font_mono=theme.FONT_MONOSPACE,
            custom_colors=self._custom_colors,
            custom_numbers=self._custom_numbers,
            set_active=set_active,
        )

    def save_preferences_silently(self):
        """Persist current session state to themes.json (no dialog)."""
        try:
            self._save_to_themes_json(set_active=True)
        except Exception as e:
            logger.warning("Failed to auto-save preferences: %s", e)

    def save_preferences(self):
        """Save preferences, apply theme and show confirmation dialog."""
        try:
            theme_name  = self.theme_combo.currentText()
            font_size   = theme.FONT_SIZE_NORMAL
            font_family = theme.FONT_FAMILY_UI
            font_mono   = theme.FONT_MONOSPACE

            theme.apply_theme(theme_name, font_size, font_family)
            if self._custom_colors:
                theme.apply_color_overrides(self._custom_colors)
            theme.FONT_MONOSPACE = font_mono
            theme.FONT_FAMILY_MONO = f"'{font_mono}', 'Courier New', monospace"
            self._custom_numbers = self._collect_number_overrides()
            theme.apply_number_overrides(self._custom_numbers)

            app = QApplication.instance()
            if app:
                from PyQt6.QtGui import QFont
                app.setFont(QFont(font_family, font_size))
                self._push_app_stylesheet()

            self._save_to_themes_json(set_active=True)

            self._refresh_color_buttons()
            self.theme_changed.emit(theme_name, font_size)

            QMessageBox.information(
                self, "Saved & Applied",
                f"Theme '{theme_name}', {font_family} {font_size}px saved and applied!"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save preferences:\n{str(e)}")

    def load_preferences(self):
        """Load active theme and per-theme settings from themes.json."""
        try:
            # Primary: read active theme name from themes.json
            theme_name = theme.get_active_theme_name()

            # Fallback: migrate from old config.json preferences section
            if theme_name == "Gruvbox Dark" and self.config_file.exists():
                try:
                    with open(self.config_file, 'r') as f:
                        config_data = json.load(f)
                    old_prefs = config_data.get("preferences", {})
                    if old_prefs.get("theme"):
                        theme_name = old_prefs["theme"]
                except Exception:
                    pass

            all_themes = theme.load_themes()
            entry = all_themes.get(theme_name, all_themes.get("Gruvbox Dark", {}))

            font_size = entry.get("font_size", 14)
            font_family = entry.get("font_family", "Segoe UI")
            font_mono = entry.get("font_mono", "Consolas")
            self._custom_colors = entry.get("custom_colors", {})
            self._custom_numbers = entry.get("custom_numbers", {})
            widget_overrides = entry.get("widgets", entry.get("__widget_overrides", {}))

            theme.apply_theme(theme_name, font_size, font_family)
            if self._custom_colors:
                theme.apply_color_overrides(self._custom_colors)
            theme.FONT_MONOSPACE = font_mono
            theme.FONT_FAMILY_MONO = f"'{font_mono}', 'Courier New', monospace"
            if self._custom_numbers:
                theme.apply_number_overrides(self._custom_numbers)

            # Block signals so setCurrentIndex doesn't trigger preview_theme mid-load
            self.theme_combo.blockSignals(True)
            index = self.theme_combo.findText(theme_name)
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)
            self.theme_combo.blockSignals(False)

            if hasattr(self, '_widget_theme_editor') and widget_overrides:
                self._widget_theme_editor.load_widgets_dict(widget_overrides)

            self._refresh_color_buttons()
            self._push_app_stylesheet()
        except Exception as e:
            logger.warning("Failed to load preferences: %s", e)
            self._custom_colors = {}
            self._custom_numbers = {}
            self.theme_combo.setCurrentText("Gruvbox Dark")

        self._load_search_settings()
        self._load_skills_settings()

    def reset_to_default(self):
        """Reset to default Gruvbox Dark theme and apply immediately."""
        self._custom_colors.clear()
        self._custom_numbers.clear()
        self.theme_combo.setCurrentText("Gruvbox Dark")
        self.apply_preferences()

    def create_full_backup(self):
        """Create full backup of Claude Code configuration"""
        try:
            backup_path = self.backup_manager.create_full_backup()
            QMessageBox.information(
                self,
                "Backup Created",
                f"Full backup created successfully!\n\nLocation:\n{backup_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Backup Error",
                f"Failed to create backup:\n{str(e)}"
            )

    def backup_program_files(self):
        """Backup Claude_DB program files"""
        try:
            import shutil
            from datetime import datetime

            # Create backup directory
            backup_base = Path(__file__).parent.parent.parent / "backup"
            backup_base.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = backup_base / f"program_backup_{timestamp}"
            backup_dir.mkdir()

            # Backup src directory
            src_dir = Path(__file__).parent.parent
            shutil.copytree(src_dir, backup_dir / "src", dirs_exist_ok=True)

            # Backup config directory
            config_dir = Path(__file__).parent.parent.parent / "config"
            if config_dir.exists():
                shutil.copytree(config_dir, backup_dir / "config", dirs_exist_ok=True)

            QMessageBox.information(
                self,
                "Backup Created",
                f"Program files backup created successfully!\n\nLocation:\n{backup_dir}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Backup Error",
                f"Failed to backup program files:\n{str(e)}"
            )

    def restart_application(self):
        """Restart the application"""
        reply = QMessageBox.question(
            self,
            "Restart Application",
            "Are you sure you want to restart the application?\n\n"
            "Any unsaved changes in other tabs will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Get the main window and close it
                main_window = self.parent()
                while main_window.parent() is not None:
                    main_window = main_window.parent()

                # Prepare restart
                python = sys.executable
                script = sys.argv[0]

                # Close main window
                main_window.close()

                # Start new instance
                QProcess.startDetached(python, [script])

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Restart Error",
                    f"Failed to restart application:\n{str(e)}\n\nPlease restart manually."
                )

    @staticmethod
    def get_theme(theme_name):
        """Get theme dictionary by name"""
        return THEMES.get(theme_name, THEMES["Gruvbox Dark"])
