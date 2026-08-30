"""
About Tab - Information and resources
"""

from pathlib import Path
import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser, QGroupBox, QPushButton,
    QDialog, QLineEdit, QDialogButtonBox, QMessageBox, QListWidget, QComboBox,
    QListWidgetItem, QFormLayout, QTextEdit
)
from PyQt6.QtCore import Qt
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.theme import *


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
        self.url_input.setPlaceholderText("e.g., https://docs.claude.com/...")
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
        self.list_widget.setAlternatingRowColors(True)
        layout.addWidget(self.list_widget)

        # Buttons
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("➕ Add Link")
        add_btn.setStyleSheet(get_button_style())
        add_btn.setFixedWidth(120)
        add_btn.clicked.connect(self.add_link)

        edit_btn = QPushButton("✏️ Edit Link")
        edit_btn.setStyleSheet(get_button_style())
        edit_btn.setFixedWidth(120)
        edit_btn.clicked.connect(self.edit_link)

        delete_btn = QPushButton("🗑️ Delete Link")
        delete_btn.setStyleSheet(get_button_style())
        delete_btn.setFixedWidth(120)
        delete_btn.clicked.connect(self.delete_link)

        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(get_button_style())
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
                with open(self.links_file, 'r') as f:
                    data = json.load(f)
                    self.official_links = data.get("official", [])
                    self.community_links = data.get("community", [])
                    self.frameworks_links = data.get("frameworks", [])
                    self.marketplaces_links = data.get("marketplaces", [])
                    return
            except Exception as e:
                print(f"Failed to load links: {e}")

        # Default links
        self.official_links = [
            ["https://support.claude.com", "Claude Support"],
            ["https://www.anthropic.com/claude", "Anthropic Claude"],
            ["https://www.anthropic.com/engineering/claude-code-best-practices", "Claude Code Best Practices"],
            ["https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills", "Agent Skills Guide"],
            ["https://www.anthropic.com/news/claude-code-plugins", "Claude Code Plugins"],
            ["https://docs.claude.com/en/docs/claude-code/cli-reference", "CLI Reference"],
            ["https://docs.claude.com/en/docs/claude-code/settings", "Settings Documentation"],
            ["https://docs.claude.com/en/docs/claude-code/memory", "Memory System"],
            ["https://docs.claude.com/en/docs/claude-code/checkpointing", "Checkpointing"],
            ["https://docs.claude.com/en/docs/claude-code/slash-commands", "Slash Commands"],
            ["https://docs.claude.com/en/docs/claude-code/interactive-mode", "Interactive Mode"],
            ["https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview", "Agent Skills Overview"],
            ["https://docs.claude.com/en/api/agent-sdk/skills", "Agent SDK Skills"],
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
            with open(self.links_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save links:\n{str(e)}")

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)

        # Compact Header with all buttons
        header_layout = QHBoxLayout()
        header = QLabel("Claude_DB v2.0.0")
        header.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {ACCENT_PRIMARY};")
        header_layout.addWidget(header)

        # Link management button
        manage_btn = QPushButton("🔗 Manage Links")
        manage_btn.setStyleSheet(get_button_style())
        manage_btn.setFixedWidth(130)
        manage_btn.clicked.connect(self.manage_links)
        header_layout.addWidget(manage_btn)

        # Documentation Button
        docs_button = QPushButton("📚 Docs")
        docs_button.setStyleSheet(get_button_style())
        docs_button.setToolTip("Open Claude_DB.html")
        docs_button.setFixedWidth(90)
        docs_button.clicked.connect(self.open_local_docs)
        header_layout.addWidget(docs_button)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Store content widgets for refresh
        self.content_widgets = {}

        # Official Documentation
        official_group, self.content_widgets['official'] = self.create_link_group("Official Documentation", self.official_links)
        layout.addWidget(official_group)

        # Community Resources
        community_group, self.content_widgets['community'] = self.create_link_group("Community Resources", self.community_links)
        layout.addWidget(community_group)

        # Frameworks & Tools
        frameworks_group, self.content_widgets['frameworks'] = self.create_link_group("Frameworks & Tools", self.frameworks_links)
        layout.addWidget(frameworks_group)

        # Plugin Marketplaces
        marketplaces_group, self.content_widgets['marketplaces'] = self.create_link_group("Plugin Marketplaces", self.marketplaces_links)
        layout.addWidget(marketplaces_group)

        # Claude Agent SDK Installation - compact
        sdk_layout = QHBoxLayout()
        sdk_label = QLabel("SDK:")
        sdk_label.setStyleSheet(f"color: {FG_PRIMARY}; font-weight: bold;")

        cmd_label = QLabel("npm install @anthropic-ai/claude-agent-sdk")
        cmd_label.setStyleSheet(f"background: {BG_DARK}; padding: 5px; color: {FG_PRIMARY}; font-family: 'Consolas', 'Monaco', monospace; border-radius: 3px;")

        copy_sdk_btn = QPushButton("📋 Copy")
        copy_sdk_btn.setStyleSheet(get_button_style())
        copy_sdk_btn.setFixedWidth(90)
        copy_sdk_btn.clicked.connect(self.copy_sdk_command)

        sdk_layout.addWidget(sdk_label)
        sdk_layout.addWidget(cmd_label)
        sdk_layout.addWidget(copy_sdk_btn)
        sdk_layout.addStretch()
        layout.addLayout(sdk_layout)

        # Developer Info - compact
        dev_info = QLabel("Rafal Staska | r.staska@gmail.com | GitHub: RafalekS")
        dev_info.setStyleSheet(f"margin-top: 5px; padding: 5px; background: {BG_MEDIUM}; color: {FG_SECONDARY}; font-size: {FONT_SIZE_SMALL}px; border-radius: 3px;")
        layout.addWidget(dev_info)

        layout.addStretch()

    def create_link_group(self, title, links):
        """Create a group of clickable links"""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {BG_LIGHT};
                border-radius: 5px;
                margin-top: 5px;
                padding-top: 10px;
                color: {ACCENT_PRIMARY};
                font-size: {FONT_SIZE_NORMAL}px;
                background: {BG_DARK};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)

        group_layout = QVBoxLayout()

        # Links display
        content = QTextBrowser()
        content.setOpenExternalLinks(True)

        html = "<ul style='line-height: 1.6; margin: 0; padding-left: 20px;'>"
        for url, text in links:
            html += f"<li><a href='{url}' style='color: {ACCENT_PRIMARY};'>{text}</a></li>"
        html += "</ul>"

        content.setHtml(html)
        content.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {BG_DARK};
                color: {FG_PRIMARY};
                border: none;
                font-size: {FONT_SIZE_SMALL}px;
            }}
        """)
        content.setMaximumHeight(120)

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
            html += f"<li><a href='{url}' style='color: {ACCENT_PRIMARY};'>{text}</a></li>"
        html += "</ul>"
        content_widget.setHtml(html)

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

    def copy_sdk_command(self):
        """Copy SDK installation command to clipboard"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText("npm install @anthropic-ai/claude-agent-sdk")
        QMessageBox.information(
            self,
            "Copied",
            "SDK installation command copied to clipboard!"
        )
