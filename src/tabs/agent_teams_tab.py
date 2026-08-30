"""
Agent Teams Tab - Configure and view multi-agent team orchestration settings
"""

import json
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QSplitter, QListWidget, QListWidgetItem,
    QGroupBox, QFormLayout, QLineEdit, QComboBox, QMessageBox,
    QScrollArea
)
from PyQt6.QtCore import Qt

from utils import theme

logger = logging.getLogger(__name__)

class AgentTeamsTab(QWidget):
    """
    Agent Teams tab — reference and config UI for Claude Code multi-agent orchestration.

    Claude Code supports agent teams where one orchestrator agent spawns and manages
    subagents. This tab explains the system and provides config helpers.
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
        header = QLabel("Agent Teams — Multi-Agent Orchestration")
        header.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};"
        )
        layout.addWidget(header)

        subtitle = QLabel(
            "Claude Code supports multi-agent pipelines where an orchestrator agent "
            "spawns subagents to work in parallel or in sequence."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_NORMAL}px;")
        layout.addWidget(subtitle)

        # Splitter: left=concepts, right=agent frontmatter reference
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Left: How it works ---
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(5)

        how_label = QLabel("How It Works")
        how_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY};")
        left_layout.addWidget(how_label)

        how_text = QTextEdit()
        how_text.setReadOnly(True)
        how_text.setHtml(self._how_it_works_html())
        left_layout.addWidget(how_text, 1)
        self._how_text = how_text

        # --- Right: Frontmatter reference ---
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(4, 0, 0, 0)
        right_layout.setSpacing(5)

        ref_label = QLabel("Agent Frontmatter — Orchestration Keys")
        ref_label.setStyleSheet(f"font-weight: bold; color: {theme.FG_PRIMARY};")
        right_layout.addWidget(ref_label)

        ref_text = QTextEdit()
        ref_text.setReadOnly(True)
        ref_text.setHtml(self._frontmatter_reference_html())
        right_layout.addWidget(ref_text, 1)
        self._ref_text = ref_text

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([500, 500])
        layout.addWidget(splitter, 1)

        # Footer tip
        tip = QLabel(
            "💡 <b>To create an agent team:</b> define an orchestrator agent that calls the "
            "<code>Agent</code> tool to spawn workers. Workers can run in parallel with "
            "<code>run_in_background: true</code>. Use the <b>Agents</b> tab to create and edit agent files."
        )
        tip.setWordWrap(True)
        tip.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; background: {theme.BG_MEDIUM}; "
            f"padding: 8px; border-radius: 3px; font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(tip)

    def apply_theme(self):
        """Refresh HTML panels with current theme colors."""
        self._how_text.setHtml(self._how_it_works_html())
        self._ref_text.setHtml(self._frontmatter_reference_html())

    def _how_it_works_html(self) -> str:
        bg = theme.BG_DARK
        fg = theme.FG_PRIMARY
        fg2 = theme.FG_SECONDARY
        acc = theme.ACCENT_PRIMARY
        code_bg = theme.BG_MEDIUM

        return f"""<html><body style="background:{bg}; color:{fg}; font-size:{theme.FONT_SIZE_SMALL}px;">
<h3 style="color:{acc};">Orchestrator → Worker Model</h3>
<p>An <b>orchestrator</b> agent uses the <code style="background:{code_bg}; padding:1px 4px;">Agent</code>
tool to spawn <b>worker</b> agents. Workers run in isolated subprocesses with their own context windows.</p>

<h3 style="color:{acc};">Agent Tool Call</h3>
<pre style="background:{code_bg}; padding:8px; border-radius:4px; font-size:{theme.FONT_SIZE_SMALL}px;">Agent({{
  "description": "Analyze authentication code",
  "subagent_type": "security-reviewer",
  "prompt": "Review src/auth/ for OWASP Top 10...",
  "run_in_background": false
}})</pre>

<h3 style="color:{acc};">Parallel Execution</h3>
<p>Launch multiple agents in a single message to run them in parallel:</p>
<pre style="background:{code_bg}; padding:8px; border-radius:4px; font-size:{theme.FONT_SIZE_SMALL}px;">// Send both in one tool_use block:
Agent({{ "subagent_type": "code-reviewer", ... }})
Agent({{ "subagent_type": "security-reviewer", ... }})</pre>

<h3 style="color:{acc};">Worktree Isolation</h3>
<p>Set <code style="background:{code_bg}; padding:1px 4px;">isolation: "worktree"</code>
in agent frontmatter to run the agent in a fresh git worktree.
The worktree is cleaned up automatically if no changes are made.</p>

<h3 style="color:{acc};">TeammateIdle Hook</h3>
<p>The <code style="background:{code_bg}; padding:1px 4px;">TeammateIdle</code> hook fires when
a team member goes idle. Use it to reassign work or log status.</p>

<h3 style="color:{acc};">Permissions in Teams</h3>
<p>Workers inherit the orchestrator's permission set by default.
Each worker agent can further restrict (but not expand) permissions
via its own frontmatter <code style="background:{code_bg}; padding:1px 4px;">permissionMode</code>.</p>
</body></html>"""

    def _frontmatter_reference_html(self) -> str:
        bg = theme.BG_DARK
        fg = theme.FG_PRIMARY
        acc = theme.ACCENT_PRIMARY
        code_bg = theme.BG_MEDIUM
        fg2 = theme.FG_SECONDARY

        return f"""<html><body style="background:{bg}; color:{fg}; font-size:{theme.FONT_SIZE_SMALL}px;">
<h3 style="color:{acc};">Orchestration-Relevant Frontmatter Keys</h3>
<table style="width:100%; border-collapse:collapse;">
<tr style="background:{code_bg};">
  <th style="text-align:left; padding:4px 8px;">Key</th>
  <th style="text-align:left; padding:4px 8px;">Values</th>
  <th style="text-align:left; padding:4px 8px;">Effect</th>
</tr>
<tr><td style="padding:3px 8px;"><code>model</code></td>
    <td style="padding:3px 8px;"><code>inherit</code>, <code>sonnet</code>, <code>opus</code>, <code>haiku</code>, <code>fable</code>, or a full model ID</td>
    <td style="padding:3px 8px;">Model for this worker (inherit = same as orchestrator; default)</td></tr>
<tr style="background:{code_bg};"><td style="padding:3px 8px;"><code>isolation</code></td>
    <td style="padding:3px 8px;"><code>worktree</code></td>
    <td style="padding:3px 8px;">Run agent in a fresh git worktree; auto-cleaned if no changes</td></tr>
<tr><td style="padding:3px 8px;"><code>permissionMode</code></td>
    <td style="padding:3px 8px;"><code>default</code>, <code>acceptEdits</code>, <code>auto</code>, <code>dontAsk</code>, <code>bypassPermissions</code>, <code>plan</code>, <code>manual</code></td>
    <td style="padding:3px 8px;">Permission behaviour for this agent's actions</td></tr>
<tr style="background:{code_bg};"><td style="padding:3px 8px;"><code>maxTurns</code></td>
    <td style="padding:3px 8px;">integer</td>
    <td style="padding:3px 8px;">Max agentic turns before the agent stops</td></tr>
<tr><td style="padding:3px 8px;"><code>disallowedTools</code></td>
    <td style="padding:3px 8px;">list of tool names</td>
    <td style="padding:3px 8px;">Tools this agent cannot use (subset of orchestrator's allowed set)</td></tr>
<tr style="background:{code_bg};"><td style="padding:3px 8px;"><code>mcpServers</code></td>
    <td style="padding:3px 8px;">list of server names</td>
    <td style="padding:3px 8px;">MCP servers available to this worker</td></tr>
<tr><td style="padding:3px 8px;"><code>skills</code></td>
    <td style="padding:3px 8px;">list of skill names</td>
    <td style="padding:3px 8px;">Skills loaded for this worker</td></tr>
<tr style="background:{code_bg};"><td style="padding:3px 8px;"><code>memory</code></td>
    <td style="padding:3px 8px;"><code>user</code>, <code>project</code>, or <code>local</code></td>
    <td style="padding:3px 8px;">Give the worker a persistent memory file at that scope</td></tr>
<tr><td style="padding:3px 8px;"><code>background</code></td>
    <td style="padding:3px 8px;"><code>true</code> / <code>false</code></td>
    <td style="padding:3px 8px;">Keep this agent in the background when spawned</td></tr>
<tr style="background:{code_bg};"><td style="padding:3px 8px;"><code>effort</code></td>
    <td style="padding:3px 8px;"><code>low</code>, <code>medium</code>, <code>high</code>, <code>xhigh</code>, <code>max</code></td>
    <td style="padding:3px 8px;">Reasoning effort for this worker (levels depend on model)</td></tr>
<tr><td style="padding:3px 8px;"><code>hooks</code></td>
    <td style="padding:3px 8px;">hook config object</td>
    <td style="padding:3px 8px;">Per-agent hooks (overrides session hooks for this worker)</td></tr>
</table>

<h3 style="color:{acc}; margin-top:12px;">Example Agent Frontmatter</h3>
<pre style="background:{code_bg}; padding:8px; border-radius:4px;">---
name: security-worker
description: Security analysis worker agent
model: opus
isolation: worktree
permissionMode: acceptEdits
maxTurns: 20
disallowedTools:
  - Bash
effort: high
memory: project
---
You are a security specialist...</pre>
</body></html>"""
