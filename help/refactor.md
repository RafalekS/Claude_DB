# Claude_DB Refactor Plan — Status Tracker

_Last updated: 2026-04-15_

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
**Status: DONE**
Both `user_hooks_subtab.py` and `project_hooks_subtab.py` are fully up to date:
- 26 hook events including all new ones (SessionEnd, InstructionsLoaded, CwdChanged, FileChanged, WorktreeCreate/Remove, PreCompact/PostCompact, Elicitation/ElicitationResult, Notification, SubagentStart/Stop, TaskCreated/Completed, TeammateIdle, StopFailure, PermissionRequest/Denied, UserPromptSubmit)
- All 4 handler types: command, http, prompt, agent (with templates for each)
- All new fields: async, asyncRewake, statusMessage, once, if, timeout
- Output keys documented: hookSpecificOutput, updatedInput, additionalContext, permissionDecision
- Old name-based format detection with migration warning

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

## Item 13 — Memory tab: restructure + QTreeWidget + JSONL parsing
**Status: DONE**
Full rewrite of `memory_tab.py`:
- Conversations tab: QTreeWidget (left) + QTextEdit (right) in a QSplitter. Projects are bold top-level items; sessions are children.
- JSONL parsing skips `type=="progress"` and `file-history-snapshot:` / `<function_calls>` entries; extracts human/assistant messages with timestamps. No entry limit.
- Project Memories tab: QTreeWidget shows `~/.claude/projects/*/memory/*.md` files grouped by project; clicking a file loads it in a QTextEdit viewer.
- File History and Shell Snapshots: QListWidget + QTextEdit viewer; path stored as UserRole data.

---

## Item 14 — User & Project Skills subtabs: review against /skills
**Status: DONE**
All fields complete in dialogs. user-invocable combo (true/false/default), paths, context (fork), substitution info bar, multi-file skills note, 1536-char limit noted, About Skills text comprehensive.

---

## Item 15 — User & Project Permissions subtabs: review against /permission-modes
**Status: DONE**
Footer converted from `QLabel` → `QTextBrowser` (text now selectable/copyable).
All modes documented: `default`, `acceptEdits`, `auto` (ML classifier, Team/Enterprise; `disableAutoMode` flag), `dontAsk`, `bypassPermissions`.
Protected paths listed. `Shift+Tab` cycling explained. Managed flags noted.

---

## Item 16 — New features list for potential tabs/subtabs
**Status: DONE**
All identified features implemented. See Feedback Items FB1–FB10 below.

---

## Feedback Session — User Feedback Items (Session 2)

### FB1 — Model Info subtab: move from User Config → Documentation tab
**Status: DONE**
`UserModelInfoSubTab` removed from `UserConfigTab`. Model info HTML added as `"🤖 Model Info"` subtab in `documentation_tab.py` — covers model IDs, context windows, effort levels, fast mode.

### FB2 — Remove Workflows from main tab AND User Config subtab
**Status: DONE**
`StylesWorkflowsTab` removed from `main.py` tab list. `UserWorkflowsSubTab` import and addTab call removed from `user_config_tab.py`.

### FB3 — Env Vars: redesign as split screen; remove from Settings subtabs
**Status: DONE**
`env_vars_tab.py` rewritten: QSplitter with left panel (current vars from settings.json: QListWidget + Add/Edit/Remove) and right panel (reference QTableWidget with 37 known env vars, 4 columns: Variable/Category/Default/Description). Double-clicking a reference row pre-fills the Add dialog.
Env var sections removed from `user_settings_subtab.py` and `project_settings_subtab.py`.

### FB4 — Make non-copyable code/command labels selectable (QLabel → QTextBrowser)
**Status: DONE**
Converted in: `mcp_tab.py`, `agents_tab.py`, `skills_tab.py`, `remote_control_tab.py`, `user_settings_subtab.py`, `user_permissions_subtab.py`, `project_permissions_subtab.py`.

### FB5 — Plugins tab: use QSplitter to reduce clutter
**Status: DONE**
`plugins_tab.py` rewrote `init_ui` with `QSplitter(Horizontal)` — left panel: Enabled + Installed plugins; right panel: Known Marketplaces + Extra Marketplaces + Plugin Capabilities reference (QTextBrowser). CLI footer as QTextBrowser (max 50px).

### FB6 — Font in Settings doesn't work; expand font list
**Status: DONE**
Root cause: `apply_theme()` never updated `FONT_FAMILY` global and never called `app.setFont()`.
Fix: added `font_family` parameter to `theme.apply_theme()`; `preferences_tab.py` now calls `app.setFont(QFont(family, size))`.
Font list expanded to: Segoe UI, Arial, Calibri, Tahoma, Verdana, Trebuchet MS, Georgia, Helvetica, Ubuntu, Noto Sans, Open Sans (plus existing mono fonts).

### FB7 — Reset to Gruvbox Dark button does nothing
**Status: DONE**
Root cause: `reset_to_default()` only set widget values without applying them.
Fix: calls `apply_preferences()` which saves and applies theme + font.

### FB8 — Memory tab: proper JSONL parsing, QTreeWidget, no entry limits
**Status: DONE**
See Item 13 above.

### FB9 — Memory: show project memories (.md files)
**Status: DONE**
See Item 13 above (Project Memories tab).

### FB10 — New feature content additions
**Status: DONE**
- Documentation tab: added Ultraplan, Sandboxing, Context Window, Headless, Telemetry, IDE Integration, GitHub Actions subtabs.
- User Settings subtab: Output Styles reference section (QTextBrowser).
- MCP tab Discover: MCP OAuth reference footer (QTextBrowser).
- Agents tab: Subagents/Task tool info added to best-practices footer.
- Permissions subtabs: Auto Mode expanded with ML classifier description.

### FB11 — Remove footer "Tip: User settings apply globally..." from User Config
**Status: DONE**
Footer label removed from `user_config_tab.py`.

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
| 13 | Memory tab: tree view + JSONL parsing + project memories | DONE |
| 14 | Skills subtabs: review new features | DONE |
| 15 | Permissions subtabs: add new modes | DONE |
| 16 | New features list | DONE |
| FB1 | Model Info → Documentation tab | DONE |
| FB2 | Remove Workflows everywhere | DONE |
| FB3 | Env Vars split screen + remove from Settings | DONE |
| FB4 | QLabel → QTextBrowser (selectable) | DONE |
| FB5 | Plugins tab QSplitter | DONE |
| FB6 | Font in Settings fix | DONE |
| FB7 | Reset to Gruvbox Dark fix | DONE |
| FB8 | Memory JSONL parsing + QTreeWidget | DONE |
| FB9 | Memory project memories tab | DONE |
| FB10 | New feature content (docs, OAuth, subagents, etc.) | DONE |
| FB11 | Remove User Config footer tip | DONE |

**All items complete.**
