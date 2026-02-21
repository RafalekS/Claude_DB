---
name: coding
description: Development, coding and programming standards for all projects. Includes project structure (help/, config/, backup/, modules/), Python/PyQt6 specifics, PowerShell/Bash preferences, Docker setup, and coding best practices. Use when writing code, starting projects, programming, writing python or discussing development work.
---

# Development & Coding Standards

## Projects: and Documentation
Every project you will work on should have these subfolders (and some files within these folders)

CLAUDE.md - Prompt/project instructions for claude code

help - Default folder for documentation files

help/README.md - this one is created at the project finish describing project. Brief information on how to use the program.

help/TODO.md - where progress of work and instructions for resuming in a new session are stored.
This document HAS to follow these rules:

  1. Concise and actionable - Focus on WHAT needs to be done, not detailed documentation of what WAS done
  2. No duplication - Don't repeat information already in the file
  3. It HAS to be updated after each completed step, phase, when given new requirements, user reports issues to fix
  4. Organized structure - Keep related items grouped together with clear headers
  5. Reference, don't document - Point to code files (e.g., "See modules/database.py") instead of documenting implementation details
  6. Focus on pending work - Current tasks and decisions needed, not comprehensive summaries
  7. Keep it scannable - Should be able to quickly see what's pending and what's next
  8. Remove stale content - Delete outdated information and old notes that are no longer relevant


help/PROMPT.md - this is where the initial requirements for the project/application/research are stored with a detailed plan for a project to be presented to user for acceptance. (optional)


backup - this is where program backups will be stored

config - used for storing  configuration files like program themes, API definitions, connection configs, database files, etc. 
config/assets - this is where the program icons will be stored
config/ui - for GUI programs only. this is where .ui files are stored
config/themes - for GUI programs only. this is where themes (if configured) will be stored
config/config.json - this is where the program configuration will be stored in json format or config.ini for simple projects)

modules - For complicated projects always create modular programs stoed in this subfolder, grouping functions by functionality, split front and backend.

logs - this is where logs will be stored 
tests - this is where all test files and cases will be stored

Do not create documentation in other or multiple separate files unless asked to. 
Whenever project is finished as prompted by user create a file __finished__.md in help subfolder that contains only the program name in it. That way I can always search for projects that are finished.

project_name/
├── CLAUDE.md           # Prompt instructions for claude code
├── help/
│   ├── PROMPT.md       # Initial project requirements and detailed plan (optional)
│   ├── TODO.md         # Progress tracking, issues, new features, improvements
│   ├── README.md       # Final project description and usage instructions (created after project is marked as completed)
│   └── __finished__.md # Completion marker (contains only program name)
├── backup/             # Program backups
├── config/             # Program configuration files, API definitions, database files, etc.
│   ├── assets/        # Program icons
│   ├── ui/            # GUI UI configuration (GUI projects only)
│   ├── themes/        # Theme files (GUI projects only)
│   └── config.json    # Program configuration (or config.ini for simple projects)
├── modules/           # Modular code grouped by functionality
├── tests/             # folder for all test scripts, cases, test data
└── logs/              # Application logs


## Coding Preferences
When coding nothing can be marked as done and working until I HAVE TESTED IT!!!
Before you remove any functionality or change any functionality - YOU HAVE TO ASK USER for Permission FIRST
You can run commands that check syntax (for example python -m py_compile), non-interactive commands, file manipulation, etc.
ALWAYS ask User to test visual/GUI things
Never hardcode anything in the program code. Use variables that can be saved in the config file.
If you are are unsure then DO not try to guess API mappings, config schemes, table and field names, etc. Ask the user first!

## Development Environments

### PowerShell
Version: > 7.5.4 with custom config
ALWAYS give user "one liners" - don't do any of that \ backslash line continuation bullshit

### Bash
WSL2 Ubuntu 24
Prefer dedicated tools over bash commands for file operations

### Python
Version: Python 3.1x
GUI: PyQt6 (use .ui for GUI creation via Qt Designer) or customtkinter/tkinter for simple applications
Syntax validation: python -m py_compile
User prefers to test himself. Just ask user to test the programs instead of running them yourself.

PyQt6 QComboBox Dropdown Height Fix:
Fusion style ignores setMaxVisibleItems() - use combobox-popup: 0; in stylesheet + max-height: 300px; on view's stylesheet to limit dropdown height.

make sure that if the button is displayed on the screen then it HAS to have a visible caption!!

### Docker
Prefers Docker containers in /share/Containers/ directory structure on QNAP device - managed by Container Station

### Other Technologies
Node.js LTS
Git
Debian >= Bookworm on Raspberry Pi4
Busybox on Linux NAS-RLS 5.10.60-qnap
n8n workflows