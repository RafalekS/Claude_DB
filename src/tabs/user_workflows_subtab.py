"""
User Workflows Sub-Tab - Common Claude Code workflows guide
"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextBrowser
)
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme


class UserWorkflowsSubTab(QWidget):
    """Workflows guide interface for user-level configuration"""

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
        layout.setSpacing(5)

        # Header with docs link
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        header = QLabel("Common Workflows")
        header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")

        docs_btn = QPushButton("📖 Workflows Docs")
        docs_btn.setStyleSheet(theme.get_button_style())
        docs_btn.setToolTip("Open official common workflows documentation in browser")
        docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://docs.claude.com/en/docs/claude-code/common-workflows")
        ))

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(docs_btn)

        layout.addLayout(header_layout)

        # Deprecation notice for output styles
        deprecation_notice = QLabel(
            "⚠️ <b>Note:</b> Output styles were deprecated on November 5, 2025. "
            "Use <code>--system-prompt-file</code>, <code>--system-prompt</code>, "
            "<code>--append-system-prompt</code>, <code>CLAUDE.md</code>, or plugins instead."
        )
        deprecation_notice.setWordWrap(True)
        deprecation_notice.setStyleSheet(f"""
            QLabel {{
                color: {theme.FG_PRIMARY};
                background-color: {theme.BG_MEDIUM};
                padding: 10px;
                border-left: 3px solid #f0ad4e;
                border-radius: 3px;
                font-size: {theme.FONT_SIZE_SMALL}px;
            }}
        """)
        layout.addWidget(deprecation_notice)

        # Workflows browser
        workflows_browser = QTextBrowser()
        workflows_browser.setOpenExternalLinks(True)
        workflows_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                padding: 15px;
                font-size: {theme.FONT_SIZE_SMALL}px;
            }}
        """)

        html = f"""
        <html>
        <body style="color: {theme.FG_PRIMARY};">
            <h2 style="color: {theme.ACCENT_PRIMARY};">Common Claude Code Workflows</h2>

            <h3 style="color: {theme.ACCENT_SECONDARY};">🔍 Codebase Understanding</h3>
            <p>Start with broad questions, then narrow down. Ask about architecture, data models, and authentication patterns.</p>
            <p><strong>Tip:</strong> Use <code>@</code> operator to reference specific files or directories for focused analysis.</p>

            <h3 style="color: {theme.ACCENT_SECONDARY}; margin-top: 15px;">🐛 Code Analysis & Fixes</h3>
            <p>Share errors with Claude, ask for recommendations, and apply fixes incrementally.</p>
            <p><strong>Best Practice:</strong> Include reproduction steps and stack traces for efficient debugging.</p>

            <h3 style="color: {theme.ACCENT_SECONDARY}; margin-top: 15px;">♻️ Refactoring</h3>
            <p>Request modernization suggestions while maintaining behavior. Do refactoring in small, testable increments.</p>
            <p><strong>Remember:</strong> Always verify with tests after each refactoring step.</p>

            <h3 style="color: {theme.ACCENT_SECONDARY}; margin-top: 15px;">🤖 Specialized Subagents</h3>
            <p>Use <code>/agents</code> to view available subagents or delegate specific tasks.</p>
            <p><strong>Create custom:</strong> Add project-specific subagents in <code>.claude/agents/</code> for team sharing.</p>

            <h3 style="color: {theme.ACCENT_SECONDARY}; margin-top: 15px;">📋 Plan Mode</h3>
            <p>Enable read-only analysis with <code>--permission-mode plan</code> or <code>Shift+Tab</code>.</p>
            <p><strong>Ideal for:</strong> Multi-file changes, exploration, and interactive development.</p>

            <h3 style="color: {theme.ACCENT_SECONDARY}; margin-top: 15px;">✅ Testing & Documentation</h3>
            <p>Identify untested code, generate test scaffolding, and add comprehensive documentation.</p>
            <p><strong>Request:</strong> Edge case and error condition coverage.</p>

            <h3 style="color: {theme.ACCENT_SECONDARY}; margin-top: 15px;">🔀 Pull Requests & Images</h3>
            <p>Generate PR summaries directly with <code>/create pr</code>.</p>
            <p><strong>Visual context:</strong> Include images via drag-and-drop, clipboard paste, or file paths.</p>

            <h3 style="color: {theme.ACCENT_SECONDARY}; margin-top: 15px;">📁 File References</h3>
            <p>Use <code>@filename</code> to include file content and <code>@directory</code> for listings.</p>
            <p><strong>Auto-context:</strong> File references automatically include relevant CLAUDE.md context.</p>

            <h3 style="color: {theme.ACCENT_SECONDARY}; margin-top: 15px;">💭 Extended Thinking</h3>
            <p>Press <code>Tab</code> to toggle thinking on-demand.</p>
            <p><strong>Useful for:</strong> Complex architecture decisions and multi-step implementations.</p>

            <h3 style="color: {theme.ACCENT_SECONDARY}; margin-top: 15px;">💾 Session Management</h3>
            <p>Resume conversations with <code>--continue</code> or <code>--resume</code> for interactive selection.</p>
            <p><strong>Preserves:</strong> Full message history and tool state.</p>

            <h3 style="color: {theme.ACCENT_SECONDARY}; margin-top: 15px;">🔧 Unix Integration</h3>
            <p>Pipe data through Claude:</p>
            <pre style="background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px;">cat file.txt | claude -p 'analyze this'</pre>
            <p><strong>Structured output:</strong> Use <code>--output-format json|text|stream-json</code> for integrations.</p>

            <h3 style="color: {theme.ACCENT_SECONDARY}; margin-top: 15px;">⚡ Custom Slash Commands</h3>
            <p>Create project commands in <code>.claude/commands/</code> (team-shared) or <code>~/.claude/commands/</code> (personal).</p>
            <p><strong>Flexible:</strong> Use <code>$ARGUMENTS</code> placeholder for inputs.</p>

            <h3 style="color: {theme.ACCENT_SECONDARY}; margin-top: 15px;">🔌 Custom System Prompts</h3>
            <p>Modify Claude's behavior using system prompt options:</p>
            <ul>
                <li><code>--system-prompt "Your instructions"</code> - Replace default system prompt</li>
                <li><code>--system-prompt-file path/to/file.md</code> - Load system prompt from file</li>
                <li><code>--append-system-prompt "Additional context"</code> - Add to existing prompt</li>
                <li><code>CLAUDE.md</code> - Project-specific instructions (automatically included)</li>
            </ul>
            <p><strong>Note:</strong> Output styles are deprecated. Use these alternatives instead.</p>

            <h3 style="color: {theme.ACCENT_SECONDARY}; margin-top: 15px;">🧩 Plugins</h3>
            <p>Extend Claude Code with community plugins:</p>
            <pre style="background: {theme.BG_MEDIUM}; padding: 8px; border-radius: 3px;">claude plugins install &lt;plugin-url&gt;
claude plugins list
claude plugins enable &lt;plugin-name&gt;</pre>
            <p><strong>Example:</strong> For explanatory output style behavior, use the <code>explanatory-output-style</code> plugin.</p>

            <p style="margin-top: 20px; padding: 10px; background-color: {theme.BG_MEDIUM}; border-left: 3px solid {theme.ACCENT_SECONDARY};">
                <strong>💡 Pro Tip:</strong> Combine workflows for maximum efficiency. For example, use Plan Mode with file references
                for complex refactorings, then create custom slash commands for repetitive tasks!
            </p>
        </body>
        </html>
        """

        workflows_browser.setHtml(html)
        layout.addWidget(workflows_browser, 1)
