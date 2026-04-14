"""
Simple text editor dialog for editing template content
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox, QLabel
from PyQt6.QtCore import Qt
from pathlib import Path
from utils import theme
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
        label.setStyleSheet(f"color: {theme.FG_PRIMARY}; font-weight: bold;")
        layout.addWidget(label)

        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(initial_text)
        layout.addWidget(self.text_edit)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_text(self):
        """Get the edited text"""
        return self.text_edit.toPlainText()
