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
        self.load_model_config()

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
        self.user_scope_widget = self.create_scope_widget("user")
        self.scope_tabs.addTab(self.user_scope_widget, "User (~/.claude)")

        # Project scope tab with folder picker
        self.project_scope_widget = self.create_project_scope_widget()
        self.scope_tabs.addTab(self.project_scope_widget, "Project")

        layout.addWidget(self.scope_tabs, 1)

    def create_scope_widget(self, scope_type):
        """Create widget for User or Project scope"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Tab widget for Model Selector and Info
        tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
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

        self.tab_widget.addTab(self.create_model_selector_tab(), "Model Selector")
        self.tab_widget.addTab(self.create_model_info_tab(), "Model Information")

        layout.addWidget(self.tab_widget, 1)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        self.reload_btn = QPushButton("🔄 Reload")
        self.reload_btn.setToolTip("Reload model configuration from settings file")
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.setToolTip("Save model configuration to settings file")
        self.backup_btn = QPushButton("📦 Backup & Save")
        self.backup_btn.setToolTip("Create timestamped backup before saving model configuration")

        for btn in [self.reload_btn, self.save_btn, self.backup_btn]:
            btn.setStyleSheet(theme.get_button_style())

        self.reload_btn.clicked.connect(self.load_model_config)
        self.save_btn.clicked.connect(self.save_model_config)
        self.backup_btn.clicked.connect(self.backup_and_save)

        button_layout.addStretch()
        button_layout.addWidget(self.reload_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.backup_btn)

        layout.addLayout(button_layout)

    def create_model_selector_tab(self):
        """Create model selector tab"""
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

        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "claude-sonnet-4-5-20250929 (Sonnet 4.5 - Best for complex coding)",
            "claude-haiku-4-5-20251001 (Haiku 4.5 - Fastest, near-frontier)",
            "claude-opus-4-1-20250805 (Opus 4.1 - Exceptional reasoning)",
            "claude-sonnet-3-5-v2@20241022 (Sonnet 3.5 v2)",
            "claude-3-5-sonnet-20241022 (Sonnet 3.5)",
            "claude-3-5-haiku-20241022 (Haiku 3.5)",
        ])
        self.model_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 8px;
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                font-family: 'Consolas', 'Monaco', monospace;
            }}
        """)
        model_layout.addRow("Model:", self.model_combo)

        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # Current configuration display
        config_label = QLabel("Current Model Configuration (JSON):")
        config_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY}; margin-top: 10px;")
        layout.addWidget(config_label)

        self.config_editor = QTextEdit()
        self.config_editor.setStyleSheet(f"""
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
        layout.addWidget(self.config_editor, 1)

        # Info tip
        tip_label = QLabel(
            "💡 The model setting determines which Claude model is used by default. "
            "You can override this per-session using command line flags like --model."
        )
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px; padding: 5px;")
        layout.addWidget(tip_label)

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

    def on_scope_changed(self, index):
        """Handle scope change"""
        scope_map = {0: "user", 1: "project", 2: "local"}
        self.current_scope = scope_map[index]
        self.load_model_config()

    def get_scope_display_name(self):
        """Get display name for current scope"""
        return {
            "user": "User",
            "project": "Project",
            "local": "Local"
        }.get(self.current_scope, "Unknown")

    def load_model_config(self):
        """Load model configuration from current scope"""
        try:
            # Get settings from appropriate scope
            if self.current_scope == "user":
                settings = self.config_manager.get_settings()
            elif self.current_scope == "project":
                project_settings_file = Path.cwd() / ".claude" / "settings.json"
                if project_settings_file.exists():
                    with open(project_settings_file, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                else:
                    settings = {}
            elif self.current_scope == "local":
                local_settings_file = Path.cwd() / ".claude" / "settings.local.json"
                if local_settings_file.exists():
                    with open(local_settings_file, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                else:
                    settings = {}

            # Extract model configuration
            model_config = settings.get("model", "claude-sonnet-4-5-20250929")

            # Update combo box
            if isinstance(model_config, str):
                # Find matching item in combo box
                for i in range(self.model_combo.count()):
                    if model_config in self.model_combo.itemText(i):
                        self.model_combo.setCurrentIndex(i)
                        break

            # Update JSON editor
            if isinstance(model_config, str):
                display_config = {"model": model_config}
            else:
                display_config = {"model": model_config}

            self.config_editor.setPlainText(json.dumps(display_config, indent=2))

        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load model config:\n{str(e)}")

    def save_model_config(self):
        """Save model configuration"""
        try:
            # Get selected model
            selected_text = self.model_combo.currentText()
            model_id = selected_text.split(" (")[0]  # Extract model ID

            # Get settings from appropriate scope
            if self.current_scope == "user":
                settings = self.config_manager.get_settings()
            elif self.current_scope == "project":
                project_settings_file = Path.cwd() / ".claude" / "settings.json"
                if project_settings_file.exists():
                    with open(project_settings_file, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                else:
                    settings = {}
            elif self.current_scope == "local":
                local_settings_file = Path.cwd() / ".claude" / "settings.local.json"
                if local_settings_file.exists():
                    with open(local_settings_file, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                else:
                    settings = {}

            # Update model setting
            settings["model"] = model_id

            # Save to appropriate file
            if self.current_scope == "user":
                self.config_manager.save_settings(settings)
            elif self.current_scope == "project":
                project_settings_file = Path.cwd() / ".claude" / "settings.json"
                project_settings_file.parent.mkdir(parents=True, exist_ok=True)
                with open(project_settings_file, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2)
            elif self.current_scope == "local":
                local_settings_file = Path.cwd() / ".claude" / "settings.local.json"
                local_settings_file.parent.mkdir(parents=True, exist_ok=True)
                with open(local_settings_file, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2)

            # Update display
            self.config_editor.setPlainText(json.dumps({"model": model_id}, indent=2))

            QMessageBox.information(
                self,
                "Saved",
                f"Model configuration saved to {self.get_scope_display_name()} scope!\n\n"
                f"Default model: {model_id}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n{str(e)}")

    def backup_and_save(self):
        """Create backup before saving"""
        try:
            # Determine which file to backup
            if self.current_scope == "user":
                file_path = self.config_manager.settings_file
            elif self.current_scope == "project":
                file_path = Path.cwd() / ".claude" / "settings.json"
            elif self.current_scope == "local":
                file_path = Path.cwd() / ".claude" / "settings.local.json"

            if file_path.exists():
                self.backup_manager.create_file_backup(file_path)

            self.save_model_config()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to backup:\n{str(e)}")
