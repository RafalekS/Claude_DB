"""
Tools Tab - External tool integration with config-based commands
"""

import json
import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QPushButton,
    QMessageBox, QGridLayout, QInputDialog, QDialog, QLineEdit, QCheckBox,
    QTextEdit, QListWidget, QSplitter, QFileDialog, QDialogButtonBox,
    QFormLayout
)
from PyQt6.QtCore import Qt, QProcess
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme
from utils.terminal_utils import run_in_terminal


class ButtonEditorDialog(QDialog):
    """Dialog for editing button configuration"""

    def __init__(self, button_config=None, parent=None):
        super().__init__(parent)
        self.button_config = button_config or {}
        self.setWindowTitle("Button Editor")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Form layout
        form = QFormLayout()

        # Button Text
        self.button_text_input = QLineEdit()
        self.button_text_input.setText(self.button_config.get("button_text", ""))
        self.button_text_input.setPlaceholderText("e.g., My Tool")
        form.addRow("Button Text*:", self.button_text_input)

        # Command
        self.command_input = QLineEdit()
        self.command_input.setText(self.button_config.get("command", ""))
        self.command_input.setPlaceholderText("e.g., npx my-tool or python script.py")
        form.addRow("Command*:", self.command_input)

        # Tooltip
        self.tooltip_input = QLineEdit()
        self.tooltip_input.setText(self.button_config.get("tooltip", ""))
        self.tooltip_input.setPlaceholderText("Description shown on hover")
        form.addRow("Tooltip:", self.tooltip_input)

        # Requires Input
        self.requires_input_checkbox = QCheckBox("Requires user input")
        self.requires_input_checkbox.setChecked(self.button_config.get("requires_input", False))
        self.requires_input_checkbox.toggled.connect(self.on_requires_input_changed)
        form.addRow("", self.requires_input_checkbox)

        # Input Prompt
        self.input_prompt_input = QLineEdit()
        self.input_prompt_input.setText(self.button_config.get("input_prompt", ""))
        self.input_prompt_input.setPlaceholderText("e.g., Enter project folder:")
        self.input_prompt_input.setEnabled(self.button_config.get("requires_input", False))
        form.addRow("Input Prompt:", self.input_prompt_input)

        # Input Label
        self.input_label_input = QLineEdit()
        self.input_label_input.setText(self.button_config.get("input_label", ""))
        self.input_label_input.setPlaceholderText("e.g., Project Folder")
        self.input_label_input.setEnabled(self.button_config.get("requires_input", False))
        form.addRow("Input Label:", self.input_label_input)

        layout.addLayout(form)

        # Info label
        info = QLabel(
            "* Required fields\n\n"
            "Use {project_folder} in command as placeholder for user input."
        )
        info.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px; padding: 5px;")
        layout.addWidget(info)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def on_requires_input_changed(self, checked):
        """Enable/disable input fields based on checkbox"""
        self.input_prompt_input.setEnabled(checked)
        self.input_label_input.setEnabled(checked)

    def validate_and_accept(self):
        """Validate inputs before accepting"""
        if not self.button_text_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Button text is required!")
            return

        if not self.command_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Command is required!")
            return

        self.accept()

    def get_button_config(self):
        """Get the button configuration from form inputs"""
        config = {
            "button_text": self.button_text_input.text().strip(),
            "command": self.command_input.text().strip(),
        }

        if self.tooltip_input.text().strip():
            config["tooltip"] = self.tooltip_input.text().strip()

        if self.requires_input_checkbox.isChecked():
            config["requires_input"] = True
            if self.input_prompt_input.text().strip():
                config["input_prompt"] = self.input_prompt_input.text().strip()
            if self.input_label_input.text().strip():
                config["input_label"] = self.input_label_input.text().strip()

        return config


class ToolsConfigDialog(QDialog):
    """Dialog for managing tools configuration"""

    def __init__(self, config_path, parent=None):
        super().__init__(parent)
        self.config_path = config_path
        self.config = self.load_config()
        self.setWindowTitle("Tools Configuration Manager")
        self.setModal(True)
        self.setMinimumSize(900, 600)
        self.init_ui()

    def load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load config:\n{str(e)}"
            )
            return {"external_tools": {}}

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Manage Tools Configuration")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")
        layout.addWidget(header)

        # Splitter for sections and buttons
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Sections
        left_panel = self.create_sections_panel()
        splitter.addWidget(left_panel)

        # Right panel - Buttons
        right_panel = self.create_buttons_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([300, 600])
        layout.addWidget(splitter, 1)

        # Bottom buttons
        bottom_layout = QHBoxLayout()

        import_btn = QPushButton("📥 Import")
        import_btn.setToolTip("Import configuration from JSON file")
        import_btn.clicked.connect(self.import_config)

        export_btn = QPushButton("📤 Export")
        export_btn.setToolTip("Export configuration to JSON file")
        export_btn.clicked.connect(self.export_config)

        bottom_layout.addWidget(import_btn)
        bottom_layout.addWidget(export_btn)
        bottom_layout.addStretch()

        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip("Save configuration to config.json")
        save_btn.clicked.connect(self.save_config)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        bottom_layout.addWidget(save_btn)
        bottom_layout.addWidget(cancel_btn)

        for btn in [import_btn, export_btn, save_btn, cancel_btn]:
            btn.setStyleSheet(theme.get_button_style())

        layout.addLayout(bottom_layout)

    def create_sections_panel(self):
        """Create left panel for section management"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel("📁 SECTIONS:")
        label.setStyleSheet(f"font-weight: bold; font-size: {theme.FONT_SIZE_NORMAL + 2}px; color: {theme.ACCENT_PRIMARY}; background: {theme.BG_LIGHT}; padding: 5px; border-radius: 3px;")
        layout.addWidget(label)

        self.sections_list = QListWidget()
        self.sections_list.itemClicked.connect(self.on_section_selected)
        self.sections_list.setStyleSheet(theme.get_list_widget_style())
        layout.addWidget(self.sections_list)

        # Buttons with distinct styling for sections
        btn_layout = QHBoxLayout()

        add_section_btn = QPushButton("➕ Section")
        add_section_btn.setToolTip("Add new section")
        add_section_btn.clicked.connect(self.add_section)

        rename_section_btn = QPushButton("✏️ Section")
        rename_section_btn.setToolTip("Rename selected section")
        rename_section_btn.clicked.connect(self.rename_section)

        remove_section_btn = QPushButton("🗑 Section")
        remove_section_btn.setToolTip("Remove selected section and ALL its buttons")
        remove_section_btn.clicked.connect(self.remove_section)

        up_btn = QPushButton("⬆")
        up_btn.setToolTip("Move section up")
        up_btn.clicked.connect(lambda: self.move_section(-1))

        down_btn = QPushButton("⬇")
        down_btn.setToolTip("Move section down")
        down_btn.clicked.connect(lambda: self.move_section(1))

        # Style section buttons differently - use orange/red for dangerous operations
        section_button_style = f"""
            QPushButton {{
                padding: 8px;
                background-color: #e67e22;
                color: white;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: #d35400;
            }}
        """

        arrow_button_style = f"""
            QPushButton {{
                padding: 8px;
                background-color: {theme.BG_LIGHT};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.ACCENT_PRIMARY};
                border-radius: 4px;
                font-weight: bold;
                min-width: 40px;
            }}
            QPushButton:hover {{
                background-color: {theme.ACCENT_PRIMARY};
                color: white;
            }}
        """

        add_section_btn.setStyleSheet(section_button_style)
        rename_section_btn.setStyleSheet(section_button_style)
        remove_section_btn.setStyleSheet(section_button_style)
        up_btn.setStyleSheet(arrow_button_style)
        down_btn.setStyleSheet(arrow_button_style)

        btn_layout.addWidget(add_section_btn)
        btn_layout.addWidget(rename_section_btn)
        btn_layout.addWidget(remove_section_btn)
        btn_layout.addWidget(up_btn)
        btn_layout.addWidget(down_btn)

        layout.addLayout(btn_layout)

        self.load_sections()

        return widget

    def create_buttons_panel(self):
        """Create right panel for button management"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.buttons_label = QLabel("🔘 BUTTONS: Select a section")
        self.buttons_label.setStyleSheet(f"font-weight: bold; font-size: {theme.FONT_SIZE_NORMAL + 2}px; color: {theme.SUCCESS_COLOR}; background: {theme.BG_LIGHT}; padding: 5px; border-radius: 3px;")
        layout.addWidget(self.buttons_label)

        self.buttons_list = QListWidget()
        self.buttons_list.setStyleSheet(theme.get_list_widget_style())
        layout.addWidget(self.buttons_list)

        # Buttons with distinct styling for buttons (green/blue theme)
        btn_layout = QHBoxLayout()

        add_button_btn = QPushButton("➕ Add Button")
        add_button_btn.setToolTip("Add new button to this section")
        add_button_btn.clicked.connect(self.add_button)

        edit_button_btn = QPushButton("✏️ Edit Button")
        edit_button_btn.setToolTip("Edit selected button")
        edit_button_btn.clicked.connect(self.edit_button)

        move_button_btn = QPushButton("📦 Move to Section")
        move_button_btn.setToolTip("Move selected button to another section")
        move_button_btn.clicked.connect(self.move_button_to_section)

        remove_button_btn = QPushButton("🗑 Remove Button")
        remove_button_btn.setToolTip("Remove selected button (section remains)")
        remove_button_btn.clicked.connect(self.remove_button)

        up_btn = QPushButton("⬆")
        up_btn.setToolTip("Move button up")
        up_btn.clicked.connect(lambda: self.move_button(-1))

        down_btn = QPushButton("⬇")
        down_btn.setToolTip("Move button down")
        down_btn.clicked.connect(lambda: self.move_button(1))

        # Style button buttons differently - use blue/green for safer operations
        button_button_style = f"""
            QPushButton {{
                padding: 8px;
                background-color: {theme.SUCCESS_COLOR};
                color: white;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: #27ae60;
            }}
        """

        arrow_button_style = f"""
            QPushButton {{
                padding: 8px;
                background-color: {theme.BG_LIGHT};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.SUCCESS_COLOR};
                border-radius: 4px;
                font-weight: bold;
                min-width: 40px;
            }}
            QPushButton:hover {{
                background-color: {theme.SUCCESS_COLOR};
                color: white;
            }}
        """

        add_button_btn.setStyleSheet(button_button_style)
        edit_button_btn.setStyleSheet(button_button_style)
        move_button_btn.setStyleSheet(button_button_style)
        remove_button_btn.setStyleSheet(button_button_style)
        up_btn.setStyleSheet(arrow_button_style)
        down_btn.setStyleSheet(arrow_button_style)

        btn_layout.addWidget(add_button_btn)
        btn_layout.addWidget(edit_button_btn)
        btn_layout.addWidget(move_button_btn)
        btn_layout.addWidget(remove_button_btn)
        btn_layout.addWidget(up_btn)
        btn_layout.addWidget(down_btn)

        layout.addLayout(btn_layout)

        return widget

    def load_sections(self):
        """Load sections into list"""
        self.sections_list.clear()
        external_tools = self.config.get("external_tools", {})
        for section_key in external_tools.keys():
            self.sections_list.addItem(section_key)

    def on_section_selected(self, item):
        """Handle section selection"""
        section_key = item.text()
        self.buttons_label.setText(f"🔘 BUTTONS in '{section_key}':")
        self.load_buttons(section_key)

    def load_buttons(self, section_key):
        """Load buttons for selected section"""
        self.buttons_list.clear()
        external_tools = self.config.get("external_tools", {})
        buttons = external_tools.get(section_key, [])
        for button_config in buttons:
            button_text = button_config.get("button_text", "Unknown")
            self.buttons_list.addItem(button_text)

    def add_section(self):
        """Add new section"""
        section_name, ok = QInputDialog.getText(
            self,
            "New Section",
            "Enter section name (e.g., 'my_tools'):"
        )

        if not ok or not section_name:
            return

        section_name = section_name.strip().lower().replace(' ', '_')

        external_tools = self.config.get("external_tools", {})
        if section_name in external_tools:
            QMessageBox.warning(self, "Duplicate", f"Section '{section_name}' already exists!")
            return

        external_tools[section_name] = []
        self.load_sections()
        QMessageBox.information(self, "Success", f"Section '{section_name}' created!")

    def rename_section(self):
        """Rename selected section"""
        current_item = self.sections_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a section to rename.")
            return

        old_section_key = current_item.text()

        new_section_name, ok = QInputDialog.getText(
            self,
            "Rename Section",
            f"Enter new name for section '{old_section_key}':",
            text=old_section_key
        )

        if not ok or not new_section_name:
            return

        new_section_name = new_section_name.strip().lower().replace(' ', '_')

        if new_section_name == old_section_key:
            return

        external_tools = self.config.get("external_tools", {})

        if new_section_name in external_tools:
            QMessageBox.warning(self, "Duplicate", f"Section '{new_section_name}' already exists!")
            return

        # Rename the section by copying buttons and deleting old
        external_tools[new_section_name] = external_tools[old_section_key]
        del external_tools[old_section_key]

        self.load_sections()

        # Select the renamed section
        for i in range(self.sections_list.count()):
            if self.sections_list.item(i).text() == new_section_name:
                self.sections_list.setCurrentRow(i)
                break

        QMessageBox.information(self, "Success", f"Section renamed from '{old_section_key}' to '{new_section_name}'!")

    def remove_section(self):
        """Remove selected section"""
        current_item = self.sections_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a section to remove.")
            return

        section_key = current_item.text()

        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Remove section '{section_key}' and all its buttons?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            external_tools = self.config.get("external_tools", {})
            del external_tools[section_key]
            self.load_sections()
            self.buttons_list.clear()
            self.buttons_label.setText("Select a section")

    def move_section(self, direction):
        """Move section up or down"""
        current_row = self.sections_list.currentRow()
        if current_row < 0:
            return

        external_tools = self.config.get("external_tools", {})
        sections = list(external_tools.keys())
        new_row = current_row + direction

        if new_row < 0 or new_row >= len(sections):
            return

        # Swap
        sections[current_row], sections[new_row] = sections[new_row], sections[current_row]

        # Rebuild dict in new order
        new_external_tools = {}
        for section_key in sections:
            new_external_tools[section_key] = external_tools[section_key]

        self.config["external_tools"] = new_external_tools
        self.load_sections()
        self.sections_list.setCurrentRow(new_row)

    def add_button(self):
        """Add new button to selected section"""
        current_item = self.sections_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a section first.")
            return

        section_key = current_item.text()

        dialog = ButtonEditorDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            button_config = dialog.get_button_config()
            external_tools = self.config.get("external_tools", {})
            external_tools[section_key].append(button_config)
            self.load_buttons(section_key)
            QMessageBox.information(self, "Success", "Button added!")

    def edit_button(self):
        """Edit selected button"""
        section_item = self.sections_list.currentItem()
        button_item = self.buttons_list.currentItem()

        if not section_item or not button_item:
            QMessageBox.warning(self, "No Selection", "Please select a button to edit.")
            return

        section_key = section_item.text()
        button_index = self.buttons_list.currentRow()

        external_tools = self.config.get("external_tools", {})
        button_config = external_tools[section_key][button_index]

        dialog = ButtonEditorDialog(button_config, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_config = dialog.get_button_config()
            external_tools[section_key][button_index] = new_config
            self.load_buttons(section_key)
            QMessageBox.information(self, "Success", "Button updated!")

    def remove_button(self):
        """Remove selected button"""
        section_item = self.sections_list.currentItem()
        button_item = self.buttons_list.currentItem()

        if not section_item or not button_item:
            QMessageBox.warning(self, "No Selection", "Please select a button to remove.")
            return

        section_key = section_item.text()
        button_index = self.buttons_list.currentRow()

        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Remove button '{button_item.text()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            external_tools = self.config.get("external_tools", {})
            del external_tools[section_key][button_index]
            self.load_buttons(section_key)

    def move_button(self, direction):
        """Move button up or down"""
        section_item = self.sections_list.currentItem()
        if not section_item:
            return

        current_row = self.buttons_list.currentRow()
        if current_row < 0:
            return

        section_key = section_item.text()
        external_tools = self.config.get("external_tools", {})
        buttons = external_tools[section_key]

        new_row = current_row + direction

        if new_row < 0 or new_row >= len(buttons):
            return

        # Swap
        buttons[current_row], buttons[new_row] = buttons[new_row], buttons[current_row]

        self.load_buttons(section_key)
        self.buttons_list.setCurrentRow(new_row)

    def move_button_to_section(self):
        """Move selected button to another section"""
        section_item = self.sections_list.currentItem()
        button_item = self.buttons_list.currentItem()

        if not section_item or not button_item:
            QMessageBox.warning(self, "No Selection", "Please select a button to move.")
            return

        source_section = section_item.text()
        button_index = self.buttons_list.currentRow()
        button_text = button_item.text()

        external_tools = self.config.get("external_tools", {})

        # Get all sections except current one
        all_sections = list(external_tools.keys())
        available_sections = [s for s in all_sections if s != source_section]

        if not available_sections:
            QMessageBox.warning(
                self,
                "No Target Sections",
                "No other sections available. Create another section first."
            )
            return

        # Show dialog to select target section
        target_section, ok = QInputDialog.getItem(
            self,
            "Move Button to Section",
            f"Move '{button_text}' from '{source_section}' to:",
            available_sections,
            0,
            False
        )

        if not ok or not target_section:
            return

        # Get the button configuration
        button_config = external_tools[source_section][button_index]

        # Remove from source section
        del external_tools[source_section][button_index]

        # Add to target section
        external_tools[target_section].append(button_config)

        # Refresh the source section view
        self.load_buttons(source_section)

        QMessageBox.information(
            self,
            "Success",
            f"Button '{button_text}' moved from '{source_section}' to '{target_section}'!"
        )

    def import_config(self):
        """Import configuration from JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Configuration",
            str(Path.home()),
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r') as f:
                imported_config = json.load(f)

            if "external_tools" not in imported_config:
                QMessageBox.warning(
                    self,
                    "Invalid File",
                    "JSON file must contain 'external_tools' key."
                )
                return

            reply = QMessageBox.question(
                self,
                "Confirm Import",
                "This will replace current configuration. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.config["external_tools"] = imported_config["external_tools"]
                self.load_sections()
                self.buttons_list.clear()
                self.buttons_label.setText("Select a section")
                QMessageBox.information(self, "Success", "Configuration imported!")

        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import:\n{str(e)}")

    def export_config(self):
        """Export configuration to JSON file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Configuration",
            str(Path.home() / "external_tools_config.json"),
            "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            export_data = {
                "external_tools": self.config.get("external_tools", {})
            }

            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2)

            QMessageBox.information(
                self,
                "Success",
                f"Configuration exported to:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export:\n{str(e)}")

    def save_config(self):
        """Save configuration back to config.json"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)

            # Ask user if they want to restart now
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Configuration Saved")
            msg_box.setText("Configuration saved to config.json!")
            msg_box.setInformativeText("The application needs to restart to apply changes.\n\nDo you want to restart now?")
            msg_box.setIcon(QMessageBox.Icon.Question)

            restart_btn = msg_box.addButton("🔄 Restart Now", QMessageBox.ButtonRole.AcceptRole)
            later_btn = msg_box.addButton("Later", QMessageBox.ButtonRole.RejectRole)

            msg_box.setDefaultButton(restart_btn)
            msg_box.exec()

            if msg_box.clickedButton() == restart_btn:
                self.accept()
                self.restart_application()
            else:
                self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n{str(e)}")

    def restart_application(self):
        """Restart the application"""
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


class ToolsTab(QWidget):
    """Tab for external tool integration - loads commands from config"""

    def __init__(self):
        super().__init__()
        self.config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
        self.commands = self.load_commands()
        self.init_ui()

    def load_commands(self):
        """Load commands from config/config.json"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            return config.get("external_tools", {})
        except Exception as e:
            QMessageBox.warning(
                None,
                "Config Load Error",
                f"Failed to load external tools from config.json:\n{str(e)}\n\nUsing empty command set."
            )
            return {}

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header with Manage button
        header_layout = QHBoxLayout()

        header = QLabel("Tools")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY}; margin-bottom: 10px;")

        manage_btn = QPushButton("⚙️ Manage Tools")
        manage_btn.setToolTip("Open configuration manager to add/edit/remove tools")
        manage_btn.setStyleSheet(theme.get_button_style())
        manage_btn.clicked.connect(self.open_config_manager)

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(manage_btn)

        layout.addLayout(header_layout)

        # Create groups dynamically from config - iterate in order from config
        # Use friendly display names if available, otherwise use the key
        display_names = {
            "configuration": "Configuration Tools",
            "claude_code_templates": "claude-code-templates@latest",
            "monitoring": "Monitoring",
            "plugins": "Plugins & Extensions"
        }

        for section_key, tools in self.commands.items():
            # Get display name or use section key as title
            display_title = display_names.get(section_key, section_key.replace('_', ' ').title())
            group = self.create_tool_group(display_title, tools)
            layout.addWidget(group)

        layout.addStretch()

    def open_config_manager(self):
        """Open the tools configuration manager dialog"""
        dialog = ToolsConfigDialog(self.config_path, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Reload commands (though restart is recommended)
            self.commands = self.load_commands()

    def create_tool_group(self, title, tools):
        """Create a group of tool buttons from config data"""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: {theme.FG_PRIMARY};
                background-color: {theme.BG_MEDIUM};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: {theme.BG_MEDIUM};
            }}
        """)
        grid = QGridLayout()
        grid.setSpacing(8)

        row = 0
        col = 0
        for tool_config in tools:
            button_text = tool_config.get("button_text", "Unknown")
            tooltip = tool_config.get("tooltip", "")

            btn = QPushButton(button_text)
            btn.setToolTip(tooltip)
            btn.clicked.connect(lambda checked, cfg=tool_config: self.handle_command(cfg))
            btn.setStyleSheet(theme.get_button_style())

            grid.addWidget(btn, row, col)

            col += 1
            if col > 3:  # 4 columns
                col = 0
                row += 1

        group.setLayout(grid)
        return group

    def handle_command(self, cmd_config):
        """Handle command execution with input if required"""
        command = cmd_config.get("command", "")
        button_text = cmd_config.get("button_text", "Command")

        # Handle input requirements
        if cmd_config.get("requires_input", False):
            input_prompt = cmd_config.get("input_prompt", "Enter value:")
            input_label = cmd_config.get("input_label", "Value")

            user_input, ok = QInputDialog.getText(
                self,
                input_label,
                input_prompt
            )

            if not ok or not user_input:
                return

            # Replace placeholder in command
            command = command.replace("{project_folder}", user_input)

        # Execute the command
        self.run_tool(command, button_text)

    def run_tool(self, command, tool_name):
        """Run external tool in PowerShell 7 using Windows Terminal"""
        run_in_terminal(command, tool_name, self, show_error=True)
