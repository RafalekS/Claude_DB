Im thinking about a rewrite of some of the functionality

I think we did it incorrectly at the beginning - I think the program structure is not correct
there are several tabs that are separate but Im not sure they should be as they use the same settings files.

for example hooks, statusline, permissions, model config, settings all use the ~/.claude/settings.json file (for user config) and 
.claude/settings.local.json and .claude/settings.local.json  for project config.

Im just thinking maybe there should be a better way to organize this and reduce number of tabs

Maybe make everything to be organised like Projects tab?
For projects that would mean to manage everything to do with a project, have only one project folder button to pick the working project folder and sub tabs to manage everything for a project

Then there would be User tab to manage everything to do with user config:

## 🧭 User (Global) Settings

| Setting / Component   | Location                                             |
| --------------------- | ---------------------------------------------------- |
| Hooks                 | `~/.claude/settings.json`                            |
| Statusline            | `~/.claude/settings.json`                            |
| Model selection       | `~/.claude/settings.json`                            |
| Temperature           | `~/.claude/settings.json`                            |
| Theme                 | `~/.claude/settings.json`                            |
| Permissions           | `~/.claude/settings.json`                            |
| Commands              | `~/.claude/commands/*.md`                            |
| Agents                | `~/.claude/agents/*.md`                              |
| MCP Servers           | `~/.claude.json`                                     |
| Skills                | `~/.claude/skills/*.md`                              |
| Plugins               | `~/.claude/plugins/`                                 |
| Plugin Hooks          | `~/.claude/plugins/<plugin>/hooks/*.json`            |
| Plugin Agents         | `~/.claude/plugins/<plugin>/agents/*.md`             |
| Plugin Commands       | `~/.claude/plugins/<plugin>/commands/*.md`           |
| Plugin MCP Servers    | `~/.claude/plugins/<plugin>/mcp.json`                |
| Environment Variables | Stored externally (e.g., shell / system environment) |
| Credentials / Tokens  | `~/.claude/cache/`                                   |
| Cache                 | Stored externally (e.g., shell / system environment) |
| Logs                  | `~/.claude/logs/`                                    |
| Session History       | `~/.claude/projects/`                                |
| Local Package Files   | `~/.claude/local/`                                   |


and then Project tab for these:

## 🧩 Project Settings

| Setting / Component   | Location                                                                                   |
| --------------------- | ------------------------------------------------------------------------------------------ |
| Hooks                 | `<project_folder>/.claude/settings.json` or `<project_folder>/.claude/settings.local.json` |
| Statusline            | `<project_folder>/.claude/settings.json` or `<project_folder>/.claude/settings.local.json` |
| Model selection       | `<project_folder>/.claude/settings.json` or `<project_folder>/.claude/settings.local.json` |
| Temperature           | `<project_folder>/.claude/settings.json` or `<project_folder>/.claude/settings.local.json` |
| Theme                 | `<project_folder>/.claude/settings.json` or `<project_folder>/.claude/settings.local.json` |
| Permissions           | `<project_folder>/.claude/settings.json` or `<project_folder>/.claude/settings.local.json` |
| MCP Servers           | `<project_folder>/.mcp.json` or `~/.claude.json` (global fallback)                         |
| Commands              | `<project_folder>/.claude/commands/*.md`                                                   |
| Agents                | `<project_folder>/.claude/agents/*.md`                                                     |
| Skills                | `<project_folder>/.claude/skills/*.md`                                                     |
| Plugins               | `<project_folder>/.claude/plugins/`                                                        |
| Plugin Hooks          | `<project_folder>/.claude/plugins/<plugin>/hooks/*.json`                                   |
| Plugin Agents         | `<project_folder>/.claude/plugins/<plugin>/agents/*.md`                                    |
| Plugin Commands       | `<project_folder>/.claude/plugins/<plugin>/commands/*.md`                                  |
| Plugin MCP Servers    | `<project_folder>/.claude/plugins/<plugin>/mcp.json`                                       |
| Local Overrides       | `<project_folder>/.claude/settings.local.json` (user-specific, gitignored)                 |
| Environment Variables | Read from environment at runtime (not stored in config)                                    |
| Session / History     | `<project_folder>/.claude/sessions/`                                                       |


I think plugins should still have a separate tab
