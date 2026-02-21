"""
Prompts Tab - managing Claude Code prompts from promptInfo.json
"""

import json
import urllib.request
import urllib.error
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QMessageBox, QListWidget, QSplitter, QLineEdit, QInputDialog,
    QListWidgetItem, QGroupBox, QCheckBox, QDialog, QDialogButtonBox,
    QTableWidget, QTableWidgetItem, QComboBox, QProgressDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme


class PromptsTab(QWidget):
    """Tab for managing Claude Code prompts from promptInfo.json"""

    def __init__(self, config_manager, backup_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager

        # Prompts file location (singular "prompt", not "prompts")
        self.prompts_file = self.config_manager.claude_dir / "prompt" / "promptInfo.json"
        self.current_prompt = None
        self.prompts_data = []

        self.init_ui()
        self.load_prompts()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        header = QLabel("Prompts Management")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")

        # Search
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search prompts...")
        self.search_box.setMaximumWidth(200)
        self.search_box.textChanged.connect(self.filter_prompts)
        self.search_box.setStyleSheet(theme.get_line_edit_style())

        # Link to Anthropic Prompt Library
        library_btn = QPushButton("📚 Prompt Library")
        library_btn.setStyleSheet(theme.get_button_style())
        library_btn.setToolTip("Open Anthropic Prompt Library for inspiration")
        library_btn.clicked.connect(lambda: self.open_url("https://docs.claude.com/en/resources/prompt-library/library"))

        # Import from GitHub button
        import_btn = QPushButton("📥 Import from GitHub")
        import_btn.setStyleSheet(theme.get_button_style())
        import_btn.setToolTip("Import prompts from a GitHub repository")
        import_btn.clicked.connect(self.import_from_github)

        header_layout.addWidget(header)
        header_layout.addWidget(self.search_box)
        header_layout.addStretch()
        header_layout.addWidget(import_btn)
        header_layout.addWidget(library_btn)

        layout.addLayout(header_layout)

        # File path display
        file_path_label = QLabel(f"File: {self.prompts_file}")
        file_path_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_SMALL}px; color: {theme.FG_SECONDARY}; padding: 5px;")
        file_path_label.setWordWrap(True)
        layout.addWidget(file_path_label)

        # Splitter for list and editor
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - prompts list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        list_label = QLabel("Available Prompts")
        list_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_NORMAL}px; font-weight: bold; color: {theme.FG_PRIMARY};")
        left_layout.addWidget(list_label)

        self.prompts_list = QListWidget()
        self.prompts_list.itemClicked.connect(self.load_prompt_content)
        self.prompts_list.setStyleSheet(theme.get_list_widget_style())
        left_layout.addWidget(self.prompts_list)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        self.new_btn = QPushButton("➕ New")
        self.new_btn.setToolTip("Create new prompt")
        self.del_btn = QPushButton("🗑 Delete")
        self.del_btn.setToolTip("Delete selected prompt")
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setToolTip("Reload prompts from file")

        for btn in [self.new_btn, self.del_btn, self.refresh_btn]:
            btn.setStyleSheet(theme.get_button_style())

        self.new_btn.clicked.connect(self.create_new_prompt)
        self.del_btn.clicked.connect(self.delete_prompt)
        self.refresh_btn.clicked.connect(self.load_prompts)

        btn_layout.addWidget(self.new_btn)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addWidget(self.refresh_btn)
        left_layout.addLayout(btn_layout)

        splitter.addWidget(left_panel)

        # Right panel - editor
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)

        # Editor header
        editor_header_layout = QHBoxLayout()
        editor_header_layout.setSpacing(5)

        self.prompt_name_label = QLabel("No prompt selected")
        self.prompt_name_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_NORMAL}px; font-weight: bold; color: {theme.FG_PRIMARY};")

        self.enable_checkbox = QCheckBox("Enabled")
        self.enable_checkbox.setStyleSheet(f"font-size: {theme.FONT_SIZE_NORMAL}px; color: {theme.FG_PRIMARY};")

        editor_header_layout.addWidget(self.prompt_name_label)
        editor_header_layout.addWidget(self.enable_checkbox)
        editor_header_layout.addStretch()

        right_layout.addLayout(editor_header_layout)

        # CMD field (read-only)
        cmd_layout = QHBoxLayout()
        cmd_layout.setSpacing(5)
        cmd_label = QLabel("CMD:")
        cmd_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_NORMAL}px; color: {theme.FG_SECONDARY};")
        self.cmd_edit = QLineEdit()
        self.cmd_edit.setReadOnly(True)
        self.cmd_edit.setStyleSheet(theme.get_line_edit_style())
        cmd_layout.addWidget(cmd_label)
        cmd_layout.addWidget(self.cmd_edit)
        right_layout.addLayout(cmd_layout)

        # ACT field
        act_layout = QHBoxLayout()
        act_layout.setSpacing(5)
        act_label = QLabel("ACT:")
        act_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_NORMAL}px; color: {theme.FG_SECONDARY};")
        self.act_edit = QLineEdit()
        self.act_edit.setStyleSheet(theme.get_line_edit_style())
        act_layout.addWidget(act_label)
        act_layout.addWidget(self.act_edit)
        right_layout.addLayout(act_layout)

        # PROMPT editor
        prompt_label = QLabel("PROMPT:")
        prompt_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_NORMAL}px; color: {theme.FG_SECONDARY};")
        right_layout.addWidget(prompt_label)

        self.editor = QTextEdit()
        self.editor.setStyleSheet(f"""
            QTextEdit {{
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: {theme.FONT_SIZE_NORMAL}px;
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                padding: 8px;
            }}
        """)
        self.editor.setPlaceholderText("Select a prompt to view/edit, or create a new one.")
        right_layout.addWidget(self.editor, 1)  # Stretch factor

        # Save/Backup/Copy buttons
        save_btn_layout = QHBoxLayout()
        save_btn_layout.setSpacing(5)

        self.copy_btn = QPushButton("📋 Copy to Clipboard")
        self.copy_btn.setToolTip("Copy current prompt content to clipboard")
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.setToolTip("Save changes to promptInfo.json")
        self.backup_btn = QPushButton("📦 Backup")
        self.backup_btn.setToolTip("Create backup of promptInfo.json")

        for btn in [self.copy_btn, self.save_btn, self.backup_btn]:
            btn.setStyleSheet(theme.get_button_style())

        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.save_btn.clicked.connect(self.save_prompts)
        self.backup_btn.clicked.connect(self.backup_prompts)

        save_btn_layout.addWidget(self.copy_btn)
        save_btn_layout.addStretch()
        save_btn_layout.addWidget(self.save_btn)
        save_btn_layout.addWidget(self.backup_btn)

        right_layout.addLayout(save_btn_layout)

        splitter.addWidget(right_panel)

        # Set splitter sizes (30% list, 70% editor)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter, 1)  # Stretch factor

        # Info section at bottom
        info_group = QGroupBox("About Prompts")
        info_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 5px;
                margin-top: 5px;
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

        info_layout = QVBoxLayout()
        info_text = QLabel(
            "Prompts are stored in ~/.claude/prompt/promptInfo.json\n"
            "• CMD: Unique identifier for the prompt\n"
            "• ACT: Display name shown in lists\n"
            "• PROMPT: The actual prompt text to be used\n"
            "• ENABLE: Whether the prompt is active or disabled"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px; padding: 5px;")
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

    def load_prompts(self):
        """Load prompts from promptInfo.json"""
        self.prompts_list.clear()
        self.prompts_data = []

        try:
            if not self.prompts_file.exists():
                QMessageBox.warning(
                    self,
                    "File Not Found",
                    f"Prompts file not found at:\n{self.prompts_file}\n\n"
                    "Creating empty prompts file."
                )
                # Create directory and empty file
                self.prompts_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.prompts_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=4)
                return

            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                self.prompts_data = json.load(f)

            # Populate list
            for prompt in self.prompts_data:
                cmd = prompt.get('CMD', '')
                act = prompt.get('ACT', '')
                enabled = prompt.get('ENABLE', False)

                # Show icon based on enabled status
                icon = "✓" if enabled else "✗"
                item = QListWidgetItem(f"{icon} {act}")
                item.setData(Qt.ItemDataRole.UserRole, prompt)

                # Color based on enabled status
                if enabled:
                    item.setForeground(QColor(theme.SUCCESS_COLOR))
                else:
                    item.setForeground(QColor(theme.FG_DIM))

                self.prompts_list.addItem(item)

            # Show message if no prompts
            if len(self.prompts_data) == 0:
                item = QListWidgetItem("No prompts found. Click 'New' to create one.")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                item.setForeground(QColor(theme.FG_DIM))
                self.prompts_list.addItem(item)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load prompts:\n{str(e)}"
            )

    def filter_prompts(self, text):
        """Filter prompts list based on search text"""
        for i in range(self.prompts_list.count()):
            item = self.prompts_list.item(i)
            if text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def load_prompt_content(self, item):
        """Load selected prompt's content into editor"""
        prompt_data = item.data(Qt.ItemDataRole.UserRole)
        if not prompt_data:
            return

        self.current_prompt = prompt_data

        # Populate fields
        self.cmd_edit.setText(prompt_data.get('CMD', ''))
        self.act_edit.setText(prompt_data.get('ACT', ''))
        self.editor.setPlainText(prompt_data.get('PROMPT', ''))
        self.enable_checkbox.setChecked(prompt_data.get('ENABLE', False))

        self.prompt_name_label.setText(f"Editing: {prompt_data.get('ACT', '')}")

    def create_new_prompt(self):
        """Create a new prompt entry"""
        # Ask for CMD
        cmd, ok = QInputDialog.getText(
            self,
            "New Prompt - CMD",
            "Enter unique CMD identifier (lowercase, underscores):"
        )

        if not ok or not cmd:
            return

        # Sanitize CMD
        cmd = cmd.strip().lower().replace(' ', '_').replace('-', '_')

        # Check if CMD already exists
        for prompt in self.prompts_data:
            if prompt.get('CMD') == cmd:
                QMessageBox.warning(
                    self,
                    "CMD Exists",
                    f"A prompt with CMD '{cmd}' already exists!"
                )
                return

        # Ask for ACT
        act, ok = QInputDialog.getText(
            self,
            "New Prompt - ACT",
            "Enter display name (ACT):"
        )

        if not ok or not act:
            return

        # Create new prompt entry
        new_prompt = {
            "CMD": cmd,
            "ACT": act,
            "PROMPT": "",
            "ENABLE": True
        }

        self.prompts_data.append(new_prompt)

        # Save immediately
        self.save_prompts_to_file()

        # Reload list
        self.load_prompts()

        QMessageBox.information(
            self,
            "Prompt Created",
            f"New prompt '{act}' created.\nYou can now edit the PROMPT text."
        )

    def delete_prompt(self):
        """Delete the selected prompt"""
        current_item = self.prompts_list.currentItem()
        if not current_item:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a prompt to delete."
            )
            return

        prompt_data = current_item.data(Qt.ItemDataRole.UserRole)
        if not prompt_data:
            return

        act = prompt_data.get('ACT', '')

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the prompt '{act}'?\n\n"
            f"This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Remove from data
                self.prompts_data.remove(prompt_data)

                # Save
                self.save_prompts_to_file()

                # Clear editor
                self.cmd_edit.clear()
                self.act_edit.clear()
                self.editor.clear()
                self.enable_checkbox.setChecked(False)
                self.prompt_name_label.setText("No prompt selected")
                self.current_prompt = None

                # Reload list
                self.load_prompts()

                QMessageBox.information(
                    self,
                    "Deleted",
                    f"Prompt '{act}' has been deleted."
                )

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Deletion Error",
                    f"Failed to delete prompt:\n{str(e)}"
                )

    def save_prompts(self):
        """Save current prompt changes"""
        if not self.current_prompt:
            QMessageBox.warning(
                self,
                "No Prompt Selected",
                "Please select a prompt to save changes."
            )
            return

        try:
            # Update current prompt data
            self.current_prompt['ACT'] = self.act_edit.text()
            self.current_prompt['PROMPT'] = self.editor.toPlainText()
            self.current_prompt['ENABLE'] = self.enable_checkbox.isChecked()

            # Save to file
            self.save_prompts_to_file()

            # Reload list to show changes
            self.load_prompts()

            QMessageBox.information(
                self,
                "Saved",
                "Prompt changes saved successfully!"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save prompt:\n{str(e)}"
            )

    def save_prompts_to_file(self):
        """Save prompts_data to promptInfo.json"""
        try:
            # Create backup if file exists
            if self.prompts_file.exists():
                self.backup_manager.create_file_backup(self.prompts_file)

            # Save with proper formatting
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts_data, f, indent=4, ensure_ascii=False)

        except Exception as e:
            raise Exception(f"Failed to write to file: {str(e)}")

    def backup_prompts(self):
        """Create manual backup of promptInfo.json"""
        if not self.prompts_file.exists():
            QMessageBox.warning(
                self,
                "File Not Found",
                f"Prompts file not found at:\n{self.prompts_file}"
            )
            return

        try:
            backup_path = self.backup_manager.create_file_backup(self.prompts_file)
            QMessageBox.information(
                self,
                "Backup Created",
                f"Backup saved to:\n{backup_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Backup Error",
                f"Failed to create backup:\n{str(e)}"
            )

    def copy_to_clipboard(self):
        """Copy current prompt content to clipboard"""
        from PyQt6.QtWidgets import QApplication

        if not self.current_prompt:
            QMessageBox.warning(
                self,
                "No Prompt Selected",
                "Please select a prompt to copy."
            )
            return

        # Get the prompt text from the editor
        prompt_text = self.editor.toPlainText()

        if not prompt_text.strip():
            QMessageBox.warning(
                self,
                "Empty Prompt",
                "The current prompt is empty."
            )
            return

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(prompt_text)

        QMessageBox.information(
            self,
            "Copied",
            f"Prompt copied to clipboard!\n\nYou can now paste it into Claude Code to start a conversation."
        )

    def open_url(self, url):
        """Open URL in default browser"""
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl(url))

    def import_from_github(self):
        """Import prompts from GitHub repository"""
        # Ask for GitHub URL
        default_url = "https://github.com/RafalekS/claude_prompts"
        url, ok = QInputDialog.getText(
            self,
            "Import from GitHub",
            f"Enter GitHub repository URL:\n(e.g., {default_url})",
            QLineEdit.EchoMode.Normal,
            default_url
        )

        if not ok or not url:
            return

        url = url.strip()

        if not url.startswith("https://github.com/"):
            QMessageBox.warning(
                self,
                "Invalid URL",
                "Please provide a valid GitHub repository URL.\n\n"
                "Examples:\n"
                "• https://github.com/user/repo\n"
                "• https://github.com/user/repo/blob/main/promptInfo.json"
            )
            return

        # Show progress dialog
        progress = QProgressDialog("Fetching prompts from GitHub...", "Cancel", 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        try:
            # Try fetching promptInfo.json first
            raw_url = self.convert_to_raw_url(url)
            imported_prompts = None

            try:
                imported_prompts = self.fetch_prompts_from_url(raw_url)
            except Exception as json_error:
                # If promptInfo.json doesn't exist, try to fetch .md files
                progress.setLabelText("promptInfo.json not found, scanning for .md files...")
                imported_prompts = self.fetch_prompts_from_md_files(url)

            progress.close()

            if not imported_prompts:
                QMessageBox.information(
                    self,
                    "No Prompts Found",
                    "No prompts found in the repository.\n\n"
                    "Looked for:\n"
                    "• promptInfo.json\n"
                    "• Individual .md files"
                )
                return

            # Show selection dialog
            dialog = GitHubImportDialog(imported_prompts, self.prompts_data, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                selected_prompts, conflict_resolution = dialog.get_selected_prompts()

                if not selected_prompts:
                    QMessageBox.information(
                        self,
                        "No Selection",
                        "No prompts were selected for import."
                    )
                    return

                # Merge prompts
                added, updated, skipped = self.merge_prompts(
                    selected_prompts,
                    conflict_resolution
                )

                # Save to file
                self.save_prompts_to_file()

                # Reload list
                self.load_prompts()

                # Show summary
                summary = f"Import Summary:\n\n"
                summary += f"✅ Added: {added}\n"
                summary += f"🔄 Updated: {updated}\n"
                summary += f"⏭ Skipped: {skipped}\n"
                summary += f"\nTotal: {added + updated} prompts imported"

                QMessageBox.information(
                    self,
                    "Import Complete",
                    summary
                )

        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to import prompts:\n\n{str(e)}"
            )

    def convert_to_raw_url(self, github_url):
        """Convert GitHub URL to raw content URL"""
        if not github_url.startswith("https://github.com/"):
            return None

        # If already pointing to a blob file, convert to raw
        if "/blob/" in github_url:
            raw_url = github_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            return raw_url

        # If just repo URL, try to get promptInfo.json from main/master branch
        # Try main branch first
        repo_path = github_url.replace("https://github.com/", "")
        raw_url = f"https://raw.githubusercontent.com/{repo_path}/main/promptInfo.json"

        return raw_url

    def fetch_prompts_from_url(self, url):
        """Fetch and parse prompts from URL"""
        try:
            # Try fetching from the URL
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Claude_DB/1.0'}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                data = response.read()
                prompts = json.loads(data.decode('utf-8'))

                if not isinstance(prompts, list):
                    raise ValueError("Invalid format: expected a list of prompts")

                return prompts

        except urllib.error.HTTPError as e:
            # If main branch failed, try master branch
            if e.code == 404 and "/main/" in url:
                master_url = url.replace("/main/", "/master/")
                try:
                    req = urllib.request.Request(
                        master_url,
                        headers={'User-Agent': 'Claude_DB/1.0'}
                    )
                    with urllib.request.urlopen(req, timeout=10) as response:
                        data = response.read()
                        prompts = json.loads(data.decode('utf-8'))
                        if not isinstance(prompts, list):
                            raise ValueError("Invalid format: expected a list of prompts")
                        return prompts
                except:
                    pass

            raise Exception(f"HTTP Error {e.code}: {e.reason}")

        except urllib.error.URLError as e:
            raise Exception(f"Network error: {str(e.reason)}")

        except json.JSONDecodeError:
            raise Exception("Invalid JSON format in the file")

        except Exception as e:
            raise Exception(f"Fetch error: {str(e)}")

    def fetch_prompts_from_md_files(self, github_url):
        """Fetch prompts from individual .md files in repository"""
        try:
            # Extract owner and repo from URL
            # Format: https://github.com/owner/repo
            parts = github_url.replace("https://github.com/", "").split("/")
            if len(parts) < 2:
                raise Exception("Invalid GitHub URL format")

            owner = parts[0]
            repo = parts[1]

            # Use GitHub API to list repository contents
            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents"

            req = urllib.request.Request(
                api_url,
                headers={
                    'User-Agent': 'Claude_DB/1.0',
                    'Accept': 'application/vnd.github.v3+json'
                }
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                files_data = json.loads(response.read().decode('utf-8'))

            # Filter for .md files
            md_files = [f for f in files_data if f.get('name', '').endswith('.md') and f.get('type') == 'file']

            if not md_files:
                return []

            # Fetch content of each .md file
            prompts = []
            for md_file in md_files:
                try:
                    download_url = md_file.get('download_url')
                    if not download_url:
                        continue

                    # Fetch file content
                    req = urllib.request.Request(
                        download_url,
                        headers={'User-Agent': 'Claude_DB/1.0'}
                    )

                    with urllib.request.urlopen(req, timeout=10) as response:
                        content = response.read().decode('utf-8')

                    # Create prompt from filename and content
                    filename = md_file.get('name', '')
                    cmd = filename.replace('.md', '').lower().replace(' ', '_').replace('-', '_')
                    act = filename.replace('.md', '').replace('_', ' ').replace('-', ' ').title()

                    prompt = {
                        "CMD": cmd,
                        "ACT": act,
                        "PROMPT": content.strip(),
                        "ENABLE": True
                    }

                    prompts.append(prompt)

                except Exception as file_error:
                    # Skip files that fail to fetch
                    print(f"Failed to fetch {md_file.get('name')}: {file_error}")
                    continue

            return prompts

        except urllib.error.HTTPError as e:
            raise Exception(f"GitHub API Error {e.code}: {e.reason}")

        except Exception as e:
            raise Exception(f"Failed to fetch .md files: {str(e)}")

    def merge_prompts(self, imported_prompts, conflict_resolution):
        """Merge imported prompts with existing data"""
        added = 0
        updated = 0
        skipped = 0

        for prompt in imported_prompts:
            cmd = prompt.get('CMD', '')

            # Find if prompt already exists
            existing_prompt = None
            existing_index = -1
            for i, p in enumerate(self.prompts_data):
                if p.get('CMD') == cmd:
                    existing_prompt = p
                    existing_index = i
                    break

            if existing_prompt:
                # Conflict! Check resolution strategy
                resolution = conflict_resolution.get(cmd, 'skip')

                if resolution == 'overwrite':
                    # Replace existing prompt
                    self.prompts_data[existing_index] = prompt
                    updated += 1
                elif resolution == 'rename':
                    # Add with modified CMD
                    new_cmd = f"{cmd}_imported"
                    counter = 1
                    while any(p.get('CMD') == new_cmd for p in self.prompts_data):
                        new_cmd = f"{cmd}_imported_{counter}"
                        counter += 1

                    prompt['CMD'] = new_cmd
                    self.prompts_data.append(prompt)
                    added += 1
                else:  # skip
                    skipped += 1
            else:
                # No conflict, add new prompt
                self.prompts_data.append(prompt)
                added += 1

        return added, updated, skipped


class GitHubImportDialog(QDialog):
    """Dialog for selecting prompts to import from GitHub"""

    def __init__(self, imported_prompts, existing_prompts, parent=None):
        super().__init__(parent)
        self.imported_prompts = imported_prompts
        self.existing_prompts = existing_prompts
        self.conflict_resolution = {}

        self.setWindowTitle("Import Prompts from GitHub")
        self.setMinimumSize(900, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Select prompts to import:")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")
        layout.addWidget(header)

        # Info label
        info = QLabel(
            f"Found {len(self.imported_prompts)} prompts in repository.\n"
            "Select which prompts to import and how to handle conflicts."
        )
        info.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px; padding: 5px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Table for prompts
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Import", "CMD", "Display Name (ACT)", "Status", "If Conflict"
        ])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setStyleSheet(theme.get_list_widget_style())

        # Populate table
        self.populate_table()

        layout.addWidget(self.table, 1)

        # Buttons
        btn_layout = QHBoxLayout()

        select_all_btn = QPushButton("✓ Select All")
        select_all_btn.clicked.connect(self.select_all)
        select_all_btn.setStyleSheet(theme.get_button_style())

        deselect_all_btn = QPushButton("✗ Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all)
        deselect_all_btn.setStyleSheet(theme.get_button_style())

        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(deselect_all_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def populate_table(self):
        """Populate table with imported prompts"""
        self.table.setRowCount(len(self.imported_prompts))

        for row, prompt in enumerate(self.imported_prompts):
            cmd = prompt.get('CMD', '')
            act = prompt.get('ACT', '')

            # Check if conflict exists
            is_conflict = any(p.get('CMD') == cmd for p in self.existing_prompts)

            # Checkbox for import
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.CheckState.Checked)
            self.table.setItem(row, 0, checkbox_item)

            # CMD
            cmd_item = QTableWidgetItem(cmd)
            cmd_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row, 1, cmd_item)

            # ACT
            act_item = QTableWidgetItem(act)
            act_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row, 2, act_item)

            # Status
            if is_conflict:
                status_item = QTableWidgetItem("⚠️ Conflict")
                status_item.setForeground(QColor("#e67e22"))
            else:
                status_item = QTableWidgetItem("✓ New")
                status_item.setForeground(QColor(theme.SUCCESS_COLOR))
            status_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row, 3, status_item)

            # Conflict resolution dropdown
            if is_conflict:
                resolution_combo = QComboBox()
                resolution_combo.addItems(["Skip", "Overwrite", "Rename"])
                resolution_combo.setStyleSheet(f"""
                    QComboBox {{
                        padding: 4px;
                        background-color: {theme.BG_DARK};
                        color: {theme.FG_PRIMARY};
                        border: 1px solid {theme.ACCENT_PRIMARY};
                        border-radius: 3px;
                    }}
                """)
                resolution_combo.setProperty("cmd", cmd)
                resolution_combo.currentTextChanged.connect(self.on_resolution_changed)
                self.table.setCellWidget(row, 4, resolution_combo)
                self.conflict_resolution[cmd] = 'skip'
            else:
                na_item = QTableWidgetItem("N/A")
                na_item.setForeground(QColor(theme.FG_DIM))
                na_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(row, 4, na_item)

        # Resize columns
        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 120)

    def on_resolution_changed(self, text):
        """Handle conflict resolution selection"""
        combo = self.sender()
        cmd = combo.property("cmd")
        self.conflict_resolution[cmd] = text.lower()

    def select_all(self):
        """Select all prompts"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)

    def deselect_all(self):
        """Deselect all prompts"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)

    def get_selected_prompts(self):
        """Get list of selected prompts and their conflict resolutions"""
        selected = []

        for row in range(self.table.rowCount()):
            checkbox_item = self.table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.CheckState.Checked:
                selected.append(self.imported_prompts[row])

        return selected, self.conflict_resolution
