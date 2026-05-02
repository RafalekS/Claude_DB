"""
About Tab - Information and resources
"""

import json
from version import __version__
import logging
import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser, QGroupBox, QPushButton,
    QDialog, QLineEdit, QDialogButtonBox, QMessageBox, QListWidget, QComboBox,
    QListWidgetItem, QFormLayout, QTextEdit, QSplitter
)
from PyQt6.QtCore import Qt
from utils import theme
from utils.ui_state_manager import UIStateManager

logger = logging.getLogger(__name__)

class LinkEditDialog(QDialog):
    """Proper dialog for adding/editing a link"""

    def __init__(self, parent, url="", title="", mode="add"):
        super().__init__(parent)
        self.setWindowTitle("Add Link" if mode == "add" else "Edit Link")
        self.setModal(True)
        self.resize(700, 250)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Title field
        title_label = QLabel("Title:")
        self.title_input = QLineEdit()
        self.title_input.setText(title)
        self.title_input.setPlaceholderText("e.g., Claude Code Documentation")
        self.title_input.setMinimumWidth(600)
        form.addRow(title_label, self.title_input)

        # URL field - using QTextEdit for multiline if needed
        url_label = QLabel("URL:")
        self.url_input = QTextEdit()
        self.url_input.setPlainText(url)
        self.url_input.setPlaceholderText("e.g., https://code.claude.com/...")
        self.url_input.setMaximumHeight(80)
        self.url_input.setMinimumWidth(600)
        form.addRow(url_label, self.url_input)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Focus on title field
        self.title_input.setFocus()

    def get_data(self):
        """Return the entered data"""
        return self.url_input.toPlainText().strip(), self.title_input.text().strip()

class LinkManagerDialog(QDialog):
    """Unified dialog for managing all links"""

    def __init__(self, parent, all_links):
        super().__init__(parent)
        self.setWindowTitle("Manage Links")
        self.setModal(True)
        self.resize(900, 700)
        self.all_links = all_links
        self.current_category = "official"

        layout = QVBoxLayout(self)

        # Category selector
        cat_layout = QHBoxLayout()
        cat_label = QLabel("Category:")
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Official Documentation", "Community Resources", "Frameworks & Tools", "Plugin Marketplaces"])
        self.category_combo.currentIndexChanged.connect(self.on_category_changed)
        cat_layout.addWidget(cat_label)
        cat_layout.addWidget(self.category_combo)
        cat_layout.addStretch()
        layout.addLayout(cat_layout)

        # Links list - show both title and URL
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        # Buttons
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("➕ Add Link")
        add_btn.setMinimumWidth(100)
        add_btn.clicked.connect(self.add_link)

        edit_btn = QPushButton("✏️ Edit Link")
        edit_btn.setMinimumWidth(100)
        edit_btn.clicked.connect(self.edit_link)

        delete_btn = QPushButton("🗑️ Delete Link")
        delete_btn.setMinimumWidth(100)
        delete_btn.clicked.connect(self.delete_link)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.load_links()

    def get_category_key(self):
        """Get category key from combo box index"""
        return ["official", "community", "frameworks", "marketplaces"][self.category_combo.currentIndex()]

    def on_category_changed(self):
        """Load links when category changes"""
        self.current_category = self.get_category_key()
        self.load_links()

    def load_links(self):
        """Load links for current category"""
        self.list_widget.clear()
        links = self.all_links[self.current_category]
        for url, title in links:
            # Show both title and URL clearly
            item = QListWidgetItem(f"{title}\n{url}")
            self.list_widget.addItem(item)

    def add_link(self):
        """Add new link"""
        dialog = LinkEditDialog(self, mode="add")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            url, title = dialog.get_data()
            if url and title:
                self.all_links[self.current_category].append([url, title])
                self.load_links()
                QMessageBox.information(self, "Success", f"Link '{title}' added!")
            else:
                QMessageBox.warning(self, "Invalid Input", "Both URL and title are required.")

    def edit_link(self):
        """Edit selected link"""
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a link to edit.")
            return

        index = self.list_widget.currentRow()
        old_url, old_title = self.all_links[self.current_category][index]

        dialog = LinkEditDialog(self, old_url, old_title, mode="edit")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            url, title = dialog.get_data()
            if url and title:
                self.all_links[self.current_category][index] = [url, title]
                self.load_links()
                QMessageBox.information(self, "Success", "Link updated!")
            else:
                QMessageBox.warning(self, "Invalid Input", "Both URL and title are required.")

    def delete_link(self):
        """Delete selected link"""
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a link to delete.")
            return

        index = self.list_widget.currentRow()
        url, title = self.all_links[self.current_category][index]

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete '{title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            del self.all_links[self.current_category][index]
            self.load_links()
            QMessageBox.information(self, "Success", "Link deleted!")

class AboutTab(QWidget):
    """Tab with information and resource links"""

    def __init__(self):
        super().__init__()
        self.links_file = Path(__file__).parent.parent.parent / "config" / "resource_links.json"
        self.load_links()
        self.init_ui()

    def load_links(self):
        """Load links from config file or use defaults"""
        if self.links_file.exists():
            try:
                with open(self.links_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.official_links = data.get("official", [])
                    self.community_links = data.get("community", [])
                    self.frameworks_links = data.get("frameworks", [])
                    self.marketplaces_links = data.get("marketplaces", [])
                    return
            except Exception as e:
                logger.warning("Failed to load links: %s", e)

        # Default links
        self.official_links = [
            ["https://support.claude.com", "Claude Support"],
            ["https://www.anthropic.com/claude", "Anthropic Claude"],
            ["https://www.anthropic.com/engineering/claude-code-best-practices", "Claude Code Best Practices"],
            ["https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills", "Agent Skills Guide"],
            ["https://www.anthropic.com/news/claude-code-plugins", "Claude Code Plugins"],
            ["https://code.claude.com/en/docs/claude-code/cli-reference", "CLI Reference"],
            ["https://code.claude.com/en/docs/claude-code/settings", "Settings Documentation"],
            ["https://code.claude.com/en/docs/claude-code/memory", "Memory System"],
            ["https://code.claude.com/en/docs/claude-code/checkpointing", "Checkpointing"],
            ["https://code.claude.com/en/docs/claude-code/slash-commands", "Slash Commands"],
            ["https://code.claude.com/en/docs/claude-code/interactive-mode", "Interactive Mode"],
            ["https://code.claude.com/en/docs/agents-and-tools/agent-skills/overview", "Agent Skills Overview"],
            ["https://code.claude.com/en/api/agent-sdk/skills", "Agent SDK Skills"],
        ]
        self.community_links = [
            ["https://claudelog.com", "ClaudeLog - Community Hub"],
            ["https://claudelog.com/configuration/", "Configuration Guide"],
            ["https://claudelog.com/mechanics/custom-agents/", "Custom Agents Guide"],
            ["https://claudecode.io/tutorials/claude-md-setup", "CLAUDE.md Setup Tutorial"],
            ["https://awesomeclaude.ai/code-cheatsheet", "Awesome Claude Cheatsheet"],
            ["https://shipyard.build/blog/claude-code-cheat-sheet/", "Shipyard Cheat Sheet"],
            ["https://neon.com/blog/our-claude-code-cheatsheet", "Neon Cheat Sheet"],
            ["https://ainativedev.io/news/configuring-claude-code", "AI Native Dev - Configuring Claude Code"],
            ["https://creatoreconomy.so/p/20-tips-to-master-claude-code-in-35-min-build-an-app", "20 Tips to Master Claude Code"],
            ["https://apidog.com/blog/claude-skills/", "Apidog - Claude Skills"],
            ["https://blog.promptlayer.com/building-agents-with-claude-codes-sdk/", "Building Agents with SDK"],
            ["https://www.reddit.com/r/ClaudeAI/", "Reddit - r/ClaudeAI"],
        ]
        self.frameworks_links = [
            ["https://github.com/SuperClaude-Org/SuperClaude_Framework", "SuperClaude Framework"],
            ["https://github.com/VoltAgent/awesome-claude-code-subagents", "Awesome Claude Code Subagents"],
            ["https://github.com/wshobson/agents", "Agent Collection"],
            ["https://github.com/ggrigo/claude-code-tools", "Claude Code Tools"],
            ["https://github.com/n8n-io/self-hosted-ai-starter-kit", "n8n Self-Hosted AI Starter Kit"],
            ["https://github.com/vincenthopf/claude-code", "vincenthopf/claude-code"],
            ["https://hub.docker.com/r/gendosu/claude-code-docker", "Docker Image - gendosu"],
            ["https://www.npmjs.com/package/@j0kz/api-designer-mcp", "MCP Tools - @j0kz"],
        ]
        self.marketplaces_links = [
            ["https://claudemarketplaces.com/", "Claude Marketplaces"],
            ["https://claudecodemarketplace.com/", "Claude Code Marketplace"],
        ]

    def save_links(self):
        """Save links to config file"""
        try:
            self.links_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "official": self.official_links,
                "community": self.community_links,
                "frameworks": self.frameworks_links,
                "marketplaces": self.marketplaces_links
            }
            with open(self.links_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save links:\n{str(e)}")

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(5)

        # Compact Header with all buttons
        header_layout = QHBoxLayout()
        header = QLabel(f"Claude_DB v{__version__}")
        header.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")
        header_layout.addWidget(header)

        # Link management button
        manage_btn = QPushButton("🔗 Manage Links")
        manage_btn.setMinimumWidth(110)
        manage_btn.clicked.connect(self.manage_links)
        header_layout.addWidget(manage_btn)

        # Documentation Button
        docs_button = QPushButton("📚 Docs")
        docs_button.setToolTip("Open Claude_DB.html")
        docs_button.setMinimumWidth(80)
        docs_button.clicked.connect(self.open_local_docs)
        header_layout.addWidget(docs_button)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Store content widgets for refresh
        self.content_widgets = {}

        # All link groups in a vertical splitter so each section is resizable
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        official_group, self.content_widgets['official'] = self.create_link_group("Official Documentation", self.official_links)
        splitter.addWidget(official_group)

        community_group, self.content_widgets['community'] = self.create_link_group("Community Resources", self.community_links)
        splitter.addWidget(community_group)

        frameworks_group, self.content_widgets['frameworks'] = self.create_link_group("Frameworks & Tools", self.frameworks_links)
        splitter.addWidget(frameworks_group)

        marketplaces_group, self.content_widgets['marketplaces'] = self.create_link_group("Plugin Marketplaces", self.marketplaces_links)
        splitter.addWidget(marketplaces_group)

        mgr = UIStateManager.instance()
        mgr.restore_splitter_state("about.links_splitter", splitter)
        mgr.connect_splitter("about.links_splitter", splitter)

        layout.addWidget(splitter, 1)

        # Developer Info - compact
        dev_info = QLabel("Rafal Staska | r.staska@gmail.com | GitHub: RafalekS")
        dev_info.setStyleSheet(f"margin-top: 5px; padding: 5px; background: {theme.BG_MEDIUM}; color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px; border-radius: 3px;")
        layout.addWidget(dev_info)

        layout.addStretch()

    def create_link_group(self, title, links):
        """Create a group of clickable links"""
        group = QGroupBox(title)

        group_layout = QVBoxLayout()

        # Links display
        content = QTextBrowser()
        content.setOpenExternalLinks(True)

        html = "<ul style='line-height: 1.6; margin: 0; padding-left: 20px;'>"
        for url, text in links:
            html += f"<li><a href='{url}' style='color: {theme.ACCENT_PRIMARY};'>{text}</a></li>"
        html += "</ul>"

        content.setHtml(html)
        content.setStyleSheet(f"""
            QTextBrowser {{
                font-size: {theme.FONT_SIZE_SMALL}px;
            }}
        """)
        group_layout.addWidget(content)
        group.setLayout(group_layout)
        return group, content

    def manage_links(self):
        """Open unified link manager dialog"""
        all_links = {
            "official": self.official_links,
            "community": self.community_links,
            "frameworks": self.frameworks_links,
            "marketplaces": self.marketplaces_links
        }

        dialog = LinkManagerDialog(self, all_links)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save changes
            self.save_links()
            # Refresh all displays
            for category, content_widget in self.content_widgets.items():
                self.refresh_link_display(content_widget, all_links[category])

    def refresh_link_display(self, content_widget, links):
        """Refresh the display of links in a QTextBrowser"""
        html = "<ul style='line-height: 1.6; margin: 0; padding-left: 20px;'>"
        for url, text in links:
            html += f"<li><a href='{url}' style='color: {theme.ACCENT_PRIMARY};'>{text}</a></li>"
        html += "</ul>"
        content_widget.setHtml(html)

    def apply_theme(self):
        """Refresh all link displays with current theme colors."""
        link_map = {
            'official': self.official_links,
            'community': self.community_links,
            'frameworks': self.frameworks_links,
            'marketplaces': self.marketplaces_links,
        }
        for category, widget in self.content_widgets.items():
            self.refresh_link_display(widget, link_map[category])

    def open_local_docs(self):
        """Open the local documentation file in default browser"""
        docs_path = Path(__file__).parent.parent.parent / "help" / "Claude_DB.html"
        if docs_path.exists():
            os.startfile(str(docs_path))
        else:
            QMessageBox.warning(
                self,
                "File Not Found",
                f"Documentation file not found at:\n{docs_path}"
            )

