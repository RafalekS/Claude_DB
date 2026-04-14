"""
Documentation Tab - Static reference docs for Claude Code with search.
Subtabs: CLI Reference, Workflows, Prompts, Commands, Tools Reference,
         Keyboard Shortcuts, Remote, Chrome, Computer Use, Plugins Reference
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextBrowser, QTabWidget, QLineEdit
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QKeySequence, QShortcut

from utils import theme


# ─── Reusable page widget ────────────────────────────────────────────────────

class DocPage(QWidget):
    """A static doc page with a search bar and QTextBrowser."""

    def __init__(self, html_content: str, docs_url: str = "", parent=None):
        super().__init__(parent)
        self._html = html_content
        self._url = docs_url
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # ── Search bar ───────────────────────────────────────────────────
        bar = QHBoxLayout()
        bar.setSpacing(4)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search… (Ctrl+F)")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._do_search)

        if self._url:
            ext_btn = QPushButton("🌐 Open in Browser")
            ext_btn.setMinimumWidth(130)
            ext_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self._url)))
            bar.addWidget(self._search, 1)
            bar.addWidget(ext_btn)
        else:
            bar.addWidget(self._search)

        layout.addLayout(bar)

        # ── Content browser ──────────────────────────────────────────────
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        self._browser.setHtml(self._html)
        layout.addWidget(self._browser, 1)

        # Ctrl+F → focus search
        sc = QShortcut(QKeySequence("Ctrl+F"), self)
        sc.activated.connect(self._search.setFocus)

    def _do_search(self, text: str):
        """Find first occurrence of text in the browser."""
        from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa: guard import
        # QTextBrowser.find is sufficient here
        if not text:
            # Reset by reloading
            self._browser.setHtml(self._html)
            return
        self._browser.find(text)


# ─── HTML helpers ─────────────────────────────────────────────────────────────

def _h(level, text):
    color = theme.ACCENT_PRIMARY if level <= 2 else theme.FG_PRIMARY
    return (f"<h{level} style='color:{color};"
            f"margin-top:{theme.MARGIN_LG}px;margin-bottom:{theme.MARGIN_SM}px;'>{text}</h{level}>")


def _p(text):
    return f"<p style='color:{theme.FG_PRIMARY};line-height:1.6;margin:{theme.MARGIN_SM}px 0;'>{text}</p>"


def _code(text):
    return (f"<code style='background:{theme.BG_MEDIUM};color:{theme.ACCENT_SECONDARY};"
            f"padding:1px {theme.PADDING_SM}px;border-radius:{theme.BORDER_RADIUS}px;"
            f"font-family:{theme.FONT_FAMILY_MONO};'>{text}</code>")


def _pre(text):
    return (f"<pre style='background:{theme.BG_MEDIUM};color:{theme.FG_PRIMARY};"
            f"padding:{theme.PADDING_MD}px;border-radius:{theme.BORDER_RADIUS}px;"
            f"font-family:{theme.FONT_FAMILY_MONO};"
            f"font-size:{theme.FONT_SIZE_SMALL}px;white-space:pre-wrap;'>{text}</pre>")


def _table(headers, rows):
    th = "".join(f"<th style='padding:{theme.PADDING_SM}px {theme.PADDING_MD}px;"
                 f"border-bottom:1px solid {theme.BG_LIGHT};"
                 f"text-align:left;color:{theme.ACCENT_PRIMARY};'>{h}</th>" for h in headers)
    body = ""
    for i, row in enumerate(rows):
        bg = theme.BG_MEDIUM if i % 2 == 0 else theme.BG_DARK
        body += f"<tr style='background:{bg};'>"
        body += "".join(
            f"<td style='padding:{theme.PADDING_SM}px {theme.PADDING_MD}px;"
            f"color:{theme.FG_PRIMARY};'>{c}</td>" for c in row)
        body += "</tr>"
    return (f"<table style='border-collapse:collapse;width:100%;margin:{theme.MARGIN_MD}px 0;'>"
            f"<thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>")


def _wrap(*parts):
    return (f"<html><body style='background:{theme.BG_DARK};color:{theme.FG_PRIMARY};"
            f"font-family:{theme.FONT_FAMILY};font-size:{theme.FONT_SIZE_NORMAL}px;"
            f"padding:{theme.PADDING_MD}px;'>{''.join(parts)}</body></html>")


# ─── Page content builders ────────────────────────────────────────────────────

def _cli_reference_html():
    rows_flags = [
        [_code("--print / -p"), "Non-interactive, print response and exit"],
        [_code("--output-format"), "Output format: text | json | stream-json"],
        [_code("--input-format"), "Input format: text | stream-json"],
        [_code("--permission-mode"), "default | acceptEdits | plan | auto | dontAsk | bypassPermissions"],
        [_code("--enable-auto-mode"), "Add 'auto' to the Shift+Tab permission mode cycle"],
        [_code("--dangerously-skip-permissions"), "Alias for --permission-mode bypassPermissions"],
        [_code("--allow-dangerously-skip-permissions"), "Add bypassPermissions to cycle without activating"],
        [_code("--model / -m"), "Model to use (overrides settings.json)"],
        [_code("--continue / -c"), "Resume the most recent conversation in this directory"],
        [_code("--resume / -r [id]"), "Resume a specific session (interactive picker if no id)"],
        [_code("--from-pr &lt;num&gt;"), "Resume session linked to a GitHub PR"],
        [_code("--name / -n &lt;name&gt;"), "Name the session for later resume"],
        [_code("--worktree / -w [name]"), "Create a git worktree and start Claude in it"],
        [_code("--add-dir &lt;path&gt;"), "Grant file access to additional directories"],
        [_code("--system-prompt / -s"), "Custom system prompt (replaces default)"],
        [_code("--append-system-prompt"), "Append to default system prompt"],
        [_code("--allowedTools"), "Comma-separated list of tools Claude may use"],
        [_code("--disallowedTools"), "Comma-separated list of tools to block"],
        [_code("--max-turns"), "Maximum agentic turns"],
        [_code("--verbose"), "Show detailed tool output"],
        [_code("--debug"), "Show debug info including plugin loading"],
        [_code("--mcp-config &lt;file&gt;"), "Load additional MCP server config from file"],
        [_code("--no-update-check"), "Skip version update check at startup"],
        [_code("--version"), "Print version and exit"],
    ]
    rows_subcmds = [
        [_code("claude"), "Start interactive REPL session"],
        [_code("claude -p &quot;prompt&quot;"), "Non-interactive single prompt"],
        [_code("claude -c"), "Continue most recent session"],
        [_code("claude --resume"), "Open session picker"],
        [_code("claude --worktree"), "Create worktree session"],
        [_code("claude remote-control"), "Start remote control host"],
        [_code("claude plugin install &lt;name&gt;"), "Install a plugin"],
        [_code("claude plugin uninstall &lt;name&gt;"), "Uninstall a plugin (--keep-data to preserve data)"],
        [_code("claude plugin enable &lt;name&gt;"), "Enable a disabled plugin"],
        [_code("claude plugin disable &lt;name&gt;"), "Disable without uninstalling"],
        [_code("claude plugin update &lt;name&gt;"), "Update to latest version"],
        [_code("claude plugin validate"), "Validate plugin manifest + hooks"],
        [_code("claude auto-mode defaults"), "Show auto mode classifier rule lists"],
        [_code("claude doctor"), "Check installation health"],
        [_code("claude update"), "Update Claude Code to latest version"],
    ]
    return _wrap(
        _h(1, "CLI Reference"),
        _h(2, "Flags"),
        _table(["Flag", "Description"], rows_flags),
        _h(2, "Commands"),
        _table(["Command", "Description"], rows_subcmds),
        _h(2, "Plugin Scopes"),
        _p("All plugin commands accept " + _code("-s / --scope user|project|local") +
           " (default: user). "
           "'project' writes to .claude/settings.json (shared via git). "
           "'local' writes to .claude/settings.local.json (gitignored)."),
        _h(2, "Output Formats"),
        _pre("# Plain text (default)\nclaude -p 'hello' --output-format text\n\n"
             "# Full JSON array\nclaude -p 'hello' --output-format json\n\n"
             "# Streaming JSON (newline-delimited objects)\nclaude -p 'hello' --output-format stream-json"),
    )


def _workflows_html():
    return _wrap(
        _h(1, "Common Workflows"),
        _h(2, "Understand a New Codebase"),
        _p("1. " + _code("cd /path/to/project && claude") + "<br>"
           "2. Ask: <em>'give me an overview of this codebase'</em><br>"
           "3. Drill down: <em>'explain the main architecture patterns'</em>, "
           "<em>'what are the key data models?'</em>"),
        _h(2, "Fix Bugs"),
        _p("Share the error message, ask for fix suggestions, then apply: <br>"
           + _code("I'm seeing an error when I run npm test") + "<br>"
           + _code("suggest a few ways to fix the @ts-ignore in user.ts")),
        _h(2, "Plan Mode — Safe Analysis"),
        _pre("claude --permission-mode plan\n# or press Shift+Tab to cycle to plan mode"),
        _p("In plan mode Claude reads files, runs shell commands, and writes a plan "
           "but does not edit source. Press Ctrl+G to open the plan in your editor."),
        _h(2, "Use Extended Thinking"),
        _p("Extended thinking is on by default. Toggle with " + _code("Alt+T") +
           " or include 'ultrathink' anywhere in your prompt to maximize thinking "
           "depth for that turn."),
        _h(2, "Work with Git Worktrees"),
        _pre("# Create isolated worktree\nclaude --worktree feature-auth\n\n"
             "# Auto-generate name\nclaude --worktree"),
        _p("Each worktree has its own branch and files. Add .claude/worktrees/ to .gitignore."),
        _h(2, "Resume Sessions"),
        _pre("claude --continue            # resume most recent\n"
             "claude --resume             # open picker\n"
             "claude --resume my-session  # resume by name\n"
             "claude --from-pr 123        # resume PR-linked session"),
        _h(2, "Run as Unix Utility"),
        _pre("# Pipe input\ncat build-error.txt | claude -p 'explain the root cause' > output.txt\n\n"
             "# Structured output\ncat code.py | claude -p 'find bugs' --output-format json"),
        _h(2, "Desktop Notifications"),
        _pre('# macOS — add to ~/.claude/settings.json\n{\n  "hooks": {\n'
             '    "Notification": [{\n      "matcher": "",\n      "hooks": [{\n'
             '        "type": "command",\n'
             '        "command": "osascript -e \'display notification \\"Claude needs attention\\" '
             'with title \\"Claude Code\\"\'"\n      }]\n    }]\n  }\n}'),
        _h(2, "Scheduled / Recurring Tasks"),
        _table(["Option", "Where it runs", "Best for"],
               [["Routines", "Anthropic cloud", "Runs even when your machine is off"],
                ["Desktop scheduled tasks", "Your machine", "Needs local files / tools"],
                ["GitHub Actions", "CI pipeline", "PR-triggered or cron in repo"],
                ["/loop", "Current session", "Quick polling while session is open"]]),
    )


def _prompts_html():
    return _wrap(
        _h(1, "System Prompts & Prompt Reference"),
        _h(2, "Custom System Prompts"),
        _pre("# Replace default system prompt\nclaude --system-prompt 'You are a strict code reviewer.'\n\n"
             "# Append to default\nclaude --append-system-prompt 'Always use British spelling.'"),
        _p("System prompt flags must be passed every invocation — better suited for scripts "
           "than interactive use. For persistent instructions, use CLAUDE.md files instead."),
        _h(2, "CLAUDE.md — Persistent Instructions"),
        _table(["Scope", "Location", "Shared?"],
               [["Managed (IT/org)", "/etc/claude-code/CLAUDE.md", "All org users"],
                ["User (personal)", "~/.claude/CLAUDE.md", "Just you"],
                ["Project", "./CLAUDE.md or ./.claude/CLAUDE.md", "Team via git"],
                ["Local", "./CLAUDE.local.md", "Just you (gitignored)"]]),
        _p("Files load from working directory upward. Nested CLAUDE.md files load on demand "
           "when Claude reads files in their directory."),
        _h(2, "CLAUDE.md Best Practices"),
        _p("• Target under 200 lines per file — longer files reduce adherence<br>"
           "• Be specific: 'Use 2-space indentation' not 'Format code nicely'<br>"
           "• Use " + _code("@path/to/file") + " imports to reference other files<br>"
           "• Use " + _code("<!-- comments -->") + " for human notes; stripped before loading<br>"
           "• Use " + _code("/init") + " to auto-generate from your codebase"),
        _h(2, "Path-Scoped Rules (.claude/rules/)"),
        _pre("---\npaths:\n  - 'src/api/**/*.ts'\n---\n\n# API Rules\n- Validate all inputs\n- Use standard error format"),
        _p("Rules without paths load every session. Path-scoped rules load only when Claude "
           "reads matching files. Organize rules in .claude/rules/ directory."),
        _h(2, "Auto Memory"),
        _p("Claude saves notes automatically to " + _code("~/.claude/projects/&lt;project&gt;/memory/") +
           ". Toggle with " + _code("autoMemoryEnabled") + " in settings. "
           "Use " + _code("/memory") + " in Claude Code to browse and edit."),
        _h(2, "# Quick Add"),
        _p("Prefix a prompt with " + _code("#") + " to instantly save it to memory: "
           + _code("# always use pnpm not npm")),
    )


def _commands_html():
    rows = [
        ["/help", "Built-in", "Show all commands and shortcuts"],
        ["/clear", "Built-in", "Clear conversation history and start new session"],
        ["/compact [instructions]", "Built-in", "Compact conversation to free context"],
        ["/config", "Built-in", "Open settings interface (model, theme, editor mode, etc.)"],
        ["/cost", "Built-in", "Show token usage and cost for current session"],
        ["/doctors", "Built-in", "Check Claude Code installation health"],
        ["/init", "Built-in", "Generate CLAUDE.md from codebase analysis"],
        ["/memory", "Built-in", "Browse and edit memory files; toggle auto memory"],
        ["/permissions", "Built-in", "Manage allow/deny rules; view recently denied"],
        ["/hooks", "Built-in", "Browse configured hooks (read-only)"],
        ["/agents", "Built-in", "Browse subagents; create new ones"],
        ["/theme", "Built-in", "Change color theme"],
        ["/model", "Built-in", "Switch Claude model"],
        ["/effort", "Built-in", "Set effort level: low | medium | high | max (Opus 4.6 only)"],
        ["/plan", "Built-in", "Prefix — run a single prompt in plan mode"],
        ["/btw &lt;question&gt;", "Built-in", "Side question (ephemeral, no history)"],
        ["/resume [id]", "Built-in", "Open session picker or resume by name/ID"],
        ["/rename [name]", "Built-in", "Name or rename the current session"],
        ["/branch", "Built-in", "Fork the conversation from this point"],
        ["/rewind", "Built-in", "Restore code / conversation to a previous state"],
        ["/feedback", "Built-in", "Submit feedback to Anthropic"],
        ["/upgrade", "Built-in", "Upgrade plan (Pro/Max only)"],
        ["/terminal-setup", "Built-in", "Install Shift+Enter binding for multiline"],
        ["/debug", "Built-in", "Toggle debug mode"],
        ["/verbose", "Built-in", "Toggle verbose output"],
        ["/powerup", "Built-in", "Interactive lessons with animated demos"],
        ["/simplify", "Skill", "Simplify and clean up code"],
        ["/batch", "Skill", "Process multiple items in parallel"],
        ["/debug (skill)", "Skill", "Systematic debugging playbook"],
        ["/loop [interval]", "Skill", "Autonomous loop with optional polling interval"],
        ["/claude-api", "Skill", "Use Claude API in code"],
    ]
    return _wrap(
        _h(1, "Commands Reference"),
        _p("Type " + _code("/") + " in Claude Code to see all available commands. "
           "Not every command appears for every user — availability depends on platform and plan. "
           "Bundled <b>Skills</b> use the same prompt mechanism as user-authored skills."),
        _table(["Command", "Type", "Description"], rows),
        _h(2, "Bash Mode"),
        _p("Prefix with " + _code("!") + " to run shell commands directly: " + _code("! npm test") +
           ". Output is added to conversation context. Press Ctrl+B to background a running command."),
        _h(2, "File References"),
        _p("Use " + _code("@path/to/file") + " in your prompt to include a file's content. "
           "Use " + _code("@dir/") + " for a directory listing."),
    )


def _tools_ref_html():
    rows = [
        ["Read", "Read a file from the filesystem"],
        ["Write", "Write/create a file"],
        ["Edit", "Exact string replacement in a file"],
        ["Bash", "Execute a shell command"],
        ["Glob", "Fast file pattern matching (glob syntax)"],
        ["Grep", "Content search (ripgrep-based)"],
        ["WebFetch", "Fetch and analyze a URL"],
        ["WebSearch", "Web search with optional domain filter"],
        ["Agent", "Spawn a subagent for complex tasks"],
        ["Task / TaskCreate / TaskUpdate / TaskGet / TaskStop", "Manage task lists"],
        ["AskUserQuestion", "Ask the user structured questions with options"],
        ["ScheduleWakeup", "Schedule next /loop dynamic wake-up"],
        ["Monitor", "Stream events from a background process"],
        ["EnterPlanMode / ExitPlanMode", "Switch to/from plan mode programmatically"],
        ["EnterWorktree / ExitWorktree", "Work in an isolated git worktree"],
        ["NotebookEdit", "Edit Jupyter notebook cells"],
        ["CronCreate / CronDelete / CronList", "Manage scheduled tasks"],
        ["RemoteTrigger", "Trigger remote Claude session"],
        ["Skill", "Invoke a skill by name"],
        ["ListMcpResourcesTool / ReadMcpResourceTool", "List/read MCP server resources"],
        ["SendMessage", "Send message to a running agent"],
    ]
    return _wrap(
        _h(1, "Tools Reference"),
        _p("These are the built-in tools available to Claude. MCP servers add additional tools "
           "prefixed with " + _code("mcp__&lt;server&gt;__") + "."),
        _table(["Tool", "Description"], rows),
        _h(2, "Tool Permission Syntax"),
        _p("Use these patterns in settings " + _code("permissions.allow") + " / " +
           _code("permissions.deny") + " arrays:"),
        _pre("Bash               # all bash commands\n"
             "Bash(git *)         # bash matching pattern\n"
             "Bash(npm test)      # exact bash command\n"
             "Read               # all reads\n"
             "Read(/home/*)       # reads matching path\n"
             "Skill(commit)       # exact skill\n"
             "Skill(deploy *)     # skill prefix match\n"
             "mcp__memory__.*    # all tools from MCP server"),
        _h(2, "Parallel Tool Execution"),
        _p("Claude can run up to 10 read-only tools and subagents in parallel. "
           "Set " + _code("CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY") + " to change the limit."),
    )


def _shortcuts_html():
    gen_rows = [
        ["Ctrl+C", "Cancel current input or generation"],
        ["Ctrl+D", "Exit Claude Code session"],
        ["Ctrl+G / Ctrl+X Ctrl+E", "Open prompt in default text editor"],
        ["Ctrl+L", "Clear prompt input (keeps conversation)"],
        ["Ctrl+O", "Toggle transcript viewer (verbose mode)"],
        ["Ctrl+R", "Reverse-search command history"],
        ["Ctrl+V / Cmd+V (iTerm2)", "Paste image from clipboard"],
        ["Ctrl+B", "Background current bash task (Tmux: press twice)"],
        ["Ctrl+T", "Toggle task list display"],
        ["Ctrl+X Ctrl+K", "Kill all background agents (confirm twice in 3s)"],
        ["Esc + Esc", "Rewind / restore to previous point"],
        ["Shift+Tab", "Cycle permission modes (default → acceptEdits → plan → auto)"],
        ["Alt+P (Win/Linux) / Option+P (macOS)", "Switch model"],
        ["Alt+T (Win/Linux) / Option+T (macOS)", "Toggle extended thinking"],
        ["Alt+O (Win/Linux) / Option+O (macOS)", "Toggle fast mode"],
        ["Up / Down arrows", "Navigate command history"],
        ["Left / Right arrows", "Cycle dialog tabs"],
        ["Tab / Right arrow", "Accept prompt suggestion"],
    ]
    text_rows = [
        ["Ctrl+K", "Delete to end of line"],
        ["Ctrl+U", "Delete from cursor to line start"],
        ["Ctrl+Y", "Paste deleted text"],
        ["Alt+Y (after Ctrl+Y)", "Cycle paste history"],
        ["Alt+B", "Move cursor back one word"],
        ["Alt+F", "Move cursor forward one word"],
    ]
    multi_rows = [
        ["Backslash + Enter (\\↵)", "All terminals"],
        ["Option+Enter", "macOS default"],
        ["Shift+Enter", "iTerm2, WezTerm, Ghostty, Kitty (out of box)"],
        ["Ctrl+J", "Line feed — works everywhere"],
    ]
    return _wrap(
        _h(1, "Keyboard Shortcuts"),
        _p("macOS: Option/Alt shortcuts require setting Option as Meta in your terminal. "
           "iTerm2: Preferences → Profiles → Keys → Left/Right Option = Esc+"),
        _h(2, "General Controls"),
        _table(["Shortcut", "Description"], gen_rows),
        _h(2, "Text Editing"),
        _table(["Shortcut", "Description"], text_rows),
        _h(2, "Multiline Input"),
        _table(["Method", "Context"], multi_rows),
        _p("Run " + _code("/terminal-setup") + " to install Shift+Enter binding in "
           "terminals that need it (VS Code, Alacritty, Zed, Warp)."),
        _h(2, "Quick Prefixes"),
        _table(["Prefix", "Effect"],
               [[_code("/"), "Command or skill menu"],
                [_code("!"), "Bash mode — run shell command and add output to context"],
                [_code("@"), "File path autocomplete"],
                [_code("#"), "Save to memory instantly"]]),
        _h(2, "Transcript Viewer (when open)"),
        _table(["Shortcut", "Action"],
               [["Ctrl+E", "Toggle show all content"],
                ["q / Ctrl+C / Esc", "Exit transcript view"]]),
    )


def _remote_html():
    return _wrap(
        _h(1, "Remote Control"),
        _p("Remote Control lets you connect to a Claude Code session running on your local machine "
           "from a web browser or mobile device at " +
           _code("https://claude.ai/code") + "."),
        _h(2, "Start a Remote Session"),
        _pre("# Start with remote control enabled\nclaude remote-control\n\n"
             "# With a specific permission mode\nclaude remote-control --permission-mode acceptEdits\n\n"
             "# Named session\nclaude remote-control --name my-session"),
        _h(2, "Available Modes in Remote Control"),
        _table(["Mode", "Available"],
               [["Ask permissions (default)", "Yes"],
                ["Auto accept edits", "Yes"],
                ["Plan mode", "Yes"],
                ["Auto mode", "No"],
                ["Bypass permissions", "No"]]),
        _h(2, "Session Name Prefix"),
        _p("Set " + _code("CLAUDE_REMOTE_CONTROL_SESSION_NAME_PREFIX") +
           " to customize auto-generated session names (default: hostname)."),
        _h(2, "Notes"),
        _p("• Permission prompts appear in the claude.ai interface for approval<br>"
           "• Sessions are tied to your Claude.ai account<br>"
           "• Remote control requires Claude Code v2.x or later<br>"
           "• Use " + _code("--from-pr &lt;num&gt;") + " to resume a PR-linked session remotely"),
    )


def _chrome_html():
    return _wrap(
        _h(1, "Chrome Extension"),
        _p("The Claude Code Chrome extension (and compatible browsers) integrates "
           "Claude Code directly into GitHub, GitLab, and other web pages."),
        _h(2, "Installation"),
        _p("Install from the Chrome Web Store. After installing, connect to your "
           "local Claude Code session using the extension popup."),
        _h(2, "Features"),
        _p("• Review PRs with Claude directly on GitHub<br>"
           "• Ask about code on any web page<br>"
           "• Reference files and discussions in your Claude prompt<br>"
           "• Link web sessions to local Claude Code sessions"),
        _h(2, "Connecting to Local Claude Code"),
        _pre("# Start local session with remote control enabled\nclaude remote-control"),
        _p("Then use the extension popup to connect to the running session. "
           "The extension can read your screen and current page context."),
        _h(2, "Security Note"),
        _p("The extension communicates with your local Claude Code via the remote control protocol. "
           "All Claude API calls are made from your local machine, not the browser extension."),
        _p("Full documentation: <a href='https://code.claude.com/docs/en/chrome'>"
           "code.claude.com/docs/en/chrome</a>"),
    )


def _computer_use_html():
    return _wrap(
        _h(1, "Computer Use"),
        _p("Computer Use lets Claude directly interact with your desktop — click buttons, "
           "type text, take screenshots, and navigate GUIs — using the computer_use tool."),
        _h(2, "Requirements"),
        _p("• Enabled via API or specific Claude Code configurations<br>"
           "• Requires explicit opt-in (not available by default in Claude Code CLI)<br>"
           "• Best used in sandboxed/VM environments"),
        _h(2, "Available Tools"),
        _table(["Tool", "Action"],
               [["computer", "Move mouse, click, type, screenshot, scroll"],
                ["bash", "Run shell commands"],
                ["text_editor", "View and edit files"]]),
        _h(2, "Safety"),
        _p("Computer Use is powerful and can affect your system. Always:<br>"
           "• Use in isolated VM or container when possible<br>"
           "• Review prompts carefully before giving Claude control<br>"
           "• Set appropriate permission mode (plan mode to verify before executing)<br>"
           "• Monitor what Claude does in real time"),
        _h(2, "Reference"),
        _p("Full documentation: <a href='https://code.claude.com/docs/en/computer-use'>"
           "code.claude.com/docs/en/computer-use</a>"),
    )


def _plugins_ref_html():
    return _wrap(
        _h(1, "Plugins Reference"),
        _h(2, "What is a Plugin?"),
        _p("A plugin is a self-contained directory of components that extends Claude Code: "
           "skills, agents, hooks, MCP servers, and LSP servers."),
        _h(2, "File Locations"),
        _table(["Component", "Default Location", "Purpose"],
               [["Manifest", ".claude-plugin/plugin.json", "Plugin metadata (optional)"],
                ["Skills", "skills/", "&lt;name&gt;/SKILL.md structure"],
                ["Commands", "commands/", "Flat .md skills (legacy; skills/ preferred)"],
                ["Agents", "agents/", "Subagent .md definitions"],
                ["Hooks", "hooks/hooks.json", "Event handlers"],
                ["MCP Servers", ".mcp.json", "External tool servers"],
                ["LSP Servers", ".lsp.json", "Language intelligence (go-to-def, diagnostics)"],
                ["Monitors", "monitors/monitors.json", "Background monitor configs"],
                ["Executables", "bin/", "Tools added to Bash PATH"],
                ["Settings", "settings.json", "Default plugin config (agent, subagentStatusLine)"]]),
        _h(2, "Plugin Scopes"),
        _table(["Scope", "Settings File", "Use Case"],
               [["user (default)", "~/.claude/settings.json", "Personal, all projects"],
                ["project", ".claude/settings.json", "Team, via git"],
                ["local", ".claude/settings.local.json", "Project-specific, gitignored"],
                ["managed", "Managed settings", "Org-wide (read-only)"]]),
        _h(2, "CLI Commands"),
        _pre("claude plugin install formatter@marketplace\n"
             "claude plugin install formatter@marketplace --scope project\n"
             "claude plugin uninstall formatter@marketplace\n"
             "claude plugin uninstall formatter@marketplace --keep-data\n"
             "claude plugin enable formatter@marketplace\n"
             "claude plugin disable formatter@marketplace\n"
             "claude plugin update formatter@marketplace\n"
             "claude plugin validate   # check plugin.json + hooks"),
        _h(2, "Plugin Variables"),
        _p(_code("${CLAUDE_PLUGIN_ROOT}") + " — absolute path to plugin install directory.<br>"
           + _code("${CLAUDE_PLUGIN_DATA}") + " — persistent data dir at "
           + _code("~/.claude/plugins/data/&lt;id&gt;/") + " — survives updates and uninstall (until last scope removed)."),
        _h(2, "plugin.json Schema (key fields)"),
        _pre('{\n  "name": "my-plugin",          // required, kebab-case\n'
             '  "version": "1.0.0",\n'
             '  "description": "...",\n'
             '  "skills": "./skills/",\n'
             '  "agents": "./agents/",\n'
             '  "hooks": "./hooks/hooks.json",\n'
             '  "mcpServers": "./.mcp.json",\n'
             '  "lspServers": "./.lsp.json",\n'
             '  "monitors": "./monitors.json",\n'
             '  "userConfig": {\n'
             '    "api_token": { "description": "API token", "sensitive": true }\n'
             '  }\n}'),
        _h(2, "How Plugins Work"),
        _p("• Settings: " + _code("enabledPlugins") + " array in settings.json<br>"
           "• Plugins are installed to the plugin cache at "
           + _code("~/.claude/plugins/cache") + "<br>"
           "• " + _code("/plugin") + " command in Claude Code terminal: browse, install, list, errors tab<br>"
           "• " + _code("claude --debug") + " shows plugin loading and registration details<br>"
           "• Use " + _code("claude plugin validate") + " to check manifest + hook syntax"),
        _h(2, "LSP Plugins (Code Intelligence)"),
        _table(["Plugin", "Language", "Install"],
               [["pyright-lsp", "Python", "pip install pyright or npm install -g pyright"],
                ["typescript-lsp", "TypeScript", "npm install -g typescript-language-server typescript"],
                ["rust-lsp", "Rust", "See rust-analyzer.github.io"]]),
    )


# ─── Main Documentation Tab ───────────────────────────────────────────────────

class DocumentationTab(QWidget):
    """Tab grouping all static reference documentation with search."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header
        header = QLabel("Documentation")
        header.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};"
        )
        layout.addWidget(header)

        # Subtab container
        tabs = QTabWidget()
        layout.addWidget(tabs, 1)

        tabs.addTab(DocPage(_cli_reference_html(),
                            "https://code.claude.com/docs/en/cli-reference"),
                    "⌨️ CLI Reference")

        tabs.addTab(DocPage(_workflows_html(),
                            "https://code.claude.com/docs/en/common-workflows"),
                    "🔄 Workflows")

        tabs.addTab(DocPage(_prompts_html(),
                            "https://code.claude.com/docs/en/memory"),
                    "💬 Prompts & Memory")

        tabs.addTab(DocPage(_commands_html(),
                            "https://code.claude.com/docs/en/commands"),
                    "/ Commands")

        tabs.addTab(DocPage(_tools_ref_html(),
                            "https://code.claude.com/docs/en/tools-reference"),
                    "🔧 Tools Ref")

        tabs.addTab(DocPage(_shortcuts_html(),
                            "https://code.claude.com/docs/en/interactive-mode"),
                    "⌨️ Shortcuts")

        tabs.addTab(DocPage(_remote_html(),
                            "https://code.claude.com/docs/en/remote-control"),
                    "🌐 Remote")

        tabs.addTab(DocPage(_chrome_html(),
                            "https://code.claude.com/docs/en/chrome"),
                    "🔵 Chrome")

        tabs.addTab(DocPage(_computer_use_html(),
                            "https://code.claude.com/docs/en/computer-use"),
                    "🖥️ Computer Use")

        tabs.addTab(DocPage(_plugins_ref_html(),
                            "https://code.claude.com/docs/en/plugins-reference"),
                    "🧩 Plugins Ref")
