# PROMPT.md - Initial Requirements for Claude_DB

## Project Name
**Claude_DB** - Claude Code Configuration Manager

## Date Created
2025-10-25

## Initial Requirements

### Primary Goal
Develop a comprehensive PyQt6 desktop application for managing ALL aspects of Claude Code configuration through a GUI interface.

---

## Core Functionality Required

### 1. Configuration Management
- Edit settings.json (User, Global, Project levels)
- Manage CLAUDE.md file
- Configure all Claude Code settings through GUI

### 2. Component Management
Must provide interfaces for:
- **Agents**: Create, edit, delete agent .md files
- **Commands**: Manage slash commands
- **Skills**: Skills configuration
- **Prompts**: Prompt management
- **Plugins**: Plugin installation and configuration
- **MCP Servers**: MCP server configuration (.mcp.json)

### 3. System Configuration
- **Hooks**: Configure event hooks
- **Statusline**: Statusline customization
- **Environment Variables**: Env var management
- **Model Configuration**: Model preferences and settings

### 4. Monitoring & Analytics
- **Memory & Checkpointing**: View history, checkpoints
- **Usage & Analytics**: Token usage, session stats
- **Monitoring**: Real-time monitoring integration
- **Costs**: Token cost tracking

### 5. Tools Integration
- **ClaudeKit**: Full suite of claudekit commands
- **Claude Code Templates**: Template management
- **External Tools**: Launch all ecosystem tools
  - ccexp (Interactive Config Browser)
  - claude-monitor
  - tweakcc
  - ccstatusline
  - claudekit (all commands)
  - Claude-Flow
  - BMad-Method
  - And more...

### 6. Documentation & Reference
- **CLI Reference**: Complete CLI command reference
- **Documentation Viewer**: Display help/Claude_DB.html
- **About**: Resource links and information

---

## Technical Requirements

### Platform
- **Primary**: Windows 11 Pro
- **Framework**: PyQt6
- **Language**: Python 3.10+

### Configuration Paths
- User Config: `~/.claude/`  (C:\Users\USERNAME\.claude)
- Settings: `~/.claude/settings.json`
- Agents: `~/.claude/agents/`
- Commands: `~/.claude/commands/`
- MCP: `~/.claude/.mcp.json`

### Key Features
1. **Backup System**
   - Automatic backups before modifications
   - Timestamped backups
   - Backup script: `backup_program.ps1`

2. **Search Functionality**
   - Search across all configuration types
   - Quick filtering in lists

3. **Validation**
   - JSON validation before saving
   - Markdown syntax checking
   - Error messages for invalid configs

4. **External Tool Execution**
   - Launch tools in PowerShell 7 (pwsh)
   - Use Windows Terminal (wt)
   - Reuse terminal windows when possible

---

## UI/UX Requirements

### Layout
- Tabbed interface with 24+ tabs
- Organized by category:
  - Core Configuration
  - Components
  - Integration
  - Customization
  - System
  - Tools & Utilities
  - Documentation

### Design Requirements (Updated)
- **Color Scheme**: Gruvbox Dark
  - Background: #282828
  - Foreground: #EBDBB2
  - Accent: #83A598
- **Font Size**: 14px minimum (readable!)
- **No Wasted Space**: Editors must fill all available space
- **Stretch Factors**: Use layout.addWidget(widget, 1) for space filling

### Tabs Required
1. Settings (User/Global/Project)
2. CLAUDE.md Editor
3. Agents
4. Commands
5. Skills
6. Prompts
7. MCP Servers
8. Plugins
9. Environment Variables
10. Hooks
11. Statusline
12. Styles & Workflows
13. Memory & Checkpointing
14. Usage & Analytics
15. Monitoring
16. Costs
17. Model Configuration
18. CLI Reference
19. ClaudeKit
20. Templates
21. External Tools
22. Documentation Viewer
23. About
24. Preferences (new)

---

## Documentation Requirements

### Reference Material
Must incorporate information from:
- https://awesomeclaude.ai/code-cheatsheet
- https://claudelog.com/configuration/
- https://docs.claude.com/en/docs/claude-code/*
- https://neon.com/blog/our-claude-code-cheatsheet
- And many more (see CLAUDE.md for full list)

### Local Documentation
- help/Claude_DB.html - Comprehensive reference database
- help/README.md - Project documentation
- help/TODO.md - Progress tracking
- help/PROMPT.md - This file

---

## Success Criteria

### Must Have (P0)
- [x] All 24 tabs functional
- [x] Gruvbox Dark theme throughout
- [x] 14px readable fonts
- [x] No wasted vertical space
- [x] Backup system working
- [ ] All stub tabs completed with real functionality
- [ ] External tools all launch correctly
- [ ] Settings management works (User/Global/Project)

### Should Have (P1)
- [ ] Search across all configs
- [ ] Preferences tab for customization
- [ ] Comprehensive error handling
- [ ] Input validation everywhere

### Nice to Have (P2)
- [ ] Live config file watching
- [ ] Keyboard shortcuts
- [ ] Dark mode toggle (vs Gruvbox)
- [ ] Config templates

---

## Constraints & Limitations

### Technical Constraints
- Must work on Windows 11 primarily
- Must use PyQt6 (no Qt5)
- Must respect ~/.claude directory structure
- Must not break existing Claude Code functionality

### User Constraints
- Must be readable (14px+ fonts)
- Must be efficient (no wasted space)
- Must use Gruvbox Dark colors
- Must have backup before all changes

---

## Known Issues to Avoid

1. **DO NOT** use tiny fonts (10-11px)
2. **DO NOT** have white text on white background
3. **DO NOT** waste vertical space (470px+)
4. **DO NOT** use Test-Item (use Test-Path)
5. **DO NOT** use powershell (use pwsh)
6. **DO NOT** fake tool launches (actually run them)
7. **DO NOT** forget stretch factors in layouts

---

## Initial Implementation Notes

### Phase 1: Structure ✅
- Created 24 tab structure
- Main window with dark theme
- Basic navigation

### Phase 2: Core Tabs ✅
- Agents tab (fully functional)
- Commands tab (fully functional)
- Settings tab (User/Global/Project)
- About tab (readable)
- Documentation viewer (readable)

### Phase 3: Theme & UX ✅
- Gruvbox Dark applied
- Font sizes increased to 14px
- Stretch factors added
- No more wasted space

### Phase 4: Completion (IN PROGRESS)
- Complete stub tabs
- Add all external tools
- Create Preferences tab
- Full testing

---

**END OF PROMPT.md**
