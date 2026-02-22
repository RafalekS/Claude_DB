"""Base Library Dialog - shared base class for Skill, Command, and MCP library dialogs"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme
from utils.template_manager import get_template_manager


class BaseLibraryDialog(QDialog):
    """Base dialog for managing template libraries (skills, commands, MCP servers).

    Subclasses must implement:
        - get_template_type() -> str: returns 'skills', 'commands', or 'mcp'
        - get_dialog_title() -> str: returns the window title
        - get_header_text() -> str: returns the header label text
        - get_info_text() -> str: returns the bottom info label text
        - load_templates(): loads self.templates dict and self.folders set
        - populate_table(): fills the table widget
        - add_template(): opens the add template dialog
        - edit_template(): opens the edit template dialog
        - get_selected_items(): returns list of selected (name, content) tuples
        - build_manage_buttons(layout): adds type-specific action buttons to layout

    Optional overrides:
        - get_bulk_add_class(): returns the bulk-add dialog class or None
    """

    def __init__(self, templates_dir, scope, parent=None):
        super().__init__(parent)
        self.templates_dir = Path(templates_dir)
        self.scope = scope
        self.template_mgr = get_template_manager()
        self.current_folder = ""
        self.templates = {}
        self.folders = set()
        self.setWindowTitle(self.get_dialog_title())
        self.setModal(True)
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)
        self.init_ui()

    # --- Abstract-like methods subclasses must implement ---

    def get_template_type(self):
        raise NotImplementedError

    def get_dialog_title(self):
        raise NotImplementedError

    def get_header_text(self):
        raise NotImplementedError

    def get_info_text(self):
        raise NotImplementedError

    def load_templates(self):
        raise NotImplementedError

    def populate_table(self):
        raise NotImplementedError

    def add_template(self):
        raise NotImplementedError

    def edit_template(self):
        raise NotImplementedError

    def get_selected_items(self):
        raise NotImplementedError

    def build_manage_buttons(self, layout):
        """Add type-specific buttons to the manage layout. Called after base buttons."""
        pass

    def get_bulk_add_class(self):
        return None

    # --- Shared UI setup ---

    def init_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel(self.get_header_text())
        header.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY}; font-size: {theme.FONT_SIZE_LARGE}px;")
        layout.addWidget(header)

        # Navigation bar
        nav_layout = QHBoxLayout()

        self.back_btn = QPushButton("Back")
        self.back_btn.setStyleSheet(theme.get_button_style())
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setVisible(False)
        nav_layout.addWidget(self.back_btn)

        self.path_label = QLabel(f"{self.templates_dir}")
        self.path_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        nav_layout.addWidget(self.path_label)
        nav_layout.addStretch()

        layout.addLayout(nav_layout)

        self.load_templates()

        self.table = self._build_table()
        self.populate_table()
        layout.addWidget(self.table)

        # Manage buttons row
        manage_layout = QHBoxLayout()
        self._add_base_manage_buttons(manage_layout)
        self.build_manage_buttons(manage_layout)
        manage_layout.addStretch()
        layout.addLayout(manage_layout)

        # Select/Deselect row
        select_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.setStyleSheet(theme.get_button_style())
        select_all_btn.clicked.connect(self.select_all)
        select_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.setStyleSheet(theme.get_button_style())
        deselect_all_btn.clicked.connect(self.deselect_all)
        select_layout.addWidget(deselect_all_btn)

        select_layout.addStretch()
        layout.addLayout(select_layout)

        info = QLabel(self.get_info_text())
        info.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _build_table(self):
        """Create the shared table widget."""
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["", "Name", "Description"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        table.setColumnWidth(0, 40)
        table.setColumnWidth(1, 200)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSortingEnabled(True)
        table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        table.doubleClicked.connect(self.on_double_click)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
            }}
            QHeaderView::section {{
                background-color: {theme.BG_MEDIUM};
                color: {theme.FG_PRIMARY};
                padding: 5px;
                border: 1px solid {theme.BG_LIGHT};
            }}
            QHeaderView::section:hover {{
                background-color: {theme.BG_LIGHT};
            }}
        """)
        return table

    def _add_base_manage_buttons(self, layout):
        """Add buttons common to all library dialogs."""
        add_btn = QPushButton("Add Template")
        add_btn.setStyleSheet(theme.get_button_style())
        add_btn.clicked.connect(self.add_template)
        layout.addWidget(add_btn)

        edit_btn = QPushButton("Edit Selected")
        edit_btn.setStyleSheet(theme.get_button_style())
        edit_btn.clicked.connect(self.edit_template)
        layout.addWidget(edit_btn)

        bulk_cls = self.get_bulk_add_class()
        if bulk_cls is not None:
            bulk_btn = QPushButton("Bulk Add")
            bulk_btn.setStyleSheet(theme.get_button_style())
            bulk_btn.clicked.connect(self._open_bulk_add)
            layout.addWidget(bulk_btn)

        delete_btn = QPushButton("Delete Selected")
        delete_btn.setStyleSheet(theme.get_button_style())
        delete_btn.clicked.connect(self.delete_selected)
        layout.addWidget(delete_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setStyleSheet(theme.get_button_style())
        refresh_btn.clicked.connect(self.refresh_templates)
        layout.addWidget(refresh_btn)

        open_folder_btn = QPushButton("Open Folder")
        open_folder_btn.setStyleSheet(theme.get_button_style())
        open_folder_btn.clicked.connect(self.open_folder)
        layout.addWidget(open_folder_btn)

    # --- Shared navigation and table helpers ---

    def _update_nav(self):
        """Update path label and back button visibility."""
        if self.current_folder:
            self.path_label.setText(f"{self.templates_dir / self.current_folder}")
            self.back_btn.setVisible(True)
        else:
            self.path_label.setText(f"{self.templates_dir}")
            self.back_btn.setVisible(False)

    def _set_table_row(self, row, item_type, name, description=""):
        """Set a row in the table for a folder or template."""
        if item_type == 'folder':
            icon_item = QTableWidgetItem("F")
            icon_item.setData(Qt.ItemDataRole.UserRole, 'folder')
            name_item = QTableWidgetItem(name)
            name_item.setForeground(QColor(theme.ACCENT_PRIMARY))
            desc_item = QTableWidgetItem("")
        else:
            icon_item = QTableWidgetItem("D")
            icon_item.setData(Qt.ItemDataRole.UserRole, 'template')
            display_name = name.split('/')[-1] if '/' in name else name
            name_item = QTableWidgetItem(display_name)
            name_item.setForeground(QColor(theme.FG_PRIMARY))
            desc_item = QTableWidgetItem(description)
            desc_item.setForeground(QColor(theme.FG_SECONDARY))

        name_item.setData(Qt.ItemDataRole.UserRole, name)
        icon_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        self.table.setItem(row, 0, icon_item)
        self.table.setItem(row, 1, name_item)
        self.table.setItem(row, 2, desc_item)

    def on_double_click(self, index):
        """Navigate into a folder on double-click."""
        row = index.row()
        icon_item = self.table.item(row, 0)
        name_item = self.table.item(row, 1)
        if icon_item and icon_item.data(Qt.ItemDataRole.UserRole) == 'folder':
            self.current_folder = name_item.text()
            self.populate_table()

    def go_back(self):
        self.current_folder = ""
        self.populate_table()

    def select_all(self):
        self.table.selectAll()

    def deselect_all(self):
        self.table.clearSelection()

    def delete_selected(self):
        """Delete selected template rows."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select templates to delete.")
            return

        selected = []
        for row_index in selected_rows:
            row = row_index.row()
            icon_item = self.table.item(row, 0)
            name_item = self.table.item(row, 1)
            if icon_item and icon_item.data(Qt.ItemDataRole.UserRole) == 'template':
                full_name = name_item.data(Qt.ItemDataRole.UserRole)
                selected.append(full_name)

        if not selected:
            QMessageBox.warning(self, "No Templates Selected",
                                "Please select templates to delete (folders cannot be deleted directly).")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete {len(selected)} template(s)?\n\n" + "\n".join(selected),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            template_type = self.get_template_type()
            for name in selected:
                try:
                    self.template_mgr.delete_template(template_type, name)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to delete {name}:\n{str(e)}")
            QMessageBox.information(self, "Success", f"Deleted {len(selected)} template(s)!")
            self.refresh_templates()

    def refresh_templates(self):
        self.load_templates()
        self.populate_table()

    def open_folder(self):
        import subprocess
        import platform
        if platform.system() == 'Windows':
            subprocess.Popen(['explorer', str(self.templates_dir)])
        elif platform.system() == 'Darwin':
            subprocess.Popen(['open', str(self.templates_dir)])
        else:
            subprocess.Popen(['xdg-open', str(self.templates_dir)])

    def _open_bulk_add(self):
        bulk_cls = self.get_bulk_add_class()
        if bulk_cls:
            dialog = bulk_cls(self.templates_dir, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.refresh_templates()
