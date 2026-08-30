"""
Shared hooks constants and dialog — imported by all three hooks tabs.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextBrowser
)
from utils import theme

# ── Grouped event tree ────────────────────────────────────────────────────────
# Each key is a group label; the list is the ordered events in that group.

HOOK_EVENT_GROUPS: dict[str, list[str]] = {
    "🔧  Tool Lifecycle": [
        "PreToolUse",
        "PostToolUse",
        "PostToolUseFailure",
        "PostToolBatch",
    ],
    "💬  User Interaction": [
        "UserPromptSubmit",
        "UserPromptExpansion",
        "MessageDisplay",
        "Notification",
        "Elicitation",
        "ElicitationResult",
    ],
    "⏹  Agent / Stop": [
        "Stop",
        "StopFailure",
        "SubagentStart",
        "SubagentStop",
        "TeammateIdle",
    ],
    "📋  Context & Memory": [
        "PreCompact",
        "PostCompact",
        "InstructionsLoaded",
    ],
    "🔒  Permissions": [
        "PermissionRequest",
        "PermissionDenied",
    ],
    "✅  Tasks": [
        "TaskCreated",
        "TaskCompleted",
    ],
    "🧠  Model": [
        "PreModelSwitch",
        "PostModelSwitch",
    ],
    "🟢  Session": [
        "SessionStart",
        "SessionEnd",
        "Setup",
    ],
    "📁  Environment": [
        "CwdChanged",
        "DirectoryAdded",
        "FileChanged",
        "ConfigChange",
    ],
    "🌿  Worktrees": [
        "WorktreeCreate",
        "WorktreeRemove",
    ],
}

# Flat ordered list derived from groups — replaces HOOK_EVENTS in each tab.
HOOK_EVENTS: list[str] = [
    event for events in HOOK_EVENT_GROUPS.values() for event in events
]

# ── Handler types & templates (shared by the project & user hooks subtabs) ────

HOOK_HANDLER_TYPES: list[str] = ["command", "http", "mcp_tool", "prompt", "agent"]

HOOK_TEMPLATES: dict[str, dict] = {
    "command": {
        "type": "command",
        "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/hook.sh",
        "timeout": 600,
        "async": False,
        "statusMessage": "",
    },
    "http": {
        "type": "http",
        "url": "https://example.com/webhook",
        "headers": {"Content-Type": "application/json"},
        "allowedEnvVars": [],
        "timeout": 30,
    },
    "mcp_tool": {
        "type": "mcp_tool",
        "server": "my_server",
        "tool": "validate",
        "input": {},
        "timeout": 60,
    },
    "prompt": {
        "type": "prompt",
        "model": "haiku",
        "prompt": "Should this action proceed? Reply with only yes or no.",
        "timeout": 30,
    },
    "agent": {
        "type": "agent",
        "prompt": "Review this action: $ARGUMENTS",
        "timeout": 60,
    },
}


# ── Reference dialog ──────────────────────────────────────────────────────────

class HookReferenceDialog(QDialog):
    """Full hooks reference — replaces the inline info browser."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hooks Reference")
        self.setMinimumSize(700, 640)
        self.resize(760, 720)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setStyleSheet(f"""
            QTextBrowser {{
                border-radius: 4px;
                padding: 10px;
                font-size: {theme.FONT_SIZE_SMALL}px;
            }}
        """)
        browser.setHtml(self._build_html())
        layout.addWidget(browser, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    @staticmethod
    def _build_html() -> str:
        bg  = theme.BG_MEDIUM
        fg  = theme.FG_PRIMARY
        fg2 = theme.FG_SECONDARY
        acc = theme.ACCENT_PRIMARY

        return f"""
        <html><body style="color:{fg}; font-family:sans-serif; font-size:{theme.FONT_SIZE_SMALL}px;">

        <h2 style="color:{acc}; margin-bottom:4px;">Hooks Reference</h2>
        <p style="color:{fg2}; margin-top:0;">Shell commands, HTTP calls, prompts or subagents that run
        automatically in response to Claude Code events.</p>
        <hr style="border:1px solid {bg};">

        <h3 style="color:{acc};">🔧 Tool Lifecycle</h3>
        <p><b>PreToolUse</b> — Before a tool executes (matcher: tool name).
           Exit&nbsp;2&nbsp;+&nbsp;stderr blocks the tool and sends the message to Claude.
           Output: <code>permissionDecision</code> (allow|deny|bypassPermissions),
           <code>updatedInput</code>, <code>additionalContext</code>.</p>
        <p><b>PostToolUse</b> — After a tool succeeds.
           Exit&nbsp;2 is non-blocking (tool already ran).
           Output key: <code>hookSpecificOutput</code>.</p>
        <p><b>PostToolUseFailure</b> — After a tool call fails.</p>
        <p><b>PostToolBatch</b> — After a batch of parallel tool calls resolves (no matcher). Can block.</p>

        <h3 style="color:{acc}; margin-top:12px;">💬 User Interaction</h3>
        <p><b>UserPromptSubmit</b> — Before a user prompt is processed (no matcher).
           Exit&nbsp;2 blocks the prompt. Plain stdout is added as context; output key: <code>additionalContext</code>.</p>
        <p><b>UserPromptExpansion</b> — When a typed command expands into a prompt (matcher: command name). Can block.</p>
        <p><b>MessageDisplay</b> — While assistant message text is displayed (no matcher).</p>
        <p><b>Notification</b> — When Claude Code sends a notification (matcher: notification type).</p>
        <p><b>Elicitation</b> / <b>ElicitationResult</b> — Around an MCP server's request for user input (matcher: MCP server name).</p>

        <h3 style="color:{acc}; margin-top:12px;">⏹ Agent / Stop</h3>
        <p><b>Stop</b> — Agent finishes a response turn.  Exit&nbsp;2 prevents stopping.</p>
        <p><b>StopFailure</b> — Turn ends due to an API error.</p>
        <p><b>SubagentStart</b> — A subagent starts executing.</p>
        <p><b>SubagentStop</b> — A subagent finishes.  Output: <code>hookSpecificOutput</code>.</p>
        <p><b>TeammateIdle</b> — An agent team member becomes idle.</p>

        <h3 style="color:{acc}; margin-top:12px;">📋 Context &amp; Memory</h3>
        <p><b>PreCompact</b> — Before context compaction.  Output key: <code>additionalContext</code>.</p>
        <p><b>PostCompact</b> — After context compaction completes.</p>
        <p><b>InstructionsLoaded</b> — After CLAUDE.md files are loaded.  Exit codes ignored.</p>

        <h3 style="color:{acc}; margin-top:12px;">🔒 Permissions</h3>
        <p><b>PermissionRequest</b> — When a tool call needs a permission decision (matcher: tool name).
           Output key: <code>permissionDecision</code> (allow | deny | bypassPermissions).  Exit codes ignored.</p>
        <p><b>PermissionDenied</b> — When auto mode denies a tool call (matcher: tool name).  Exit codes ignored.</p>

        <h3 style="color:{acc}; margin-top:12px;">✅ Tasks</h3>
        <p><b>TaskCreated</b> — A task is created (no matcher). Can block.</p>
        <p><b>TaskCompleted</b> — A task is marked complete (no matcher). Can block.</p>

        <h3 style="color:{acc}; margin-top:12px;">🧠 Model</h3>
        <p><b>PreModelSwitch</b> — Before a model switch (matcher: canonical model name). Can block.</p>
        <p><b>PostModelSwitch</b> — After the session model changes. Plain stdout added as context.</p>

        <h3 style="color:{acc}; margin-top:12px;">🟢 Session</h3>
        <p><b>SessionStart</b> — Session begins or resumes (matcher: startup | resume | clear | compact | fork).
           Plain stdout added as context.</p>
        <p><b>SessionEnd</b> — Session ends (matcher: clear | resume | logout | prompt_input_exit | other).</p>
        <p><b>Setup</b> — With <code>--init</code> / <code>--init-only</code> / <code>--maintenance</code> (matcher: init | maintenance).</p>

        <h3 style="color:{acc}; margin-top:12px;">📁 Environment</h3>
        <p><b>CwdChanged</b> — Working directory changes (no matcher).</p>
        <p><b>DirectoryAdded</b> — A working directory is added mid-session (matcher: slash_command | register_repo_root).</p>
        <p><b>FileChanged</b> — A watched file changes on disk (matcher: literal filenames, e.g. <code>.env|.envrc</code>).</p>
        <p><b>ConfigChange</b> — A config file changes (matcher: user_settings | project_settings | local_settings | policy_settings | skills).</p>

        <h3 style="color:{acc}; margin-top:12px;">🌿 Worktrees</h3>
        <p><b>WorktreeCreate</b> — A git worktree is created.</p>
        <p><b>WorktreeRemove</b> — A git worktree is removed.</p>

        <hr style="border:1px solid {bg}; margin-top:16px;">

        <h3 style="color:{acc};">Handler Types</h3>
        <table cellspacing="0" cellpadding="4" style="width:100%;">
          <tr><td width="100"><b>command</b></td>
              <td>Run a shell command.  Event JSON is sent on stdin.
              Fields: <code>command</code>, <code>args</code>, <code>shell</code>, <code>timeout</code>.</td></tr>
          <tr><td><b>http</b></td>
              <td>POST JSON to a URL.  Fields: <code>url</code>, <code>headers</code>,
              <code>allowedEnvVars</code>, <code>timeout</code>.</td></tr>
          <tr><td><b>mcp_tool</b></td>
              <td>Call an MCP tool.  Fields: <code>server</code>, <code>tool</code>,
              <code>input</code>, <code>timeout</code>.</td></tr>
          <tr><td><b>prompt</b></td>
              <td>Claude model evaluates the action.
              Fields: <code>prompt</code>, <code>model</code>, <code>timeout</code>.</td></tr>
          <tr><td><b>agent</b></td>
              <td>Invoke a subagent.
              Fields: <code>prompt</code>, <code>timeout</code>.</td></tr>
        </table>

        <h3 style="color:{acc}; margin-top:12px;">Hook Fields</h3>
        <table cellspacing="0" cellpadding="4" style="width:100%;">
          <tr><td width="130"><b>type</b></td>
              <td>command | http | mcp_tool | prompt | agent</td></tr>
          <tr><td><b>timeout</b></td>
              <td>Seconds (defaults: command=600, http=30, mcp_tool=60, prompt=30, agent=60)</td></tr>
          <tr><td><b>async</b> / <b>asyncRewake</b></td>
              <td>Run without blocking Claude / wake Claude when it completes (default: false)</td></tr>
          <tr><td><b>statusMessage</b></td>
              <td>String shown in the UI while the hook runs</td></tr>
          <tr><td><b>once</b></td>
              <td>true/false — fire only once per session (skill/subagent hooks)</td></tr>
          <tr><td><b>if</b></td>
              <td>Per-handler argument matcher, e.g. <code>"Bash(git *)"</code></td></tr>
        </table>

        <h3 style="color:{acc}; margin-top:12px;">Matcher Syntax</h3>
        <p>Exact: <code>Bash</code>, <code>Edit,Write</code>, <code>Bash|Edit</code> &nbsp;·&nbsp;
           Regex (unanchored): <code>mcp__.*__write.*</code>, <code>^Edit$</code> &nbsp;·&nbsp;
           All: <code>*</code>, <code>""</code>, or omit.</p>

        <h3 style="color:{acc}; margin-top:12px;">Output Keys (stdout JSON)</h3>
        <table cellspacing="0" cellpadding="4" style="width:100%;">
          <tr><td width="180"><b>hookSpecificOutput</b></td>
              <td>Arbitrary data passed back to Claude</td></tr>
          <tr><td><b>updatedInput</b></td>
              <td>Modified tool input (PreToolUse only)</td></tr>
          <tr><td><b>additionalContext</b></td>
              <td>Extra context appended to Claude's context</td></tr>
          <tr><td><b>permissionDecision</b></td>
              <td>allow | deny | bypassPermissions (PreToolUse, PermissionRequest)</td></tr>
          <tr><td><b>retry</b></td>
              <td>true — ask Claude to retry the tool call</td></tr>
        </table>
        <p style="color:{fg2};">Wrap these in <code>hookSpecificOutput</code> with
        <code>"hookEventName": "&lt;event&gt;"</code>.</p>

        <h3 style="color:{acc}; margin-top:12px;">Exit Codes</h3>
        <table cellspacing="0" cellpadding="4" style="width:100%;">
          <tr><td width="60"><b>0</b></td><td>Success — hook output passed to Claude</td></tr>
          <tr><td><b>2</b></td>
              <td>Blocking error for PreToolUse / UserPromptSubmit — stderr sent to Claude.
              Non-blocking for PostToolUse (tool already ran).</td></tr>
          <tr><td>other</td><td>Non-blocking error; action proceeds. Valid JSON on stdout is still honored.
              (Exception: <code>WorktreeCreate</code> aborts on any nonzero exit.)</td></tr>
          <tr><td>—</td>
              <td>Exit codes ignored for: PermissionRequest, PermissionDenied, InstructionsLoaded</td></tr>
        </table>
        <p style="color:{fg2};">Events that honor exit 2 as blocking: PreToolUse, UserPromptSubmit,
        UserPromptExpansion, PreModelSwitch, Stop, SubagentStop, TeammateIdle, TaskCreated,
        TaskCompleted, PostToolBatch, ConfigChange.</p>

        <h3 style="color:{acc}; margin-top:12px;">Scope &amp; Precedence</h3>
        <p><b>User</b> (~/.claude/settings.json) — Global, applies to all projects.</p>
        <p><b>Project Shared</b> (.claude/settings.json) — Team-shared, committed to git.</p>
        <p><b>Project Local</b> (.claude/settings.local.json) — User-specific, gitignored.</p>
        <p>MCP tool pattern: <code>mcp__&lt;server&gt;__&lt;tool&gt;</code></p>

        <h3 style="color:{acc}; margin-top:12px;">Example</h3>
        <pre style="background:{bg}; padding:10px; border-radius:4px; font-size:11px;">{{
  "hooks": {{
    "PostToolUse": [{{
      "matcher": "Write|Edit",
      "hooks": [{{
        "type": "command",
        "command": "jq -r '.tool_input.file_path' | xargs -r black",
        "timeout": 30,
        "statusMessage": "Auto-formatting..."
      }}]
    }}],
    "PreToolUse": [{{
      "matcher": "Bash",
      "hooks": [{{
        "type": "command",
        "if": "Bash(rm *)",
        "command": "${{CLAUDE_PROJECT_DIR}}/.claude/hooks/guard.sh",
        "timeout": 10
      }}]
    }}]
  }}
}}</pre>
        <p style="color:{fg2};">Command hooks receive the event JSON on stdin — use <code>jq</code>
        to read fields such as <code>.tool_input.file_path</code>. There are no
        <code>$TOOL_*</code> substitutions.</p>

        </body></html>
        """
