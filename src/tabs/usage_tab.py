"""
Usage & Analytics Tab - Token usage statistics and monitoring
"""

import subprocess
import re
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QMessageBox, QGroupBox, QCheckBox, QLineEdit, QComboBox,
    QGridLayout, QFrame
)
from PyQt6.QtCore import Qt
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme


class UsageTab(QWidget):
    """Tab for viewing usage and analytics"""

    def __init__(self, config_manager, backup_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.init_ui()

    def showEvent(self, event):
        """Override showEvent to refresh stats when tab is shown"""
        super().showEvent(event)
        # Refresh stats when tab is shown
        self.refresh_stats()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header
        header = QLabel("Usage & Analytics")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")
        layout.addWidget(header)

        # Quick Stats Display Section
        stats_group = QGroupBox("Quick Stats")
        stats_group.setStyleSheet(f"""
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

        stats_layout = QGridLayout()
        stats_layout.setSpacing(8)

        # Create stat cards (only tokens and sessions available from ccusage)
        self.tokens_card = self.create_stat_card("📊 Total Tokens", "0")
        self.sessions_card = self.create_stat_card("📅 Days Active", "0")

        stats_layout.addWidget(self.tokens_card, 0, 0)
        stats_layout.addWidget(self.sessions_card, 0, 1)

        refresh_stats_btn = QPushButton("🔄 Refresh Stats")
        refresh_stats_btn.setStyleSheet(theme.get_button_style())
        refresh_stats_btn.setToolTip("Refresh usage statistics from configuration")
        refresh_stats_btn.clicked.connect(self.refresh_stats)
        stats_layout.addWidget(refresh_stats_btn, 0, 2)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Real-time Monitoring Section
        monitoring_group = QGroupBox("Real-time Monitoring")
        monitoring_group.setStyleSheet(f"""
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

        monitoring_layout = QHBoxLayout()
        monitoring_layout.setSpacing(5)

        # View mode selector
        view_label = QLabel("View:")
        view_label.setStyleSheet(f"color: {theme.FG_PRIMARY};")

        self.view_combo = QComboBox()
        self.view_combo.addItems(["realtime", "daily", "monthly", "session"])
        self.view_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 6px;
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.ACCENT_PRIMARY};
                border-radius: 3px;
            }}
        """)

        self.ccmonitor_btn = QPushButton("🖥️ Launch ccmonitor")
        self.ccmonitor_btn.setToolTip("Launch real-time token usage monitor")
        self.ccmonitor_btn.setStyleSheet(theme.get_button_style())
        self.ccmonitor_btn.clicked.connect(self.launch_ccmonitor)

        monitoring_layout.addWidget(view_label)
        monitoring_layout.addWidget(self.view_combo)
        monitoring_layout.addWidget(self.ccmonitor_btn)
        monitoring_layout.addStretch()

        monitoring_group.setLayout(monitoring_layout)
        layout.addWidget(monitoring_group)

        # ccusage Commands Section
        ccusage_group = QGroupBox("ccusage - Usage Reports")
        ccusage_group.setStyleSheet(f"""
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

        ccusage_layout = QVBoxLayout()

        # Options row
        options_layout = QHBoxLayout()
        options_layout.setSpacing(5)

        self.breakdown_check = QCheckBox("Show Breakdown")
        self.breakdown_check.setStyleSheet(f"color: {theme.FG_PRIMARY};")
        self.breakdown_check.setToolTip("Show per-model cost breakdown")

        self.instances_check = QCheckBox("Show Instances")
        self.instances_check.setStyleSheet(f"color: {theme.FG_PRIMARY};")
        self.instances_check.setToolTip("Show usage breakdown by project/instance")

        self.json_check = QCheckBox("JSON Output")
        self.json_check.setStyleSheet(f"color: {theme.FG_PRIMARY};")
        self.json_check.setToolTip("Output in JSON format")

        options_layout.addWidget(self.breakdown_check)
        options_layout.addWidget(self.instances_check)
        options_layout.addWidget(self.json_check)
        options_layout.addStretch()

        ccusage_layout.addLayout(options_layout)

        # Report buttons
        reports_layout = QHBoxLayout()
        reports_layout.setSpacing(5)

        self.daily_btn = QPushButton("📅 Daily Report")
        self.daily_btn.setToolTip("Show usage report grouped by date (ccusage daily)")
        self.weekly_btn = QPushButton("📊 Weekly Report")
        self.weekly_btn.setToolTip("Show usage report grouped by week (ccusage weekly)")
        self.monthly_btn = QPushButton("📈 Monthly Report")
        self.monthly_btn.setToolTip("Show usage report grouped by month (ccusage monthly)")
        self.session_btn = QPushButton("💬 Session Report")
        self.session_btn.setToolTip("Show usage report grouped by conversation session (ccusage session)")
        self.blocks_btn = QPushButton("🧱 Blocks Report")
        self.blocks_btn.setToolTip("Show usage report grouped by session billing blocks (ccusage blocks)")

        for btn in [self.daily_btn, self.weekly_btn, self.monthly_btn, self.session_btn, self.blocks_btn]:
            btn.setStyleSheet(theme.get_button_style())

        self.daily_btn.clicked.connect(lambda: self.run_ccusage("daily"))
        self.weekly_btn.clicked.connect(lambda: self.run_ccusage("weekly"))
        self.monthly_btn.clicked.connect(lambda: self.run_ccusage("monthly"))
        self.session_btn.clicked.connect(lambda: self.run_ccusage("session"))
        self.blocks_btn.clicked.connect(lambda: self.run_ccusage("blocks"))

        reports_layout.addWidget(self.daily_btn)
        reports_layout.addWidget(self.weekly_btn)
        reports_layout.addWidget(self.monthly_btn)
        reports_layout.addWidget(self.session_btn)
        reports_layout.addWidget(self.blocks_btn)

        ccusage_layout.addLayout(reports_layout)
        ccusage_group.setLayout(ccusage_layout)
        layout.addWidget(ccusage_group)

        # Output Display
        output_group = QGroupBox("Command Output")
        output_group.setStyleSheet(f"""
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

        output_layout = QVBoxLayout()

        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setPlaceholderText("Click a report button to view usage statistics...")
        self.output_display.setStyleSheet(f"""
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

        clear_btn = QPushButton("🗑️ Clear Output")
        clear_btn.setStyleSheet(theme.get_button_style())
        clear_btn.setToolTip("Clear the output display")
        clear_btn.clicked.connect(lambda: self.output_display.clear())

        output_layout.addWidget(self.output_display)
        output_layout.addWidget(clear_btn)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group, 1)  # Stretch factor

        # Info section
        info_group = QGroupBox("About Usage & Analytics")
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
            "Usage tracking tools:\n"
            "• ccusage: Command-line tool for viewing historical usage reports (daily/weekly/monthly/session/blocks)\n"
            "• ccmonitor: Real-time token usage monitoring with different views (realtime/daily/monthly/session)\n"
            "• API: Fetch usage data via Anthropic Usage Cost API\n\n"
            "Documentation: https://docs.claude.com/en/docs/claude-code/monitoring-usage"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px; padding: 5px;")
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

    def strip_ansi_codes(self, text):
        """Strip ANSI escape codes from text for clean display"""
        # Remove ANSI escape sequences (colors, formatting, cursor movement)
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def run_ccusage(self, report_type):
        """Run ccusage command with specified report type"""
        try:
            # Build command - use .cmd for Windows npm scripts
            cmd = ["ccusage.cmd", report_type]

            # Add options
            if self.breakdown_check.isChecked():
                cmd.append("--breakdown")
            if self.instances_check.isChecked():
                cmd.append("--instances")
            if self.json_check.isChecked():
                cmd.append("--json")

            self.output_display.append(f"\n{'='*60}\n")
            self.output_display.append(f"Running: {' '.join(cmd)}\n")
            self.output_display.append(f"{'='*60}\n\n")

            # Run command with UTF-8 encoding for Unicode characters
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30
            )

            if result.returncode == 0:
                # Strip ANSI codes for clean display
                clean_output = self.strip_ansi_codes(result.stdout)
                self.output_display.append(clean_output)
            else:
                clean_error = self.strip_ansi_codes(result.stderr)
                self.output_display.append(f"Error running ccusage:\n{clean_error}")

        except FileNotFoundError:
            QMessageBox.warning(
                self,
                "Command Not Found",
                "ccusage.cmd not found. Please ensure it is installed and in your PATH.\n\n"
                "You can install it with: npm install -g ccusage"
            )
        except subprocess.TimeoutExpired:
            self.output_display.append("\n[Command timed out after 30 seconds]")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to run ccusage:\n{str(e)}"
            )

    def launch_ccmonitor(self):
        """Launch ccmonitor in a separate terminal window"""
        from utils.terminal_utils import run_in_terminal
        import platform
        view_mode = self.view_combo.currentText()
        binary = "ccmonitor.exe" if platform.system() == "Windows" else "ccmonitor"
        run_in_terminal(
            f"{binary} --view={view_mode}",
            title="ccmonitor",
            parent_widget=self,
        )

    def create_stat_card(self, title, value):
        """Create a stat card widget"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {theme.BG_DARK};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 5px;
                padding: 10px;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        value_label = QLabel(value)
        value_label.setObjectName("value_label")
        value_label.setStyleSheet(f"color: {theme.ACCENT_PRIMARY}; font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)

        return card

    def update_stat_card(self, card, value):
        """Update the value in a stat card"""
        value_label = card.findChild(QLabel, "value_label")
        if value_label:
            value_label.setText(str(value))

    def refresh_stats(self):
        """Refresh quick stats from ccusage output"""
        try:
            # Run ccusage daily with JSON output to parse
            result = subprocess.run(
                ["ccusage.cmd", "daily", "--json"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30
            )

            if result.returncode == 0:
                clean_output = self.strip_ansi_codes(result.stdout)
                # Try to parse JSON
                try:
                    data = json.loads(clean_output)

                    # Extract totals from ccusage JSON
                    totals = data.get("totals", {})
                    total_tokens = totals.get("totalTokens", 0)

                    # Count days active (number of daily entries)
                    daily_data = data.get("daily", [])
                    days_active = len(daily_data)

                    # Update stat cards
                    self.update_stat_card(self.tokens_card, f"{total_tokens:,}")
                    self.update_stat_card(self.sessions_card, str(days_active))
                except json.JSONDecodeError as e:
                    QMessageBox.warning(
                        self,
                        "Parse Error",
                        f"Could not parse ccusage JSON output:\n{str(e)}"
                    )
            else:
                clean_error = self.strip_ansi_codes(result.stderr)
                QMessageBox.warning(
                    self,
                    "ccusage Error",
                    f"Failed to run ccusage:\n{clean_error}"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to refresh stats:\n{str(e)}"
            )

