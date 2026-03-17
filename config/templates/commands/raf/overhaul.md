# Command: overhaul

## Purpose
Perform a full architectural refactor and PyQt6 migration of the provided Python project while preserving all functionality and enforcing modern engineering standards.

---

## Execution Mode
One-shot transformation of entire project.

Confirm before destructive changes.

---

## Primary Objectives

1. Preserve all existing functionality.
2. Refactor codebase to modern Python standards.
3. Remove dead code and duplication.
4. Fix detected bugs.
5. Migrate GUI to PyQt6 (if not already).
6. Ensure cross-platform compatibility:
   - Windows (primary)
   - Debian Linux (secondary)
7. Externalize all configuration.
8. Persist UI layout settings.
9. Generate `summary.md`.
10. Commit and push changes to GitHub (if configured).

---

## Architecture Rules

- Enforce modular project structure.
- Merge duplicate logic into reusable components.
- Remove unused imports and libraries.
- No dead code.
- Maintain strict separation of:
  - UI
  - Business logic
  - Configuration

---

## GUI Requirements (PyQt6)

### Hard Rules

- Never use `setFixedWidth()` on `QPushButton`.
- Never use `header.setStretchLastSection(True)`.

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

### Appearance

- Professional
- Modern
- Fully resizable layouts

---

## Configuration Rules

- No hardcoded paths.
- No hardcoded values.
- Never rely on `~` expansion (Python does NOT expand it automatically).
- Use OS-agnostic path handling.
- Store all settings in config file.
- Config must work on Windows and Debian.

---

## CLI Handling

If the project is terminal-based:

Ask the user whether a PyQt6 GUI should also be developed.

---

## Cross-Platform Requirements

- No Windows-only APIs.
- No Linux-only assumptions.
- Use `pathlib`.
- Ensure consistent behavior across OS.

---

## Finalization Steps

1. Generate `summary.md` containing:
   - Changes made
   - Bugs fixed
   - Structural improvements
   - Migration details
2. Create clean commit.
3. Push to GitHub (if remote configured).

---

## Constraints

- Do NOT remove functionality.
- Do NOT lock table columns.
- Do NOT restrict automatic button sizing.