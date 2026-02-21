# Claude_DB Template System

## Overview

Claude_DB uses a unified template system where ALL templates are stored as `.md` files in organized folders. This allows you to easily add, modify, or remove templates by simply dropping files in the appropriate folder.

## Folder Structure

```
config/templates/
├── agents/          # Agent templates (.md files)
├── skills/          # Skill templates (.md files)
├── commands/        # Command templates (.md files)
├── mcp/             # MCP server templates (.json files)
├── hooks/           # Hook templates (.md files)
└── statuslines/     # Statusline templates (.md files)
```

## How It Works

### Adding Templates

Simply drop a properly formatted file into the appropriate folder:
- **Agents**: `config/templates/agents/your-template.md`
- **Skills**: `config/templates/skills/your-template.md`
- **Commands**: `config/templates/commands/your-template.md`
- **MCP Servers**: `config/templates/mcp/your-server.json`

The template will automatically appear in the GUI dropdown when creating new items.

**Note:** MCP templates use `.json` format, all others use `.md` format.

### Template Format

#### Agents and Skills (with frontmatter)

```markdown
---
name: {name}
description: {description}
tools: Read, Grep, Glob, Bash
model: inherit
---

# Your Template Content

Your content here. Use {name}, {description}, {NAME} as placeholders.
```

#### Commands (no frontmatter)

```markdown
Your command instructions here.

Use $ARGUMENTS for command arguments.
```

#### MCP Servers (JSON format)

```json
{
  "mcpServers": {
    "server-name": {
      "command": "cmd",
      "args": [
        "/c",
        "npx",
        "-y",
        "package-name"
      ],
      "env": {
        "ENV_VAR": "value"
      }
    }
  }
}
```

**Important for Windows:** Use `cmd /c` wrapper for npx/uvx/bunx commands.

### Placeholders

Templates support automatic placeholders:
- `{name}` - Replaced with the actual name (lowercase-with-hyphens)
- `{NAME}` - Replaced with title case version
- `{description}` - Replaced with the actual description
- `{model}`, `{tools}`, `{color}`, etc. - Replaced with their values

### Current Templates

**Agents (6 templates):**
- `example-agent.md` - General template
- `code-reviewer.md` - Code review specialist
- `test-generator.md` - Test generation
- `documentation-writer.md` - Documentation specialist
- `refactoring-expert.md` - Code refactoring
- `security-auditor.md` - Security auditing

**Skills (1 template):**
- `example-skill.md` - General skill template

**Commands (3 templates):**
- `example-command.md` - Multi-format command examples
- `simple-command.md` - Simple command template
- `command-with-args.md` - Command with $ARGUMENTS

**MCP Servers (10 templates):**
- `everything-search.json` - Everything search integration
- `qnap-nas.json` - QNAP NAS integration
- `google-keep.json` - Google Keep integration
- `n8n.json` - n8n automation platform
- `mcp-mermaid.json` - Mermaid diagram generation
- `filesystem.json` - File system access (Windows)
- `github.json` - GitHub integration
- `memory.json` - Memory/knowledge base
- `puppeteer.json` - Browser automation
- `fetch.json` - Web fetching

## Adding Your Own Templates

1. Create a `.md` file with proper format
2. Drop it in the appropriate folder
3. Restart Claude_DB (or the template will appear on next load)
4. Your template appears in the dropdown!

## Unified Template Manager

All template operations use `src/utils/template_manager.py`:
- `list_templates(type)` - List available templates
- `read_template(type, name)` - Read template content
- `save_template(type, name, content)` - Save new template
- `create_from_template(type, template, name, replacements)` - Create from template

No more hardcoded templates in the code!
