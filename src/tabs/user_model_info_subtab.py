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
            <h2 style="color: {theme.ACCENT_PRIMARY};">Claude Models in Claude Code</h2>
            <p style="color: {theme.FG_SECONDARY};">Current family: Claude 5 (Sonnet / Opus / Fable) plus Haiku 4.5.
            Verify live details with <code>/model</code> or the model-config docs linked below.</p>

            <h3 style="color: {theme.ACCENT_PRIMARY}; margin-top: 16px;">Aliases</h3>
            <table border="1" cellpadding="6" style="border-collapse: collapse; width: 100%; background: {theme.BG_MEDIUM};">
                <tr style="background: {theme.BG_LIGHT};"><th>Alias</th><th>Model ID</th><th>Notes</th></tr>
                <tr><td><code>sonnet</code></td><td><code>claude-sonnet-5</code></td><td>Balanced default for coding</td></tr>
                <tr><td><code>opus</code></td><td><code>claude-opus-5</code></td><td>Deepest reasoning</td></tr>
                <tr><td><code>fable</code></td><td><code>claude-fable-5</code></td><td>Most capable; long-horizon agentic work</td></tr>
                <tr><td><code>haiku</code></td><td><code>claude-haiku-4-5-20251001</code></td><td>Fastest / cheapest; worker agents</td></tr>
                <tr><td><code>opusplan</code></td><td>—</td><td>Opus in Plan mode, Sonnet in execution</td></tr>
            </table>

            <h3 style="color: {theme.ACCENT_PRIMARY}; margin-top: 16px;">Context windows</h3>
            <ul>
                <li><b>Sonnet 5 / Opus 5 / Fable 5:</b> 1M-token context (native).</li>
                <li><b>Haiku 4.5:</b> 200K-token context.</li>
                <li>Add <code>[1m]</code> to force the 1M window where it isn't on by default, e.g.
                    <code>/model opus[1m]</code> or <code>claude --model claude-opus-5[1m]</code>.</li>
            </ul>

            <h3 style="color: {theme.ACCENT_PRIMARY}; margin-top: 16px;">Effort levels</h3>
            <p><code>low</code> · <code>medium</code> · <code>high</code> · <code>xhigh</code> · <code>max</code>
            (plus <code>ultracode</code>). Claude Code defaults to <code>xhigh</code>. Change with
            <code>/effort &lt;level&gt;</code>, <code>claude --effort &lt;level&gt;</code>, or the
            <code>effortLevel</code> setting. <code>max</code> and <code>ultracode</code> apply to the current session only.</p>

            <h3 style="color: {theme.ACCENT_PRIMARY}; margin-top: 16px;">Choosing a model</h3>
            <table border="1" cellpadding="8" style="border-collapse: collapse; width: 100%; background: {theme.BG_MEDIUM};">
                <tr style="background: {theme.BG_LIGHT};"><th>Use Case</th><th>Model</th></tr>
                <tr><td>Main Claude Code session</td><td><b>Sonnet 5</b></td></tr>
                <tr><td>Hardest architecture / reasoning</td><td><b>Opus 5</b></td></tr>
                <tr><td>Long autonomous agentic runs</td><td><b>Fable 5</b></td></tr>
                <tr><td>Worker / subagents, high-volume loops</td><td><b>Haiku 4.5</b></td></tr>
            </table>

            <h3 style="color: {theme.ACCENT_PRIMARY}; margin-top: 16px;">Setting the model</h3>
            <pre style="background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px;"># one session
claude --model opus
claude -p "task" --model claude-haiku-4-5-20251001

# in session (saves as your default)
/model sonnet
/model                       # open the picker

# settings file (~/.claude/settings.json)
{{ "model": "sonnet" }}

# env vars
export ANTHROPIC_MODEL=sonnet            # overrides the setting for the session
export ANTHROPIC_DEFAULT_MODEL=opus      # default for new sessions only</pre>

            <h3 style="color: {theme.ACCENT_PRIMARY}; margin-top: 16px;">Related settings</h3>
            <ul>
                <li><code>fallbackModel</code> — chain of backups when the primary is overloaded
                    (<code>claude --fallback-model sonnet,haiku</code>)</li>
                <li><code>availableModels</code> + <code>enforceAvailableModels</code> — restrict which models
                    <code>/model</code> / <code>--model</code> may pick (managed)</li>
                <li><code>modelPicker</code> — customise the <code>/model</code> picker rows (user/managed, v2.1.242+)</li>
                <li><code>fastMode</code> — Fast mode (research preview; Opus tier; toggle with <code>/fast</code>)</li>
            </ul>

            <p style="margin-top: 16px;"><b>Docs:</b>
            <a href="https://code.claude.com/docs/en/model-config">Model configuration</a> ·
            <a href="https://code.claude.com/docs/en/settings-reference">Settings reference</a></p>
        </body>
        </html>
        """

        info_browser.setHtml(html)
        layout.addWidget(info_browser)
