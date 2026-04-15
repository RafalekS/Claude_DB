"""
Remote Control Tab - Configure and use Claude Code's remote/headless API access
"""

import json
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QSplitter, QGroupBox, QFormLayout, QLineEdit,
    QComboBox, QCheckBox, QSpinBox, QTextBrowser
)
from PyQt6.QtCore import Qt

from utils import theme

logger = logging.getLogger(__name__)

class RemoteControlTab(QWidget):
    """
    Remote Control tab — reference for Claude Code's --output-format, --print (headless),
    and SDK/API usage for programmatic/remote control of Claude Code instances.
    """

    def __init__(self, config_manager, backup_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        # Header
        header = QLabel("Remote Control — Headless & Programmatic Usage")
        header.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};"
        )
        layout.addWidget(header)

        subtitle = QLabel(
            "Claude Code can be driven headlessly via CLI flags, piped input, JSON output, "
            "and the Claude Code SDK for embedding in scripts or CI pipelines."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_NORMAL}px;")
        layout.addWidget(subtitle)

        # Splitter: left=CLI patterns, right=SDK / hooks
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(4)
        left_label = QLabel("CLI Headless Patterns")
        left_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY};")
        left_layout.addWidget(left_label)
        left_text = QTextEdit()
        left_text.setReadOnly(True)
        left_text.setHtml(self._cli_patterns_html())
        left_layout.addWidget(left_text, 1)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(4, 0, 0, 0)
        right_layout.setSpacing(4)
        right_label = QLabel("SDK & Programmatic Control")
        right_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY};")
        right_layout.addWidget(right_label)
        right_text = QTextEdit()
        right_text.setReadOnly(True)
        right_text.setHtml(self._sdk_html())
        right_layout.addWidget(right_text, 1)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([500, 500])
        layout.addWidget(splitter, 1)

        # Footer
        tip = QTextBrowser()
        tip.setOpenExternalLinks(False)
        tip.setMaximumHeight(55)
        tip.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; background: {theme.BG_MEDIUM}; "
            f"padding: 4px; border-radius: 3px; font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        tip.setHtml(
            f"<span style='font-size:{theme.FONT_SIZE_SMALL}px; color:{theme.FG_SECONDARY};'>"
            "💡 <b>Key flags:</b> "
            "<code>-p</code>/<code>--print</code> — non-interactive &nbsp;|&nbsp; "
            "<code>--output-format json</code> — machine-readable &nbsp;|&nbsp; "
            "<code>--permission-prompt-tool mcp__server__tool</code> — delegate permissions &nbsp;|&nbsp; "
            "<code>--no-markdown</code> — plain text for piping"
            "</span>"
        )
        layout.addWidget(tip)

    def _cli_patterns_html(self) -> str:
        bg = theme.BG_DARK
        fg = theme.FG_PRIMARY
        acc = theme.ACCENT_PRIMARY
        code_bg = theme.BG_MEDIUM
        sm = theme.FONT_SIZE_SMALL

        return f"""<html><body style="background:{bg}; color:{fg}; font-size:{sm}px;">
<h3 style="color:{acc};">Non-Interactive (Print) Mode</h3>
<pre style="background:{code_bg}; padding:8px; border-radius:4px;"># Single prompt, print response, exit
claude -p "Explain this function" --no-markdown

# Pipe input
cat main.py | claude -p "Review this code"

# From a file
claude -p "$(cat prompt.txt)"</pre>

<h3 style="color:{acc};">JSON Output for Scripts</h3>
<pre style="background:{code_bg}; padding:8px; border-radius:4px;"># Stream JSON events
claude -p "task" --output-format json

# Parse with jq
claude -p "task" --output-format json | jq '.result'</pre>

<h3 style="color:{acc};">Headless with Permission Handling</h3>
<pre style="background:{code_bg}; padding:8px; border-radius:4px;"># Delegate permission prompts to MCP tool
claude -p "task" \\
  --permission-prompt-tool mcp__approver__approve

# Skip all prompts (dangerous — use in trusted CI only)
claude -p "task" \\
  --dangerously-skip-permissions</pre>

<h3 style="color:{acc};">CI/CD Usage</h3>
<pre style="background:{code_bg}; padding:8px; border-radius:4px;"># GitHub Actions example
- name: Run Claude Code review
  run: |
    claude -p "Review PR changes for security issues" \\
      --output-format json \\
      --no-markdown \\
      > review.json</pre>

<h3 style="color:{acc};">Custom System Prompt</h3>
<pre style="background:{code_bg}; padding:8px; border-radius:4px;"># Replace default system prompt
claude -p "task" --system-prompt "You are a code auditor..."

# Append to default
claude -p "task" --append-system-prompt "Always respond in JSON"</pre>

<h3 style="color:{acc};">Continue / Resume Sessions</h3>
<pre style="background:{code_bg}; padding:8px; border-radius:4px;"># Continue most recent session
claude -c

# Resume specific session
claude -r &lt;session-id&gt;

# Resume with different model
claude -r &lt;session-id&gt; --model claude-opus-4-6</pre>
</body></html>"""

    def _sdk_html(self) -> str:
        bg = theme.BG_DARK
        fg = theme.FG_PRIMARY
        acc = theme.ACCENT_PRIMARY
        code_bg = theme.BG_MEDIUM
        sm = theme.FONT_SIZE_SMALL

        return f"""<html><body style="background:{bg}; color:{fg}; font-size:{sm}px;">
<h3 style="color:{acc};">Claude Code SDK (Python)</h3>
<pre style="background:{code_bg}; padding:8px; border-radius:4px;">pip install claude-code-sdk</pre>

<pre style="background:{code_bg}; padding:8px; border-radius:4px;">import asyncio
from claude_code_sdk import query, ClaudeCodeOptions

async def main():
    options = ClaudeCodeOptions(
        max_turns=5,
        system_prompt="You are a code reviewer",
        allowed_tools=["Read", "Grep"],
    )
    async for message in query(
        prompt="Review src/main.py",
        options=options
    ):
        print(message)

asyncio.run(main())</pre>

<h3 style="color:{acc};">SDK — Key Options</h3>
<table style="width:100%; border-collapse:collapse;">
<tr style="background:{code_bg};">
  <th style="text-align:left; padding:4px 8px;">Option</th>
  <th style="text-align:left; padding:4px 8px;">Type</th>
  <th style="text-align:left; padding:4px 8px;">Description</th>
</tr>
<tr><td style="padding:3px 8px;"><code>max_turns</code></td>
    <td style="padding:3px 8px;">int</td>
    <td style="padding:3px 8px;">Max agentic turns</td></tr>
<tr style="background:{code_bg};"><td style="padding:3px 8px;"><code>system_prompt</code></td>
    <td style="padding:3px 8px;">str</td>
    <td style="padding:3px 8px;">Override system prompt</td></tr>
<tr><td style="padding:3px 8px;"><code>allowed_tools</code></td>
    <td style="padding:3px 8px;">list[str]</td>
    <td style="padding:3px 8px;">Whitelist of tools</td></tr>
<tr style="background:{code_bg};"><td style="padding:3px 8px;"><code>permission_mode</code></td>
    <td style="padding:3px 8px;">str</td>
    <td style="padding:3px 8px;"><code>default</code>, <code>acceptEdits</code>, <code>auto</code></td></tr>
<tr><td style="padding:3px 8px;"><code>cwd</code></td>
    <td style="padding:3px 8px;">Path</td>
    <td style="padding:3px 8px;">Working directory for the session</td></tr>
<tr style="background:{code_bg};"><td style="padding:3px 8px;"><code>model</code></td>
    <td style="padding:3px 8px;">str</td>
    <td style="padding:3px 8px;">Model ID (e.g. <code>claude-opus-4-6</code>)</td></tr>
</table>

<h3 style="color:{acc}; margin-top:12px;">RemoteTrigger Tool</h3>
<p>Claude Code exposes a <code style="background:{code_bg}; padding:1px 4px;">RemoteTrigger</code>
tool that lets external systems send prompts to a running Claude Code session:</p>
<pre style="background:{code_bg}; padding:8px; border-radius:4px;"># Configure in settings.json:
{{
  "remoteAccess": {{
    "enabled": true,
    "port": 8080,
    "token": "your-secret-token"
  }}
}}</pre>

<h3 style="color:{acc};">MCP as Remote Interface</h3>
<p>Run Claude Code as an MCP server and control it from another process:</p>
<pre style="background:{code_bg}; padding:8px; border-radius:4px;">claude --mcp-server</pre>
<p style="color:{theme.FG_SECONDARY};">This exposes Claude Code tools over the MCP protocol,
allowing any MCP client to invoke them programmatically.</p>
</body></html>"""
