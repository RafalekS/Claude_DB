"""
Preferences Tab - Application settings and theme management
"""

from pathlib import Path
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QPushButton, QMessageBox, QGroupBox, QFormLayout,
    QDialog, QListWidget, QLineEdit, QTextEdit, QListWidgetItem, QInputDialog,
    QApplication, QTabWidget, QCheckBox, QAbstractItemView, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import pyqtSignal, QProcess, Qt
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme
from tabs.config_sync_tab import ConfigSyncTab


# Load themes from config file
THEMES = theme.AVAILABLE_THEMES


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
        info.setStyleSheet(f"font-size: 12px; color: #999; font-style: italic;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Row 1 tabs
        row1_label = QLabel("Row 1 Tabs:")
        row1_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")
        layout.addWidget(row1_label)

        self.row1_list = QListWidget()
        self.row1_list.setAlternatingRowColors(True)
        self.row1_list.setStyleSheet(f"""
            QListWidget {{
                font-size: 13px;
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid #444;
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

        up1_btn.setStyleSheet(theme.get_button_style())
        down1_btn.setStyleSheet(theme.get_button_style())
        rename1_btn.setStyleSheet(theme.get_button_style())
        to_row2_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 10px;
                background-color: #f39c12;
                color: white;
                border-radius: 4px;
                font-weight: bold;
                min-width: 150px;
            }}
            QPushButton:hover {{
                background-color: #e67e22;
            }}
        """)

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
        row2_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {theme.ACCENT_PRIMARY}; margin-top: 10px;")
        layout.addWidget(row2_label)

        self.row2_list = QListWidget()
        self.row2_list.setAlternatingRowColors(True)
        self.row2_list.setStyleSheet(f"""
            QListWidget {{
                font-size: 13px;
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid #444;
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

        up2_btn.setStyleSheet(theme.get_button_style())
        down2_btn.setStyleSheet(theme.get_button_style())
        rename2_btn.setStyleSheet(theme.get_button_style())
        to_row1_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 10px;
                background-color: #f39c12;
                color: white;
                border-radius: 4px;
                font-weight: bold;
                min-width: 150px;
            }}
            QPushButton:hover {{
                background-color: #e67e22;
            }}
        """)

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
        save_btn.setStyleSheet(theme.get_button_style())
        cancel_btn.setStyleSheet(theme.get_button_style())
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
        create_btn.setStyleSheet(theme.get_button_style())
        cancel_btn.setStyleSheet(theme.get_button_style())
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

        # Header
        header = QLabel("Application Preferences")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY}; margin-bottom: 10px;")
        layout.addWidget(header)

        # Create subtabs
        self.subtabs = QTabWidget()
        self.subtabs.setStyleSheet(theme.get_tab_widget_style())

        # Create subtabs
        self.create_tab_settings_subtab()
        self.create_appearance_subtab()
        self.create_backup_subtab()
        self.create_search_subtab()
        self.create_skills_subtab()

        layout.addWidget(self.subtabs)

    def create_tab_settings_subtab(self):
        """Create Tab Settings subtab"""
        tab_settings_widget = QWidget()
        layout = QVBoxLayout(tab_settings_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Tab Management Group
        tab_mgmt_group = QGroupBox("Tab Management")
        tab_mgmt_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {theme.FONT_SIZE_NORMAL}px;
                font-weight: bold;
                color: {theme.ACCENT_PRIMARY};
                border: 2px solid {theme.ACCENT_PRIMARY};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        tab_mgmt_layout = QHBoxLayout()
        tab_mgmt_layout.setSpacing(10)

        self.edit_tabs_btn = QPushButton("🔀 Edit Tabs")
        self.edit_tabs_btn.setToolTip("Reorder and rename tabs in one dialog")
        self.edit_tabs_btn.setStyleSheet(theme.get_button_style())
        self.edit_tabs_btn.clicked.connect(self.open_tab_editor_dialog)

        self.add_tab_btn = QPushButton("➕ Add New Tab")
        self.add_tab_btn.setToolTip("Create a new empty tab")
        self.add_tab_btn.setStyleSheet(theme.get_button_style())
        self.add_tab_btn.clicked.connect(self.open_add_tab_dialog)

        tab_mgmt_layout.addWidget(self.edit_tabs_btn)
        tab_mgmt_layout.addWidget(self.add_tab_btn)
        tab_mgmt_layout.addStretch()

        tab_mgmt_group.setLayout(tab_mgmt_layout)
        layout.addWidget(tab_mgmt_group)

        layout.addStretch()
        self.subtabs.addTab(tab_settings_widget, "⚙️ Tab Settings")

    def create_appearance_subtab(self):
        """Create Appearance subtab"""
        appearance_widget = QWidget()
        layout = QVBoxLayout(appearance_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Theme Settings Group
        theme_group = QGroupBox("Theme Settings")
        theme_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {theme.FONT_SIZE_NORMAL}px;
                font-weight: bold;
                color: {theme.ACCENT_PRIMARY};
                border: 2px solid {theme.ACCENT_PRIMARY};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        theme_layout = QFormLayout()
        theme_layout.setSpacing(10)

        # Theme selector
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(THEMES.keys())
        self.theme_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 6px;
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.ACCENT_PRIMARY};
                border-radius: 3px;
                font-size: {theme.FONT_SIZE_NORMAL}px;
                combobox-popup: 0;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {theme.FG_PRIMARY};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                selection-background-color: {theme.ACCENT_PRIMARY};
                selection-color: {theme.BG_DARK};
                max-height: 300px;
            }}
        """)
        self.theme_combo.currentTextChanged.connect(self.preview_theme)

        theme_label = QLabel("Color Theme:")
        theme_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_NORMAL}px; color: {theme.FG_PRIMARY};")
        theme_layout.addRow(theme_label, self.theme_combo)

        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)

        # Font Settings Group
        font_group = QGroupBox("Font Settings")
        font_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {theme.FONT_SIZE_NORMAL}px;
                font-weight: bold;
                color: {theme.ACCENT_PRIMARY};
                border: 2px solid {theme.ACCENT_PRIMARY};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        font_layout = QFormLayout()
        font_layout.setSpacing(10)

        # Font family dropdown
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems([
            "Consolas",
            "Monaco",
            "Courier New",
            "SF Mono",
            "Menlo",
            "DejaVu Sans Mono",
            "Liberation Mono",
            "Cascadia Code",
            "Fira Code",
            "JetBrains Mono",
            "Source Code Pro"
        ])
        self.font_family_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 6px;
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.ACCENT_PRIMARY};
                border-radius: 3px;
                font-size: {theme.FONT_SIZE_NORMAL}px;
                combobox-popup: 0;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {theme.FG_PRIMARY};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                selection-background-color: {theme.ACCENT_PRIMARY};
                selection-color: {theme.BG_DARK};
                max-height: 300px;
            }}
        """)

        font_family_label = QLabel("Font Family:")
        font_family_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_NORMAL}px; color: {theme.FG_PRIMARY};")
        font_layout.addRow(font_family_label, self.font_family_combo)

        # Font size spinner
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 24)
        self.font_size_spin.setValue(14)
        self.font_size_spin.setSuffix(" px")
        self.font_size_spin.setStyleSheet(f"""
            QSpinBox {{
                padding: 6px;
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.ACCENT_PRIMARY};
                border-radius: 3px;
                font-size: {theme.FONT_SIZE_NORMAL}px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {theme.ACCENT_PRIMARY};
                border: none;
                width: 20px;
            }}
            QSpinBox::up-arrow, QSpinBox::down-arrow {{
                width: 10px;
                height: 10px;
            }}
        """)

        font_label = QLabel("Font Size:")
        font_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_NORMAL}px; color: {theme.FG_PRIMARY};")
        font_layout.addRow(font_label, self.font_size_spin)

        font_group.setLayout(font_layout)
        layout.addWidget(font_group)

        # Theme Preview
        preview_group = QGroupBox("Theme Preview")
        preview_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {theme.FONT_SIZE_NORMAL}px;
                font-weight: bold;
                color: {theme.ACCENT_PRIMARY};
                border: 2px solid {theme.ACCENT_PRIMARY};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        preview_layout = QVBoxLayout()

        self.preview_label = QLabel("Preview of selected theme colors")
        self.preview_label.setWordWrap(True)
        self.preview_label.setMinimumHeight(100)
        self.preview_label.setStyleSheet(f"""
            QLabel {{
                padding: 15px;
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.ACCENT_PRIMARY};
                border-radius: 3px;
                font-size: {theme.FONT_SIZE_NORMAL}px;
            }}
        """)
        preview_layout.addWidget(self.preview_label)

        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.apply_btn = QPushButton("Apply Theme")
        self.apply_btn.setToolTip("Apply theme changes to the current session")
        self.apply_btn.clicked.connect(self.apply_preferences)
        self.apply_btn.setStyleSheet(theme.get_button_style())

        self.save_btn = QPushButton("Save Preferences")
        self.save_btn.setToolTip("Save preferences to config file")
        self.save_btn.clicked.connect(self.save_preferences)
        self.save_btn.setStyleSheet(theme.get_button_style())

        self.reset_btn = QPushButton("Reset to Gruvbox Dark")
        self.reset_btn.setToolTip("Reset theme to default Gruvbox Dark")
        self.reset_btn.clicked.connect(self.reset_to_default)
        self.reset_btn.setStyleSheet(theme.get_button_style())

        self.restart_btn = QPushButton("🔄 Restart Application")
        self.restart_btn.setToolTip("Restart the application to apply all changes")
        self.restart_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 10px;
                background-color: #e74c3c;
                color: white;
                border-radius: 4px;
                font-weight: bold;
                min-width: 150px;
            }}
            QPushButton:hover {{
                background-color: #c0392b;
            }}
        """)
        self.restart_btn.clicked.connect(self.restart_application)

        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.restart_btn)

        layout.addLayout(button_layout)
        layout.addStretch()

        self.subtabs.addTab(appearance_widget, "🎨 Appearance")

    def create_backup_subtab(self):
        """Create Backup subtab"""
        backup_widget = QWidget()
        layout = QVBoxLayout(backup_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Backup Management Group
        backup_group = QGroupBox("Backup Management")
        backup_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: {theme.FONT_SIZE_NORMAL}px;
                font-weight: bold;
                color: {theme.ACCENT_PRIMARY};
                border: 2px solid {theme.ACCENT_PRIMARY};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        backup_layout = QHBoxLayout()
        backup_layout.setSpacing(10)

        self.full_backup_btn = QPushButton("📦 Create Full Backup")
        self.full_backup_btn.setToolTip("Create backup of all Claude Code configuration files")
        self.full_backup_btn.setStyleSheet(theme.get_button_style())
        self.full_backup_btn.clicked.connect(self.create_full_backup)

        self.program_backup_btn = QPushButton("💾 Backup Program Files")
        self.program_backup_btn.setToolTip("Create backup of Claude_DB program files")
        self.program_backup_btn.setStyleSheet(theme.get_button_style())
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
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        group_style = f"""
            QGroupBox {{
                font-size: {theme.FONT_SIZE_NORMAL}px; font-weight: bold;
                color: {theme.ACCENT_PRIMARY};
                border: 2px solid {theme.ACCENT_PRIMARY};
                border-radius: 5px;
                margin-top: 10px; padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin; left: 10px; padding: 0 5px;
            }}
        """

        # ── GitHub ──────────────────────────────────────────────────────
        github_group = QGroupBox("GitHub API")
        github_group.setStyleSheet(group_style)
        github_layout = QFormLayout(github_group)
        github_layout.setSpacing(8)

        token_row = QHBoxLayout()
        self._github_token_input = QLineEdit()
        self._github_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._github_token_input.setPlaceholderText("ghp_xxxxxxxxxxxxxxxxxxxx (optional)")
        self._github_token_input.setStyleSheet(theme.get_line_edit_style())
        token_row.addWidget(self._github_token_input)

        show_btn = QPushButton("👁")
        show_btn.setFixedWidth(32)
        show_btn.setCheckable(True)
        show_btn.setStyleSheet(theme.get_button_style())
        show_btn.toggled.connect(
            lambda on: self._github_token_input.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
            )
        )
        token_row.addWidget(show_btn)

        test_btn = QPushButton("Test")
        test_btn.setStyleSheet(theme.get_button_style())
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
        mcp_group.setStyleSheet(group_style)
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
            cb.setStyleSheet(f"color: {theme.FG_PRIMARY};")
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
        clear_btn.setStyleSheet(theme.get_button_style())
        clear_btn.clicked.connect(self._clear_mcp_cache)
        mcp_cache_row.addWidget(clear_btn)
        mcp_cache_row.addStretch()
        mcp_layout.addLayout(mcp_cache_row)
        layout.addWidget(mcp_group)

        # Save button
        save_btn = QPushButton("Save Search Settings")
        save_btn.setStyleSheet(theme.get_button_style())
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

            with open(self.config_file, "w") as f:
                json.dump(config_data, f, indent=2)

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
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        group_style = f"""
            QGroupBox {{
                font-size: {theme.FONT_SIZE_NORMAL}px; font-weight: bold;
                color: {theme.ACCENT_PRIMARY};
                border: 2px solid {theme.ACCENT_PRIMARY};
                border-radius: 5px;
                margin-top: 10px; padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin; left: 10px; padding: 0 5px;
            }}
        """
        # ── Skill directories ────────────────────────────────────────────
        dir_group = QGroupBox("Skill Directories")
        dir_group.setStyleSheet(group_style)
        dir_layout = QFormLayout(dir_group)
        dir_layout.setSpacing(8)

        user_row = QHBoxLayout()
        self._skills_user_dir = QLineEdit()
        self._skills_user_dir.setPlaceholderText("Leave blank for ~/.claude/skills/")
        self._skills_user_dir.setStyleSheet(theme.get_line_edit_style())
        user_row.addWidget(self._skills_user_dir)
        user_browse = QPushButton("Browse")
        user_browse.setStyleSheet(theme.get_button_style())
        user_browse.clicked.connect(lambda: self._browse_skills_dir(self._skills_user_dir))
        user_row.addWidget(user_browse)
        dir_layout.addRow("User skills dir:", user_row)

        proj_row = QHBoxLayout()
        self._skills_proj_dir = QLineEdit()
        self._skills_proj_dir.setPlaceholderText("Leave blank for .claude/skills/ in current project")
        self._skills_proj_dir.setStyleSheet(theme.get_line_edit_style())
        proj_row.addWidget(self._skills_proj_dir)
        proj_browse = QPushButton("Browse")
        proj_browse.setStyleSheet(theme.get_button_style())
        proj_browse.clicked.connect(lambda: self._browse_skills_dir(self._skills_proj_dir))
        proj_row.addWidget(proj_browse)
        dir_layout.addRow("Project skills dir:", proj_row)
        layout.addWidget(dir_group)

        # ── Skill sources ────────────────────────────────────────────────
        src_group = QGroupBox("Skill Sources (config/skill_sources.json)")
        src_group.setStyleSheet(group_style)
        src_layout = QVBoxLayout(src_group)

        self._skill_sources_table = QTableWidget()
        self._skill_sources_table.setColumnCount(4)
        self._skill_sources_table.setHorizontalHeaderLabels(["Owner/Repo", "Description", "Type", "Skills Prefix"])
        hdr = self._skill_sources_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        UIStateManager.instance().restore_table_state("prefs.skill_sources", self._skill_sources_table)
        UIStateManager.instance().connect_table("prefs.skill_sources", self._skill_sources_table)
        self._skill_sources_table.verticalHeader().hide()
        self._skill_sources_table.setStyleSheet(theme.get_table_style())
        self._skill_sources_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        src_layout.addWidget(self._skill_sources_table)

        src_btns = QHBoxLayout()
        for label, slot in [
            ("Add", self._add_skill_source),
            ("Remove", self._remove_skill_source),
            ("Reset to Defaults", self._reset_skill_sources),
        ]:
            btn = QPushButton(label)
            btn.setStyleSheet(theme.get_button_style())
            btn.clicked.connect(slot)
            src_btns.addWidget(btn)
        src_btns.addStretch()
        src_layout.addLayout(src_btns)
        layout.addWidget(src_group)

        save_btn = QPushButton("Save Skills Settings")
        save_btn.setStyleSheet(theme.get_button_style())
        save_btn.clicked.connect(self._save_skills_settings)
        layout.addWidget(save_btn)
        layout.addStretch()

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

            with open(self.config_file, "w") as f:
                json.dump(config_data, f, indent=2)

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
            with open(_sources_file, "w") as f:
                json.dump(sources, f, indent=2)

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
        except Exception:
            pass

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
        except Exception:
            pass

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
            print(f"Error reading config, using UI: {e}")
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
                print(f"Error reading config for mapping: {e}")

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

            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
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

            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

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
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextBrowser, QLabel
)
from PyQt6.QtCore import Qt

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme
from utils.ui_state_manager import UIStateManager


class {class_name}Tab(QWidget):
    """Custom tab: {tab_data["name"]}"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
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
                background-color: {{theme.BG_DARK}};
                color: {{theme.FG_PRIMARY}};
                border: 1px solid {{theme.BG_LIGHT}};
                border-radius: 3px;
                padding: 15px;
                font-family: 'Consolas', 'Monaco', monospace;
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
        """Preview selected theme colors"""
        if theme_name in THEMES:
            theme_colors = THEMES[theme_name]
            preview_text = f"""
            <b>Theme: {theme_name}</b><br><br>
            <span style='color: {theme_colors["foreground"]};'>■ Foreground Text</span><br>
            <span style='color: {theme_colors["brightBlue"]};'>■ Accent Blue</span><br>
            <span style='color: {theme_colors["brightGreen"]};'>■ Accent Green</span><br>
            <span style='color: {theme_colors["brightYellow"]};'>■ Accent Yellow</span><br>
            <span style='color: {theme_colors["brightRed"]};'>■ Accent Red</span><br>
            <br>
            Background: {theme_colors["background"]}<br>
            Selection: {theme_colors["selection"]}
            """

            self.preview_label.setStyleSheet(f"""
                QLabel {{
                    padding: 15px;
                    background-color: {theme_colors["background"]};
                    color: {theme_colors["foreground"]};
                    border: 2px solid {theme_colors["brightBlue"]};
                    border-radius: 3px;
                    font-size: {theme.FONT_SIZE_NORMAL}px;
                }}
            """)
            self.preview_label.setText(preview_text)

    def apply_preferences(self):
        """Apply preferences immediately — emits theme_changed signal for instant update."""
        theme_name = self.theme_combo.currentText()
        font_size = self.font_size_spin.value()

        # Apply locally first
        theme.apply_theme(theme_name, font_size)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(theme.generate_app_stylesheet())

        # Emit signal → main window calls apply_theme_change on all tabs
        self.theme_changed.emit(theme_name, font_size)

        # Save preferences
        self.save_preferences_silently()

        # Report via status bar if main window has set_status, else show dialog
        main_win = self.window()
        if hasattr(main_win, "set_status"):
            main_win.set_status(f"Theme '{theme_name}' applied ({font_size}px)")
        else:
            QMessageBox.information(
                self,
                "Theme Applied",
                f"Theme '{theme_name}' with {font_size}px font applied."
            )

    def save_preferences_silently(self):
        """Save preferences to file without showing message"""
        try:
            # Load existing config
            config_data = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)

            # Update preferences section
            config_data["preferences"] = {
                "theme": self.theme_combo.currentText(),
                "font_size": self.font_size_spin.value()
            }

            # Save merged config
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            print(f"Failed to save preferences: {e}")

    def save_preferences(self):
        """Save preferences to file and apply theme"""
        try:
            theme_name = self.theme_combo.currentText()
            font_size = self.font_size_spin.value()

            # Apply theme
            theme.apply_theme(theme_name, font_size)

            # Load existing config
            config_data = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)

            # Update preferences section
            config_data["preferences"] = {
                "theme": theme_name,
                "font_size": font_size
            }

            # Save merged config
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)

            # Emit signal for instant theme refresh across all tabs
            self.theme_changed.emit(theme_name, font_size)

            QMessageBox.information(
                self,
                "Saved & Applied",
                f"Theme '{theme_name}' with {font_size}px font saved and applied!"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save preferences:\n{str(e)}")

    def load_preferences(self):
        """Load preferences from file and apply theme"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)

                # Get preferences section
                prefs = config_data.get("preferences", {})
                theme_name = prefs.get("theme", "Gruvbox Dark")
                font_size = prefs.get("font_size", 14)

                # Apply the theme
                theme.apply_theme(theme_name, font_size)

                # Set UI values
                index = self.theme_combo.findText(theme_name)
                if index >= 0:
                    self.theme_combo.setCurrentIndex(index)

                self.font_size_spin.setValue(font_size)
                self.preview_theme(theme_name)
            else:
                # No config file - use defaults
                self.theme_combo.setCurrentText("Gruvbox Dark")
                self.font_size_spin.setValue(14)
        except Exception as e:
            print(f"Failed to load preferences: {e}")
            # Use defaults on error
            self.theme_combo.setCurrentText("Gruvbox Dark")
            self.font_size_spin.setValue(14)

        self._load_search_settings()
        self._load_skills_settings()

    def reset_to_default(self):
        """Reset to default Gruvbox Dark theme"""
        self.theme_combo.setCurrentText("Gruvbox Dark")
        self.font_size_spin.setValue(14)
        self.preview_theme("Gruvbox Dark")

        QMessageBox.information(
            self,
            "Reset",
            "Preferences reset to Gruvbox Dark theme with 14px font.\n\n"
            "Click 'Save Preferences' to make this permanent."
        )

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
