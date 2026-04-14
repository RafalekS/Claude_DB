"""
User Model Information Sub-Tab - Claude model comparison and information
"""

from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser

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
        layout.setContentsMargins(6, 6, 6, 6)

        info_browser = QTextBrowser()
        info_browser.setOpenExternalLinks(True)
        info_browser.setStyleSheet(f"""
            QTextBrowser {{
                border-radius: 3px;
                padding: 10px;
                font-size: {theme.FONT_SIZE_SMALL}px;
            }}
        """)

        html = f"""
        <html>
        <body style="color: {theme.FG_PRIMARY};">
            <h2 style="color: {theme.ACCENT_PRIMARY};">Claude Model Comparison</h2>
            <p style="color: {theme.FG_SECONDARY};">Current family: Claude 4.6 &amp; 4.5 — as of Claude Code model ID reference.</p>

            <h3 style="color: {theme.ACCENT_PRIMARY}; margin-top: 16px;">Claude Sonnet 4.6 — Best Coding Model</h3>
            <p><b>API ID:</b> <code>claude-sonnet-4-6</code></p>
            <ul>
                <li><b>Context Window:</b> 200K tokens</li>
                <li><b>Max Output:</b> 64K tokens</li>
                <li><b>Best For:</b> Main development work, orchestrating multi-agent workflows, complex coding tasks</li>
                <li><b>Use In Claude Code:</b> Default model — highest capability/cost balance for coding</li>
            </ul>

            <h3 style="color: {theme.ACCENT_PRIMARY}; margin-top: 16px;">Claude Opus 4.6 — Deepest Reasoning</h3>
            <p><b>API ID:</b> <code>claude-opus-4-6</code></p>
            <ul>
                <li><b>Context Window:</b> 200K tokens</li>
                <li><b>Max Output:</b> 32K tokens</li>
                <li><b>Best For:</b> Complex architectural decisions, maximum reasoning, research and analysis</li>
                <li><b>Use In Claude Code:</b> <code>claude --model claude-opus-4-6</code> for the hardest tasks</li>
            </ul>

            <h3 style="color: {theme.ACCENT_PRIMARY}; margin-top: 16px;">Claude Haiku 4.5 — Fastest &amp; Cheapest</h3>
            <p><b>API ID:</b> <code>claude-haiku-4-5-20251001</code></p>
            <ul>
                <li><b>Context Window:</b> 200K tokens</li>
                <li><b>Max Output:</b> 64K tokens</li>
                <li><b>Best For:</b> Lightweight agents with frequent invocation, pair programming, worker agents</li>
                <li><b>Cost:</b> ~3× cheaper than Sonnet — ideal for high-volume agentic loops</li>
            </ul>

            <h3 style="color: {theme.ACCENT_PRIMARY}; margin-top: 16px;">Model Selection Guide</h3>
            <table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; background: {theme.BG_MEDIUM};">
                <tr style="background: {theme.BG_LIGHT};">
                    <th>Use Case</th>
                    <th>Recommended Model</th>
                    <th>Reason</th>
                </tr>
                <tr>
                    <td>Main Claude Code session</td>
                    <td><b>Sonnet 4.6</b></td>
                    <td>Best coding, default</td>
                </tr>
                <tr>
                    <td>Complex architecture / research</td>
                    <td><b>Opus 4.6</b></td>
                    <td>Deepest reasoning</td>
                </tr>
                <tr>
                    <td>Worker agents in multi-agent</td>
                    <td><b>Haiku 4.5</b></td>
                    <td>90% capability, 3× cheaper</td>
                </tr>
                <tr>
                    <td>Fast iteration / prototyping</td>
                    <td><b>Haiku 4.5</b></td>
                    <td>Lowest latency, lowest cost</td>
                </tr>
                <tr>
                    <td>Orchestrator in multi-agent</td>
                    <td><b>Sonnet 4.6</b></td>
                    <td>Coordinates workers reliably</td>
                </tr>
            </table>

            <h3 style="color: {theme.ACCENT_PRIMARY}; margin-top: 16px;">Command Line Override</h3>
            <p>Override the model for a session or single prompt:</p>
            <pre style="background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px;">claude --model claude-opus-4-6
claude -p "task" --model claude-haiku-4-5-20251001</pre>

            <h3 style="color: {theme.ACCENT_PRIMARY}; margin-top: 16px;">Set Default Model in Settings</h3>
            <pre style="background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px;"># ~/.claude/settings.json
{{
  "model": "claude-sonnet-4-6"
}}</pre>

            <p style="margin-top: 16px;"><b>Links:</b></p>
            <ul>
                <li><a href="https://code.claude.com/docs/en/about-claude/models/overview">Model Overview</a></li>
                <li><a href="https://code.claude.com/docs/en/about-claude/models/choosing-a-model">Choosing a Model</a></li>
            </ul>
        </body>
        </html>
        """

        info_browser.setHtml(html)
        layout.addWidget(info_browser)
