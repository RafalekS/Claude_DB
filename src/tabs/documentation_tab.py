"""
Documentation Tab - Static reference docs for Claude Code with search.
Subtabs: CLI Reference, Workflows, Prompts, Commands, Tools Reference,
         Keyboard Shortcuts, Remote, Chrome, Computer Use, Plugins Reference,
         Agent Teams, Remote Control
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextBrowser, QTabWidget, QLineEdit
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QKeySequence, QShortcut
from tabs.agent_teams_tab import AgentTeamsTab
from tabs.remote_control_tab import RemoteControlTab

from utils import theme


# ─── Reusable page widget ────────────────────────────────────────────────────

class DocPage(QWidget):
    """A static doc page with a search bar and QTextBrowser.

    Accepts either a pre-rendered HTML string or a callable that produces HTML.
    When a callable is passed, apply_theme() regenerates the HTML from it so
    the content re-renders with the latest theme colours.
    """

    def __init__(self, html_or_callable, docs_url: str = "", parent=None):
        super().__init__(parent)
        if callable(html_or_callable):
            self._html_fn = html_or_callable
            self._html = html_or_callable()
        else:
            self._html_fn = None
            self._html = html_or_callable
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
        from PyQt6.QtGui import QFont
        self._browser.setFont(QFont(theme.FONT_FAMILY_UI, theme.FONT_SIZE_NORMAL))
        self._browser.setOpenExternalLinks(True)
        self._browser.setHtml(self._html)
        layout.addWidget(self._browser, 1)

        # Ctrl+F → focus search
        sc = QShortcut(QKeySequence("Ctrl+F"), self)
        sc.activated.connect(self._search.setFocus)

    def apply_theme(self):
        """Regenerate HTML with current theme colours and refresh the browser."""
        if self._html_fn is not None:
            self._html = self._html_fn()
        self._browser.setHtml(self._html)
        from PyQt6.QtGui import QFont
        self._browser.setFont(QFont(theme.FONT_FAMILY_UI, theme.FONT_SIZE_NORMAL))

    def _do_search(self, text: str):
        """Find first occurrence of text in the browser."""
        if not text:
            self._browser.setHtml(self._html)
            return
        self._browser.find(text)


# ─── HTML helpers ─────────────────────────────────────────────────────────────

def _h(level, text):
    # No inline color — body text color comes from the HTML Content widget editor
    # (setDefaultStyleSheet). Accent heading colors are set there too.
    return (f"<h{level} style='"
            f"margin-top:{theme.MARGIN_LG}px;margin-bottom:{theme.MARGIN_SM}px;'>{text}</h{level}>")


def _p(text):
    # No inline color — inherited from body via the document default stylesheet.
    return f"<p style='line-height:1.6;margin:{theme.MARGIN_SM}px 0;'>{text}</p>"


def _code(text):
    # Keep background/font-family inline (layout); remove color (from stylesheet).
    return (f"<code style='background:{theme.BG_MEDIUM};"
            f"padding:1px {theme.PADDING_SM}px;border-radius:{theme.BORDER_RADIUS}px;"
            f"font-family:{theme.FONT_FAMILY_MONO};'>{text}</code>")


def _pre(text):
    # Keep layout/font inline; remove color (from stylesheet).
    return (f"<pre style='background:{theme.BG_MEDIUM};"
            f"padding:{theme.PADDING_MD}px;border-radius:{theme.BORDER_RADIUS}px;"
            f"font-family:{theme.FONT_FAMILY_MONO};"
            f"font-size:{theme.FONT_SIZE_SMALL}px;white-space:pre-wrap;'>{text}</pre>")


def _table(headers, rows):
    # Header cells keep accent color (structural); body cells drop color.
    th = "".join(f"<th style='padding:{theme.PADDING_SM}px {theme.PADDING_MD}px;"
                 f"border-bottom:2px solid {theme.ACCENT_PRIMARY};"
                 f"text-align:left;color:{theme.ACCENT_PRIMARY};'>{h}</th>" for h in headers)
    body = ""
    for row in rows:
        body += f"<tr style='background:{theme.BG_DARK};border-bottom:1px solid {theme.BG_LIGHT};'>"
        body += "".join(
            f"<td style='padding:{theme.PADDING_SM}px {theme.PADDING_MD}px;'>{c}</td>"
            for c in row)
        body += "</tr>"
    return (f"<table style='border-collapse:collapse;width:100%;margin:{theme.MARGIN_MD}px 0;'>"
            f"<thead><tr style='background:{theme.BG_MEDIUM};'>{th}</tr></thead>"
            f"<tbody>{body}</tbody></table>")


def _wrap(*parts):
    # Drop color from body — comes from the HTML Content widget editor stylesheet.
    return (f"<html><body style='background:{theme.BG_DARK};"
            f"font-size:{theme.FONT_SIZE_NORMAL}px;"
            f"padding:{theme.PADDING_MD}px;'>{''.join(parts)}</body></html>")


# ─── Page content builders ────────────────────────────────────────────────────

def _cli_reference_html():
    rows_flags = [
        [_code("--print / -p"), "Non-interactive, print response and exit"],
        [_code("--output-format"), "Output format: text | json | stream-json"],
        [_code("--input-format"), "Input format: text | stream-json"],
        [_code("--permission-mode"), "default | acceptEdits | plan | auto | dontAsk | bypassPermissions | manual"],
        [_code("--dangerously-skip-permissions"), "Skip permission prompts (sandboxed automation only)"],
        [_code("--allow-dangerously-skip-permissions"), "Add bypassPermissions to the Shift+Tab cycle without activating it"],
        [_code("--model &lt;alias|id&gt;"), "Model for this session (aliases: sonnet, opus, haiku, fable)"],
        [_code("--effort &lt;level&gt;"), "Reasoning effort: low | medium | high | xhigh | max | ultracode"],
        [_code("--fallback-model &lt;list&gt;"), "Backup model(s) when the primary is overloaded"],
        [_code("--settings &lt;file|json&gt;"), "Apply settings for one session (above user/project/local)"],
        [_code("--setting-sources &lt;list&gt;"), "Restrict setting sources loaded: user,project,local"],
        [_code("--continue / -c"), "Resume the most recent conversation in this directory"],
        [_code("--resume / -r [session]"), "Resume a session by ID or name (picker if omitted)"],
        [_code("--fork-session"), "On resume, start a new session ID instead of reusing it"],
        [_code("--from-pr &lt;num&gt;"), "Filter the session picker to PR-linked sessions"],
        [_code("--name / -n &lt;name&gt;"), "Name the session for later resume"],
        [_code("--session-id &lt;uuid&gt;"), "Use a specific session ID (must be a valid UUID)"],
        [_code("--worktree [name]"), "Create a git worktree and start Claude in it"],
        [_code("--add-dir &lt;path&gt;"), "Grant file access to additional directories"],
        [_code("--agents &lt;json&gt;"), "Define subagents dynamically (JSON object keyed by name)"],
        [_code("--agent &lt;name&gt;"), "Run the current session as a named agent"],
        [_code("--system-prompt &lt;text&gt;"), "Replace the entire system prompt"],
        [_code("--system-prompt-file &lt;path&gt;"), "Replace the system prompt from a file"],
        [_code("--append-system-prompt &lt;text&gt;"), "Append text to the default system prompt"],
        [_code("--append-system-prompt-file &lt;path&gt;"), "Append system prompt text from a file"],
        [_code("--allowedTools"), "Tools that run without a permission prompt"],
        [_code("--disallowedTools"), "Deny rules for tools"],
        [_code("--max-turns"), "Maximum agentic turns (print mode only)"],
        [_code("--max-budget-usd &lt;amount&gt;"), "Cap API spend for a -p run"],
        [_code("--verbose"), "Show detailed tool output"],
        [_code("--debug[=categories]"), "Debug logging, e.g. --debug=mcp,startup"],
        [_code("--mcp-config &lt;file|json&gt;"), "Load additional MCP servers from a file or string"],
        [_code("--strict-mcp-config"), "Use only MCP servers from --mcp-config"],
        [_code("--safe-mode"), "Start with all customizations disabled"],
        [_code("--bare"), "Minimal mode: skip auto-discovery of hooks/skills/commands"],
        [_code("--version"), "Print version and exit"],
    ]
    rows_subcmds = [
        [_code("claude"), "Start interactive REPL session"],
        [_code("claude -p &quot;prompt&quot;"), "Non-interactive single prompt"],
        [_code("claude -c"), "Continue most recent session"],
        [_code("claude --resume [session]"), "Resume by ID/name, or open the picker"],
        [_code("claude --worktree [name]"), "Create worktree session"],
        [_code("claude --cloud &quot;prompt&quot;"), "Create/queue a web session on claude.ai"],
        [_code("claude update"), "Update Claude Code to latest version"],
        [_code("claude install [version]"), "Install/reinstall the native binary"],
        [_code("claude doctor"), "Print installation + settings diagnostics"],
        [_code("claude mcp"), "Configure MCP servers (add/list/remove/get)"],
        [_code("claude auth login|logout|status"), "Manage Anthropic account sign-in"],
        [_code("claude setup-token"), "Generate a long-lived OAuth token for CI"],
        [_code("claude remote-control"), "Start Remote Control host"],
        [_code("claude plugin init &lt;name&gt;"), "Scaffold a skills-directory plugin"],
        [_code("claude plugin install &lt;name&gt;@&lt;marketplace&gt;"), "Install a plugin"],
        [_code("claude plugin uninstall &lt;name&gt;@&lt;marketplace&gt;"), "Uninstall a plugin"],
        [_code("claude plugin enable / disable &lt;name&gt;"), "Toggle an installed plugin"],
        [_code("claude plugin marketplace add &lt;src&gt;"), "Register a marketplace"],
        [_code("claude plugin validate &lt;path&gt;"), "Validate a plugin (--strict for warnings)"],
        [_code("claude auto-mode defaults|config|reset"), "Inspect / reset the auto-mode classifier"],
    ]
    return _wrap(
        _h(1, "CLI Reference"),
        _h(2, "Flags"),
        _table(["Flag", "Description"], rows_flags),
        _h(2, "Commands"),
        _table(["Command", "Description"], rows_subcmds),
        _h(2, "Config &amp; Settings"),
        _p("There is no <code>claude config</code> subcommand. Change settings by editing the "
           "settings JSON files, the in-session " + _code("/config") + " menu "
           "(" + _code("/config key=value") + "), or " + _code("--settings '{...}'") + " for one session. "
           "Global-config keys (autoConnectIde, diffTool, …) live in <code>~/.claude.json</code>."),
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
        _p("Thinking is adaptive — Claude decides when and how much. Force it on with the "
           + _code("alwaysThinkingEnabled") + " setting, raise the ceiling with "
           + _code("/effort xhigh|max") + ", or include the word <b>ultrathink</b> anywhere in a "
           "prompt to maximise thinking for that one turn."),
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
        _pre("Bash                  # all bash commands (bare name = remove tool as deny)\n"
             "Bash(npm run *)       # prefix match — put the * after the subcommand\n"
             "Bash(npm test)        # exact command\n"
             "Bash(ls:*)            # :* suffix == trailing ' *'\n"
             "Read(./.env)          # read a path (relative to cwd)\n"
             "Read(~/Documents/**)  # ~ = home;  //abs = filesystem root\n"
             "Edit(src/**)          # file writes are checked against Edit(), not Write()\n"
             "WebFetch(domain:github.com)\n"
             "mcp__memory__*        # allow-glob: only after a literal mcp__<server>__ prefix\n"
             "mcp__*                # deny/ask only: every MCP tool"),
        _p("Note: <code>Bash(command:...)</code>, and path rules on <code>Write</code>, "
           "<code>NotebookEdit</code>, or <code>Glob</code>, are accepted but never enforced "
           "(Claude Code warns at startup). Use <code>Bash(prefix *)</code>, "
           "<code>Edit(path)</code>, and <code>Read(path)</code> instead."),
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


def _model_info_html():
    return _wrap(
        _h(1, "Model Information"),
        _h(2, "Available Models"),
        _table(["Alias", "Model ID", "Description"],
               [["sonnet", "claude-sonnet-5", "Balanced default for coding"],
                ["opus", "claude-opus-5", "Deepest reasoning — architecture, hard problems"],
                ["fable", "claude-fable-5", "Most capable — long-horizon agentic work"],
                ["haiku", "claude-haiku-4-5-20251001", "Fast &amp; cheap — worker / subagents"],
                ["opusplan", "—", "Opus in Plan mode, Sonnet in execution"]]),
        _h(2, "Selecting a Model"),
        _pre("claude --model opus                 # one session\n"
             "/model sonnet                       # in session, saves as default\n"
             "/model                              # open the picker\n"
             "export ANTHROPIC_MODEL=sonnet       # session override\n"
             "export ANTHROPIC_DEFAULT_MODEL=opus # default for new sessions only\n"
             '# settings.json:  { "model": "sonnet" }'),
        _p("Add " + _code("[1m]") + " for the 1M context window where it isn't default, e.g. "
           + _code("/model opus[1m]") + ". " + _code("fallbackModel") + " sets overload backups; "
           + _code("availableModels") + " + " + _code("enforceAvailableModels") + " restrict choices."),
        _h(2, "Effort Levels"),
        _table(["Level", "Use Case"],
               [["low", "Fast, latency-sensitive tasks; subagents"],
                ["medium", "Cost-sensitive work"],
                ["high", "Balanced intelligence / cost"],
                ["xhigh", "Deep reasoning — Claude Code's default"],
                ["max", "Correctness over cost (session-only)"],
                ["ultracode", "xhigh + dynamic workflows (session-only)"]]),
        _p("Change with " + _code("/effort &lt;level&gt;") + ", " + _code("claude --effort &lt;level&gt;") +
           ", the " + _code("effortLevel") + " setting, or " + _code("CLAUDE_CODE_EFFORT_LEVEL") + ". "
           "The fixed 'budget tokens' model is gone — effort replaces it."),
        _h(2, "Controlling Thinking"),
        _p("Thinking is adaptive on current models — Claude decides when and how much. "
           "Setting key: " + _code("alwaysThinkingEnabled") + ". Show summaries with "
           + _code("showThinkingSummaries") + ". The word <b>ultrathink</b> anywhere in a prompt "
           "maximises thinking for that turn."),
        _h(2, "Context Window"),
        _table(["Model", "Context Window"],
               [["Sonnet 5 / Opus 5 / Fable 5", "1M tokens (native)"],
                ["Haiku 4.5", "200K tokens"]]),
        _p("Claude Code tracks context usage and auto-compacts (" + _code("autoCompactEnabled") +
           ", " + _code("autoCompactWindow") + "). Use " + _code("/compact") + " to summarise, "
           + _code("/context") + " to see the map, " + _code("/clear") + " to start fresh."),
        _h(2, "Fast Mode"),
        _p("Toggle with " + _code("/fast") + " (also " + _code("fastMode") + " setting). Runs the same "
           "Opus model with faster output — it does <b>not</b> downgrade to a smaller model. "
           "Research preview; availability depends on your plan/model."),
        _h(2, "Cost & Token Tracking"),
        _p("Claude Code tracks token usage per session. Use the Usage &amp; Analytics tab to view "
           "historical usage, costs, and per-project breakdowns.<br>"
           "Set " + _code("ANTHROPIC_API_KEY") + " environment variable for API access."),
    )


def _ultraplan_html():
    return _wrap(
        _h(1, "Deep Planning &amp; Thinking"),
        _p("There is no built-in <code>/ultraplan</code> or <code>/ultrathink</code> command. "
           "Deep planning in Claude Code comes from three real mechanisms:"),
        _h(2, "1. Plan mode"),
        _p("Claude explores with reads and read-only shell, then writes a plan without touching "
           "source. Enter it with <b>Shift+Tab</b> (cycle to Plan) or "
           + _code("claude --permission-mode plan") + ". Press <b>Ctrl+G</b> to open the plan in your editor."),
        _h(2, "2. The 'ultrathink' keyword"),
        _p("Include the word <b>ultrathink</b> anywhere in a prompt to maximise thinking depth for "
           "that one turn. Thinking is adaptive otherwise — Claude decides when and how much."),
        _h(2, "3. Effort level"),
        _table(["Level", "Effect"],
               [["high", "Balanced intelligence / cost"],
                ["xhigh", "Deep reasoning — Claude Code's default"],
                ["max", "Correctness over cost (current session only)"],
                ["ultracode", "xhigh + dynamic workflows (current session only)"]]),
        _p("Set with " + _code("/effort max") + ", " + _code("claude --effort xhigh") + ", or the "
           + _code("effortLevel") + " setting."),
        _h(2, "Related settings"),
        _table(["Setting", "Effect"],
               [["alwaysThinkingEnabled", "Force extended thinking on"],
                ["showThinkingSummaries", "Show readable summaries of the reasoning"],
                ["effortLevel", "Persistent default effort level"]]),
    )


def _sandboxing_html():
    return _wrap(
        _h(1, "Sandboxing"),
        _h(2, "What is Sandboxing?"),
        _p("Sandboxing isolates Claude Code's bash command execution in a containerised environment, "
           "preventing unintended changes to the host system."),
        _h(2, "Bash sandboxing (settings)"),
        _p("Sandboxing is configured through the " + _code("sandbox") + " key in a settings file, "
           "not a CLI flag. Turn it on with " + _code('"sandbox": {"enabled": true}') + " and tune "
           "it with " + _code("sandbox.filesystem.allowWrite/denyRead") + ", "
           + _code("sandbox.network.allowedDomains") + ", " + _code("sandbox.excludedCommands") + ", etc. "
           "See the settings reference for the full <code>sandbox.*</code> tree."),
        _p("On macOS it uses the built-in " + _code("sandbox-exec") + " (Seatbelt); on Linux it uses "
           "bubblewrap (" + _code("bwrap") + ")."),
        _h(2, "Docker / container isolation"),
        _p("For a hard boundary, run Claude Code inside a container and use "
           + _code("--permission-mode bypassPermissions") + " (or " + _code("--dangerously-skip-permissions") +
           ") only there. Install with " + _code("npm install -g @anthropic-ai/claude-code") +
           " or the native installer."),
        _h(2, "Permission Modes with Sandboxing"),
        _table(["Mode", "Sandboxing Benefit"],
               [["bypassPermissions", "Requires container/VM — sandboxing provides the safety boundary"],
                ["acceptEdits", "File edits auto-approved; sandboxing limits blast radius"],
                ["default", "Prompts on dangerous ops; sandboxing adds second layer"]]),
        _h(2, "Best Practices"),
        _p("• Always use sandboxing in CI/CD pipelines<br>"
           "• Use " + _code("bypassPermissions") + " only inside containers<br>"
           "• Mount only necessary directories as volumes<br>"
           "• Use read-only mounts for reference files"),
    )


def _context_window_html():
    return _wrap(
        _h(1, "Context Window"),
        _h(2, "What is the Context Window?"),
        _p("The context window is the total number of tokens Claude can see at once — "
           "including the conversation history, file contents, tool outputs, and system prompts."),
        _h(2, "Token Limits"),
        _table(["Model", "Context Window"],
               [["claude-sonnet-5", "1,000,000 tokens (native)"],
                ["claude-opus-5", "1,000,000 tokens (native)"],
                ["claude-fable-5", "1,000,000 tokens (native)"],
                ["claude-haiku-4-5", "200,000 tokens"]]),
        _p("Force the 1M window where it isn't default with the " + _code("[1m]") +
           " suffix, e.g. " + _code("/model sonnet[1m]") + "."),
        _h(2, "Compaction"),
        _pre("/compact\n/compact Focus on the authentication changes\n/clear    # start fresh"),
        _p(_code("/compact") + " summarises the current conversation into a shorter form, "
           "freeing context space while preserving key information.<br>"
           "Hook: " + _code("PreCompact") + " fires before, " + _code("PostCompact") + " fires after."),
        _h(2, "Context Pressure Indicators"),
        _p("Claude Code warns when approaching context limits. Signs of high context usage:<br>"
           "• Responses become shorter or less detailed<br>"
           "• Tool calls start failing due to token limits<br>"
           "• Status line shows high token count"),
        _h(2, "Managing Context"),
        _p("• Use " + _code("/compact") + " regularly in long sessions<br>"
           "• Avoid reading very large files unnecessarily<br>"
           "• Use focused " + _code("Glob") + " and " + _code("Grep") + " instead of reading entire directories<br>"
           "• Break large tasks into smaller sub-conversations"),
    )


def _headless_html():
    return _wrap(
        _h(1, "Headless / Non-Interactive Mode"),
        _h(2, "Overview"),
        _p("Headless mode runs Claude Code non-interactively — useful for CI/CD, scripting, and automation."),
        _h(2, "Basic Usage"),
        _pre('# Single prompt, print and exit\nclaude -p "Fix the tests"\n\n'
             '# Pipe input\ncat error.log | claude -p "Explain this error"\n\n'
             '# From a file\nclaude -p "$(cat prompt.txt)"\n\n'
             '# JSON output for machine parsing\nclaude -p "List all functions" --output-format json'),
        _h(2, "Key Flags"),
        _table(["Flag", "Description"],
               [["-p / --print", "Non-interactive, print response and exit"],
                ["--output-format text", "Plain text output (default for -p)"],
                ["--output-format json", "Machine-readable JSON output"],
                ["--output-format stream-json", "Stream JSON events as they arrive"],
                ["--json-schema '<schema>'", "Constrain -p output to a JSON Schema"],
                ["--permission-prompt-tool mcp__s__t", "Delegate permission prompts to an MCP tool"],
                ["--allowedTools <list>", "Tools that run without a permission prompt"],
                ["--disallowedTools <list>", "Tools to block"],
                ["--max-turns <n>", "Limit agentic turns (default: unlimited)"],
                ["--max-budget-usd <amount>", "Cap total API spend for the run"]]),
        _h(2, "CI/CD Example"),
        _pre('# GitHub Actions step\n- name: Run Claude Code review\n'
             '  run: claude -p "Review the changes in this PR" --output-format json \\\n'
             '    --allowedTools Bash,Read,Grep'),
        _h(2, "Exit Codes"),
        _table(["Code", "Meaning"],
               [["0", "Success"],
                ["1", "General error"],
                ["2", "Blocked by hook (stderr shown to user)"]]),
    )


def _telemetry_html():
    return _wrap(
        _h(1, "OpenTelemetry / Telemetry"),
        _h(2, "Overview"),
        _p("Claude Code supports OpenTelemetry (OTEL) for tracing and observability. "
           "Enable it to send spans to any OTLP-compatible backend (Jaeger, Zipkin, Datadog, etc.)."),
        _h(2, "Configuration"),
        _pre('export CLAUDE_CODE_ENABLE_TELEMETRY=1\n'
             'export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318\n'
             'export OTEL_EXPORTER_OTLP_HEADERS="x-api-key=YOUR_KEY"'),
        _h(2, "Environment Variables"),
        _table(["Variable", "Description"],
               [["CLAUDE_CODE_ENABLE_TELEMETRY", "Set to 1 to enable OTEL tracing"],
                ["OTEL_EXPORTER_OTLP_ENDPOINT", "OTLP receiver endpoint URL"],
                ["OTEL_EXPORTER_OTLP_HEADERS", "Auth headers (key=value,key=value)"],
                ["OTEL_SERVICE_NAME", "Service name for traces (default: claude-code)"],
                ["OTEL_RESOURCE_ATTRIBUTES", "Additional trace attributes"]]),
        _h(2, "What is Traced"),
        _p("• Every tool call (Bash, Read, Edit, etc.)<br>"
           "• LLM API requests and responses (token counts, model, latency)<br>"
           "• Session start/end events<br>"
           "• Hook executions<br>"
           "• MCP server calls"),
        _h(2, "Usage Analytics"),
        _p("Built-in usage analytics (token counts, cost estimates) are shown in the "
           "Usage &amp; Analytics tab. This is separate from OTEL and always enabled."),
    )


def _ide_integration_html():
    return _wrap(
        _h(1, "IDE Integration"),
        _h(2, "VS Code Extension"),
        _pre("code --install-extension anthropic.claude-code"),
        _p("Or search " + _code("Claude Code") + " in the VS Code Extensions marketplace."),
        _h(2, "VS Code Features"),
        _p("• Inline diff review directly in the editor<br>"
           "• File open/close triggered by Claude<br>"
           "• Terminal integration — Claude runs in VS Code terminal<br>"
           "• Status bar showing Claude Code session state<br>"
           "• Multi-root workspace support"),
        _h(2, "JetBrains Plugin"),
        _pre("# Install via JetBrains Marketplace\n# Search: Claude Code"),
        _p("Supports IntelliJ IDEA, PyCharm, WebStorm, GoLand, Rider, and all JetBrains IDEs."),
        _h(2, "JetBrains Features"),
        _p("• Diff view in IDE diff tool<br>"
           "• File navigation triggered by Claude<br>"
           "• Terminal panel integration"),
        _h(2, "Auto-Install"),
        _p("Set " + _code("autoInstallIdeExtension: true") + " in settings.json to automatically "
           "install/update the IDE extension when Claude Code starts."),
        _h(2, "Settings"),
        _table(["Setting", "Type", "Description"],
               [["autoInstallIdeExtension", "boolean", "Auto-install/update IDE extension on startup"]]),
    )


def _github_actions_html():
    return _wrap(
        _h(1, "GitHub Actions / CI Integration"),
        _h(2, "Overview"),
        _p("Claude Code can run in GitHub Actions workflows for automated code review, "
           "test generation, documentation, and more."),
        _h(2, "Basic Workflow"),
        _pre('name: Claude Code Review\non:\n  pull_request:\n\njobs:\n  review:\n    runs-on: ubuntu-latest\n'
             '    steps:\n      - uses: actions/checkout@v4\n      - name: Install Claude Code\n'
             '        run: npm install -g @anthropic-ai/claude-code\n      - name: Run review\n'
             '        env:\n          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}\n'
             '        run: |\n          claude -p "Review this PR for bugs and security issues" \\\n'
             '            --output-format json --allowedTools Read,Grep,Glob'),
        _p("Anthropic also ships an official <code>anthropics/claude-code-action</code> GitHub "
           "Action — prefer it over a hand-rolled npm install for CI."),
        _h(2, "Permission Modes in CI"),
        _table(["Mode", "Use Case"],
               [["--dangerously-skip-permissions", "Full automation in isolated containers (not recommended in shared runners)"],
                ["--allowedTools", "Whitelist specific tools for safety"],
                ["--disallowedTools", "Block dangerous tools (Bash, Edit, Write)"]]),
        _h(2, "Secrets"),
        _p("Store " + _code("ANTHROPIC_API_KEY") + " as a GitHub Actions secret. "
           "Never hardcode API keys in workflows."),
        _h(2, "Best Practices"),
        _p("• Use read-only tools in PR review jobs (" + _code("--allowedTools Read,Grep,Glob") + ")<br>"
           "• Pin Claude Code version for reproducibility<br>"
           "• Cache npm install between runs<br>"
           "• Use " + _code("--max-turns") + " to limit API costs<br>"
           "• Use " + _code("--output-format json") + " for structured results"),
    )


def _memory_system_html():
    return _wrap(
        _h(1, "Memory System"),
        _h(2, "Memory Hierarchy (Highest → Lowest)"),
        _p("<ol style='line-height:1.8;margin:0;padding-left:1.4em;'>"
           "<li><b>Enterprise Policy:</b> " + _code("/etc/claude/CLAUDE.md") + "</li>"
           "<li><b>User Memory:</b> " + _code("~/.claude/CLAUDE.md") + " — applies to all projects</li>"
           "<li><b>Project Memory:</b> " + _code("./CLAUDE.md") + " — in git, shared with team</li>"
           "<li><b>Local Project:</b> " + _code("./CLAUDE.local.md") + " — personal, gitignored</li>"
           "</ol>"),
        _p("<b>Quick add:</b> prefix prompt with " + _code("#") + " to save instantly to memory.&nbsp;&nbsp;"
           "<b>Edit:</b> " + _code("/memory") + " opens CLAUDE.md in editor."),
        _h(2, "Auto Memory"),
        _p("When " + _code("autoMemoryEnabled: true") + " in settings, Claude Code automatically "
           "extracts key information to " + _code("autoMemoryDirectory") +
           " (default: " + _code("~/.claude/memory/") + ")."),
        _h(2, "Context Compaction"),
        _p("<ul style='line-height:1.8;margin:0;padding-left:1.4em;'>"
           "<li>" + _code("/compact") + " — compact history to free context window</li>"
           "<li>" + _code("/compact &lt;instructions&gt;") + " — compact with focus</li>"
           "<li>Hook: " + _code("PostCompact") + " fires after compaction</li>"
           "</ul>"),
        _h(2, "Conversation Storage"),
        _p("<ul style='line-height:1.8;margin:0;padding-left:1.4em;'>"
           "<li><b>Global history:</b> " + _code("~/.claude/history.jsonl") + "</li>"
           "<li><b>Per-project:</b> " + _code("~/.claude/projects/&lt;encoded-path&gt;/&lt;uuid&gt;.jsonl") + "</li>"
           "<li><b>Resume:</b> " + _code("claude -c") + " (last) or " + _code("claude -r &lt;uuid&gt;") + "</li>"
           "</ul>"),
        _h(2, "Project Memories"),
        _p("Per-project memory files live at "
           + _code("~/.claude/projects/&lt;encoded-path&gt;/memory/") + ". "
           "View them per-project in <b>Project Config → Memories</b>."),
        _h(2, "File History"),
        _p("Before every Write or Edit, Claude Code saves a pre-edit snapshot to "
           + _code("~/.claude/file-history/&lt;session-uuid&gt;/&lt;hash&gt;@v&lt;n&gt;") + ". "
           "Browse per-project in <b>Project Config → File History</b>."),
        _h(2, "Shell Snapshots"),
        _p("Bash state snapshots saved to " + _code("~/.claude/shell-snapshots/") +
           " when Claude Code captures the shell environment."),
    )


# ─── Main Documentation Tab ───────────────────────────────────────────────────

class DocumentationTab(QWidget):
    """Tab grouping all static reference documentation with search."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._header = None
        self._pages: list[DocPage] = []
        self._themed_widgets: list = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header
        self._header = QLabel("Documentation")
        self._header.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};"
        )
        layout.addWidget(self._header)

        # Subtab container
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs, 1)

        # Each entry: (html_callable, url, tab_label)
        _page_defs = [
            (_cli_reference_html,    "https://code.claude.com/docs/en/cli-reference",    "⌨️ CLI Reference"),
            (_workflows_html,        "https://code.claude.com/docs/en/common-workflows", "🔄 Workflows"),
            (_prompts_html,          "https://code.claude.com/docs/en/memory",           "💬 Prompts & Memory"),
            (_commands_html,         "https://code.claude.com/docs/en/commands",         "/ Commands"),
            (_tools_ref_html,        "https://code.claude.com/docs/en/tools-reference",  "🔧 Tools Ref"),
            (_shortcuts_html,        "https://code.claude.com/docs/en/interactive-mode", "⌨️ Shortcuts"),
            (_remote_html,           "https://code.claude.com/docs/en/remote-control",   "🌐 Remote"),
            (_chrome_html,           "https://code.claude.com/docs/en/chrome",           "🔵 Chrome"),
            (_computer_use_html,     "https://code.claude.com/docs/en/computer-use",     "🖥️ Computer Use"),
            (_plugins_ref_html,      "https://code.claude.com/docs/en/plugins-reference","🧩 Plugins Ref"),
            (_model_info_html,       "https://code.claude.com/docs/en/model-config",     "🤖 Model Info"),
            (_ultraplan_html,        "https://code.claude.com/docs/en/model-config",     "🧠 Ultraplan"),
            (_sandboxing_html,       "https://code.claude.com/docs/en/sandboxing",       "🔒 Sandboxing"),
            (_context_window_html,   "https://code.claude.com/docs/en/context-window",   "📐 Context Window"),
            (_headless_html,         "https://code.claude.com/docs/en/headless",         "🤖 Headless"),
            (_telemetry_html,        "https://code.claude.com/docs/en/monitoring-usage", "📡 Telemetry"),
            (_ide_integration_html,  "https://code.claude.com/docs/en/vs-code",          "🖥️ IDE Integration"),
            (_github_actions_html,   "https://code.claude.com/docs/en/github-actions",   "🔁 GitHub Actions"),
            (_memory_system_html,    "https://code.claude.com/docs/en/memory",            "🧠 Memory"),
        ]
        for fn, url, label in _page_defs:
            page = DocPage(fn, url)
            self._pages.append(page)
            self._tabs.addTab(page, label)

        agent_teams = AgentTeamsTab(None, None)
        self._themed_widgets.append(agent_teams)
        self._tabs.addTab(agent_teams, "👥 Agent Teams")

        remote_control = RemoteControlTab(None, None)
        self._themed_widgets.append(remote_control)
        self._tabs.addTab(remote_control, "🌐 Remote Control")

    def apply_theme(self):
        """Refresh header style and regenerate all HTML pages with current theme."""
        if self._header:
            self._header.setStyleSheet(
                f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};"
            )
        for page in self._pages:
            page.apply_theme()
        for w in self._themed_widgets:
            w.apply_theme()
