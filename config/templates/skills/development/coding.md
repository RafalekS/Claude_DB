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

## Git Repository Rules

Always include `.gitattributes`:
* text=auto eol=lf

---

## Coding Rules

- Enforce modular design
- Merge duplicate logic into reusable components
- NEVER hardcode paths, values, or formatting
- EVERYTHING configurable must be in config
- If unsure → ASK (do NOT guess)

---

## Tables & Lists (MANDATORY)

ALL tables MUST support:

- Resizable columns (manual drag)
- Reorderable columns
- Sortable columns
- Persistent column order
- Persistent column width
- Persistent sorting state

Also persist:

- Window geometry
- Dialog sizes
- UI preferences

---

## Testing & Completion

- Nothing is complete until user tests it
- ALWAYS ask user to test (especially GUI)
- DO NOT run GUI apps for the user

---

## Change Control

- NEVER remove or change functionality without explicit approval

---

## Execution Rules

Allowed:

- Syntax checks (`python -m py_compile`)
- Non-interactive commands
- File operations

---

## Error Handling (STRICT)

- NEVER suppress errors
- NEVER use `except: pass`
- NEVER hide stderr/logs
- ALWAYS fix root cause

---

## Development Environments

### PowerShell
Version: > 7.5.4 with custom config.
ALWAYS give the user one-liners. Do not use backslash line continuation.

### Bash
WSL2 Ubuntu 24.
Prefer dedicated tools over bash commands for file operations.

### Python

- Version: 3.1x
- Use `python`, NOT `python3`
- Syntax check: `python -m py_compile`
- GUI: PyQt6
- All buttons MUST have visible captions

---
# PyQt6 Guidance (CRITICAL)

## QTableWidget / QTableView — STRICT CONTRACT

### REQUIRED BEHAVIOUR

- All columns must be manually resizable
- Columns must be reorderable
- Sorting must work correctly
- Column order, width, and sorting MUST persist
- No column may become locked or non-resizable

---

## HARD FAIL CONDITIONS (INVALID IMPLEMENTATION)

Any implementation containing the following is **invalid** and must be corrected before submission:

* **Prohibited Attributes:**
    * `setStretchLastSection(True)` is used anywhere (Delete it).
    * Any column uses `ResizeMode.Stretch` (Change to `Interactive`).
* **Logic Errors:**
    * Sorting is enabled **during** data population.
    * `restoreState()` is called inside a loop or after every `populate()` call (Move to startup only).
* **Behavioral Failures:**
    * The last column cannot be resized manually.
    * Columns "snap back" to default sizes after a user resizes them.
    * Column order, widths, or sorting states do not persist after a restart.

---

## REQUIRED HEADER CONFIGURATION (DO NOT MODIFY)

```python
header = table.horizontalHeader()

for i in range(table.columnCount()):
    header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)

header.setSectionsMovable(True)
```

### RULES

- Apply immediately after table creation
- DO NOT replace with shortcuts
- DO NOT introduce Stretch unless explicitly required
- DO NOT use `setStretchLastSection`
- DO NOT “improve” or rewrite this logic

---

## SORTING RULE (STRICT ORDER — DO NOT CHANGE)

```python
populate_table()

table.setSortingEnabled(True)

restore_table_state()
```

- Sorting MUST be disabled during population

---

## STATE PERSISTENCE (MANDATORY)

### REQUIRED STARTUP SEQUENCE (STRICT ORDER)
1.  **Initialize UI**: Setup windows and instantiate empty tables.
2.  **Configure Headers**: Apply `Interactive` resize mode and `setSectionsMovable(True)`.
3.  **Populate Data**: Load initial data/rows into the table.
4.  **Enable Sorting**: Set `table.setSortingEnabled(True)`.
5.  **Restore State**: Execute `restore_table_state()` once to apply saved widths and sort order.

### PERSISTENCE LOGIC
```python
# Save/Restore bytearray for ordering and sorting
state = table.horizontalHeader().saveState()
table.horizontalHeader().restoreState(state)
```
* Note: Save explicit column widths via columnWidth(i) as a list and restore via setColumnWidth(i, w) during startup. Do NOT call restoreState() after every population; Interactive mode naturally maintains widths across setRowCount(0) refreshes.

### NUMERIC SORTING
Any column displaying formatted numbers (bytes, duration, counts, IDs) MUST use a NumericItem (QTableWidgetItem subclass). Standard items sort lexicographically (e.g., "9 GB" > "10 GB"), which is strictly prohibited.


## STATE SAVE/LOAD RULES

### Debounced Save

- Use `QTimer`
- 500ms delay
- `setSingleShot(True)`
- Restart on every change

### Save Triggers

- Column resize
- Column reorder
- Sort change
- `hideEvent()`
- `closeEvent()` (force immediate save)

### Load Order

1. Populate table
2. Enable sorting
3. Restore state

---

## SIGNAL BLOCKING (MANDATORY)

```python
widget.blockSignals(True)
# restore state
widget.blockSignals(False)
```

---

## Path Handling (CRITICAL)

Python does NOT expand `~`.

ALWAYS:

```python
os.path.expanduser()
os.path.expandvars()
```

Applies to ALL:

- config paths
- user input
- JSON values

Use `$HOME` in deploy configs, but STILL expand in Python.

---

## UI Rules

### Output Panels

Use `QPlainTextEdit` for:

- logs
- errors
- command output

---

### QPushButton

- NEVER use `setFixedWidth`
- Let Qt auto-size

---

### Windows Taskbar Icon

`setWindowIcon()` is NOT enough.

Use `SendMessageW` with `ICON_BIG` AFTER `window.show()`.

Taskbar icon: After window.show(), send WM_SETICON via ctypes with LoadImageW.restype = ctypes.c_void_p (required on 64-bit Windows) — without it, the HANDLE is truncated to 32-bit and the taskbar shows the generic placeholder icon.
---

### Subprocess (GUI apps)

When using `pythonw`:

- ALWAYS call `no_window()` for subprocesses

---

### QComboBox Dropdown Fix

Fusion style ignores `setMaxVisibleItems()`.

Use:

- `combobox-popup: 0;`
- set `max-height` via stylesheet

---

# Final Rule

Do NOT simplify, optimize, or replace defined patterns.
Follow this document EXACTLY.