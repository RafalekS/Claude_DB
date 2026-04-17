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
    ],
    "💬  User Interaction": [
        "UserPromptSubmit",
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
    "🟢  Session": [
        "SessionStart",
        "SessionEnd",
    ],
    "📁  Environment": [
        "CwdChanged",
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
        <p><b>PreToolUse</b> — Before a tool executes.
           Exit&nbsp;2&nbsp;+&nbsp;stderr blocks the tool and sends the message to Claude.
           Output key: <code>updatedInput</code> (modify the tool's input).</p>
        <p><b>PostToolUse</b> — After a tool succeeds.
           Exit&nbsp;2 is non-blocking (tool already ran).
           Output key: <code>hookSpecificOutput</code>.</p>
        <p><b>PostToolUseFailure</b> — After a tool call fails.</p>

        <h3 style="color:{acc}; margin-top:12px;">💬 User Interaction</h3>
        <p><b>UserPromptSubmit</b> — Before a user prompt is processed.
           Exit&nbsp;2 blocks the prompt. Output key: <code>additionalContext</code>.</p>
        <p><b>Notification</b> — When Claude Code sends a notification to the user.</p>
        <p><b>Elicitation</b> — When Claude needs to ask the user something interactively.</p>
        <p><b>ElicitationResult</b> — After an elicitation response is received.</p>

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
        <p><b>PermissionRequest</b> — Claude requests permission for an action.
           Output key: <code>permissionDecision</code> (allow | deny).  Exit codes ignored.</p>
        <p><b>PermissionDenied</b> — A permission was denied.  Exit codes ignored.</p>

        <h3 style="color:{acc}; margin-top:12px;">✅ Tasks</h3>
        <p><b>TaskCreated</b> — A TodoWrite task is created.</p>
        <p><b>TaskCompleted</b> — A TodoWrite task is marked complete.</p>

        <h3 style="color:{acc}; margin-top:12px;">🟢 Session</h3>
        <p><b>SessionStart</b> — Session begins (runs once at startup or resume).</p>
        <p><b>SessionEnd</b> — Session ends.</p>

        <h3 style="color:{acc}; margin-top:12px;">📁 Environment</h3>
        <p><b>CwdChanged</b> — Working directory changes.</p>
        <p><b>FileChanged</b> — A watched file changes on disk.</p>
        <p><b>ConfigChange</b> — Claude Code configuration file changes.</p>

        <h3 style="color:{acc}; margin-top:12px;">🌿 Worktrees</h3>
        <p><b>WorktreeCreate</b> — A git worktree is created.</p>
        <p><b>WorktreeRemove</b> — A git worktree is removed.</p>

        <hr style="border:1px solid {bg}; margin-top:16px;">

        <h3 style="color:{acc};">Handler Types</h3>
        <table cellspacing="0" cellpadding="4" style="width:100%;">
          <tr><td width="100"><b>command</b></td>
              <td>Run a shell command.  Event JSON is sent on stdin.</td></tr>
          <tr><td><b>http</b></td>
              <td>POST JSON to a URL.  Fields: <code>url</code>, <code>headers</code>,
              <code>allowedEnvVars</code>, <code>timeout</code>.</td></tr>
          <tr><td><b>prompt</b></td>
              <td>Claude model evaluates yes/no.
              Fields: <code>model</code>, <code>prompt</code>, <code>timeout</code>.</td></tr>
          <tr><td><b>agent</b></td>
              <td>Invoke a subagent.
              Fields: <code>agent</code>, <code>model</code>, <code>timeout</code>.</td></tr>
        </table>

        <h3 style="color:{acc}; margin-top:12px;">Hook Fields</h3>
        <table cellspacing="0" cellpadding="4" style="width:100%;">
          <tr><td width="130"><b>type</b></td>
              <td>command | http | prompt | agent</td></tr>
          <tr><td><b>timeout</b></td>
              <td>Seconds (defaults: command=600, http=30, prompt=30, agent=60)</td></tr>
          <tr><td><b>async</b></td>
              <td>true/false — run without blocking Claude (default: false)</td></tr>
          <tr><td><b>asyncRewake</b></td>
              <td>true/false — wake Claude when async hook completes</td></tr>
          <tr><td><b>statusMessage</b></td>
              <td>String shown in the UI while the hook runs</td></tr>
          <tr><td><b>once</b></td>
              <td>true/false — fire only once per session</td></tr>
          <tr><td><b>if</b></td>
              <td>Expression string for conditional execution</td></tr>
        </table>

        <h3 style="color:{acc}; margin-top:12px;">Output Keys (stdout JSON)</h3>
        <table cellspacing="0" cellpadding="4" style="width:100%;">
          <tr><td width="180"><b>hookSpecificOutput</b></td>
              <td>Arbitrary data passed back to Claude</td></tr>
          <tr><td><b>updatedInput</b></td>
              <td>Modified tool input (PreToolUse only)</td></tr>
          <tr><td><b>additionalContext</b></td>
              <td>Extra context appended to Claude's context</td></tr>
          <tr><td><b>permissionDecision</b></td>
              <td>allow | deny (PermissionRequest only)</td></tr>
        </table>

        <h3 style="color:{acc}; margin-top:12px;">Exit Codes</h3>
        <table cellspacing="0" cellpadding="4" style="width:100%;">
          <tr><td width="60"><b>0</b></td><td>Success — hook output passed to Claude</td></tr>
          <tr><td><b>2</b></td>
              <td>Blocking error for PreToolUse / UserPromptSubmit — stderr sent to Claude.
              Non-blocking for PostToolUse (tool already ran).</td></tr>
          <tr><td>other</td><td>Non-blocking, hook output logged but not acted on</td></tr>
          <tr><td>—</td>
              <td>Exit codes ignored for: PermissionDenied, InstructionsLoaded</td></tr>
        </table>

        <h3 style="color:{acc}; margin-top:12px;">Scope &amp; Precedence</h3>
        <p><b>User</b> (~/.claude/settings.json) — Global, applies to all projects.</p>
        <p><b>Project Shared</b> (.claude/settings.json) — Team-shared, committed to git.</p>
        <p><b>Project Local</b> (.claude/settings.local.json) — User-specific, gitignored.</p>
        <p>MCP tool pattern: <code>mcp__&lt;server&gt;__&lt;tool&gt;</code></p>

        <h3 style="color:{acc}; margin-top:12px;">Example</h3>
        <pre style="background:{bg}; padding:10px; border-radius:4px; font-size:11px;">{{
  "hooks": {{
    "PostToolUse": [{{
      "matcher": "Write",
      "hooks": [{{
        "type": "command",
        "command": "black $TOOL_OUTPUT_FILE",
        "timeout": 30,
        "async": false,
        "statusMessage": "Auto-formatting..."
      }}]
    }}],
    "PreToolUse": [{{
      "matcher": "Bash",
      "hooks": [{{
        "type": "command",
        "command": "echo 'Bash about to run'",
        "timeout": 10
      }}]
    }}]
  }}
}}</pre>

        </body></html>
        """
