# Claude_DB

**A comprehensive PyQt6 desktop application for Claude Code configuration management**

[![Python](https://img.shields.io/badge/python-3.1x-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## Overview

Claude_DB is a powerful GUI application that provides comprehensive management of Claude Code configurations without requiring terminal commands. It centralizes all Claude Code settings, agents, commands, skills, MCP servers, plugins, hooks, and more into an intuitive tabbed interface with **24 fully functional tabs**.

**No more terminal commands - manage everything through a professional GUI!**

### Key Features

- **24 Comprehensive Tabs** covering every aspect of Claude Code configuration
- **Settings Management** (User, Project, Local) with precedence hierarchy
- **Agent & Command Management** with markdown editor support
- **Skills System** (User and Project-level) with folder management
- **MCP Server Configuration** across User/Local/Project scopes
- **Plugin Marketplace Browser** with multi-format repository support
- **Project Management** with path decoding and session tracking
- **GitHub Sync** for configuration backup and synchronization
- **Dynamic Tools Configuration** with custom command buttons
- **Memory & Checkpointing** with hierarchy visualization
- **Hooks & Statusline** configuration with event documentation
- **ClaudeKit Integration** for setup, linting, and profiling
- **Prompt Management** with GitHub import functionality
- **Real-time Backups** before any configuration change
- **Cross-platform Support** (Windows primary, Linux/macOS compatible)

---

## Installation

### Prerequisites

- **Python 3.1x** (Python 3.10 or higher)
- **PyQt6** GUI framework
- **Claude Code CLI** installed and configured
- **Git** (for Config Sync tab)

### Install Dependencies

```bash
pip install PyQt6
```

### Clone or Download

```bash
git clone https://github.com/RafalekS/Claude_DB.git
cd Claude_DB
```

---

## Usage

### Launch Application

```bash
python src/main.py
```

Or on Windows:

```powershell
python src\main.py
```

### Quick Start

1. **Launch the application** - The app will detect your Claude configuration directory (`~/.claude/`)
2. **Browse tabs** - Two rows of tabs provide access to all configuration areas
3. **Make changes** - Edit settings, add agents, configure MCP servers, etc.
4. **Automatic backups** - All changes are backed up to `backup/` with timestamps
5. **Validate** - Built-in validation ensures JSON/Markdown syntax correctness

---

## Features by Tab

### Row 1 - Core Configuration (12 Tabs)

1. **⚙️ Settings** - Manage user and project settings with precedence visualization
2. **📝 CLAUDE.md** - Edit project-specific instructions for Claude Code
3. **🤖 Agents** - Create and manage custom agents with best practices guide
4. **⌨️ Commands** - Configure slash commands with markdown templates
5. **💡 Skills** - Manage user and project skills (directory-based)
6. **💬 Prompts** - Store reusable prompts with GitHub import functionality
7. **🔌 MCP Servers** - Configure Model Context Protocol servers (User/Local/Project)
8. **🧩 Plugins** - Manage plugins with marketplace browser
9. **🌍 Env Variables** - Set environment variables for Claude Code sessions
10. **🪝 Hooks** - Configure lifecycle hooks with event documentation
11. **📊 Statusline** - Customize terminal statusline with user/project configurations
12. **💾 Memory** - Manage memory files with hierarchy precedence

### Row 2 - Advanced Tools (12 Tabs)

13. **📈 Usage & Analytics** - View usage statistics and token consumption
14. **🧠 Model Config** - Configure model selection and parameters
15. **📖 CLI Reference** - Quick reference for Claude Code CLI commands
16. **🎨 Styles & Workflows** - Manage coding styles and workflows
17. **🛠️ ClaudeKit** - ClaudeKit integration (setup, lint, profile, doctor)
18. **🔧 Tools** - Dynamic tool configuration with custom commands
19. **🔄 Config Sync** - GitHub integration for config backup/restore
20. **📂 Projects** - Project management with path decoding and session tracking
21. **ℹ️ About** - Application info and external resource links
22. **🎨 Preferences** - Application preferences (theme, font size, backups)

---

## Configuration

### Configuration Directory

Claude_DB manages configurations in the standard Claude Code directory:

- **Windows**: `C:\Users\<username>\.claude\`
- **Linux/macOS**: `~/.claude/`

### Settings Precedence

Settings are applied in order (highest to lowest priority):

1. **Enterprise Managed** (`managed-settings.json`) - IT/DevOps policies
2. **Command Line Arguments** - Temporary session overrides
3. **Local Project** (`.claude/settings.local.json`) - Personal project settings (gitignored)
4. **Shared Project** (`.claude/settings.json`) - Team-shared project settings
5. **User Settings** (`~/.claude/settings.json`) - Personal global settings

### Important Paths

- **User Settings**: `~/.claude/settings.json`
- **Agents**: `~/.claude/agents/`
- **Commands**: `~/.claude/commands/`
- **Skills**: `~/.claude/skills/` (user) and `./.claude/skills/` (project)
- **MCP Config**: `~/.claude/.mcp.json`
- **Hooks**: `~/.claude/hooks/`
- **Projects**: `~/.claude/projects/`

### Backup System

All configuration changes trigger automatic backups:

- **Location**: `backup/` directory in project root
- **Format**: `backup_YYYYMMDD_HHMMSS.zip`
- **Contents**: Complete snapshot of `~/.claude/` directory
- **Restore**: Manual restoration from Preferences tab

---

## Development

### Project Structure

```
Claude_DB/
├── src/
│   ├── main.py                      # Application entry point
│   ├── tabs/                        # All 24 tab implementations
│   │   ├── settings_tab.py
│   │   ├── agents_tab.py
│   │   ├── commands_tab.py
│   │   ├── skills_tab.py
│   │   ├── prompts_tab.py
│   │   ├── mcp_tab.py
│   │   ├── plugins_tab.py
│   │   ├── hooks_tab.py
│   │   ├── statusline_tab.py
│   │   ├── memory_tab.py
│   │   ├── config_sync_tab.py
│   │   ├── projects_tab.py
│   │   ├── tools_tab.py
│   │   ├── claudekit_tab.py
│   │   └── ... (24 total tabs)
│   ├── dialogs/                     # Reusable dialog components
│   │   ├── plugin_marketplace_browser.py
│   │   └── __init__.py
│   └── utils/                       # Utility modules
│       ├── config_manager.py        # Configuration file management
│       ├── backup_manager.py        # Backup operations
│       ├── terminal_utils.py        # Terminal command execution
│       └── theme.py                 # Application theming
├── help/
│   ├── README.md                    # This file
│   ├── TODO.md                      # Development progress tracker
│   ├── PROMPT.md                    # Initial project requirements
│   └── Claude_DB.html               # Comprehensive reference database
├── backup/                          # Configuration backups (timestamped)
├── config/
│   └── config.json                  # Application configuration
├── CLAUDE.md                        # Project instructions for Claude Code
└── requirements.txt                 # Python dependencies
```

### Key Modules

- **ConfigManager** (`utils/config_manager.py`) - Handles JSON/Markdown file operations
- **BackupManager** (`utils/backup_manager.py`) - Creates timestamped backup archives
- **Terminal Utils** (`utils/terminal_utils.py`) - Executes external commands in Windows Terminal
- **Theme** (`utils/theme.py`) - Dark theme styling for consistent UI

### Design Guidelines

All tabs follow consistent design patterns:

- **Button Styling**: Purple primary color (#667eea) with hover effects
- **Group Boxes**: Bordered sections with consistent margins
- **Spacing**: 10px margins, 5-8px spacing throughout
- **Layout**: Grid layouts for forms, vertical for lists

### Adding New Features

To add new functionality:

1. Create new tab in `src/tabs/`
2. Import and register in `src/main.py`
3. Follow existing tab patterns for consistency
4. Update `help/TODO.md` with progress
5. Test backup/restore functionality

---

## Development History

Claude_DB was developed over **10 comprehensive sessions** (Sessions 1-10), achieving full functionality across all tiers:

### Session Highlights

- **Session 1-2**: Core infrastructure, Tiers 1-2 (quick wins, best practices, terminal utils)
- **Session 3**: Tooltips (60+ buttons), User/Project nested tabs (6 tabs restructured)
- **Session 4**: Terminal utils migration (tools_tab, mcp_tab, claudekit_tab)
- **Session 5**: Tab enhancements with community best practices (6 tabs)
- **Session 6**: Dynamic Tools Tab Configuration (TIER 3 complete)
- **Session 7**: GitHub Prompts Import with dual format support (TIER 3 complete)
- **Session 8**: Config Sync Tab with GitHub integration (TIER 4 complete)
- **Session 9**: Projects Management Tab with path decoding (TIER 4 complete)
- **Session 10**: Plugin Marketplace Browser GUI (TIER 4 complete)

**Status**: All 24 tabs fully functional. All Tier 1-4 tasks complete.

For detailed session-by-session progress, see [`help/TODO.md`](TODO.md).

---

## External Tools Integration

Claude_DB integrates with various Claude Code ecosystem tools:

### ClaudeKit Commands

```bash
claudekit setup              # Interactive setup wizard
claudekit setup --all        # Install all agents
claudekit list               # Show all components
claudekit list agents        # List agents with token counts
claudekit doctor             # System diagnostics
claudekit lint-commands      # Lint slash commands
claudekit lint-agents        # Lint agent files
claudekit-hooks profile      # Profile hook performance
```

### Additional Tools

- **ccexp** - Interactive config file browser (launch from Tools tab)
- **claude-monitor** - Real-time monitoring tool
- **npx claude-code-templates** - Template system
- **npx tweakcc** - Configuration tweaker
- **npx ccstatusline** - Statusline configurator

### MCP Tools

```bash
# Code Quality
npx @j0kz/smart-reviewer-mcp
npx @j0kz/test-generator-mcp

# Architecture
npx @j0kz/architecture-analyzer-mcp
npx @j0kz/api-designer-mcp

# Documentation
npx @j0kz/doc-generator-mcp
npx @j0kz/security-scanner-mcp
```
