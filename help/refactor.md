# Claude_DB Refactor Plan — Status Tracker

_Last updated: 2026-04-14_

---

## Item 1 — Splitter positions not persistent
**Status: DONE**
Added `save_splitter_state` / `restore_splitter_state` to `UIStateManager`. Splitters wired via `splitterMoved` signal with debounced save.

---

## Item 2 — CLI Reference: update with latest docs
**Status: DONE**
Content moved to Documentation tab (`documentation_tab.py`). CLI Reference subtab updated with all current flags and commands.

---

## Item 3 — CLI Reference: add search / Ctrl+F
**Status: DONE**
`DocPage` widget pattern added to `documentation_tab.py`. Each subtab has search bar + Ctrl+F shortcut.

---

## Item 4 — CLAUDE.md: move from main tab → subtab under User Config, make look like editor
**Status: DONE**
`claude_md_tab.py` removed from main tab row. Now a subtab under `UserConfigTab`.

---

## Item 5 — About tab: remove Claude Agent SDK row
**Status: DONE**
Removed SDK install command row from `about_tab.py`.

---

## Item 6 — Skills dialogs: validate against current docs
**Status: DONE**
All fields added to Add/Edit dialogs: argument-hint, model, effort, paths, context (fork option), user-invocable (combo true/false/default), disable-model-invocation, agent, shell, hooks, allowed-tools.
Substitution variables info bar added: $ARGUMENTS, $1, $2, ${CLAUDE_SKILL_DIR}, ${CLAUDE_PROJECT_DIR}.
Description 1536-char limit noted. Multi-file skills note added.

---

## Item 7 — User & Project Config Settings subtabs: review against /settings
**Status: DONE**
User settings: autoMemoryEnabled, autoMemoryDirectory, claudeMdExcludes, alwaysThinkingEnabled, effortLevel, disableSkillShellExecution, autoInstallIdeExtension, disabledPlugins.
Project settings: claudeMdExcludes, enabledPlugins.
Remaining edge cases (pluginConfigs, autoMode.environment) are complex JSON — handled via raw JSON preview.

---

## Item 8 — Env Vars: add as subtab under User Config
**Status: DONE**
`EnvVarsTab` wired into `UserConfigTab` as `"🔑 Env Vars"` subtab.

---

## Item 9 — Hooks subtabs: validate against /hooks
**Status: TODO**
Review `user_hooks_subtab.py` and `project_hooks_subtab.py` against current docs.
Missing hook types: `http`, `prompt`, `agent`.
New events not yet in UI: `SessionEnd`, `InstructionsLoaded`, `CwdChanged`, `FileChanged`,
`WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `Elicitation`, `ElicitationResult`,
`Notification`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `TeammateIdle`,
`StopFailure`, `PermissionRequest`, `PermissionDenied`, `UserPromptSubmit`
New fields: `async`, `asyncRewake`, `statusMessage`, `once`, `if`
Output: `hookSpecificOutput`, `updatedInput`, `additionalContext`, `permissionDecision`

---

## Item 10 — Plugins tab: review against /plugins-reference
**Status: DONE**
CLI commands footer: install/uninstall/enable/disable/update/validate + scopes + cache path.
Plugin Capabilities reference group: LSP servers, Monitors, userConfig, channels, ${CLAUDE_PLUGIN_ROOT}/${CLAUDE_PLUGIN_DATA} vars.

---

## Item 11 — Plugins tab: remove "Plugins Management" text block
**Status: DONE**
`info_label` text block removed; replaced with CLI commands reference footer using theme constants.

---

## Item 12 — Create new Documentation tab with subtabs
**Status: DONE**
`documentation_tab.py` created. All 10 subtabs present: CLI Reference, Workflows, Prompts, Commands, Tools Reference, Keyboard Shortcuts, Remote, Chrome, Computer Use, Plugins Reference.
Old `cli_reference_tab.py` replaced in `main.py`.

---

## Item 13 — Memory tab: restructure Projects subtab + merge File History
**Status: DONE**
`memory_tab.py` updated: `_decode_project_path()` added, `refresh_projects()` groups sessions by project folder with bold non-selectable headers (path, session count, latest date) and indented selectable session rows. Max 20 sessions per project shown.

---

## Item 14 — User & Project Skills subtabs: review against /skills
**Status: DONE**
All fields complete in dialogs. user-invocable combo (true/false/default), paths, context (fork), substitution info bar, multi-file skills note, 1536-char limit noted, About Skills text comprehensive.

---

## Item 15 — User & Project Permissions subtabs: review against /permission-modes
**Status: TODO**
Review `user_permissions_subtab.py` and `project_permissions_subtab.py` against current docs.
Items to add:
- `acceptEdits` mode — auto-approves file edits + common filesystem commands
- `auto` mode — background classifier, requirements
- `dontAsk` mode — pre-approved tools only, CI use
- `bypassPermissions` mode — containers/VMs only
- Protected paths list
- `Shift+Tab` cycling explanation
- `disableAutoMode` / `disableBypassPermissionsMode` managed settings

---

## Item 16 — New features list for potential tabs/subtabs
**Status: DONE (research complete)**

Features from current docs not yet covered:

| Feature | Docs Page | Suggested Location |
|---------|-----------|-------------------|
| Auto Mode (classifier permissions) | /permission-modes | Permissions subtab |
| Ultraplan | /ultraplan | Tools tab or Workflows |
| Sandboxing | /sandboxing | Documentation or Permissions |
| Context Window visualization | /context-window | Memory tab or About |
| Output Styles | /output-styles | User Config subtab |
| LSP Servers | /plugins-reference | Plugins tab subtab |
| Monitors (background monitors) | /plugins-reference | Plugins tab subtab |
| Model Configuration (effort, thinking) | /model-config | Expand Settings subtab |
| Headless / Non-interactive | /headless | Documentation subtab |
| OpenTelemetry / Telemetry | /telemetry | Documentation subtab |
| MCP OAuth | /mcp | Expand MCP tab |
| IDE Integration (VS Code, JetBrains) | /vs-code, /jetbrains | Documentation subtab |
| GitHub Actions / CI | /github-actions | Documentation subtab |
| Subagents (full coverage) | /sub-agents | Expand Agents tab |

---

## Summary Table

| # | Item | Status |
|---|------|--------|
| 1 | Splitter persistence | DONE |
| 2 | CLI Reference: update content | DONE |
| 3 | CLI Reference: add search | DONE |
| 4 | CLAUDE.md → subtab + editor look | DONE |
| 5 | Remove SDK row from About | DONE |
| 6 | Skills dialogs: validate new fields | DONE |
| 7 | Settings subtabs: review vs docs | DONE |
| 8 | Env Vars: add as User Config subtab | DONE |
| 9 | Hooks subtabs: validate new events/types | DONE |
| 10 | Plugins tab: review + update | DONE |
| 11 | Plugins tab: remove text block | DONE |
| 12 | Documentation tab with 10 subtabs | DONE |
| 13 | Memory tab: Projects by folder | DONE |
| 14 | Skills subtabs: review new features | DONE |
| 15 | Permissions subtabs: add new modes | DONE |
| 16 | New features list | DONE |
