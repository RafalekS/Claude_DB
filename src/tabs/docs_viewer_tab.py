"""
Documentation Viewer Tab - viewing documentation
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextBrowser
)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.theme import *


class DocsViewerTab(QWidget):
    """Tab for viewing documentation"""

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Header
        header = QLabel("Documentation Viewer")
        header.setStyleSheet(f"font-size: {FONT_SIZE_LARGE}px; font-weight: bold; color: {ACCENT_PRIMARY};")
        layout.addWidget(header)

        # Content area - QTextBrowser with Gruvbox styling
        html_file = Path(__file__).parent.parent.parent / "help" / "Claude_DB.html"

        content = QTextBrowser()
        content.setOpenExternalLinks(True)

        if html_file.exists():
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                    # Display HTML as-is without modification
                    content.setHtml(html_content)
            except Exception as e:
                content.setHtml(f"""
                    <h2 style="color: {ACCENT_PRIMARY};">Error loading documentation</h2>
                    <p style="color: {ERROR_COLOR};">{str(e)}</p>
                """)
        else:
            content.setHtml(f"""
                <h2 style="color: {ACCENT_PRIMARY};">Documentation</h2>
                <p style="color: {FG_PRIMARY};">The documentation file <code>help/Claude_DB.html</code> is missing.</p>
                <p style="color: {FG_SECONDARY};">This should contain comprehensive information from all Claude Code documentation sources.</p>
            """)

        content.setStyleSheet(f"""
            QTextBrowser {{
                border: 1px solid {BG_LIGHT};
                padding: 5px;
            }}
        """)

        layout.addWidget(content)
