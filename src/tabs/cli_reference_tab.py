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
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        # Header with link to docs
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        header = QLabel("Claude Code CLI Reference")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")

        docs_btn = QPushButton("📖 Open Full Docs")
        docs_btn.setToolTip("Open official CLI reference documentation in browser")
        docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://code.claude.com/docs/en/cli-reference")
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
                border-radius: 3px;
                padding: 15px;
                font-family: {theme.FONT_FAMILY_MONO};
                font-size: {theme.FONT_SIZE_NORMAL}px;
            }}
            QTextBrowser h2 {{
                padding-bottom: 5px;
                margin-top: 15px;
            }}
            QTextBrowser h3 {{
                margin-top: 10px;
            }}
            QTextBrowser code {{
                padding: 2px 6px;
                border-radius: 3px;
                font-family: {theme.FONT_FAMILY_MONO};
            }}
            QTextBrowser pre {{
                padding: 10px;
                border-radius: 3px;
            }}
        """)

        self.load_cli_reference()
        layout.addWidget(self.browser, 1)

    def apply_theme(self):
        """Reload HTML so inline styles pick up the new theme palette."""
        self.load_cli_reference()

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

            <p><code>claude -r &lt;session&gt; "query"</code> (or <code>--resume</code>) — Resume a session by ID or name</p>
            <pre>claude -r "auth-refactor" "Finish this PR"</pre>

            <h3>Config &amp; Diagnostics</h3>
            <p>The <code>claude config</code> subcommand has been removed. Change settings by editing the
               settings JSON files, from the in-session <code>/config</code> menu (<code>/config key=value</code>),
               or for one session with the <code>--settings</code> flag.</p>
            <p><code>claude doctor</code> — Print installation and settings diagnostics (rejected/invalid entries)</p>
            <p><code>claude update</code> — Update to latest version</p>
            <p><code>claude install [version]</code> — Install or reinstall the native binary</p>
            <p><code>claude mcp</code> — Configure Model Context Protocol servers</p>
            <p><code>claude plugin</code> — Manage plugins and marketplaces</p>
            <p><code>claude auth login|logout|status</code> — Manage Anthropic account sign-in</p>
            <p><code>claude setup-token</code> — Generate a long-lived OAuth token for CI/scripts</p>

            <hr>

            <h2>Flags</h2>

            <h3>Model &amp; Behavior</h3>
            <p><code>--model &lt;alias|id&gt;</code> — Set model. Aliases: <code>sonnet</code>, <code>opus</code>, <code>haiku</code>, <code>fable</code>. Full IDs: <code>claude-sonnet-5</code>, <code>claude-opus-5</code>, …</p>
            <pre>claude --model opus "complex task"</pre>

            <p><code>--effort &lt;level&gt;</code> — Reasoning depth: <code>low</code>, <code>medium</code>, <code>high</code>, <code>xhigh</code>, <code>max</code>, <code>ultracode</code></p>
            <p><code>--fallback-model &lt;list&gt;</code> — Backup model(s) when the primary is overloaded</p>

            <p><code>--max-turns &lt;n&gt;</code> — Limit agentic turns in non-interactive mode</p>
            <pre>claude -p "task" --max-turns 5</pre>

            <p><code>--max-budget-usd &lt;amount&gt;</code> — Cap API spend for a <code>-p</code> run</p>
            <p><code>--verbose</code> — Enable detailed turn-by-turn output</p>
            <p><code>--debug[=categories]</code> — Enable debug logging (e.g. <code>--debug=mcp,startup</code>)</p>

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

            <p><code>--permission-mode &lt;mode&gt;</code> — Start in a permission mode:
               <code>default</code>, <code>acceptEdits</code>, <code>plan</code>, <code>auto</code>,
               <code>dontAsk</code>, <code>bypassPermissions</code>, <code>manual</code></p>
            <pre>claude --permission-mode plan</pre>
            <p><code>--settings &lt;file|json&gt;</code> — Apply settings for one session (above user/project/local, below managed)</p>
            <p><code>--setting-sources &lt;list&gt;</code> — Restrict which setting sources load: <code>user,project,local</code></p>

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
            <p><code>--agents &lt;json&gt;</code> — Define custom subagents dynamically. The value is a JSON
               <em>object keyed by agent name</em> (no longer an array).</p>
            <pre>claude --agents '{{"code-reviewer":{{"description":"Reviews code","prompt":"Review for bugs","tools":["Read","Grep"],"model":"sonnet"}}}}'</pre>
            <p>Per-agent keys: <code>description</code> (required), <code>prompt</code> (required), plus optional
               <code>tools</code>, <code>disallowedTools</code>, <code>model</code>, <code>permissionMode</code>,
               <code>mcpServers</code>, <code>hooks</code>, <code>maxTurns</code>, <code>skills</code>,
               <code>memory</code>, <code>effort</code>, <code>background</code>, <code>isolation</code>.</p>
            <p><code>--agent &lt;name&gt;</code> — Run the current session as a named agent</p>
            <p><code>--append-subagent-system-prompt "text"</code> — Append text to every subagent's system prompt</p>

            <hr>

            <h2>Slash Commands (in REPL)</h2>
            <p>Type these in the interactive REPL:</p>
            <p><code>/help</code> — Show help</p>
            <p><code>/clear</code> — Start a new conversation with empty context</p>
            <p><code>/compact</code> — Free up context by summarizing the conversation</p>
            <p><code>/context</code> — Visualize current context usage as a colored grid</p>
            <p><code>/rewind</code> — Roll code and/or conversation back to a checkpoint</p>
            <p><code>/status</code> — Show session status and loaded setting sources</p>
            <p><code>/config</code> — Open settings, or <code>/config key=value</code> to set one</p>
            <p><code>/usage</code> — Show plan usage and rate-limit status (<code>/cost</code> is an alias)</p>
            <p><code>/model</code> — Switch the model mid-session</p>
            <p><code>/effort</code> — Change the reasoning effort level</p>
            <p><code>/bug</code> — Report a bug / share the conversation</p>
            <p><code>/feedback</code> — Send product feedback about Claude Code</p>
            <p><code>/exit</code> (or <code>/quit</code>) — Exit the REPL</p>
            <p><code>! &lt;command&gt;</code> — Run a shell command in the current session</p>
            <p>Bundled skills: <code>/code-review</code>, <code>/debug</code>, <code>/loop</code>, <code>/batch</code>,
               <code>/deep-research</code>, <code>/doctor</code>, <code>/verify</code>, <code>/claude-api</code>, …</p>

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
                <a href="https://code.claude.com/docs/en/cli-reference" style="color: {theme.ACCENT_SECONDARY};">official CLI reference</a>.
            </p>
        </body>
        </html>
        """

        self.browser.setHtml(html_content)
