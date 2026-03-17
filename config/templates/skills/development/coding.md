---
name: coding
description: Development, coding and programming standards for all projects. Includes project structure (help/, config/, backup/, modules/), Python/PyQt6 specifics, PowerShell/Bash preferences, Docker setup, and coding best practices. Use when writing code, starting projects, programming, writing python or discussing development work.
---

# Development & Coding Standards

## Scope
Use these standards whenever writing code, starting projects, programming, writing Python, or discussing development work.

## Project Structure and Documentation
Every project you work on must include these folders and files:

project_name/
├── CLAUDE.md           # Prompt instructions for claude code
├── help/               # Default folder for documentation files
│   ├── TODO.md         # Progress tracking, issues, new features, improvements
│   └── README.md       # Final project description and usage instructions (created after project is completed)
├── backup/             # Program backups
├── config/             # Program configuration files, API definitions, database files, etc.
│   ├── assets/         # Program icons
│   ├── ui/             # GUI UI configuration (optional - GUI projects only)
│   ├── themes/         # Theme files (GUI projects only)
│   └── config.json     # Program configuration (or config.ini for simple projects)
├── modules/            # Always create modular programs stored here; group functions by functionality; split front and backend
└── logs/               # Application logs

Do not create documentation in other or multiple separate files unless asked to.

### help/TODO.md Rules (Mandatory)
1. Concise and actionable: focus on WHAT needs to be done, not detailed documentation of what WAS done.
2. No duplication: do not repeat information already in the file.
3. Update after each completed step, phase, new requirement, or user-reported issue.
4. Organized structure: keep related items grouped together with clear headers.
5. Reference, do not document: point to code files (e.g., "See modules/database.py") instead of documenting implementation details.
6. Focus on pending work: current tasks and decisions needed, not comprehensive summaries.
7. Scannable: you should be able to quickly see what's pending and what's next.
8. Remove stale content: delete outdated information and old notes that are no longer relevant.
9. Clean up and compact after big updates.
10. Note down the mistakes you made and how you fixed them.

## Coding Rules
Always include a .gitattributes file at the root with * text=auto eol=lf to normalise all line endings to LF in the repository, preventing CRLF/LF conflicts on Windows
### Structure
Enforce modular project structure.
Merge duplicate logic into reusable components.

### Tables & Lists Must Support

- Resizable columns
- Reorderable columns
- Sortable columns
- Persistent column order
- Persistent column width
- Persistent sorting state

### Persist Also

- Window geometry
- Dialog sizes
- UI preferences

### Testing and Completion
Nothing can be marked as done and working until the user has tested it.
The user prefers to test themselves. ALWAYS ask the user to test programs instead of running them yourself (especially GUI).

### Change Control
Before removing or changing any functionality, you MUST ask the user for permission first.

### Allowed Actions
You can run commands that check syntax (for example `python -m py_compile`), non-interactive commands, file manipulation, etc.

### Dont's and Error Handling
Never hardcode paths, variables, values, formatting, or styles in program code. Use variables that can be saved in the config file.
If you are unsure, DO NOT guess API mappings, config schemes, table or field names, etc. Ask the user first.
NEVER suppress or silence errors. Do not set logger levels to hide errors, do not add broad `except: pass`, and do not redirect stderr to `/dev/null`. Find and fix the ROOT CAUSE. Suppressing errors hides real bugs and lets them compound.

## Development Environments

### PowerShell
Version: > 7.5.4 with custom config.
ALWAYS give the user one-liners. Do not use backslash line continuation.

### Bash
WSL2 Ubuntu 24.
Prefer dedicated tools over bash commands for file operations.

### Python
Version: Python 3.1x.
GUI: PyQt6.
Syntax validation: `python -m py_compile`.
When running Python, do not use the `python3` executable.
If a button is displayed on the screen, it MUST have a visible caption.

## PyQt6 Guidance

### QTableWidget Column Handling (Critical)
Never use `header.setStretchLastSection(True)` if you want ALL columns to be resizable by the user.
`setStretchLastSection(True)` LOCKS the last column and prevents manual resizing.

```python
# CORRECT: all columns including last can be resized
header = table.horizontalHeader()
header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
# Do NOT call setStretchLastSection at all
```

Every table header must also have:
- `header.setSectionsMovable(True)` (not set by default)
- Disable sorting before populating, re-enable after. `setSortingEnabled(True)` during population causes items to land in wrong rows.
- Apply all header settings at creation time. Widgets outside MainWindow are not covered by any generic restore loop.

### Path Expansion (Critical)
Python does NOT expand `~` in paths.

`os.makedirs("~/.test")` creates a LITERAL directory named `~`, not the home directory.
ALWAYS use `os.path.expanduser()` (and `os.path.expandvars()` for `$HOME`) before any file operation. This applies to ALL paths read from config files, JSON, or user input. They are plain strings, NOT shell-expanded.
When building config JSON to deploy to remote systems, use `$HOME` (expanded by bash in deploy scripts) instead of `~` (not expanded by Python). But ALWAYS expanduser/expandvars on the Python side too as a safety net.

### Table View State Persistence
When implementing table column manipulation (sort, resize, reorder, filter) with persistence between program runs:

1. Use QTimer for debounced saving.
   Save state 500ms after last change (prevents saving 50+ times during drag).
   Use `QTimer.setSingleShot(True)` and restart on each change.

2. Save on application close.
   Override `hideEvent()` to save when tab hidden.
   Override `closeEvent()` to save when window closes.
   Stop debounce timer and save immediately (bypass delay).

3. Load state after table population.
   Populate table with data FIRST.
   Enable sorting SECOND.
   Load saved state LAST (so sort/widths can be applied).

4. Block signals during load.
   Use `widget.blockSignals(True)` before setting values from saved state.
   Prevents triggering multiple refresh/reload cycles.
   Always unblock after: `widget.blockSignals(False)`.

5. Correct load order example:
```python
def load_data(self):
    # 1. Populate table
    self.table.setRowCount(0)
    for row_data in data:
        # Add rows

    # 2. Enable sorting
    self.table.setSortingEnabled(True)

    # 3. Load saved state (widths, order, sort)
    self.view_state.load_state(self.table, "table_id")
```
### Dialogs, warnings, errors
Use QPlainTextEdit for all output (errors, status, command outputs) so it is easy for user to copy it from the screen.

### QPushButton Width (Critical)
Never use `setFixedWidth` on `QPushButton`. Let Qt auto-size buttons to fit their text content.

### Windows Taskbar Icon (PyQt6)
`setWindowIcon()` only sets the title bar icon. For the Windows taskbar icon, use:
`ctypes.windll.user32.SendMessageW(hwnd, 0x0080, ICON_BIG, hicon)` via `LoadImageW` after `window.show()`.

### Prevent Console Windows in GUI Apps
When using `pythonw`, always call `no_window()` (from `subprocess_utils`) on every `subprocess.run()` or `subprocess.Popen()` call.

### QComboBox Dropdown Height Fix (PyQt6)
Fusion style ignores `setMaxVisibleItems()`. Use `combobox-popup: 0;` in the stylesheet and set `max-height` on the view's stylesheet to limit dropdown height.