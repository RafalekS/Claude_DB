"""
Plugin Marketplace Browser Dialog - GUI for browsing and installing plugins from marketplaces
"""

import json
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QLineEdit, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QTextEdit, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme


class MarketplaceFetcherThread(QThread):
    """Background thread to fetch marketplace data"""
    finished = pyqtSignal(dict)  # Emits {success: bool, data: dict/str}

    def __init__(self, marketplace_name, marketplace_config):
        super().__init__()
        self.marketplace_name = marketplace_name
        self.marketplace_config = marketplace_config

    def run(self):
        """Fetch marketplace data"""
        try:
            source_info = self.marketplace_config.get('source', {})
            source_type = source_info.get('source', '')

            if source_type == 'github':
                # Fetch from GitHub raw URL
                repo = source_info.get('repo', '')
                if not repo:
                    self.finished.emit({'success': False, 'error': 'No GitHub repo specified'})
                    return

                import urllib.request
                import urllib.error

                # Strategy 1: Try marketplace.json format first (at root or in .claude-plugin/)
                for branch in ['main', 'master']:
                    # Try root first
                    url = f"https://raw.githubusercontent.com/{repo}/{branch}/marketplace.json"
                    try:
                        with urllib.request.urlopen(url, timeout=10) as response:
                            data = json.loads(response.read().decode('utf-8'))
                            self.finished.emit({'success': True, 'data': data})
                            return
                    except urllib.error.HTTPError:
                        pass
                    except Exception:
                        pass

                    # Try .claude-plugin/marketplace.json
                    url = f"https://raw.githubusercontent.com/{repo}/{branch}/.claude-plugin/marketplace.json"
                    try:
                        with urllib.request.urlopen(url, timeout=10) as response:
                            data = json.loads(response.read().decode('utf-8'))
                            self.finished.emit({'success': True, 'data': data})
                            return
                    except urllib.error.HTTPError:
                        continue
                    except Exception:
                        continue

                # Strategy 2: Try single-plugin format (entire repo is one plugin)
                # Check if .claude-plugin/plugin.json exists at root
                for branch in ['main', 'master']:
                    try:
                        plugin_json_url = f"https://raw.githubusercontent.com/{repo}/{branch}/.claude-plugin/plugin.json"
                        with urllib.request.urlopen(plugin_json_url, timeout=10) as response:
                            plugin_data = json.loads(response.read().decode('utf-8'))
                            # Extract repo name from repo string (e.g., "owner/repo" -> "repo")
                            repo_name = repo.split('/')[-1]
                            plugin_name = plugin_data.get('name', repo_name)
                            plugins = {plugin_name: plugin_data}
                            self.finished.emit({'success': True, 'data': {'plugins': plugins}})
                            return
                    except urllib.error.HTTPError:
                        continue
                    except Exception:
                        continue

                # Strategy 3: Try plugins/ directory format (multi-plugin marketplace)
                # This is what anthropics/claude-code uses
                for branch in ['main', 'master']:
                    try:
                        # Fetch plugins directory listing via GitHub API
                        api_url = f"https://api.github.com/repos/{repo}/contents/plugins"
                        request = urllib.request.Request(
                            api_url,
                            headers={'Accept': 'application/vnd.github.v3+json'}
                        )
                        with urllib.request.urlopen(request, timeout=10) as response:
                            contents = json.loads(response.read().decode('utf-8'))

                        # Filter to only directories (type: "dir")
                        plugin_dirs = [item for item in contents if item.get('type') == 'dir']

                        if not plugin_dirs:
                            continue

                        # Fetch plugin.json for each plugin directory
                        plugins = {}
                        for plugin_dir in plugin_dirs:
                            dir_name = plugin_dir['name']
                            plugin_json_url = f"https://raw.githubusercontent.com/{repo}/{branch}/plugins/{dir_name}/.claude-plugin/plugin.json"

                            try:
                                with urllib.request.urlopen(plugin_json_url, timeout=10) as plugin_response:
                                    plugin_data = json.loads(plugin_response.read().decode('utf-8'))
                                    # Use name from plugin.json if available, otherwise use directory name
                                    plugin_name = plugin_data.get('name', dir_name)
                                    plugins[plugin_name] = plugin_data
                            except:
                                # If plugin.json doesn't exist, create basic metadata using directory name
                                plugins[dir_name] = {
                                    'name': dir_name,
                                    'version': 'unknown',
                                    'author': 'unknown',
                                    'description': f'Plugin from {repo}'
                                }

                        if plugins:
                            self.finished.emit({'success': True, 'data': {'plugins': plugins}})
                            return

                    except urllib.error.HTTPError:
                        continue
                    except Exception:
                        continue

                # If we got here, all strategies failed
                error_msg = (
                    f"Could not load plugins from repository '{repo}'.\n\n"
                    f"Tried:\n"
                    f"1. marketplace.json (root or .claude-plugin/ directory)\n"
                    f"2. Single-plugin format (.claude-plugin/plugin.json)\n"
                    f"3. Multi-plugin format (plugins/ directory)\n\n"
                    f"Make sure the repository is public and contains valid plugin metadata."
                )
                self.finished.emit({'success': False, 'error': error_msg})
                return

            elif source_type == 'directory':
                # Load from local directory
                path = Path(source_info.get('path', ''))

                # Try marketplace.json at root first
                marketplace_file = path / 'marketplace.json'
                if marketplace_file.exists():
                    with open(marketplace_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.finished.emit({'success': True, 'data': data})
                        return

                # Try .claude-plugin/marketplace.json
                marketplace_file = path / '.claude-plugin' / 'marketplace.json'
                if marketplace_file.exists():
                    with open(marketplace_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.finished.emit({'success': True, 'data': data})
                        return

                # Neither found
                self.finished.emit({'success': False, 'error': f'No marketplace.json found in {path} or {path}/.claude-plugin/'})
                return

            elif source_type == 'git':
                # Clone/fetch from git URL
                url = source_info.get('url', '')
                if not url:
                    self.finished.emit({'success': False, 'error': 'No Git URL specified'})
                    return

                # Try to extract GitHub repo from git URL
                # Supports: https://github.com/owner/repo.git, git@github.com:owner/repo.git
                import re
                github_match = re.search(r'github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$', url)

                if github_match:
                    # Extract repo (e.g., "davila7/claude-code-templates")
                    repo = github_match.group(1)

                    # Use same GitHub fetching logic as 'github' source type
                    import urllib.request
                    import urllib.error

                    # Try all three strategies for GitHub repos
                    # Strategy 1: marketplace.json (at root or in .claude-plugin/)
                    for branch in ['main', 'master']:
                        # Try root first
                        try:
                            marketplace_url = f"https://raw.githubusercontent.com/{repo}/{branch}/marketplace.json"
                            with urllib.request.urlopen(marketplace_url, timeout=10) as response:
                                data = json.loads(response.read().decode('utf-8'))
                                self.finished.emit({'success': True, 'data': data})
                                return
                        except:
                            pass

                        # Try .claude-plugin/marketplace.json
                        try:
                            marketplace_url = f"https://raw.githubusercontent.com/{repo}/{branch}/.claude-plugin/marketplace.json"
                            with urllib.request.urlopen(marketplace_url, timeout=10) as response:
                                data = json.loads(response.read().decode('utf-8'))
                                self.finished.emit({'success': True, 'data': data})
                                return
                        except:
                            continue

                    # Strategy 2: Single-plugin format
                    for branch in ['main', 'master']:
                        try:
                            plugin_json_url = f"https://raw.githubusercontent.com/{repo}/{branch}/.claude-plugin/plugin.json"
                            with urllib.request.urlopen(plugin_json_url, timeout=10) as response:
                                plugin_data = json.loads(response.read().decode('utf-8'))
                                repo_name = repo.split('/')[-1]
                                plugin_name = plugin_data.get('name', repo_name)
                                plugins = {plugin_name: plugin_data}
                                self.finished.emit({'success': True, 'data': {'plugins': plugins}})
                                return
                        except:
                            continue

                    # Strategy 3: Multi-plugin format
                    for branch in ['main', 'master']:
                        try:
                            api_url = f"https://api.github.com/repos/{repo}/contents/plugins"
                            request = urllib.request.Request(
                                api_url,
                                headers={'Accept': 'application/vnd.github.v3+json'}
                            )
                            with urllib.request.urlopen(request, timeout=10) as response:
                                contents = json.loads(response.read().decode('utf-8'))

                            plugin_dirs = [item for item in contents if item.get('type') == 'dir']
                            if not plugin_dirs:
                                continue

                            plugins = {}
                            for plugin_dir in plugin_dirs:
                                dir_name = plugin_dir['name']
                                plugin_json_url = f"https://raw.githubusercontent.com/{repo}/{branch}/plugins/{dir_name}/.claude-plugin/plugin.json"
                                try:
                                    with urllib.request.urlopen(plugin_json_url, timeout=10) as plugin_response:
                                        plugin_data = json.loads(plugin_response.read().decode('utf-8'))
                                        plugin_name = plugin_data.get('name', dir_name)
                                        plugins[plugin_name] = plugin_data
                                except:
                                    plugins[dir_name] = {
                                        'name': dir_name,
                                        'version': 'unknown',
                                        'author': 'unknown',
                                        'description': f'Plugin from {repo}'
                                    }

                            if plugins:
                                self.finished.emit({'success': True, 'data': {'plugins': plugins}})
                                return
                        except:
                            continue

                    # All strategies failed
                    self.finished.emit({'success': False, 'error': f'Could not load plugins from git repository: {url}'})
                else:
                    # Non-GitHub git URL - would require actual cloning
                    self.finished.emit({'success': False, 'error': 'Only GitHub git URLs are currently supported'})
                return
            else:
                self.finished.emit({'success': False, 'error': f'Unknown source type: {source_type}'})
                return

        except Exception as e:
            self.finished.emit({'success': False, 'error': str(e)})


class PluginMarketplaceBrowserDialog(QDialog):
    """Dialog for browsing and installing plugins from marketplaces"""

    def __init__(self, parent, known_marketplaces, extra_marketplaces):
        super().__init__(parent)
        self.known_marketplaces = known_marketplaces
        self.extra_marketplaces = extra_marketplaces
        self.all_marketplaces = {**known_marketplaces, **extra_marketplaces}
        self.current_plugins = []
        self.fetcher_thread = None

        self.init_ui()

    @staticmethod
    def get_author_string(author_field):
        """Extract author string from author field (handles both string and object formats)"""
        if isinstance(author_field, dict):
            # Author is an object with name/email
            name = author_field.get('name', 'Unknown')
            email = author_field.get('email', '')
            if email:
                return f"{name} <{email}>"
            return name
        elif isinstance(author_field, str):
            # Author is already a string
            return author_field
        else:
            return 'N/A'

    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Plugin Marketplace Browser")
        self.setMinimumSize(1000, 700)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Header
        header = QLabel("Browse & Install Plugins from Marketplaces")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")
        layout.addWidget(header)

        # Marketplace selector
        selector_layout = QHBoxLayout()
        selector_layout.setSpacing(10)

        selector_label = QLabel("Marketplace:")
        selector_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_NORMAL}px; font-weight: bold;")
        selector_layout.addWidget(selector_label)

        self.marketplace_combo = QComboBox()
        self.marketplace_combo.setStyleSheet(theme.get_line_edit_style())
        self.marketplace_combo.currentIndexChanged.connect(self.on_marketplace_changed)
        selector_layout.addWidget(self.marketplace_combo, 1)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet(theme.get_button_style())
        self.refresh_btn.setToolTip("Reload marketplace data")
        self.refresh_btn.clicked.connect(self.load_current_marketplace)
        selector_layout.addWidget(self.refresh_btn)

        layout.addLayout(selector_layout)

        # Search box
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)

        search_label = QLabel("Search:")
        search_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_NORMAL}px;")
        search_layout.addWidget(search_label)

        self.search_box = QLineEdit()
        self.search_box.setStyleSheet(theme.get_line_edit_style())
        self.search_box.setPlaceholderText("Type to filter plugins...")
        self.search_box.textChanged.connect(self.filter_plugins)
        search_layout.addWidget(self.search_box, 1)

        layout.addLayout(search_layout)

        # Status label
        self.status_label = QLabel("Select a marketplace to browse plugins")
        self.status_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-style: italic;")
        layout.addWidget(self.status_label)

        # Splitter for table and details
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Plugins table
        self.plugins_table = QTableWidget()
        self.plugins_table.setColumnCount(5)
        self.plugins_table.setHorizontalHeaderLabels(["Name", "Version", "Author", "Description", "Install"])
        self.plugins_table.setStyleSheet(theme.get_list_widget_style())
        self.plugins_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.plugins_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.plugins_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.plugins_table.horizontalHeader().setStyleSheet(f"background-color: {theme.BG_MEDIUM}; color: {theme.FG_PRIMARY}; font-weight: bold;")
        self.plugins_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.plugins_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.plugins_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.plugins_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.plugins_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.plugins_table.currentItemChanged.connect(self.on_plugin_selected)

        splitter.addWidget(self.plugins_table)

        # Plugin details viewer
        self.details_viewer = QTextEdit()
        self.details_viewer.setReadOnly(True)
        self.details_viewer.setStyleSheet(theme.get_text_edit_style())
        self.details_viewer.setMaximumHeight(200)
        self.details_viewer.setPlaceholderText("Select a plugin to view details...")

        splitter.addWidget(self.details_viewer)
        splitter.setSizes([500, 200])

        layout.addWidget(splitter, 1)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.install_selected_btn = QPushButton("⬇️ Install Selected Plugin")
        self.install_selected_btn.setStyleSheet(theme.get_button_style())
        self.install_selected_btn.setEnabled(False)
        self.install_selected_btn.clicked.connect(self.install_selected_plugin)
        button_layout.addWidget(self.install_selected_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(theme.get_button_style())
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        # Load marketplaces
        self.load_marketplaces()

    def load_marketplaces(self):
        """Load marketplaces into dropdown"""
        self.marketplace_combo.clear()

        if not self.all_marketplaces:
            self.marketplace_combo.addItem("No marketplaces configured")
            self.status_label.setText("⚠️ No marketplaces configured. Add marketplaces in the Plugins tab first.")
            return

        for name in sorted(self.all_marketplaces.keys()):
            source_info = self.all_marketplaces[name].get('source', {})
            source_type = source_info.get('source', 'unknown')
            self.marketplace_combo.addItem(f"{name} ({source_type})", name)

    def on_marketplace_changed(self, index):
        """Handle marketplace selection change"""
        if index < 0 or not self.all_marketplaces:
            return

        self.load_current_marketplace()

    def load_current_marketplace(self):
        """Load plugins from current marketplace"""
        marketplace_name = self.marketplace_combo.currentData()
        if not marketplace_name or marketplace_name not in self.all_marketplaces:
            return

        marketplace_config = self.all_marketplaces[marketplace_name]

        # Clear table and disable buttons
        self.plugins_table.setRowCount(0)
        self.details_viewer.clear()
        self.install_selected_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.status_label.setText(f"⏳ Fetching plugins from {marketplace_name}...")

        # Fetch marketplace data in background thread
        self.fetcher_thread = MarketplaceFetcherThread(marketplace_name, marketplace_config)
        self.fetcher_thread.finished.connect(self.on_marketplace_loaded)
        self.fetcher_thread.start()

    def on_marketplace_loaded(self, result):
        """Handle marketplace data loaded"""
        self.refresh_btn.setEnabled(True)

        if not result.get('success'):
            error = result.get('error', 'Unknown error')
            self.status_label.setText(f"❌ Failed to load marketplace")

            # Create detailed error message
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Marketplace Load Error")
            msg.setText("Failed to fetch marketplace data")
            msg.setInformativeText(error)

            # Add helpful details
            if "marketplace.json" in error:
                msg.setDetailedText(
                    "Plugin Marketplace Requirements:\n\n"
                    "A valid plugin marketplace must contain a 'marketplace.json' file with this structure:\n\n"
                    "{\n"
                    '  "plugins": {\n'
                    '    "plugin-name": {\n'
                    '      "version": "1.0.0",\n'
                    '      "author": "Author Name",\n'
                    '      "description": "Plugin description"\n'
                    "    }\n"
                    "  }\n"
                    "}\n\n"
                    "Tip: Use the '📦 Browse in Terminal' button to browse plugins\n"
                    "via the official Claude CLI: claude /plugin"
                )

            msg.exec()
            return

        data = result.get('data', {})
        plugins_data = data.get('plugins', {})

        if not plugins_data:
            self.status_label.setText("⚠️ No plugins found in this marketplace")
            return

        self.current_plugins = []

        # Handle both formats: dictionary and list
        if isinstance(plugins_data, dict):
            # Dictionary format: {"plugin-name": {...}}
            for plugin_name, plugin_info in plugins_data.items():
                self.current_plugins.append({
                    'name': plugin_name,
                    'info': plugin_info
                })
        elif isinstance(plugins_data, list):
            # List format: [{"name": "plugin-name", ...}]
            for plugin_info in plugins_data:
                plugin_name = plugin_info.get('name', 'Unknown')
                self.current_plugins.append({
                    'name': plugin_name,
                    'info': plugin_info
                })
        else:
            self.status_label.setText("⚠️ Invalid plugins format in marketplace")
            return

        self.populate_table(self.current_plugins)
        self.status_label.setText(f"✅ Loaded {len(self.current_plugins)} plugins")

    def populate_table(self, plugins):
        """Populate table with plugins"""
        self.plugins_table.setRowCount(0)

        for plugin in plugins:
            plugin_name = plugin['name']
            plugin_info = plugin['info']

            row = self.plugins_table.rowCount()
            self.plugins_table.insertRow(row)

            # Name
            name_item = QTableWidgetItem(plugin_name)
            name_item.setData(Qt.ItemDataRole.UserRole, plugin)
            name_item.setForeground(QColor(theme.ACCENT_PRIMARY))
            self.plugins_table.setItem(row, 0, name_item)

            # Version
            version = plugin_info.get('version', 'N/A')
            version_item = QTableWidgetItem(version)
            self.plugins_table.setItem(row, 1, version_item)

            # Author
            author_field = plugin_info.get('author', 'N/A')
            author = self.get_author_string(author_field)
            author_item = QTableWidgetItem(author)
            self.plugins_table.setItem(row, 2, author_item)

            # Description
            description = plugin_info.get('description', 'No description')
            desc_item = QTableWidgetItem(description)
            self.plugins_table.setItem(row, 3, desc_item)

            # Install button
            install_btn = QPushButton("⬇️ Install")
            install_btn.setStyleSheet(theme.get_button_style())
            install_btn.clicked.connect(lambda checked, p=plugin: self.install_plugin(p))
            self.plugins_table.setCellWidget(row, 4, install_btn)

    def filter_plugins(self):
        """Filter plugins based on search text"""
        search_text = self.search_box.text().lower()

        if not search_text:
            self.populate_table(self.current_plugins)
            return

        filtered = [
            p for p in self.current_plugins
            if search_text in p['name'].lower() or
               search_text in p['info'].get('description', '').lower() or
               search_text in self.get_author_string(p['info'].get('author', '')).lower()
        ]

        self.populate_table(filtered)
        self.status_label.setText(f"🔍 Found {len(filtered)} plugins matching '{search_text}'")

    def on_plugin_selected(self, current, previous):
        """Handle plugin selection"""
        if not current:
            self.details_viewer.clear()
            self.install_selected_btn.setEnabled(False)
            return

        plugin = current.data(Qt.ItemDataRole.UserRole)
        if not plugin:
            return

        self.install_selected_btn.setEnabled(True)

        # Display plugin details
        plugin_name = plugin['name']
        plugin_info = plugin['info']

        author_field = plugin_info.get('author', 'N/A')
        author_str = self.get_author_string(author_field)

        details_html = f"""
        <h3 style="color: {theme.ACCENT_PRIMARY};">{plugin_name}</h3>
        <p><b>Version:</b> {plugin_info.get('version', 'N/A')}</p>
        <p><b>Author:</b> {author_str}</p>
        <p><b>Description:</b> {plugin_info.get('description', 'No description')}</p>
        """

        # Add additional fields if available
        if 'repository' in plugin_info:
            details_html += f"<p><b>Repository:</b> {plugin_info['repository']}</p>"
        if 'homepage' in plugin_info:
            details_html += f"<p><b>Homepage:</b> {plugin_info['homepage']}</p>"
        if 'license' in plugin_info:
            details_html += f"<p><b>License:</b> {plugin_info['license']}</p>"

        self.details_viewer.setHtml(details_html)

    def install_selected_plugin(self):
        """Install the currently selected plugin"""
        current_item = self.plugins_table.currentItem()
        if not current_item:
            return

        plugin = current_item.data(Qt.ItemDataRole.UserRole)
        if plugin:
            self.install_plugin(plugin)

    def install_plugin(self, plugin):
        """Install a plugin"""
        plugin_name = plugin['name']
        marketplace_name = self.marketplace_combo.currentData()

        # Full plugin identifier: plugin-name@marketplace-name
        full_name = f"{plugin_name}@{marketplace_name}"

        reply = QMessageBox.question(
            self,
            "Confirm Installation",
            f"Install plugin '{full_name}'?\n\n"
            f"This will run: claude plugin install {full_name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Run installation
        try:
            result = subprocess.run(
                ["claude.cmd", "plugin", "install", full_name],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=120,
                shell=True
            )

            if result.returncode == 0:
                QMessageBox.information(
                    self,
                    "Success",
                    f"Plugin '{full_name}' installed successfully!\n\n{result.stdout}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Installation Failed",
                    f"Failed to install plugin '{full_name}':\n\n{result.stderr}"
                )

        except subprocess.TimeoutExpired:
            QMessageBox.critical(self, "Timeout", "Plugin installation timed out after 120 seconds")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to install plugin:\n{str(e)}")
