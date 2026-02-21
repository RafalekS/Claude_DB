"""
Simple text editor dialog for editing template content
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QLabel
from PyQt6.QtCore import Qt
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.theme import *


class SimpleTextDialog(QDialog):
    """Simple dialog for editing text content"""

    def __init__(self, title, label_text, parent=None, initial_text=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.init_ui(label_text, initial_text)

    def init_ui(self, label_text, initial_text):
        layout = QVBoxLayout(self)

        # Label
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {FG_PRIMARY}; font-weight: bold;")
        layout.addWidget(label)

        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(initial_text)
        self.text_edit.setStyleSheet(get_text_edit_style())
        layout.addWidget(self.text_edit)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.setStyleSheet(get_button_style())
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_text(self):
        """Get the edited text"""
        return self.text_edit.toPlainText()
