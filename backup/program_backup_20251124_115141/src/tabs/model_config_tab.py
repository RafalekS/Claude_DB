"""
Model Configuration Tab - Manage Claude model settings
"""

import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QMessageBox, QTextBrowser, QGroupBox, QComboBox,
    QFormLayout, QTabWidget, QLineEdit, QFileDialog
)
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme


class ModelConfigTab(QWidget):
    """Tab for model configuration"""

    def __init__(self, config_manager, backup_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.project_folder = Path.cwd()  # Default to current working directory
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header with docs link
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        header = QLabel("Model Configuration")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")

        docs_btn = QPushButton("📖 Model Docs")
        docs_btn.setStyleSheet(theme.get_button_style())
        docs_btn.setToolTip("Open official models documentation in browser")
        docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://docs.claude.com/en/docs/about-claude/models/overview")
        ))

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(docs_btn)

        layout.addLayout(header_layout)

        # Main tab widget for User / Project scope
        self.scope_tabs = QTabWidget()
        self.scope_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {theme.BG_LIGHT};
                background-color: {theme.BG_MEDIUM};
            }}
            QTabBar::tab {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid {theme.BG_LIGHT};
            }}
            QTabBar::tab:selected {{
                background-color: {theme.ACCENT_PRIMARY};
                color: white;
            }}
            QTabBar::tab:hover {{
                background-color: {theme.BG_LIGHT};
            }}
        """)

        # User scope tab
        self.user_widget = self.create_user_tab()
        self.scope_tabs.addTab(self.user_widget, "User (~/.claude)")

        # Project scope tab with folder picker
        self.project_widget = self.create_project_tab()
        self.scope_tabs.addTab(self.project_widget, "Project")

        layout.addWidget(self.scope_tabs, 1)

    def create_user_tab(self):
        """Create User scope tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Inner tabs for Model Selector and Info
        inner_tabs = QTabWidget()
        inner_tabs.setStyleSheet(theme.get_tab_widget_style())

        inner_tabs.addTab(self.create_model_selector_tab("user"), "Model Selector")
        inner_tabs.addTab(self.create_model_info_tab(), "Model Information")

        layout.addWidget(inner_tabs)

        return widget

    def create_project_tab(self):
        """Create Project scope tab with folder picker"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Folder picker row
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(5)

        folder_label = QLabel("Project Folder:")
        folder_label.setStyleSheet(f"color: {theme.FG_PRIMARY}; font-weight: bold;")

        self.project_folder_edit = QLineEdit()
        self.project_folder_edit.setText("C:\Scripts")
        self.project_folder_edit.setReadOnly(True)
        self.project_folder_edit.setStyleSheet(f"""
            QLineEdit {{
                padding: 6px;
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
            }}
        """)

        browse_btn = QPushButton("📁 Browse...")
        browse_btn.setStyleSheet(theme.get_button_style())
        browse_btn.setToolTip("Select project folder")
        browse_btn.clicked.connect(self.browse_project_folder)

        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.project_folder_edit, 1)
        folder_layout.addWidget(browse_btn)

        layout.addLayout(folder_layout)

        # Inner tabs for settings.json and settings.local.json
        self.project_inner_tabs = QTabWidget()
        self.project_inner_tabs.setStyleSheet(theme.get_tab_widget_style())

        self.project_inner_tabs.addTab(self.create_model_selector_tab("project"), "Shared (settings.json)")
        self.project_inner_tabs.addTab(self.create_model_selector_tab("local"), "Local (settings.local.json)")
        self.project_inner_tabs.addTab(self.create_model_info_tab(), "Model Information")

        layout.addWidget(self.project_inner_tabs)

        return widget

    def browse_project_folder(self):
        """Browse for project folder"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Project Folder",
            "C:\Scripts"
        )
        if folder:
            self.project_folder = Path(folder)
            self.project_folder_edit.setText("C:\Scripts")
            # Refresh project tabs
            self.refresh_project_tabs()

    def refresh_project_tabs(self):
        """Refresh project tabs with new folder"""
        # Clear and recreate tabs
        self.project_inner_tabs.clear()
        self.project_inner_tabs.addTab(self.create_model_selector_tab("project"), "Shared (settings.json)")
        self.project_inner_tabs.addTab(self.create_model_selector_tab("local"), "Local (settings.local.json)")
        self.project_inner_tabs.addTab(self.create_model_info_tab(), "Model Information")

    def create_model_selector_tab(self, scope):
        """Create model selector tab for given scope"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Model selection group
        model_group = QGroupBox("Select Default Model")
        model_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: {theme.FG_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        model_layout = QFormLayout()

        model_combo = QComboBox()
        model_combo.addItems([
            "claude-sonnet-4-5-20250929 (Sonnet 4.5 - Best for complex coding)",
            "claude-haiku-4-5-20251001 (Haiku 4.5 - Fastest, near-frontier)",
            "claude-opus-4-1-20250805 (Opus 4.1 - Exceptional reasoning)",
            "claude-sonnet-3-5-v2@20241022 (Sonnet 3.5 v2)",
            "claude-3-5-sonnet-20241022 (Sonnet 3.5)",
            "claude-3-5-haiku-20241022 (Haiku 3.5)",
        ])
        model_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 8px;
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                font-family: 'Consolas', 'Monaco', monospace;
            }}
        """)
        model_layout.addRow("Model:", model_combo)

        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # Current configuration display
        config_label = QLabel("Current Model Configuration (JSON):")
        config_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY}; margin-top: 10px;")
        layout.addWidget(config_label)

        config_editor = QTextEdit()
        config_editor.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: {theme.FONT_SIZE_SMALL}px;
            }}
        """)
        layout.addWidget(config_editor, 1)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        reload_btn = QPushButton("🔄 Reload")
        reload_btn.setToolTip("Reload model configuration from settings file")
        save_btn = QPushButton("💾 Save")
        save_btn.setToolTip("Save model configuration to settings file")
        backup_btn = QPushButton("📦 Backup & Save")
        backup_btn.setToolTip("Create timestamped backup before saving")

        for btn in [reload_btn, save_btn, backup_btn]:
            btn.setStyleSheet(theme.get_button_style())

        reload_btn.clicked.connect(lambda: self.load_model_config(scope, model_combo, config_editor))
        save_btn.clicked.connect(lambda: self.save_model_config(scope, model_combo, config_editor))
        backup_btn.clicked.connect(lambda: self.backup_and_save(scope, model_combo, config_editor))

        button_layout.addStretch()
        button_layout.addWidget(reload_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(backup_btn)

        layout.addLayout(button_layout)

        # Info tip
        tip_label = QLabel(
            "💡 The model setting determines which Claude model is used by default. "
            "You can override this per-session using command line flags like --model."
        )
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px; padding: 5px;")
        layout.addWidget(tip_label)

        # Load initial config
        self.load_model_config(scope, model_combo, config_editor)

        return widget

    def create_model_info_tab(self):
        """Create model information tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)

        info_browser = QTextBrowser()
        info_browser.setOpenExternalLinks(True)
        info_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                padding: 10px;
                font-size: {theme.FONT_SIZE_SMALL}px;
            }}
        """)

        html = f"""
        <html>
        <body style="color: {theme.FG_PRIMARY};">
            <h2 style="color: {theme.ACCENT_PRIMARY};">Claude Model Comparison</h2>

            <h3 style="color: {theme.ACCENT_PRIMARY}; margin-top: 20px;">Claude Sonnet 4.5</h3>
            <p><b>API ID:</b> <code>claude-sonnet-4-5-20250929</code></p>
            <ul>
                <li><b>Context Window:</b> 200K tokens (1M tokens beta)</li>
                <li><b>Max Output:</b> 64K tokens</li>
                <li><b>Pricing:</b> $3/MTok input, $15/MTok output</li>
                <li><b>Best For:</b> Complex agents, advanced coding, tool orchestration</li>
                <li><b>Speed:</b> Fast latency with Priority Tier</li>
            </ul>

            <h3 style="color: {theme.ACCENT_PRIMARY}; margin-top: 20px;">Claude Haiku 4.5</h3>
            <p><b>API ID:</b> <code>claude-haiku-4-5-20251001</code></p>
            <ul>
                <li><b>Context Window:</b> 200K tokens</li>
                <li><b>Max Output:</b> 64K tokens</li>
                <li><b>Pricing:</b> $1/MTok input, $5/MTok output</li>
                <li><b>Best For:</b> Real-time applications, high-volume tasks, rapid prototyping</li>
                <li><b>Speed:</b> Fastest latency - near-frontier intelligence</li>
            </ul>

            <h3 style="color: {theme.ACCENT_PRIMARY}; margin-top: 20px;">Claude Opus 4.1</h3>
            <p><b>API ID:</b> <code>claude-opus-4-1-20250805</code></p>
            <ul>
                <li><b>Context Window:</b> 200K tokens</li>
                <li><b>Max Output:</b> 32K tokens</li>
                <li><b>Pricing:</b> $15/MTok input, $75/MTok output</li>
                <li><b>Best For:</b> Specialized reasoning, scientific/mathematical tasks</li>
                <li><b>Speed:</b> Moderate latency</li>
            </ul>

            <h3 style="color: {theme.ACCENT_PRIMARY}; margin-top: 20px;">Model Selection Guide</h3>
            <table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; background: {theme.BG_MEDIUM};">
                <tr style="background: {theme.BG_LIGHT};">
                    <th>Use Case</th>
                    <th>Recommended Model</th>
                </tr>
                <tr>
                    <td>Complex agents & coding</td>
                    <td><b>Claude Sonnet 4.5</b></td>
                </tr>
                <tr>
                    <td>Specialized reasoning tasks</td>
                    <td><b>Claude Opus 4.1</b></td>
                </tr>
                <tr>
                    <td>Real-time/high-volume apps</td>
                    <td><b>Claude Haiku 4.5</b></td>
                </tr>
                <tr>
                    <td>Cost-sensitive prototyping</td>
                    <td><b>Claude Haiku 4.5</b></td>
                </tr>
            </table>

            <h3 style="color: {theme.ACCENT_PRIMARY}; margin-top: 20px;">Choosing Your Model</h3>
            <p><b>Start Lean:</b> Begin with Haiku 4.5 for fast iteration and low cost. Upgrade if needed.</p>
            <p><b>Start Powerful:</b> Use Sonnet 4.5 for complex tasks where intelligence is critical.</p>

            <h3 style="color: {theme.ACCENT_PRIMARY}; margin-top: 20px;">Command Line Override</h3>
            <p>Override the default model for a specific session:</p>
            <pre style="background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px;">claude --model claude-haiku-4-5-20251001</pre>

            <p style="margin-top: 20px;"><b>Links:</b></p>
            <ul>
                <li><a href="https://docs.claude.com/en/docs/about-claude/models/overview">Model Overview</a></li>
                <li><a href="https://docs.claude.com/en/docs/about-claude/models/choosing-a-model">Choosing a Model</a></li>
            </ul>
        </body>
        </html>
        """

        info_browser.setHtml(html)
        layout.addWidget(info_browser)

        return widget

    def get_settings_file_path(self, scope):
        """Get settings file path for given scope"""
        if scope == "user":
            return self.config_manager.settings_file
        elif scope == "project":
            return self.project_folder / ".claude" / "settings.json"
        elif scope == "local":
            return self.project_folder / ".claude" / "settings.local.json"
        return None

    def load_model_config(self, scope, model_combo, config_editor):
        """Load model configuration from given scope"""
        try:
            file_path = self.get_settings_file_path(scope)

            if file_path and file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = {}

            # Extract model configuration
            model_config = settings.get("model", "claude-sonnet-4-5-20250929")

            # Update combo box
            if isinstance(model_config, str):
                for i in range(model_combo.count()):
                    if model_config in model_combo.itemText(i):
                        model_combo.setCurrentIndex(i)
                        break

            # Update JSON editor
            display_config = {"model": model_config}
            config_editor.setPlainText(json.dumps(display_config, indent=2))

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load model config:\n{str(e)}")

    def save_model_config(self, scope, model_combo, config_editor):
        """Save model configuration"""
        try:
            # Get selected model
            selected_text = model_combo.currentText()
            model_id = selected_text.split(" (")[0]  # Extract model ID

            file_path = self.get_settings_file_path(scope)

            if file_path and file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = {}

            # Update model setting
            settings["model"] = model_id

            # Save to file
            if file_path:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2)

            # Update display
            config_editor.setPlainText(json.dumps({"model": model_id}, indent=2))

            QMessageBox.information(
                self,
                "Saved",
                f"Model configuration saved to {scope} scope!\n\n"
                f"Default model: {model_id}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n{str(e)}")

    def backup_and_save(self, scope, model_combo, config_editor):
        """Create backup before saving"""
        try:
            file_path = self.get_settings_file_path(scope)

            if file_path and file_path.exists():
                self.backup_manager.create_file_backup(file_path)

            self.save_model_config(scope, model_combo, config_editor)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to backup:\n{str(e)}")
