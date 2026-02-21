"""
User Model Information Sub-Tab - Claude model comparison and information
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme


class UserModelInfoSubTab(QWidget):
    """Model Information interface for user-level configuration"""

    def __init__(self, config_manager, backup_manager, settings_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.settings_manager = settings_manager
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
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
