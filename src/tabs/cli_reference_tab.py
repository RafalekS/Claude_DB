"""
CLI Reference Tab - Display Claude Code CLI commands and options
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextBrowser, QLabel
)
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QDesktopServices

from utils import theme


class CLIReferenceTab(QWidget):
    """Tab displaying CLI reference documentation"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header with link to docs
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        header = QLabel("Claude Code CLI Reference")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")

        docs_btn = QPushButton("📖 Open Full Docs")
        docs_btn.setStyleSheet(theme.get_button_style())
        docs_btn.setToolTip("Open official CLI reference documentation in browser")
        docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://code.claude.com/en/docs/claude-code/cli-reference")
        ))

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(docs_btn)

        layout.addLayout(header_layout)

        # Content browser
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                padding: 15px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: {theme.FONT_SIZE_NORMAL}px;
            }}
            QTextBrowser h2 {{
                color: {theme.ACCENT_PRIMARY};
                border-bottom: 2px solid {theme.ACCENT_PRIMARY};
                padding-bottom: 5px;
                margin-top: 15px;
            }}
            QTextBrowser h3 {{
                color: {theme.ACCENT_SECONDARY};
                margin-top: 10px;
            }}
            QTextBrowser code {{
                background-color: {theme.BG_MEDIUM};
                color: {theme.SUCCESS_COLOR};
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Consolas', 'Monaco', monospace;
            }}
            QTextBrowser pre {{
                background-color: {theme.BG_MEDIUM};
                color: {theme.FG_PRIMARY};
                padding: 10px;
                border-radius: 3px;
                border-left: 3px solid {theme.ACCENT_PRIMARY};
            }}
        """)

        self.load_cli_reference()
        layout.addWidget(self.browser, 1)

    def load_cli_reference(self):
        """Load CLI reference content"""
        html_content = f"""
        <html>
        <body>
            <h2>Core Commands</h2>

            <h3>Interactive Sessions</h3>
            <p><code>claude</code> — Start interactive REPL</p>
            <p><code>claude "query"</code> — Launch REPL with initial prompt</p>
            <pre>claude "explain this project"</pre>

            <p><code>claude -p "query"</code> (or <code>--print</code>) — Query via SDK, then exit (headless/non-interactive mode)</p>
            <pre>claude -p "explain this function"</pre>

            <p><code>claude -c</code> (or <code>--continue</code>) — Continue most recent conversation</p>

            <p><code>claude -r &lt;session-id&gt; "query"</code> (or <code>--resume</code>) — Resume specific session by ID</p>
            <pre>claude -r "abc123" "Finish this PR"</pre>

            <h3>Config & Diagnostics</h3>
            <p><code>claude config get &lt;key&gt;</code> — Get a config value</p>
            <pre>claude config get model</pre>
            <p><code>claude config set &lt;key&gt; &lt;value&gt;</code> — Set a config value</p>
            <pre>claude config set theme dark</pre>
            <p><code>claude config list</code> — List all config values</p>
            <p><code>claude doctor</code> — Diagnose environment and configuration issues</p>
            <p><code>claude update</code> — Update to latest version</p>
            <p><code>claude bug</code> — File a bug report</p>
            <p><code>claude mcp</code> — Configure Model Context Protocol servers</p>

            <hr>

            <h2>Flags</h2>

            <h3>Model &amp; Behavior</h3>
            <p><code>--model &lt;alias|id&gt;</code> — Set model. Aliases: <code>sonnet</code>, <code>opus</code>, <code>haiku</code></p>
            <pre>claude --model opus "complex task"</pre>

            <p><code>--max-turns &lt;n&gt;</code> — Limit agentic turns in non-interactive mode</p>
            <pre>claude -p "task" --max-turns 5</pre>

            <p><code>--verbose</code> — Enable detailed turn-by-turn output</p>
            <p><code>--debug</code> — Enable debug logging</p>
            <p><code>--no-markdown</code> — Disable markdown rendering in terminal output</p>

            <h3>System Prompt</h3>
            <p><code>--system-prompt "text"</code> — Set the system prompt directly (replaces default)</p>
            <pre>claude -p "task" --system-prompt "You are a code reviewer"</pre>

            <p><code>--append-system-prompt "text"</code> — Append to the existing system prompt</p>
            <pre>claude --append-system-prompt "Always use 2-space indentation"</pre>

            <h3>Input/Output</h3>
            <p><code>--output-format &lt;format&gt;</code> — Output format: <code>text</code>, <code>json</code>, <code>stream-json</code></p>
            <pre>claude -p "query" --output-format json</pre>

            <p><code>--input-format &lt;format&gt;</code> — Input format: <code>text</code>, <code>stream-json</code></p>
            <p><code>--include-partial-messages</code> — Include streaming partial events (requires <code>--print</code> + <code>stream-json</code>)</p>

            <h3>Permissions &amp; Tools</h3>
            <p><code>--allowedTools &lt;list&gt;</code> — Pre-approve tools (comma-separated)</p>
            <pre>claude --allowedTools Read,Write,Bash</pre>

            <p><code>--disallowedTools &lt;list&gt;</code> — Block tools (comma-separated)</p>
            <pre>claude --disallowedTools WebFetch,WebSearch</pre>

            <p><code>--permission-mode &lt;mode&gt;</code> — Start in a permission mode</p>
            <pre>claude --permission-mode auto</pre>

            <p><code>--permission-prompt-tool &lt;tool&gt;</code> — MCP tool to handle permission prompts in headless mode</p>
            <pre>claude -p "task" --permission-prompt-tool mcp__my_server__ask_permission</pre>

            <p><code>--dangerously-skip-permissions</code> — Skip all permission prompts (headless automation only)</p>

            <h3>Workspace &amp; MCP</h3>
            <p><code>--add-dir &lt;path&gt;</code> — Add a working directory (can be used multiple times)</p>
            <pre>claude --add-dir /project1 --add-dir /project2</pre>

            <p><code>--mcp-config &lt;path&gt;</code> — Load MCP server config from a specific file</p>
            <pre>claude --mcp-config /path/to/mcp.json</pre>

            <p><code>--ide</code> — Launch in IDE integration mode</p>

            <h3>Subagents</h3>
            <p><code>--agents &lt;json&gt;</code> — Define custom subagents dynamically</p>
            <pre>claude --agents '[{{"description":"Code reviewer","prompt":"Review for bugs","model":"haiku"}}]'</pre>
            <p>Agent object keys: <code>description</code> (required), <code>prompt</code> (required), <code>tools</code> (optional), <code>model</code> (optional)</p>

            <hr>

            <h2>Slash Commands (in REPL)</h2>
            <p>Type these in the interactive REPL:</p>
            <p><code>/help</code> — Show help</p>
            <p><code>/clear</code> — Clear conversation history</p>
            <p><code>/compact</code> — Compact context window</p>
            <p><code>/status</code> — Show session status</p>
            <p><code>/exit</code> (or <code>/quit</code>) — Exit the REPL</p>
            <p><code>/cost</code> — Show token usage and cost for this session</p>
            <p><code>/model &lt;alias&gt;</code> — Switch model mid-session</p>
            <p><code>/allowed-tools</code> — List allowed tools</p>
            <p><code>/bug</code> — File a bug report</p>
            <p><code>! &lt;command&gt;</code> — Run a shell command in the current session</p>

            <hr>

            <h2>Common Patterns</h2>

            <h3>Headless Automation</h3>
            <pre>claude -p "migrate codebase" --output-format json --dangerously-skip-permissions</pre>

            <h3>Pipe input</h3>
            <pre>cat file.py | claude -p "review this code"</pre>

            <h3>JSON output for scripting</h3>
            <pre>claude -p "list all TODO comments" --output-format json | jq '.result'</pre>

            <h3>Resume session with new model</h3>
            <pre>claude -r abc123 --model opus "continue"</pre>

            <h3>Restricted tool access</h3>
            <pre>claude --allowedTools Read,Grep,Glob --disallowedTools Bash</pre>

            <p style="margin-top: 20px; padding: 10px; background-color: {theme.BG_MEDIUM}; border-left: 3px solid {theme.ACCENT_SECONDARY};">
                <strong>💡 Tip:</strong> For the complete up-to-date reference, see the
                <a href="https://code.claude.com/en/docs/claude-code/cli-reference" style="color: {theme.ACCENT_SECONDARY};">official CLI reference</a>.
            </p>
        </body>
        </html>
        """

        self.browser.setHtml(html_content)
