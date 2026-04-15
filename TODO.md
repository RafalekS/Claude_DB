# TODO - Claude_DB Development Tracker

## COMPLETED (Session 22/11/2025)

### MCP Tab Improvements
- [x] **MCP source separation**: Editor now shows .mcp.json and .claude.json servers separately
  - Clicking on a server switches editor to that source file
  - Clear source labels [.mcp.json] and [.claude.json] in server list
  - Saves to correct file based on current editing source
- [x] **HTTP MCP server templates**: New "Add HTTP Template" button in MCP Library
  - Simple dialog for URL-based MCP servers
  - Auto-suggests name from URL
  - Supports HTTP and SSE types
- [x] **MCP template renaming**: Can now rename MCP templates (was disabled in edit mode)

### Command Template Improvements
- [x] **5 separate fields** for command templates:
  - Description (role, purpose, overview)
  - Requirements (arguments, parameters, prerequisites)
  - Instructions (step-by-step guide)
  - Examples (code examples, usage examples, reference workflows)
  - Important Notes (warnings, limitations, considerations)
- [x] **Flexible section parsing**: Matches various section names from different sources
- [x] **Increased field heights**: Better visibility for content
- [x] **Template renaming**: Can now rename command templates
- [x] **Save logic updated**: Uses shared _build_template_content() method

### Skill Template Improvements
- [x] **Skill template renaming**: Can now rename skill templates

### MCP Template Organization
- [x] **Folder structure**: Templates organized into subfolders (ai, development, integration, media, productivity, search)
- [x] **Folder navigation UI**: MCP Library now shows folders first, double-click to enter, Back button to return
- [x] **5 new media servers added**: imdb-mrbourne, imdb-uzaysozen, mediasage, plex-niavasha, plex-vladimir

### Other Fixes
- [x] **Browse project folder**: All dialogs now start at C:\Scripts
- [x] **NPX Windows wrapper**: cmd /c wrapper option for npx commands
- [x] **Bulk MCP import fixes**: Auto-escapes backslashes, fixes missing quotes, balances braces
- [x] **Projects dropdown height**: Limited to 10 items visible

---

## COMPLETED - CRITICAL ISSUES (Session 2026-04-15)

### 1. Skills Tab Issues
- [x] **New Skill button**: Full form dialog with YAML frontmatter fields (name, description, argument-hint, model, effort, paths, context, tools, flags, hooks)
- [x] **Edit button**: GUI dialog pre-filled from existing frontmatter
- [x] **Skills Library - Add Template**: Single proper form (name, description, allowed-tools checkboxes)
- [x] **Remove excessive pop-ups**: Save/delete now uses status line label instead of QMessageBox.information

### 2. Commands Tab Issues
- [x] **Edit button**: Full GUI dialog with all 5 sections (Description, Requirements, Instructions, Examples, Important Notes) — parses existing content and rebuilds correctly
- [x] **New button**: Full form with all 5 content sections

### 3. Agents Tab Issues
- [x] **No "Template" field** in New Agent dialog or Edit Agent dialog
- [x] **Agent Library - Add Template**: Has name, description, color, model, tools
- [x] **Agent Library - Edit Template**: Proper GUI form with all fields including subfolder

---

## REQUIREMENTS (met)
- All Add/Edit operations use proper GUI forms, NOT text editors ✓
- All forms have ALL relevant fields ✓
- Status line used for save/delete feedback instead of excessive QMessageBox pop-ups ✓
- Consistent experience across all tabs (Agents, Skills, Commands, MCP) ✓
