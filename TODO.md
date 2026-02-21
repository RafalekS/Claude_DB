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

## PENDING - CRITICAL ISSUES

### 1. Skills Tab Issues
- [ ] **New Skill button**: Skills created without proper YAML frontmatter - needs proper form dialog
- [ ] **Edit button**: Does nothing - needs to open GUI dialog for editing skill
- [ ] **Skills Library - Add Template**: Uses two separate tiny dialogs - consolidate into ONE proper form with:
  - Name
  - Description
  - Allowed-tools
- [ ] **Remove excessive pop-ups**: Use status line instead of QMessageBox for create/delete confirmations

### 2. Commands Tab Issues
- [ ] **Edit button**: Does nothing - needs to open GUI dialog for editing command
- [ ] **New button**: Only asks for name - needs proper form with all fields

### 3. Agents Tab Issues
- [ ] **Remove "Template" field from New Agent dialog** - user doesn't understand why it's there
- [ ] **Remove "Template" field from Edit Agent dialog** - same issue
- [ ] **Agent Library - Add Template**: Missing fields:
  - Subfolder
  - Category
  - Color
- [ ] **Agent Library - Edit Template**: Uses text editor - should use proper GUI form with ALL fields

---

## REQUIREMENTS
- All Add/Edit operations MUST use proper GUI forms, NOT text editors
- All forms MUST have ALL relevant fields
- Use status line for feedback instead of excessive QMessageBox pop-ups
- Consistent experience across all tabs (Agents, Skills, Commands, MCP)
