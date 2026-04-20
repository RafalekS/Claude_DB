# Claude_DB — Project Instructions

## Status
All initial tasks completed. Codebase refactored, UI modernised, bugs fixed, theme system rebuilt.

## Remote Repository
This project is linked to remote repository: https://github.com/RafalekS/Claude_DB.git
When making changes, `git push` is required for the user to test.

## Key Architecture Notes

### Theme System
- All theme data lives in `config/themes/themes.json` — single source of truth
- `active_theme` key at root selects the current theme
- `config/config.json` has NO `preferences` section
- `src/utils/theme.py` — `generate_app_stylesheet()`, `apply_theme()`, `save_theme_to_file()`

### HTML Content Theming (QTextBrowser)
Body text color in HTML tabs requires a three-step approach (see memory for full details):
1. Local widget stylesheet override beats app-level QSS
2. Two-pass render via `QTimer.singleShot(0)` for async palette update
3. No inline `color:` styles in HTML — let `setDefaultStyleSheet` control colors
- `src/main.py` monkey-patches `QTextBrowser.setHtml` to track `_html_source` and apply `_doc_css`
- `src/tabs/preferences_tab.py` — `_reinject_html_css()` / `_rerender_browsers()`
- `src/tabs/documentation_tab.py` — `_p()`, `_h()`, `_wrap()` helpers must not have inline colors

### Widget Theme Editor
- `src/tabs/widget_theme_editor.py` — live editor for all Qt widget styles + HTML Content
- HTML Content overrides stored with tuple keys `(element, css_property)` in `_overrides`
- `build_document_css()` generates CSS for QTextDocument; `build_overrides_qss()` for Qt widgets

### Config
- `config/config.json` — app-level settings (project path, tab layout, UI state)
- `config/themes/themes.json` — all theme definitions + active_theme pointer

## Coding Standards
- Python 3.1x, PyQt6
- Never use `setStretchLastSection(True)` if all columns should be resizable
- Never use `setFixedWidth` on QPushButton
- Always use `os.path.expanduser()` for paths from config
- Never suppress errors — find root cause
- Nothing marked done until user has tested it
