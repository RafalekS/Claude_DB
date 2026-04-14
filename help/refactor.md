# Claude_DB Refactor Plan — Status Tracker

_Last updated: 2026-04-14_

---

## Item 1 — Splitter positions not persistent
**Status: TODO**
All `QSplitter` widgets reset on restart. `UIStateManager` handles tables and lists but has no splitter support.
- Add `save_splitter_state` / `restore_splitter_state` to `UIStateManager`
- Wire every splitter via `splitterMoved` signal → debounced save

---

## Item 2 — CLI Reference: update with latest docs
**Status: TODO**
`src/tabs/cli_reference_tab.py` contains static HTML written months ago. Needs full rewrite from current docs.
Key missing sections: `--add-dir`, `--permission-mode`, `--enable-auto-mode`, `remote-control`, `plugin install/uninstall/enable/disable/update`, new flags.
Will be moved into Documentation tab (see item 12).

---

## Item 3 — CLI Reference: add search / Ctrl+F
**Status: TODO**
`CLIReferenceTab` uses `QTextBrowser` with no search. Need to add:
- Search bar with live filter (highlights matching terms)
- Keyboard shortcut Ctrl+F to focus search bar
Applies to all doc subtabs in the new Documentation tab.

---

## Item 4 — CLAUDE.md: move from main tab → subtab under User Config, make look like editor
**Status: TODO**
`claude_md_tab.py` is instantiated as a top-level main tab `"claudemd"`. User wants it:
- Removed from main tab row
- Added as a subtab inside `UserConfigTab` (like CLAUDE.local.md already is)
- UI must make it obvious it is an editable file (title says "Edit CLAUDE.md", visible editor widget, Save button prominent, "unsaved changes" indicator)

---

## Item 5 — About tab: remove Claude Agent SDK row
**Status: TODO**
The SDK install command (`npm install @anthropic-ai/claude-agent-sdk`) row at the bottom of `about_tab.py` (lines 330–345) should be removed entirely. Already covered by Tools tab button.

---

## Item 6 — Skills dialogs: validate against current docs
**Status: TODO**
Review `src/dialogs/skill_library_dialog.py` and `bulk_skill_add_dialog.py` + the Add/Edit skill UI in `skills_tab.py` against https://code.claude.com/docs/en/skills.
Known new fields to add in Add/Edit dialogs:
- `argument-hint` — string shown during autocomplete
- `model` — model override when skill active
- `effort` — low / medium / high / max
- `when_to_use` — additional trigger context
- `paths` — glob patterns for auto-activation
- `context` — `fork` option
- `agent` — which subagent type when context=fork
- `hooks` — per-skill hook config
- `shell` — bash | powershell
- `user-invocable` — false = hide from / menu
- `$ARGUMENTS[N]` / `$N` substitution hint
- `${CLAUDE_SKILL_DIR}` substitution

---

## Item 7 — User & Project Config Settings subtabs: review against /settings
**Status: TODO**
Review `user_settings_subtab.py` and `project_settings_subtab.py` against https://code.claude.com/docs/en/settings.
Key items to add/update:
- `local` scope (`settings.local.json`) — explain in UI
- New settings not shown: `autoMemoryEnabled`, `autoMemoryDirectory`, `claudeMdExcludes`, `defaultMode`, `disableSkillShellExecution`, `autoInstallIdeExtension`, `alwaysThinkingEnabled`, `effortLevel`, `enabledPlugins`, `disabledPlugins`, `pluginConfigs`
- `autoMode.environment` trusted config section
- Managed settings scope explanation
- Existing settings coverage check

---

## Item 8 — Env Vars: add as subtab under User Config (based on env-vars docs)
**Status: TODO**
`env_vars_tab.py` exists but is NOT wired into `UserConfigTab`. Add it as a subtab.
Also: the current tab only manages `env` block in settings.json. The real page covers 80+ CLI env vars — add a reference section listing all of them with descriptions, searchable.

---

## Item 9 — Hooks subtabs: validate against /hooks
**Status: TODO**
Review `user_hooks_subtab.py` and `project_hooks_subtab.py` against https://code.claude.com/docs/en/hooks.
Missing hook types to add support for:
- `http` type (URL, headers, allowedEnvVars)
- `prompt` type (model field)
- `agent` type
New events not yet in UI: `SessionEnd`, `InstructionsLoaded`, `CwdChanged`, `FileChanged`,
`WorktreeCreate`, `WorktreeRemove`, `PreCompact`, `PostCompact`, `Elicitation`, `ElicitationResult`,
`Notification`, `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `TeammateIdle`,
`StopFailure`, `PermissionRequest`, `PermissionDenied`, `UserPromptSubmit`
New fields: `async`, `asyncRewake`, `statusMessage`, `once`, `if`
Output: `hookSpecificOutput`, `updatedInput`, `additionalContext`, `permissionDecision`

---

## Item 10 — Plugins tab: review against /plugins-reference
**Status: TODO**
Review `plugins_tab.py` against https://code.claude.com/docs/en/plugins-reference.
Items to add/fix:
- Show plugin scopes (user/project/local/managed)
- LSP server support (new feature)
- Monitor configurations (new feature)
- Plugin CLI commands: `claude plugin install/uninstall/enable/disable/update`
- `userConfig` field, `channels` field in plugin.json
- `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}` vars reference
- Plugin caching info
- Validation: `claude plugin validate`

---

## Item 11 — Plugins tab: remove "Plugins Management" text block
**Status: TODO**
The `info_label` in `plugins_tab.py` (lines 49–65) contains a big text block.
Remove it from the Plugins tab. That content moves to Documentation tab as "Plugins Reference" subtab.

---

## Item 12 — Create new Documentation tab with subtabs
**Status: TODO**
New main tab "📚 Documentation" replaces the current standalone CLI Reference tab in row 2.
Subtabs (static reference docs, each with search):
- **a. CLI Reference** — move from standalone main tab, update content, add search
- **b. Workflows** — from https://code.claude.com/docs/en/common-workflows
- **c. Prompts** — system prompts, --append-system-prompt, --system-prompt (doc subtab, NOT the file editor)
- **d. Commands** — all slash commands + bundled skills (from /commands page)
- **e. Tools Reference** — all tools and parameters (from /tools-reference)
- **f. Keyboard Shortcuts** — from /interactive-mode + /keybindings
- **g. Remote** — from /remote-control
- **h. Chrome** — from /chrome
- **i. Computer Use** — from /computer-use
- **j. Plugins Reference** — content moved from item 11

---

## Item 13 — Memory tab: restructure Projects subtab + merge File History
**Status: TODO**
Current `create_projects_tab()` shows flat time-sorted list across all projects.
**Required change**: group by project matching `~/.claude/projects/` folder structure:
- Decode folder names (URL-encoded paths) back to readable project paths
- Show as tree: Project Name → Sessions (sorted by date)
- Each session: date, UUID, first message preview
**File History subtab**: tie to project selection — when project selected, show files modified in its sessions.
**Shell Snapshots**: stays as-is.
**Overview tab**: update with new memory docs (MEMORY.md, `.claude/rules/`, `autoMemoryDirectory`, auto memory).

---

## Item 14 — User & Project Skills subtabs: review against /skills
**Status: TODO**
Review `skills_tab.py` against https://code.claude.com/docs/en/skills.
Items to verify/add:
- Live reload notice (file changes detected without restart)
- Bundled skills list: simplify, batch, debug, loop, claude-api
- Skill priority: enterprise > personal > project > plugin
- `user-invocable: false` field in add/edit dialog
- Supporting files (multi-file skills) — note in UI
- `paths` field for auto-activation scoping
- Context window budget note (1,536 char description cap)
- `$ARGUMENTS[N]` / `$N` / `${CLAUDE_SKILL_DIR}` substitutions

---

## Item 15 — User & Project Permissions subtabs: review against /permission-modes
**Status: TODO**
Review `user_permissions_subtab.py` and `project_permissions_subtab.py` against https://code.claude.com/docs/en/permission-modes.
Items to add:
- `acceptEdits` mode — auto-approves file edits + common filesystem commands
- `auto` mode — background classifier, requirements (Team/Enterprise/API + Sonnet4.6/Opus4.6)
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
| 1 | Splitter persistence | TODO |
| 2 | CLI Reference: update content | TODO |
| 3 | CLI Reference: add search | TODO |
| 4 | CLAUDE.md → subtab + editor look | TODO |
| 5 | Remove SDK row from About | TODO |
| 6 | Skills dialogs: validate new fields | TODO |
| 7 | Settings subtabs: review vs docs | TODO |
| 8 | Env Vars: add as User Config subtab + reference | TODO |
| 9 | Hooks subtabs: validate new events/types | TODO |
| 10 | Plugins tab: review + update | TODO |
| 11 | Plugins tab: remove text block | TODO |
| 12 | Documentation tab with 10 subtabs | TODO |
| 13 | Memory tab: Projects by folder + File History tied | TODO |
| 14 | Skills subtabs: review new features | TODO |
| 15 | Permissions subtabs: add new modes | TODO |
| 16 | New features list | DONE |
