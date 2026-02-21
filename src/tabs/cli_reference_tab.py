"""
CLI Reference Tab - Display Claude Code CLI commands and options
"""

from pathlib import Path
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextBrowser, QLabel
)
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QDesktopServices

sys.path.insert(0, str(Path(__file__).parent.parent))
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
            QUrl("https://docs.claude.com/en/docs/claude-code/cli-reference")
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
            <p><code>claude</code> - Start interactive REPL</p>
            <p><code>claude "query"</code> - Launch REPL with initial prompt</p>
            <pre>claude "explain this project"</pre>

            <p><code>claude -p "query"</code> - Query via SDK, then exit (headless mode)</p>
            <pre>claude -p "explain this function"</pre>

            <p><code>claude -c</code> - Continue most recent conversation</p>

            <p><code>claude -r &lt;session-id&gt; "query"</code> - Resume specific session by ID</p>
            <pre>claude -r "abc123" "Finish this PR"</pre>

            <h3>System Commands</h3>
            <p><code>claude update</code> - Update to latest version</p>
            <p><code>claude mcp</code> - Configure Model Context Protocol servers</p>

            <hr>

            <h2>Key Flags</h2>

            <h3>Model & Behavior</h3>
            <p><code>--model</code> - Set model with alias (<code>sonnet</code>, <code>opus</code>) or full name</p>
            <pre>claude --model opus "complex task"</pre>

            <p><code>--max-turns</code> - Limit agentic turns in non-interactive mode</p>
            <pre>claude -p "task" --max-turns 5</pre>

            <p><code>--verbose</code> - Enable detailed turn-by-turn output</p>

            <h3>Input/Output</h3>
            <p><code>--output-format</code> - Specify format: <code>text</code>, <code>json</code>, <code>stream-json</code></p>
            <pre>claude -p "query" --output-format json</pre>

            <p><code>--input-format</code> - Specify input type: <code>text</code>, <code>stream-json</code></p>

            <p><code>--include-partial-messages</code> - Include streaming events (requires <code>--print</code> and <code>stream-json</code>)</p>

            <h3>Permissions & Tools</h3>
            <p><code>--allowedTools</code> - Pre-approve specific tools without prompting</p>
            <pre>claude --allowedTools Read,Write,Bash</pre>

            <p><code>--disallowedTools</code> - Block specific tools without prompting</p>
            <pre>claude --disallowedTools WebFetch,WebSearch</pre>

            <p><code>--permission-mode</code> - Begin in specified permission mode</p>
            <pre>claude --permission-mode auto</pre>

            <p><code>--dangerously-skip-permissions</code> - Skip all permission prompts (use with caution!)</p>

            <h3>Additional Options</h3>
            <p><code>--add-dir</code> - Add working directories for file access</p>
            <pre>claude --add-dir /path/to/project</pre>

            <p><code>--append-system-prompt</code> - Add custom instructions (with <code>--print</code>)</p>
            <pre>claude --append-system-prompt "Always format code with 2 spaces"</pre>

            <p><code>--agents</code> - Define custom subagents dynamically via JSON</p>
            <pre>claude --agents '[{{"description":"Custom agent","prompt":"System prompt"}}]'</pre>

            <hr>

            <h2>Subagents Flag Format</h2>
            <p>Define custom agents using <code>--agents</code> with JSON containing:</p>
            <ul>
                <li><strong>description</strong> (required) - When to invoke the agent</li>
                <li><strong>prompt</strong> (required) - System prompt guiding behavior</li>
                <li><strong>tools</strong> (optional) - Specific allowed tools</li>
                <li><strong>model</strong> (optional) - Model alias to use</li>
            </ul>

            <hr>

            <h2>Common Usage Patterns</h2>

            <h3>Headless Automation</h3>
            <pre>claude -p "migrate codebase" --output-format json --dangerously-skip-permissions</pre>

            <h3>Interactive with Model Override</h3>
            <pre>claude --model opus --verbose</pre>

            <h3>Restricted Tool Access</h3>
            <pre>claude --allowedTools Read,Grep,Glob --disallowedTools Bash</pre>

            <h3>Custom Workspace</h3>
            <pre>claude --add-dir /project1 --add-dir /project2</pre>

            <p style="margin-top: 20px; padding: 10px; background-color: {theme.BG_MEDIUM}; border-left: 3px solid {theme.ACCENT_SECONDARY};">
                <strong>💡 Tip:</strong> For full documentation and latest updates, visit the
                <a href="https://docs.claude.com/en/docs/claude-code/cli-reference" style="color: {theme.ACCENT_SECONDARY};">official CLI reference</a>.
            </p>
        </body>
        </html>
        """

        self.browser.setHtml(html_content)
