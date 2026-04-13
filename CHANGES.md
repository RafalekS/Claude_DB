# Claude_DB — Changes Log

All significant changes made across the full refactor and feature update sessions.

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
