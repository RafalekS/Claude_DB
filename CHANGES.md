# Claude_DB — Changes Log

All significant changes made across the full refactor and feature update sessions.

---

## Session Prompt — What Was Asked

> Review this project using my coding skill and @python-reviewer.
>
> Claude_DB is a PyQt6 desktop application for managing Claude Code configuration.
> After the code review, cross-reference the implementation against the current Claude Code
> documentation at https://code.claude.com/docs/en/ — specifically check:
>
> - Skills: are they structured, named, and invoked correctly?
> - Hooks (PreToolUse / PostToolUse / Stop): correct event names, matcher syntax, exit codes?
> - Agents
> - Commands
> - Statusline
> - Permissions
> - Plugins / MCP servers: registration format, config schema, tool naming conventions?
> - Project config (.claude/settings.json): valid fields and values?
> - User config (~/.claude/settings.json): any fields the app reads/writes correctly?
>
> Flag anything the app does that conflicts with or is now outdated relative to the docs.

---

## Code Review Findings (33 Items)

Full code review produced 33 findings. Status of each:

### CRITICAL

| # | Issue | Status |
|---|-------|--------|
| 1 | Command injection — `shell=True` with list arg in `plugins_tab.py`, `mcp_tab.py`, `plugin_marketplace_browser.py` | ✅ Fixed |
| 2 | `statusline` key written as `"statusline"` — Claude Code uses `"statusLine"` (camelCase) — silent data loss | ✅ Fixed |

### HIGH

| # | Issue | Status |
|---|-------|--------|
| 3 | `_notify_watchers` never called from `save_settings` — `watch_file()` callbacks never fire | ✅ Fixed |
| 4 | Cache key mismatch in `SettingsManager` — `_load_settings` uses caller-supplied key, `save_settings` derives its own | ✅ Fixed |
| 5 | `browse_project_folder` always resets text field to home instead of selected folder | ✅ Fixed |
| 6 | Non-atomic file writes in `hooks_tab.py` and `preferences_tab.py` — crash mid-write truncates settings | ✅ Fixed |
| 7 | `apply_theme_change` wipes ALL per-widget stylesheets — widgets unstyled after theme switch until restart | ✅ Fixed |
| 8 | `setFixedWidth` on `QPushButton` in 4 files (violates project standard) | ✅ Fixed |
| 9 | Silent `except: pass` at module level in `skills_tab.py` swallows config load failures | ✅ Fixed |
| 10 | `sys.path.insert` in 46 files — global path mutation at import time | ✅ Fixed |
| 11 | `print()` used instead of `logging` in 25+ locations — bypasses file logging entirely | ✅ Fixed |
| 12 | Bare `except` blocks in `github_client.py`, `mcp_tab.py`, `preferences_tab.py` | ✅ Fixed |
| 13 | MCP config path wrong — app reads `~/.claude/.mcp.json`; correct paths are `~/.claude.json` (user) and `<proj>/.mcp.json` | ✅ Fixed |
| 14 | 17 hook events missing — app had 9, docs define 26 | ✅ Fixed — all 26 now present |
| 15 | Hook timeout default 60s — Claude Code default is 600s | ✅ Fixed |
| 16 | Hook handler types `http`, `prompt`, `agent` not exposed — app only offered `command` | ✅ Fixed |

### MEDIUM

| # | Issue | Status |
|---|-------|--------|
| 17 | Hardcoded window geometry `setGeometry(100,100,1200,800)` — should use `resize()` | ✅ Fixed |
| 18 | Hardcoded stylesheet hex colours in `main.py` | ✅ Fixed |
| 19 | Config file path repeated in 5 modules with different depth counts | ✅ Fixed |
| 20 | Module-level config reads at import time in `agents_tab.py`, `skills_tab.py` | ✅ Fixed |
| 21 | Paths from config not expanded with `expanduser`/`expandvars` | ✅ Fixed |
| 22 | Skill `name` field incorrectly required — docs say it's optional | ✅ Fixed |
| 23 | 11 of 13 skill frontmatter fields not validated or exposed (`argument-hint`, `model`, etc.) | ⚠️ Partial — `argument-hint` and `model` added to dialogs; remaining 9 fields still not exposed |
| 24 | Agent frontmatter has non-standard fields (`displayName`, `category`) and is missing 11 documented fields | ✅ Fixed — non-standard fields removed; standard fields corrected |
| 25 | Agent model field missing `inherit` option and full model IDs | ✅ Fixed |
| 26 | `defaultMode` permission setting not exposed anywhere in app | ✅ Fixed — dropdown added to both user and project permissions subtabs |
| 27 | Redundant `import json` / `from utils import theme` inside method body in `main.py` | ✅ Fixed |
| 28 | Hook exit code tooltip misleading — exit 2 behaviour differs per event type | ✅ Fixed — hooks_tab.py tip now correctly differentiates PreToolUse vs PostToolUse vs ignored events |

### LOW

| # | Issue | Status |
|---|-------|--------|
| 29 | Shebang uses `python3` — project rule says use `python` | ✅ Fixed |
| 30 | Docs URL buttons point to old domain `docs.claude.com` | ✅ Fixed |
| 31 | `mcp_validator.py` whitelists `python3` instead of `python` | ✅ Fixed |
| 32 | Agent `color` field missing `pink` | ✅ Fixed |
| 33 | Commands/skills merge not explained in UI | ✅ Fixed — note added to commands_tab.py footer |

---

## Follow-Up Prompt — 9 Points

> 1.) themes and their application - has this been looked at and improved? Also need you to have a serious look at trying to compact the UI. There is a lot of clutter on the screen.
>
> 2.) what about styles, formats, fonts, colors, visual elements? have you checked if anything is hardcoded or not?
> have you checked if they are uniform and look the same throughout the application?
> I can already tell that for example all the widgets displaying json, variables, parameters, list of files, contents of files, etc. look different in almost every window, tab, module, etc.!
>
> 3.) all the info in widgets, labels, etc. explaining settings, explaining claude config, etc. - was all this verified against changed documentation from
> https://code.claude.com/docs/en
> and further
> https://code.claude.com/docs/en/features-overview
>
> 4.) have you added any new things from the website like rules?
> https://code.claude.com/docs/en/memory#organize-rules-with-claude/rules/
> what about subagents? Have you added any of this to the application?
> https://code.claude.com/docs/en/sub-agents
> what about settings - very important - have you verified this against the program?
> https://code.claude.com/docs/en/settings
>
> 5.) Have you verified ever changing file structure from
> https://code.claude.com/docs/en/claude-directory
>
> 6.) Find all of the new things in claude that are not in the program, give me a list and I will tell you which ones to add.
>
> 7.) Have you verified tab CLI Reference against the website?
> We cannot have outdated info if this program is to be a source of help for users of claude code!
>
> 8.) were all the tables verified against coding skill? format persistence, etc.
>
> 9.) skill sources widget in Preferences/Skills need to have an option to change its height (needs a draggable divider at the end)

| Point | Status |
|-------|--------|
| 1 — UI compactness / theme application | ✅ Done — global stylesheet padding tightened; outer margins reduced across 37+ files; redundant per-widget stylesheet calls removed |
| 2 — Hardcoded styles, fonts, colors; widget uniformity | ⚠️ Partial — hex colours replaced with theme vars across 8 files; widget uniformity pass not done |
| 3 — Verify all info labels against docs | ✅ Done — 13 corrections made across hooks, MCP, settings, rules tabs |
| 4 — New features: Rules tab, subagents, settings keys | ✅ Done — Rules tab added; autoMemoryEnabled/Directory, claudeMdExcludes, agentsAllowed added to settings UI |
| 5 — Verify .claude/ file structure against docs | ✅ Done — verified correct; one MCP label bug fixed in mcp_tab.py |
| 6 — List new Claude features not in app | ✅ Done — 39-item gap analysis produced (see below) |
| 7 — Verify CLI Reference tab against docs | ✅ Done — 12+ flags, subcommands, slash commands added |
| 8 — Table state persistence against coding skill | ✅ Done — UIStateManager wired to all tables via BaseLibraryDialog |
| 9 — Resizable skill sources widget | ✅ Done — QSplitter (horizontal + vertical) in skills_tab.py |

---

## Feature Gap Analysis (39 Items)

After the code review, a gap analysis against current Claude Code docs produced 39 items.
The user confirmed: implement all of them.

### Hook Events — 17 missing events added (#1–17)

| # | Feature | Status |
|---|---------|--------|
| 1 | `PostToolUseFailure` event | ✅ Done |
| 2 | `PostCompact` event | ✅ Done |
| 3 | `SubagentStart` event | ✅ Done |
| 4 | `InstructionsLoaded` event | ✅ Done |
| 5 | `PermissionRequest` event | ✅ Done |
| 6 | `PermissionDenied` event | ✅ Done |
| 7 | `TaskCreated` event | ✅ Done |
| 8 | `TaskCompleted` event | ✅ Done |
| 9 | `StopFailure` event | ✅ Done |
| 10 | `TeammateIdle` event | ✅ Done |
| 11 | `CwdChanged` event | ✅ Done |
| 12 | `FileChanged` event | ✅ Done |
| 13 | `ConfigChange` event | ✅ Done |
| 14 | `WorktreeCreate` event | ✅ Done |
| 15 | `WorktreeRemove` event | ✅ Done |
| 16 | `Elicitation` event | ✅ Done |
| 17 | `ElicitationResult` event | ✅ Done |

### Hook Handler Types — 3 missing types documented (#18–20)

| # | Feature | Status |
|---|---------|--------|
| 18 | `http` handler type | ✅ Done — documented in info panel and templates |
| 19 | `prompt` handler type | ✅ Done |
| 20 | `agent` handler type | ✅ Done |

### Settings Keys — 4 new keys (#21–24)

| # | Feature | Status |
|---|---------|--------|
| 21 | `autoMemoryEnabled` setting | ✅ Done |
| 22 | `autoMemoryDirectory` setting | ✅ Done |
| 23 | `claudeMdExcludes` setting | ✅ Done |
| 24 | `agentsAllowed` setting | ✅ Done |

### New Features / Tabs (#25–29)

| # | Feature | Status |
|---|---------|--------|
| 25 | Rules Manager tab — `.claude/rules/` with frontmatter and `paths:` scoping | ✅ Done — `rules_tab.py` |
| 26 | CLAUDE.local.md editor — create/edit UI (currently info-text only) | ✅ Done — claude_local_md_tab.py |
| 27 | Worktrees tab — create/list/remove git worktrees | ✅ Done — worktrees_tab.py |
| 28 | Agent Teams UI — multi-agent orchestration config | ✅ Done — agent_teams_tab.py |
| 29 | Remote Control — configure remote Claude Code access via API | ✅ Done — remote_control_tab.py |

### CLI Reference — Missing Flags (#30–39)

| # | Feature | Status |
|---|---------|--------|
| 30 | `--system-prompt` flag | ✅ Done |
| 31 | `--no-markdown` flag | ✅ Done |
| 32 | `--ide` flag | ✅ Done |
| 33 | `--debug` flag | ✅ Done |
| 34 | `--mcp-config <path>` flag | ✅ Done |
| 35 | `--permission-prompt-tool` flag | ✅ Done |
| 36 | `claude config get/set/list` subcommand | ✅ Done |
| 37 | `claude doctor` subcommand | ✅ Done |
| 38 | `claude bug` subcommand | ✅ Done |
| 39 | Slash commands reference (`/help`, `/clear`, `/compact`, etc.) | ✅ Done |

---

### Still Pending (from all sessions)

| Item | Description |
|------|-------------|
| Review #23 | Remaining 9 skill frontmatter fields not exposed in dialogs (`disable-model-invocation`, `user-invocable`, `allowed-tools`, `effort`, `context`, `agent`, `hooks`, `paths`, `shell`) |
| 9-Point #2 | Widget uniformity — all content viewers use consistent monospace font now, but visual styling pass across all dialogs not yet fully done |

---

## Version 2.0.3 — Feature Update (9-Point Review)

### Hooks — Expanded from 9 to 26 Events

All three hook files updated (`hooks_tab.py`, `user_hooks_subtab.py`, `project_hooks_subtab.py`):

**17 new events added:**
| Event | When it fires |
|---|---|
| `PostToolUseFailure` | After a tool call fails (was missing; PostToolUse is success-only) |
| `PostCompact` | After context compaction completes |
| `SubagentStart` | When a subagent begins |
| `StopFailure` | When a Stop hook returns non-zero |
| `InstructionsLoaded` | After CLAUDE.md instructions are loaded |
| `PermissionRequest` | When Claude requests a permission |
| `PermissionDenied` | When a permission is denied |
| `TaskCreated` | When a TodoWrite task is created |
| `TaskCompleted` | When a task is marked complete |
| `Elicitation` | When Claude needs to ask the user something |
| `ElicitationResult` | After elicitation gets a response |
| `CwdChanged` | When the working directory changes |
| `FileChanged` | When a watched file changes |
| `ConfigChange` | When Claude Code config changes |
| `WorktreeCreate` | When a git worktree is created |
| `WorktreeRemove` | When a git worktree is removed |
| `TeammateIdle` | When an agent team member is idle |

**Other hook fixes:**
- Info panel rewritten with categorised event descriptions
- All 4 handler types now documented: `command`, `http`, `prompt`, `agent`
- Template timeout corrected: `60` → `600` (the actual default)
- Footer updated to reflect 26 events and all handler types

---

### CLI Reference Tab — Completed

Missing flags and commands added:

| Added | Description |
|---|---|
| `--system-prompt` | Set system prompt directly (replaces default) |
| `--no-markdown` | Disable markdown rendering |
| `--debug` | Enable debug logging |
| `--ide` | Launch in IDE integration mode |
| `--mcp-config <path>` | Load MCP config from a specific file |
| `--permission-prompt-tool` | MCP tool to handle permission prompts in headless mode |
| `claude config get/set/list` | Read and write config values from CLI |
| `claude doctor` | Diagnose environment and configuration issues |
| `claude bug` | File a bug report |
| `-p` / `--print` | Documented as aliases |
| `-c` / `--continue` | Documented as aliases |
| `-r` / `--resume` | Documented as aliases |

New sections added:
- Slash commands reference (for use inside the REPL)
- Pipe input patterns
- JSON output for scripting patterns
- `! <command>` shell execution syntax

---

### User Settings — Advanced Settings Section

New group added below Theme in the User Settings subtab:

| Setting | Key | Type |
|---|---|---|
| Auto Memory toggle | `autoMemoryEnabled` | boolean |
| Memory directory path | `autoMemoryDirectory` | string path |
| CLAUDE.md exclude patterns | `claudeMdExcludes` | comma-separated globs |
| Agents allowed toggle | `agentsAllowed` | boolean |

Both `load_settings()` and `save_settings()` updated to read/write these keys.

**Model list updated** to include current Claude 4.x models:
- `claude-sonnet-4-6` — Sonnet 4.6 (best coding)
- `claude-opus-4-6` — Opus 4.6 (deepest reasoning)
- `claude-haiku-4-5-20251001` — Haiku 4.5 (fastest)
- Plus Claude 4.5 and 3.5 variants retained

---

### Rules Tab — New Tab

New `RulesTab` (`src/tabs/rules_tab.py`) added and registered in `main.py`.

**Features:**
- Two scope tabs: User (`~/.claude/rules/`) and Project (`.claude/rules/`)
- File list with YAML frontmatter summary display
- `📍` icon for path-scoped rules vs `📄` for global rules
- Create new rule — dialog with name, description, paths fields
- Auto-generates frontmatter + placeholder content
- Edit rule files directly in the built-in editor
- Delete rule files with confirmation
- Frontmatter strip shown above editor when a file is selected
- Footer explains scoping, `paths:` frontmatter, and `claudeMdExcludes` interaction

---

### Skills Discover — Resizable Panes

Source Repos sub-tab in Skills Discover:
- Replaced `QHBoxLayout` with `QSplitter(Horizontal)` — left list and right panel are now drag-resizable
- Added `QSplitter(Vertical)` between results table and preview pane — height is user-adjustable with a drag handle
- Default sizes: left 200px, right expands; results 300px, preview 150px

---

### Theme — Hardcoded Colour Cleanup

Replaced hardcoded hex values with theme variables across 8 files:

| Hex | Replaced with |
|---|---|
| `#fb4934` | `theme.ERROR_COLOR` |
| `#fabd2f` | `theme.WARNING_COLOR` |
| `#4ade80`, `#27ae60` | `theme.SUCCESS_COLOR` |
| `#f0ad4e`, `#e67e22`, `#f39c12` | `theme.WARNING_COLOR` |
| `#667eea` | `theme.ACCENT_PRIMARY` |
| `#999` | `theme.FG_SECONDARY` |
| `#ddd` | `theme.FG_PRIMARY` |
| `#444` | `theme.BG_LIGHT` |
| `#e74c3c`, `#c0392b` | `theme.ERROR_COLOR` |

Files updated: `preferences_tab.py`, `tools_tab.py`, `styles_workflows_tab.py`,
`user_workflows_subtab.py`, `project_config_tab.py`, `skills_tab.py`,
`settings_tab.py`, `mcp_tab.py`, `main.py`

---

### Version System

- Created `src/version.py` as single source of truth: `__version__ = "2.0.x"`
- `src/tabs/about_tab.py` now reads version dynamically via `from version import __version__`
- `.git/hooks/pre-commit` auto-increments the patch number on every commit
- Version at time of writing: **2.0.3**

---

### Skills Tab — Dialogs

- `NewSkillDialog` and `EditSkillDialog`: removed `display_name` field (not a standard frontmatter key)
- Added `argument-hint` field (QLineEdit) — documented in Claude Code skill frontmatter
- Added `model` field (QComboBox) with options: `(default)`, `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5-20251001`
- Frontmatter builder only emits `argument-hint` and `model` lines when non-empty
- Fixed `theme.get_combo_box_style()` → `theme.get_combo_style()` (correct function name)

### Agents Tab — Dialog Cleanup

- Removed `Display Name` and `Category` fields from `NewAgentDialog`, `NewAgentTemplateDialog`, `EditAgentTemplateDialog` — these are not standard Claude Code frontmatter keys
- Added `pink` to the colour picker in all three dialogs
- Model list corrected to `["inherit", "sonnet", "opus", "haiku"]` with `inherit` as default
- All `get_agent_data()` / `get_template_data()` methods updated to drop `displayName`/`category` keys
- All frontmatter builders updated accordingly

---

## Version 2.0.1–2.0.2 — Code Quality Fixes (Tasks 1–16)

### Bug Fixes

- **MCP "local" scope removed** — `~/.claude/.mcp.json` does not exist; the valid scopes are `user` (~/.claude.json) and `project` (<proj>/.mcp.json). All "local" MCP branches deleted from `config_manager.py` and `mcp_tab.py`; default scope changed from `"local"` to `"user"`
- **`setGeometry` → `resize`** in `main.py` — removed hardcoded window position (100, 100); window now opens wherever the OS places it
- **Docs URL** corrected across all tabs: `docs.claude.com` → `code.claude.com`
- **Hook timeout example** corrected: `60` → `600` in hooks info panels and templates

### Dead Code Removal

- All `sys.path.insert(0, ...)` statements removed from every source file (were unnecessary path hacks left over from development)
- Removed `self.mcp_file` pointing to non-existent local MCP path

### Hardcoded Values → Theme Variables (main.py)

Tab bar and header styles converted from hardcoded hex to theme variables:
- `#3c3c3c` → `theme.BG_MEDIUM`
- `#667eea` → `theme.ACCENT_PRIMARY`
- `#4c4c4c` → `theme.BG_LIGHT`
- `#444` → `theme.BG_LIGHT`
- `#2b2b2b` → `theme.BG_DARK`
- `#999` → `theme.FG_SECONDARY`

---

## Earlier Phases — Initial Refactor

### Phase 1 — Audit & Cleanup

- Deleted dead/backup files (old tab variants, unused imports)
- All hardcoded Windows and user-specific paths externalised to `config/config.json`
- Extracted `BaseLibraryDialog` to remove duplicated dialog boilerplate
- Fixed broken imports across all tabs
- Added `.gitignore` to exclude `.claude/` directory from tracking

### Phase 2 — Infrastructure

- **GitHub client** (`src/utils/github_client.py`): centralised GitHub API calls with rate-limit tracking, added missing `get_file_content()` method
- **UIStateManager** (`src/utils/ui_state_manager.py`): column width and scroll position persistence for all `QTableWidget` and `QListWidget` instances
- **Logging**: replaced bare `print()` calls with `logging` module throughout
- **Status bar**: centralised `set_status()` method in `main.py`; tabs call `self.window().set_status()` instead of manipulating UI directly
- **Theme switching**: `PreferencesTab` theme-change signal wired to instant theme refresh without restart
- **SettingsManager** crash fix: graceful handling when settings file is missing or malformed

### Phase 3 — MCP Tab Integration

- MCP_Search project merged: Discover tab with GitHub search, curated sources, and URL import
- MCP server inspector and validator integrated
- Scope handling corrected (user/project only — no local)
- Import conflict resolution dialog added
- `UIStateManager.connect_table()` wired to discover results table

### Phase 4 — Skills Tab Integration

- skills_builder project merged: full Discover sub-tab with Source Repos, GitHub Search, URL Import
- `AVAILABLE_TOOLS` list loaded from `config/config.json` instead of hardcoded
- Skill frontmatter validation (name, description, length, reserved words)
- Validation label with colour-coded error/warning display
- `UIStateManager` wired to source results and GitHub results tables
- `SkillLibraryDialog` with persistent column widths via `BaseLibraryDialog`

### Phase 5 — UI Polish

- Tab bar dual-row layout implemented
- `setGeometry` replaced with `resize` (OS-managed window placement)
- Consistent use of `theme.*` constants in all new UI elements
- `UIStateManager` column persistence added to all library dialogs via `BaseLibraryDialog`

---

## Files Added

| File | Purpose |
|---|---|
| `src/version.py` | Single source of truth for app version |
| `src/tabs/rules_tab.py` | New Rules Manager tab |
| `src/utils/github_client.py` | Centralised GitHub API client |
| `src/utils/ui_state_manager.py` | Table/list column and scroll persistence |
| `src/utils/backup_manager.py` | File backup utility |
| `src/utils/settings_manager.py` | Settings file read/write with caching |
| `src/utils/project_context.py` | Current project path tracking |
| `src/utils/template_manager.py` | Template loading for skills/commands/agents |
| `src/utils/mcp_inspector.py` | MCP server inspection |
| `src/utils/mcp_validator.py` | MCP config schema validation |
| `src/dialogs/base_library_dialog.py` | Base class for all library browser dialogs |
| `src/dialogs/skill_library_dialog.py` | Skills library browser |
| `src/dialogs/command_library_dialog.py` | Commands library browser |
| `src/dialogs/mcp_library_dialog.py` | MCP library browser |
| `src/dialogs/plugin_marketplace_browser.py` | Plugin marketplace browser |
| `src/tabs/user_config_tab.py` | Refactored user config container tab |
| `src/tabs/project_config_tab.py` | Refactored project config container tab |
| `src/tabs/user_hooks_subtab.py` | User-level hooks sub-tab |
| `src/tabs/project_hooks_subtab.py` | Project-level hooks sub-tab |
| `src/tabs/user_settings_subtab.py` | User settings sub-tab |
| `src/tabs/project_settings_subtab.py` | Project settings sub-tab |
| `src/tabs/user_permissions_subtab.py` | User permissions sub-tab |
| `src/tabs/project_permissions_subtab.py` | Project permissions sub-tab |
| `src/tabs/user_statusline_subtab.py` | User statusline sub-tab |
| `src/tabs/project_statusline_subtab.py` | Project statusline sub-tab |
| `src/tabs/user_workflows_subtab.py` | User workflows sub-tab |
| `src/tabs/user_model_info_subtab.py` | User model info sub-tab |
| `.git/hooks/pre-commit` | Auto-increments patch version on every commit |

---

## Files Removed / Deprecated

- All `*_old.py` and `*_backup.py` tab variants
- `src/tabs/model_config_tab_old.py`
- `src/tabs/settings_tab_backup.py`
- `src/tabs/project_permissions_subtab_old.py`
- `src/tabs/user_permissions_subtab_old.py`
- Redundant `sys.path.insert` calls in every source file
- `.claude/agents/`, `.claude/commands/`, `.claude/scripts/`, `.claude/settings.json` (removed from git tracking; added to `.gitignore`)
