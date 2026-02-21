# Refactoring Plan: User/Project Configuration Consolidation

**Goal:** Reorganize the application to match Claude Code's actual file structure, eliminating settings.json conflicts and reducing tab complexity.

**Status:** Planning Phase
**Started:** 2025-11-04
**Estimated Duration:** 4-6 sessions (depending on complexity)

---

## Current Problems

1. **Multiple tabs edit `settings.json` independently** - Risk of file conflicts and data loss
2. **Inconsistent UX** - Related settings scattered across 5+ separate tabs
3. **No centralized project folder management** - Each tab manages project path separately
4. **Structure doesn't match Claude Code's filesystem organization**

---

## Target Architecture

### New Tab Structure

```
📁 User (Global) Configuration
├── 🎛️ Settings (hooks, statusline, model, permissions, theme, temperature)
├── 🤖 Agents (~/.claude/agents/*.md)
├── ⚡ Commands (~/.claude/commands/*.md)
├── 🔌 MCP Servers (~/.mcp.json)
└── 🎓 Skills (~/.claude/skills/*.md)

📁 Project Configuration
├── 📂 [Project Folder Picker - applies to ALL sub-tabs]
├── 🎛️ Settings (Shared & Local)
│   ├── Shared (.claude/settings.json)
│   └── Local (.claude/settings.local.json)
├── 🤖 Agents (.claude/agents/*.md)
├── ⚡ Commands (.claude/commands/*.md)
├── 🔌 MCP Servers (.mcp.json)
└── 🎓 Skills (.claude/skills/*.md)

📁 Standalone Tabs (unchanged)
├── 🧩 Plugins
├── 💾 Memory & Checkpointing
├── 📖 CLI Reference
├── 🔄 Workflows
├── 📈 Usage & Analytics
├── 🛠️ ClaudeKit
├── 🔧 Tools
├── 🔄 Config Sync
├── 📝 CLAUDE.md
├── ℹ️ About
└── 🎨 Preferences
```

---

## Context Management Strategy

**Goal:** Prevent context overflow and ensure smooth progress across multiple sessions

### Checkpoint Protocol

After completing EACH task:
1. **I will explicitly state:** "✅ Task X.Y complete"
2. **I will recommend:** Git commit with specific message format
3. **I will check context:** Report current token usage
4. **Decision point:** Continue to next task OR checkpoint and resume later

**Commit Message Format:**
```bash
git commit -m "refactor(phase-X): completed task X.Y - <brief description>"

# Examples:
git commit -m "refactor(phase-1): completed task 1.1 - add SettingsManager utility"
git commit -m "refactor(phase-2): completed task 2.1 - create UserConfigTab"
```

### Context Thresholds

| Token Usage | Action |
|-------------|--------|
| 0-85% (0-170k) | ✅ **Safe** - Continue working |
| 85-90% (170k-180k) | ⚠️ **Warning** - Finish current task, then checkpoint |
| 90-95% (180k-190k) | 🔶 **Critical** - Complete current task immediately, checkpoint required |
| 95%+ (190k+) | 🛑 **Stop** - Must checkpoint, resume in new session |

### Session Boundaries

**Natural stopping points (recommended):**
- After completing any Phase
- After Task 2.4 (before starting Phase 2.5)
- After Task 2.5.11 (before Phase 3)
- After Task 3.4 (before Phase 4)
- If context exceeds 85%

**Emergency stopping points (if needed):**
- Mid-phase if context hits 90%
- After any completed task if context is critical

### Monitoring Strategy

**I will:**
- Check token usage after each task completion
- Provide explicit token count: "Current: XXk/200k (XX%)"
- Recommend checkpoint when approaching thresholds
- Suggest which phase/task to resume from

**You can:**
- Run `/context` anytime to check usage
- Request checkpoint at any time
- Use 5-hour window if we hit limits mid-critical-task

### File Reading Strategy

**To minimize context usage:**
- Read only files relevant to current task
- Use `offset` and `limit` parameters for large files
- Reference previous reads when possible
- Avoid re-reading unchanged files

### Communication Efficiency

**I will:**
- Focus on implementation over explanation
- Provide concise summaries
- Use code blocks instead of lengthy descriptions
- Save detailed documentation for commit messages and refactor.md updates

---

## Phase 1: Infrastructure & Planning

**Goal:** Create foundation without breaking existing functionality

### Task 1.1: Create Unified Settings Manager
**File:** `src/utils/settings_manager.py` (new)
**Purpose:** Centralize all `settings.json` read/write operations to prevent conflicts

**Features:**
- Load settings.json with file watching
- Merge hooks, statusline, model, permissions, theme, temperature
- Save with atomic write (temp file + rename)
- Cache in-memory to reduce I/O
- Emit signals on external changes
- Handle User vs Project vs Local scopes

**API:**
```python
class SettingsManager:
    def get_user_settings() -> dict
    def get_project_settings(project_path: Path) -> dict  # Merges shared + local
    def get_project_shared_settings(project_path: Path) -> dict
    def get_project_local_settings(project_path: Path) -> dict

    def update_user_setting(key: str, value: any)
    def update_project_setting(project_path: Path, key: str, value: any, local: bool = False)

    def watch_file(path: Path, callback: Callable)
    def save_settings(path: Path, data: dict)
```

**Token Estimate:** ~500 tokens (small utility class)

---

### Task 1.2: Create Project Context Manager
**File:** `src/utils/project_context.py` (new)
**Purpose:** Centralize project folder selection and state

**Features:**
- Store current project path
- Validate .claude folder exists
- Emit signals when project changes
- Provide helper methods for all project paths

**API:**
```python
class ProjectContext(QObject):
    project_changed = pyqtSignal(Path)  # Emits when project folder changes

    def set_project(path: Path)
    def get_project() -> Optional[Path]
    def get_claude_folder() -> Path  # <project>/.claude/
    def get_agents_folder() -> Path  # <project>/.claude/agents/
    def get_commands_folder() -> Path  # <project>/.claude/commands/
    def get_skills_folder() -> Path  # <project>/.claude/skills/
    def get_mcp_file() -> Path  # <project>/.mcp.json
    def get_settings_file() -> Path  # <project>/.claude/settings.json
    def get_local_settings_file() -> Path  # <project>/.claude/settings.local.json
```

**Token Estimate:** ~400 tokens

---

### Task 1.3: Audit Current Implementation
**Goal:** Verify all tabs match Claude Code Configuration Map

**Check each tab against proposition.md:**
- ✅ Settings tab → settings.json? ✓
- ✅ Hooks tab → settings.json? ✓
- ✅ Statusline tab → settings.json? (need to verify)
- ✅ Permissions tab → settings.json? ✓
- ✅ Model Config tab → settings.json? ✓
- ✅ Commands tab → .claude/commands/*.md? ✓
- ✅ Agents tab → .claude/agents/*.md? ✓
- ✅ MCP tab → .mcp.json? ✓
- ✅ Skills tab → .claude/skills/*.md? ✓
- ✅ Plugins tab → .claude/plugins/? (need to verify)

**Deliverable:** Audit report in this file (Task 1.3 Results section below)

**Token Estimate:** ~300 tokens (reading + documenting)

---

## Phase 2: Create New Container Tabs

**Goal:** Build User and Project tabs without removing old tabs yet

### Task 2.1: Create User Configuration Tab
**File:** `src/tabs/user_config_tab.py` (new)
**Purpose:** Top-level container with sub-tabs for all user-level configuration

**Structure (8 Sub-Tabs):**
```python
class UserConfigTab(QWidget):
    def __init__(self, config_manager, backup_manager, settings_manager):
        # Header with "User (Global) Configuration"
        # QTabWidget with 8 sub-tabs:
        #   1. 🎛️ Settings - Model, Theme (Task 2.2)
        #   2. 🪝 Hooks - User hooks (Task 2.2.1)
        #   3. 🔒 Permissions - User permissions (Task 2.2.2)
        #   4. 📊 Statusline - User statusline (Task 2.2.3)
        #   5. 🤖 Agents - Re-use AgentsTab (scope="user", Phase 3)
        #   6. ⚡ Commands - Re-use CommandsTab (scope="user", Phase 3)
        #   7. 🔌 MCP Servers - Re-use MCPTab (scope="user", Phase 3)
        #   8. 🎓 Skills - Re-use SkillsTab (scope="user", Phase 3)
```

**Key Points:**
- Reuse existing tab implementations as sub-tabs
- Pass `settings_manager` instead of individual loading
- All sub-tabs work on `~/.claude/` paths
- Consistent styling with existing tabs
- Hooks, Permissions, Statusline are SEPARATE subtabs (not in Settings)

**Token Estimate:** ~800 tokens (new container + integration)

---

### Task 2.2: Create User Settings Sub-Tab
**File:** `src/tabs/user_settings_subtab.py` (new)
**Purpose:** Settings subtab for Model and Theme ONLY (NOT Hooks/Permissions/Statusline)

**Sections:**
1. **Model & Temperature** - reuse model_config_tab.py UI elements
2. **Theme** - from settings_tab.py
3. **Other Settings** - remaining settings.json fields (if any)

**Key Points:**
- Works on `~/.claude/settings.json` via `settings_manager`
- Real-time preview of JSON
- Single Save/Backup button
- Validation before save
- **DOES NOT include Hooks, Permissions, or Statusline** (separate subtabs)

**Token Estimate:** ~600 tokens (simpler, less consolidation)

---

### Task 2.2.1: Create User Hooks Sub-Tab
**File:** `src/tabs/user_hooks_subtab.py` (new)
**Purpose:** Dedicated subtab for user-level hooks configuration

**Sections:**
- Reuse hooks_tab.py UI elements
- Works on `~/.claude/settings.json` hooks section via `settings_manager`

**Token Estimate:** ~300 tokens

---

### Task 2.2.2: Create User Permissions Sub-Tab
**File:** `src/tabs/user_permissions_subtab.py` (new)
**Purpose:** Dedicated subtab for user-level permissions configuration

**Sections:**
- Reuse permissions_tab.py UI elements
- Works on `~/.claude/settings.json` permissions section via `settings_manager`

**Token Estimate:** ~300 tokens

---

### Task 2.2.3: Create User Statusline Sub-Tab
**File:** `src/tabs/user_statusline_subtab.py` (new)
**Purpose:** Dedicated subtab for user-level statusline configuration

**Sections:**
- Reuse statusline_tab.py UI elements
- Works on `~/.claude/settings.json` statusline section via `settings_manager`

**Token Estimate:** ~300 tokens

---

### Task 2.3: Create Project Configuration Tab
**File:** `src/tabs/project_config_tab.py` (new)
**Purpose:** Top-level container with centralized project folder picker

**Structure (8 Sub-Tabs):**
```python
class ProjectConfigTab(QWidget):
    def __init__(self, config_manager, backup_manager, settings_manager, project_context):
        # Header with project folder picker button
        # Current project display
        # QTabWidget with 8 sub-tabs:
        #   1. 🎛️ Settings - Model, Theme (Task 2.4)
        #   2. 🪝 Hooks - Project hooks (Task 2.4.1)
        #   3. 🔒 Permissions - Project permissions (Task 2.4.2)
        #   4. 📊 Statusline - Project statusline (Task 2.4.3)
        #   5. 🤖 Agents - Re-use AgentsTab (scope="project", Phase 3)
        #   6. ⚡ Commands - Re-use CommandsTab (scope="project", Phase 3)
        #   7. 🔌 MCP Servers - Re-use MCPTab (scope="project", Phase 3)
        #   8. 🎓 Skills - Re-use SkillsTab (scope="project", Phase 3)
```

**Key Features:**
- **Single project folder picker** at top (ONLY folder picker in entire tab)
- When folder changes, ALL sub-tabs update automatically (via `project_context.project_changed` signal)
- Display current project path prominently
- Browse button with folder picker dialog
- Validate .claude folder exists
- Hooks, Permissions, Statusline are SEPARATE subtabs (not in Settings)

**Token Estimate:** ~1000 tokens (new container + centralized picker)

---

### Task 2.4: Create Project Settings Sub-Tab
**File:** `src/tabs/project_settings_subtab.py` (new)
**Purpose:** Settings subtab for Model and Theme ONLY (NOT Hooks/Permissions/Statusline)

**Structure:**
- **Nested tabs:** "Shared" and "Local"
- Shared tab: `.claude/settings.json` (team-shared, committed to git)
- Local tab: `.claude/settings.local.json` (user-specific, gitignored)
- **Sections:** Model, Theme, Other Settings (same as UserSettingsSubTab)

**Key Points:**
- Uses `project_context` to get current project paths
- Listen to `project_context.project_changed` signal to reload
- Clear indication of which file is being edited
- Both use `settings_manager` for file operations
- **DOES NOT include Hooks, Permissions, or Statusline** (separate subtabs)

**Token Estimate:** ~800 tokens

---

### Task 2.4.1: Create Project Hooks Sub-Tab
**File:** `src/tabs/project_hooks_subtab.py` (new)
**Purpose:** Dedicated subtab for project-level hooks configuration

**Structure:**
- **Nested tabs:** "Shared" and "Local"
- Shared: `.claude/settings.json` hooks section
- Local: `.claude/settings.local.json` hooks section
- Reuse hooks_tab.py UI elements
- Listen to `project_context.project_changed` signal

**Token Estimate:** ~400 tokens

---

### Task 2.4.2: Create Project Permissions Sub-Tab
**File:** `src/tabs/project_permissions_subtab.py` (new)
**Purpose:** Dedicated subtab for project-level permissions configuration

**Structure:**
- **Nested tabs:** "Shared" and "Local"
- Shared: `.claude/settings.json` permissions section
- Local: `.claude/settings.local.json` permissions section
- Reuse permissions_tab.py UI elements
- Listen to `project_context.project_changed` signal

**Token Estimate:** ~400 tokens

---

### Task 2.4.3: Create Project Statusline Sub-Tab
**File:** `src/tabs/project_statusline_subtab.py` (new)
**Purpose:** Dedicated subtab for project-level statusline configuration

**Structure:**
- **Nested tabs:** "Shared" and "Local"
- Shared: `.claude/settings.json` statusline section
- Local: `.claude/settings.local.json` statusline section
- Reuse statusline_tab.py UI elements
- Listen to `project_context.project_changed` signal

**Token Estimate:** ~400 tokens

---

## Phase 2.5: Template Sources System

**Goal:** Add template library system for all component types (like MCP Sources)

### Overview

Create centralized template libraries for Commands, Agents, Hooks, Statuslines, Skills, and Prompts similar to the existing MCP Sources system. This enables:
- Quick enable/disable of components without losing configurations
- Easy sharing and backup of configurations
- Token savings (load only what's needed)
- Consistent UI pattern across all component types

**New Directory Structure:**
```
config/sources/
├── mcp_servers.json       (moved from config/mcp_sources.json)
├── commands.json          (new)
├── agents.json            (new)
├── hooks.json             (new)
├── statuslines.json       (new)
├── skills.json            (new)
└── prompts.json           (new - if needed)
```

---

### Task 2.5.1: Move MCP Sources File
**Action:** Relocate existing MCP sources to new directory structure

**Steps:**
1. Create `config/sources/` directory
2. Move `config/mcp_sources.json` → `config/sources/mcp_servers.json`
3. Update all references in `src/tabs/mcp_tab.py`

**Token Estimate:** ~100 tokens (simple file move + path updates)

---

### Task 2.5.2: Create Commands Sources Template
**File:** `config/sources/commands.json` (new)
**Structure:**
```json
{
  "commands": {
    "quick-commit": {
      "name": "quick-commit",
      "description": "Quick git commit with conventional commit format",
      "content": "Create a git commit with:\n- Conventional commit format\n- Clear, concise message\n- Run: git add . && git commit"
    },
    "review-security": {
      "name": "review-security",
      "description": "Security review of current changes",
      "content": "Review staged changes for:\n- SQL injection\n- XSS vulnerabilities\n- Authentication issues\n- Sensitive data exposure"
    }
  }
}
```

**Token Estimate:** ~200 tokens (template + sample entries)

---

### Task 2.5.3: Add Commands Library UI to CommandsTab
**File:** `src/tabs/commands_tab.py` (modify)

**New Features:**
- **"📚 Command Library"** button (like MCP Sources)
- Opens dialog with checkbox table of available command templates
- **"➕ Bulk Add Commands"** - Paste & convert commands
- **"🗑️ Delete Selected"** - Remove from library
- **"🔄 Refresh"** - Reload from file
- Deploy selected commands to User or Project scope

**UI Pattern:** Reuse MCPSourcesDialog structure:
- Table with: Checkbox | Name | Description
- Bulk add dialog accepts formats:
  - `name,description,content` (explicit)
  - `name: content` (auto-description)
  - JSON paste from commands.json

**Token Estimate:** ~800 tokens (reuse MCP dialog pattern)

---

### Task 2.5.4: Create Agents Sources Template
**File:** `config/sources/agents.json` (new)
**Structure:**
```json
{
  "agents": {
    "test-generator": {
      "name": "test-generator",
      "description": "Generate comprehensive test suites",
      "content": "# Test Generator Agent\n\nGenerate unit and integration tests with:\n- Edge case coverage\n- Mocking examples\n- Assertion best practices"
    },
    "code-reviewer": {
      "name": "code-reviewer",
      "description": "Code review with best practices",
      "content": "# Code Review Agent\n\nReview code for:\n- Code style consistency\n- Performance issues\n- Security vulnerabilities\n- Documentation completeness"
    }
  }
}
```

**Token Estimate:** ~200 tokens

---

### Task 2.5.5: Add Agents Library UI to AgentsTab
**File:** `src/tabs/agents_tab.py` (modify)

**New Features:** Same pattern as Commands Library (Task 2.5.3)

**Token Estimate:** ~800 tokens

---

### Task 2.5.6: Create Hooks Sources Template
**File:** `config/sources/hooks.json` (new)
**Structure:**
```json
{
  "hooks": {
    "pre-commit-lint": {
      "name": "pre-commit-lint",
      "type": "user-prompt-submit-hook",
      "command": "npm run lint",
      "description": "Run linter before committing"
    },
    "post-tool-backup": {
      "name": "post-tool-backup",
      "type": "tool-post-call-hook",
      "command": "python backup.py",
      "description": "Backup after file modifications"
    }
  }
}
```

**Token Estimate:** ~200 tokens

---

### Task 2.5.7: Add Hooks Library UI to UserSettingsSubTab
**File:** `src/tabs/user_settings_subtab.py` (modify - Hooks section)

**New Features:** Library button in Hooks section

**Token Estimate:** ~600 tokens (integrated into settings tab)

---

### Task 2.5.8: Create Statuslines Sources Template
**File:** `config/sources/statuslines.json` (new)
**Structure:**
```json
{
  "statuslines": {
    "minimal": {
      "name": "minimal",
      "format": "{{model}} | {{tokens}}",
      "description": "Minimal statusline showing only model and tokens"
    },
    "detailed": {
      "name": "detailed",
      "format": "{{model}} | {{tokens}}/{{limit}} ({{percent}}%) | {{project}}",
      "description": "Detailed statusline with project info"
    }
  }
}
```

**Token Estimate:** ~200 tokens

---

### Task 2.5.9: Add Statuslines Library UI to UserSettingsSubTab
**File:** `src/tabs/user_settings_subtab.py` (modify - Statusline section)

**New Features:** Library button in Statusline section

**Token Estimate:** ~600 tokens

---

### Task 2.5.10: Create Skills Sources Template
**File:** `config/sources/skills.json` (new)
**Structure:**
```json
{
  "skills": {
    "api-design": {
      "name": "api-design",
      "description": "Design RESTful APIs following best practices",
      "content": "# API Design Skill\n\nDesign APIs with:\n- RESTful principles\n- Proper HTTP methods\n- Clear endpoint naming\n- Versioning strategy"
    }
  }
}
```

**Token Estimate:** ~200 tokens

---

### Task 2.5.11: Add Skills Library UI to SkillsTab
**File:** `src/tabs/skills_tab.py` (modify)

**New Features:** Same pattern as Commands/Agents Library

**Token Estimate:** ~800 tokens

---

### Task 2.5.12: Create Prompts Sources Template (Optional)
**File:** `config/sources/prompts.json` (new)
**Purpose:** Template storage for system prompts / CLAUDE.md snippets

**Decision Point:** Do we need this? CLAUDE.md is already per-project. Skip for now, can add later if needed.

**Token Estimate:** 0 tokens (skipped)

---

**Phase 2.5 Total Token Estimate:** ~5300 tokens

**Note:** This phase can be done incrementally. Each component type (Commands, Agents, etc.) is independent.

---

## Phase 3: Refactor Tabs for Single-Scope Operation

**Goal:** Remove internal User/Project structure and folder pickers from component tabs

**Critical Understanding:**
- These tabs currently have INTERNAL User/Project sub-tabs with folder pickers
- After refactor: each tab instance handles ONLY ONE scope (user OR project)
- NO folder pickers in these tabs - parent container (UserConfigTab/ProjectConfigTab) manages scope
- These tabs will ONLY exist as sub-tabs, never standalone (old standalone tabs deprecated in Phase 5)

### Task 3.1: Refactor AgentsTab to Single-Scope ✅ COMPLETE
**File:** `src/tabs/agents_tab.py` (modify)
**Status:** Completed - Commit 2ed89b7
**Changes:**
- ✅ REMOVED internal User/Project sub-tabs structure (QTabWidget)
- ✅ REMOVED folder picker methods (`create_agents_editor_with_folder`, `browse_project_folder`)
- ✅ Accept REQUIRED `scope` parameter ("user" or "project")
- ✅ Accept optional `project_context` parameter (REQUIRED if scope="project")
- ✅ Created single editor UI (no nested tabs)
- ✅ Added `on_project_changed` method to handle project context changes
- ✅ For project scope: listen to `project_context.project_changed` signal to reload
- ✅ For user scope: always use ~/.claude/agents/
- ✅ Simplified widget references (removed scope_widgets dict pattern)

**Result:** Net reduction of 181 lines (287 deleted, 106 added)
**Token Usage:** ~700 tokens

---

### Task 3.2: Refactor CommandsTab to Single-Scope ✅ COMPLETE
**File:** `src/tabs/commands_tab.py` (modify)
**Status:** Completed - Commit 6fcc0e8
**Changes:** Same pattern as AgentsTab
- ✅ REMOVED internal User/Project sub-tabs structure (QTabWidget)
- ✅ REMOVED folder picker methods (`create_commands_editor_with_folder`, `browse_project_folder`)
- ✅ Accept REQUIRED `scope` parameter ("user" or "project")
- ✅ Accept optional `project_context` parameter (REQUIRED if scope="project")
- ✅ Created single editor UI (no nested tabs)
- ✅ Added `on_project_changed` method to handle project context changes
- ✅ Simplified widget references (removed scope_widgets dict pattern)

**Result:** Net reduction of 168 lines (266 deleted, 98 added)
**Token Usage:** ~650 tokens

---

### Task 3.3: Refactor MCPTab to Single-Scope ✅ COMPLETE
**File:** `src/tabs/mcp_tab.py` (modify)
**Status:** Completed - Commit e197929
**Changes:**
- ✅ REMOVED internal User/Local/Project sub-tabs structure (QTabWidget)
- ✅ REMOVED `create_mcp_editor_with_folder` method (173 lines)
- ✅ REMOVED `browse_project_folder` method
- ✅ Accept REQUIRED `scope` parameter ("user", "local", or "project")
- ✅ Accept optional `project_context` parameter (REQUIRED if scope="project" or "local")
- ✅ Created single editor UI (no nested tabs)
- ✅ Added `on_project_changed` method to handle project context changes
- ✅ For project/local scope: listen to `project_context.project_changed` signal to reload
- ✅ For user scope: always use ~/.claude.json
- ✅ Simplified widget references (removed scope_widgets dict pattern)
- ✅ Updated all methods: add_server, remove_server, edit_server, list_server_tools, validate_json, save_mcp_config, backup_and_save, open_mcp_sources, reset_project_choices

**Result:** Net reduction of 195 lines (352 deleted, 157 added)
**Token Usage:** ~1,200 tokens

---

### Task 3.4: Refactor SkillsTab to Single-Scope ✅ COMPLETE
**File:** `src/tabs/skills_tab.py` (modify)
**Status:** Completed - Commit faa39b9
**Changes:**
- ✅ REMOVED internal User/Project sub-tabs structure (QTabWidget)
- ✅ REMOVED `create_skills_editor_with_folder` method (167 lines)
- ✅ REMOVED `browse_project_folder` method
- ✅ Accept REQUIRED `scope` parameter ("user" or "project")
- ✅ Accept optional `project_context` parameter (REQUIRED if scope="project")
- ✅ Created single editor UI (no nested tabs)
- ✅ Added `on_project_changed` method to handle project context changes
- ✅ For project scope: listen to `project_context.project_changed` signal to reload
- ✅ For user scope: always use ~/.claude/skills/
- ✅ Simplified widget references (removed scope_widgets dict pattern)
- ✅ Updated all methods: load_skills, filter_skills, load_skill_content, create_new_skill, delete_skill, save_skill, backup_and_save_skill, revert_skill, open_skill_library, deploy_skills

**Result:** Net reduction of 185 lines (290 deleted, 105 added)
**Token Usage:** ~1,100 tokens

---

## Phase 3.5: UI Consistency Fixes ✅ COMPLETE

### UI Consistency Pass - All 4 Tabs
**Files:** `agents_tab.py`, `commands_tab.py`, `mcp_tab.py`, `skills_tab.py`
**Status:** Completed - Commits c5f3592, 7705791, 7e3f0b3

**Issues Fixed:**
1. ✅ MCPTab layout completely refactored to match other tabs
   - Added search box at top
   - Moved buttons to left panel
   - Moved Save/Backup to right panel header
   - Removed Validate button (redundant)
   - Added filter_servers() method

2. ✅ Added Edit button to CommandsTab and SkillsTab
   - Added ✏️ Edit button between New and Delete
   - Added edit_command() and edit_skill() methods

3. ✅ Button order consistency (all tabs)
   - Order: ➕ New, ✏️ Edit, 🗑️ Delete, 🔄 Refresh, 📚 Library
   - AgentsTab: Moved Delete from 5th to 3rd position

4. ✅ Emoji consistency (all tabs)
   - AgentsTab: Added emojis to all buttons
   - All tabs now use same emoji set

5. ✅ Revert button added to MCPTab
   - Added Revert button to editor header
   - Added revert_mcp_config() method

**Commits:**
- c5f3592: MCPTab UI refactoring
- 7705791: Edit buttons for Commands/Skills
- 7e3f0b3: Button order and emoji consistency
- fe3d5cd: Documentation update
- 874d640: Final UI consistency fixes (editor buttons, labels, relative paths)

### Final UI Consistency Pass - All 4 Tabs
**Files:** `agents_tab.py`, `commands_tab.py`, `mcp_tab.py`, `skills_tab.py`
**Status:** Completed - Commit 874d640

**Issues Fixed:**
1. ✅ Added missing emojis to editor buttons
   - CommandsTab: Added 💾 and 📦 emojis to Save/Backup buttons
   - AgentsTab: Added 💾 and 📦 emojis to Save/Backup buttons
   - SkillsTab: Already had emojis
   - MCPTab: Already had emojis

2. ✅ Show relative paths instead of absolute paths
   - CommandsTab: Changed label to show relative path (e.g., "config/bash-timeout.md")
   - AgentsTab: Changed label to show relative path (e.g., "agents-md/migration.md")
   - SkillsTab: Already showing relative path
   - MCPTab: Shows server name only

3. ✅ Fixed label styling consistency
   - SkillsTab: Changed from bold to non-bold with secondary color
   - MCPTab: Changed from bold to non-bold with secondary color
   - CommandsTab: Already had correct styling
   - AgentsTab: Already had correct styling

4. ✅ Made MCP label dynamic
   - Changed static "Configuration:" to dynamic label
   - Shows "No server selected" by default
   - Shows "Editing: servername" when server selected
   - Resets to "No server selected" on config reload

**Result:** All tabs now have:
- Consistent emoji usage: 💾 Save, 📦 Backup & Save, Revert
- Non-bold labels with secondary color
- Relative paths in editor labels
- Consistent UI pattern across all tabs

---

## Phase 2.5: Create Missing Subtabs ✅ COMPLETE

### Creating Hooks/Permissions/Statusline Subtabs
**Files Created:** `hooks_subtab.py`, `permissions_subtab.py`, `statusline_subtab.py`, `test_phase25_subtabs.py`
**Status:** Completed - Commit 9def769
**Session:** 22 (November 2025)

**Context:** These subtabs were deferred from Phase 2 and created following the UI Consistency Checklist established in Phase 3.5.

**Subtabs Created:**

1. **HooksSubtab** (`src/tabs/hooks_subtab.py`)
   - Manages Claude Code hooks (SessionStart, PreToolUse, PostToolUse, etc.)
   - JSON editor with validation and pretty-printing
   - User scope: `~/.claude/hooks/*.json`
   - Project scope: `./.claude/hooks/*.json`
   - Template includes SessionStart hook with command/timeout configuration

2. **PermissionsSubtab** (`src/tabs/permissions_subtab.py`)
   - Manages tool permissions (allow/deny patterns)
   - JSON editor with validation and pretty-printing
   - User scope: `~/.claude/permissions/*.json`
   - Project scope: `./.claude/permissions/*.json`
   - Template includes allow patterns for basic tools (ls, git, Read)

3. **StatuslineSubtab** (`src/tabs/statusline_subtab.py`)
   - Manages statusline configurations
   - JSON editor with validation and pretty-printing
   - User scope: `~/.claude/statusline/*.json`
   - Project scope: `./.claude/statusline/*.json`
   - Template includes command-type statusline with basic echo

**UI Consistency Features (all subtabs):**
- ✅ Single-scope architecture (user OR project, never both)
- ✅ Parameter validation: `if scope == "project" and not project_context: raise ValueError`
- ✅ Consistent button layout: ➕ New, ✏️ Edit, 🗑️ Delete, 🔄 Refresh
- ✅ Editor buttons: 💾 Save, 📦 Backup & Save, Revert
- ✅ Non-bold labels with secondary color: `get_label_style("normal", "secondary")`
- ✅ Dynamic labels: "No [item] selected" / "Editing: filename"
- ✅ Search functionality with filter method
- ✅ Project context change handling via `on_project_changed()` signal
- ✅ JSON validation on save with pretty-printing
- ✅ Splitter ratio: 300/1000
- ✅ All widget references stored as instance variables

**Testing (`test_phase25_subtabs.py`):**
- ✅ Parameter validation test - project scope requires project_context
- ✅ User scope instantiation test - all UI elements and methods present
- ✅ Project scope instantiation test - scope and project_context verified
- ✅ All tests passed (3/3)

**Result:**
- 3 new subtabs created (1,438 lines total)
- All following UI Consistency Checklist patterns
- Ready for Phase 4 integration into User/Project config tabs
- Token Usage: ~3,500 tokens

**Commit:** 9def769 - Add Phase 2.5 subtabs: Hooks, Permissions, Statusline

---

## Phase 4: Integration & Testing

### Task 4.1: Add New Tabs to Main Window
**File:** `src/main.py` (modify)
**Changes:**
- Import new tabs
- Instantiate `SettingsManager` and `ProjectContext`
- Add "userconfig" and "projectconfig" to `all_tabs` dictionary
- Keep old tabs for now (parallel operation)

**Token Estimate:** ~200 tokens

---

### Task 4.2: Test New Tabs
**Manual Testing Checklist:**
- [ ] User tab loads all sub-tabs correctly
- [ ] User Settings sub-tab shows all sections
- [ ] User Settings can save to ~/.claude/settings.json
- [ ] User Agents/Commands/MCP/Skills work correctly
- [ ] Project tab folder picker works
- [ ] Project folder change updates all sub-tabs
- [ ] Project Settings (Shared) works
- [ ] Project Settings (Local) works
- [ ] Project Agents/Commands/MCP/Skills respect current project
- [ ] No file conflicts when switching between tabs
- [ ] SettingsManager prevents race conditions

**Token Estimate:** ~500 tokens (bug fixes during testing)

---

## Phase 5: Migration & Cleanup

### Task 5.1: Update Default Tab Configuration
**File:** `config/config.json` (modify)
**Changes:**
- Remove old tab entries: settings, hooks, statusline, permissions, modelconfig, agents, commands, mcp, skills, projects
- Add new entries: userconfig, projectconfig
- Update tab order/rows

**Token Estimate:** ~100 tokens

---

### Task 5.2: Remove Old Tabs
**Files to remove or deprecate:**
- Keep: `settings_tab.py` (reference implementation)
- Keep: `hooks_tab.py` (reference implementation)
- Keep: `statusline_tab.py` (reference implementation)
- Keep: `permissions_tab.py` (reference implementation)
- Keep: `model_config_tab.py` (reference implementation)
- Remove: `projects_tab.py` (replaced by new ProjectConfigTab)

**Note:** Don't delete tab files immediately - rename with `.deprecated` suffix for backup

**Token Estimate:** ~200 tokens (file operations + cleanup)

---

### Task 5.3: Update Documentation
**Files:**
- `help/README.md` - Update tab descriptions
- `help/TODO.md` - Document refactor completion
- `CLAUDE.md` - Update architecture notes

**Token Estimate:** ~300 tokens

---

## Phase 6: Polish & Optimization

### Task 6.1: Performance Optimization
- Implement lazy loading for sub-tabs (only load when clicked)
- Cache file reads in SettingsManager
- Debounce file save operations

**Token Estimate:** ~400 tokens

---

### Task 6.2: UI/UX Improvements
- Add visual indicator when project context changes
- Add breadcrumb navigation (e.g., "User > Settings > Hooks")
- Improve sub-tab styling for consistency
- Add tooltips explaining User vs Project differences

**Token Estimate:** ~300 tokens

---

## Rollback Plan

If refactor causes critical issues:

1. **Immediate rollback:** Git revert to pre-refactor commit
2. **Partial rollback:** Remove new tabs from `all_tabs` dictionary, restore old tabs
3. **Data safety:** All changes use backup system - user data is safe

---

## Token Budget Estimation

| Phase | Task | Estimated Tokens |
|-------|------|------------------|
| **Phase 1** | | |
| 1.1 | Settings Manager | 500 |
| 1.2 | Project Context | 400 |
| 1.3 | Audit | 300 |
| **Phase 2** | | |
| 2.1 | User Config Tab | 800 |
| 2.2 | User Settings Sub-Tab | 1200 |
| 2.3 | Project Config Tab | 1000 |
| 2.4 | Project Settings Sub-Tab | 1200 |
| **Phase 2.5** | **Template Sources System** | |
| 2.5.1 | Move MCP Sources | 100 |
| 2.5.2 | Commands Sources Template | 200 |
| 2.5.3 | Commands Library UI | 800 |
| 2.5.4 | Agents Sources Template | 200 |
| 2.5.5 | Agents Library UI | 800 |
| 2.5.6 | Hooks Sources Template | 200 |
| 2.5.7 | Hooks Library UI | 600 |
| 2.5.8 | Statuslines Sources Template | 200 |
| 2.5.9 | Statuslines Library UI | 600 |
| 2.5.10 | Skills Sources Template | 200 |
| 2.5.11 | Skills Library UI | 800 |
| 2.5.12 | Prompts Sources (skipped) | 0 |
| **Phase 3** | | |
| 3.1-3.4 | Refactor Tabs (Single-Scope) | 2400 |
| **Phase 4** | | |
| 4.1 | Integration | 200 |
| 4.2 | Testing | 500 |
| **Phase 5** | | |
| 5.1-5.3 | Migration & Cleanup | 600 |
| **Phase 6** | | |
| 6.1-6.2 | Polish | 700 |
| **Total** | | **~14,500 tokens** |

**Sessions Required:** 7-9 sessions (with Phase 2.5 additions)

**Session Breakdown:**
- Session 1: Phase 1 (Infrastructure) - ~1200 tokens
- Session 2: Phase 2 Tasks 2.1-2.2 - ~2000 tokens
- Session 3: Phase 2 Tasks 2.3-2.4 - ~2200 tokens
- Session 4: Phase 2.5 Tasks 2.5.1-2.5.5 (MCP + Commands + Agents) - ~2100 tokens
- Session 5: Phase 2.5 Tasks 2.5.6-2.5.11 (Hooks + Statuslines + Skills) - ~2400 tokens
- Session 6: Phase 3 + Phase 4.1 (Update tabs + Integration) - ~1800 tokens
- Session 7: Phase 4.2 + Phase 5 (Testing + Cleanup) - ~1300 tokens
- Session 8: Phase 6 (Polish) - ~700 tokens
- Session 9: Buffer for unexpected issues

---

## Task 1.3 Results: Implementation Audit ✅

**Completed:** 2025-11-04
**Result:** All tabs match Claude Code Configuration Map specifications

### Settings Tab ✅
- **Location:** `src/tabs/settings_tab.py`
- **Files Modified:**
  - User: `~/.claude/settings.json`
  - Project Shared: `.claude/settings.json`
  - Project Local: `.claude/settings.local.json`
- **Components:** Theme, model, temperature, general settings
- **Status:** ✅ **Matches spec** - Correctly implements User, Project Shared, and Project Local scopes

### Hooks Tab ✅
- **Location:** `src/tabs/hooks_tab.py`
- **Files Modified:**
  - User: `~/.claude/settings.json`
  - Project: `.claude/settings.json`
- **Components:** Hook configurations (user-prompt-submit, tool-pre-call, tool-post-call, etc.)
- **Status:** ✅ **Matches spec** - Stores hooks in settings.json as per Claude Code standard

### Statusline Tab ✅
- **Location:** `src/tabs/statusline_tab.py`
- **Files Modified:**
  - User: `~/.claude/settings.json` (lines 331, 354)
  - Project: `.claude/settings.json` (lines 217, 323)
- **Components:** Statusline configuration (command, template, colors, padding, etc.)
- **Verification:** Confirmed via code inspection - uses `load_statusline()` and `save_statusline()` methods
- **Status:** ✅ **Matches spec** - Correctly stores statusline in settings.json

### Permissions Tab ✅
- **Location:** `src/tabs/permissions_tab.py`
- **Files Modified:**
  - User: `~/.claude/settings.json`
  - Project: `.claude/settings.json`
- **Components:** Permission settings (bash, read, write, edit, etc.)
- **Status:** ✅ **Matches spec** - Permissions stored in settings.json

### Model Config Tab ✅
- **Location:** `src/tabs/model_config_tab.py`
- **Files Modified:**
  - User: `~/.claude/settings.json`
  - Project Shared: `.claude/settings.json`
  - Project Local: `.claude/settings.local.json`
- **Components:** Model selection, temperature, thinking settings
- **Status:** ✅ **Matches spec** - Nested tab structure with User/Project scopes

### Agents Tab ✅
- **Location:** `src/tabs/agents_tab.py`
- **Files Modified:**
  - User: `~/.claude/agents/*.md`
  - Project: `.claude/agents/*.md`
- **Status:** ✅ **Matches spec** - Markdown files in correct locations

### Commands Tab ✅
- **Location:** `src/tabs/commands_tab.py`
- **Files Modified:**
  - User: `~/.claude/commands/*.md`
  - Project: `.claude/commands/*.md`
- **Status:** ✅ **Matches spec** - Markdown files in correct locations

### MCP Tab ✅
- **Location:** `src/tabs/mcp_tab.py`
- **Files Modified:**
  - User: `~/.mcp.json`
  - Project: `.mcp.json`
- **Status:** ✅ **Matches spec** - JSON files in correct locations

### Skills Tab ✅
- **Location:** `src/tabs/skills_tab.py`
- **Files Modified:**
  - User: `~/.claude/skills/*.md`
  - Project: `.claude/skills/*.md`
- **Status:** ✅ **Matches spec** - Markdown directory structure (not JSON as per docs)

### Plugins Tab ✅
- **Location:** `src/tabs/plugins_tab.py`
- **Files Modified:**
  - Settings: `~/.claude/settings.json` (enabledPlugins, extraKnownMarketplaces)
  - Plugin directory: `~/.claude/plugins/`
  - Plugin config: `~/.claude/plugins/config.json`
  - Marketplaces: `~/.claude/plugins/known_marketplaces.json`
- **Verification:** Confirmed via code inspection (lines 29-32, 59, 165)
- **Status:** ✅ **Matches spec** - Manages both settings.json entries and ~/.claude/plugins/ directory

---

### Audit Summary

**Key Findings:**

1. ✅ **FILE CONFLICT CONFIRMED** - Multiple tabs independently edit `settings.json`:
   - Settings Tab
   - Hooks Tab
   - Statusline Tab
   - Permissions Tab
   - Model Config Tab
   - Plugins Tab (partial)

2. ✅ **All tabs match Claude Code Configuration Map** - No discrepancies found

3. ✅ **Settings.json contains these sections** (that will be consolidated):
   - `model` (Model Config Tab)
   - `temperature` (Model Config Tab)
   - `theme` (Settings Tab)
   - `permissions` (Permissions Tab)
   - `hooks` (Hooks Tab)
   - `statusline` (Statusline Tab)
   - `enabledPlugins` (Plugins Tab)
   - `extraKnownMarketplaces` (Plugins Tab)

4. ✅ **Refactor justification validated** - The proposed consolidation will:
   - Eliminate 6 tabs accessing same file independently
   - Prevent race conditions and file conflicts
   - Improve UX by grouping related settings

**Conclusion:** Current implementation correctly follows Claude Code specs, but suffers from architectural issue of multiple tabs editing settings.json. Refactor plan is justified and will resolve this issue.

---

## Notes & Decisions

- **Code Reuse:** ~99% of existing tab code can be reused by extracting UI sections into reusable widgets
- **File Conflicts:** SettingsManager will use file locking and atomic writes
- **User Impact:** Zero - you're the only user, no migration needed
- **Backwards Compatibility:** Not required since no external users
- **Git Strategy:** Create feature branch `refactor/user-project-consolidation` for safety

---

## Next Steps

1. ✅ Review this plan and approve
2. ✅ Add template sources system (Phase 2.5)
3. ✅ Add context management strategy
4. 🔄 Start Phase 1, Task 1.1 (Settings Manager)
5. Complete each task sequentially, testing as we go
6. Update this document with progress and any deviations

---

**Last Updated:** 2025-11-04 (Updated with Phase 2.5 and Context Strategy)
**Status:** 🔄 In Progress - Phase 1

---

## Progress Tracker

### Phase 1: Infrastructure & Planning ✅
- [x] Task 1.1: SettingsManager utility ✅ (Commit: 0fc3c9f)
- [x] Task 1.2: ProjectContext manager ✅ (Commit: 2b719e0)
- [x] Task 1.3: Implementation Audit ✅ (Completed - see audit results above)

### Phase 2: Container Tabs (Updated Plan - 8 subtabs) ✅
- [x] Task 2.1: User Config Tab ✅ (Commit: d10c3c3, Updated: 26a8009) **8 subtabs added**
- [x] Task 2.2: User Settings Sub-Tab ✅ (Commit: 6f174c2, Refactored: 633b85b) **Model+Theme only (651 lines removed)**
- [x] Task 2.2.1: User Hooks Sub-Tab ✅ (Commit: 45236b5) **308 lines**
- [x] Task 2.2.2: User Permissions Sub-Tab ✅ (Commit: f90150e) **318 lines**
- [x] Task 2.2.3: User Statusline Sub-Tab ✅ (Commit: d459d31) **278 lines**
- [x] Task 2.3: Project Config Tab ✅ (Commit: 8938130, Updated: d2ebcf2) **8 subtabs added**
- [x] Task 2.4: Project Settings Sub-Tab ✅ (Commit: c3b6497, Refactored: f9e45a2) **Model+Theme only (11 lines removed)**
- [x] Task 2.4.1: Project Hooks Sub-Tab ✅ (Commit: 00007b4) **354 lines**
- [x] Task 2.4.2: Project Permissions Sub-Tab ✅ (Commit: 2884073) **355 lines**
- [x] Task 2.4.3: Project Statusline Sub-Tab ✅ (Commit: b006bb0) **338 lines**

### Phase 2.5: Template Sources System ✅
- [x] Task 2.5.1: Move MCP Sources File ✅ (Commit: 0b7365b)
- [x] Task 2.5.2: Commands Sources Template ✅ (Commit: a2e81ab)
- [x] Task 2.5.3: Commands Library UI ✅ (Commit: cbcc426)
- [x] Task 2.5.4: Agents Sources Template ✅ (Commit: 824d8c6)
- [x] Task 2.5.5: Agents Library UI ✅ (Commit: 536e1a1)
- [x] Task 2.5.6: Hooks Sources Template ✅ (Commit: 16c29f9)
- [x] Task 2.5.7: Hooks Library UI ✅ (Commit: 210ee75)
- [x] Task 2.5.8: Statuslines Sources Template ✅ (Commit: 48c4b27)
- [x] Task 2.5.9: Statuslines Library UI ✅ (Commit: 89be259)
- [x] Task 2.5.10: Skills Sources Template ✅ (Commit: 9a5a36f)
- [x] Task 2.5.11: Skills Library UI ✅ (Commit: a3e3bd2)

### Phase 3: Update Existing Tabs
- [ ] Task 3.1-3.4: Make tabs dual-mode (4 tasks)

### Phase 4: Integration & Testing
- [ ] Task 4.1: Integration
- [ ] Task 4.2: Testing

### Phase 5: Migration & Cleanup
- [ ] Task 5.1-5.3: Cleanup (3 tasks)

### Phase 6: Polish
- [ ] Task 6.1-6.2: Performance & UX (2 tasks)

---

**Status:** ✅ Phase 2 COMPLETE! All container tabs and 8 subtabs implemented!
✅ Phase 2.5 complete! Template library systems implemented.
✅ 6 new dedicated subtabs created (Hooks, Permissions, Statusline for User and Project).
📋 Next: Phase 3 - Refactor existing tabs for single-scope operation.
