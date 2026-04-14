# Refactor & Fix Log

All reported issues and requested fixes with resolution notes.

---

1. **New tabs (Rules, CLAUDE.local.md, Worktrees, Agent Teams, Remote Control) appearing as standalone main tabs**
   These are subtabs inside UserConfigTab and ProjectConfigTab only. Removed from main.py all_tabs; added as subtabs to both container tabs.

2. **Standalone Hooks main tab created**
   Hooks is a subtab in User and Project Config, not a main tab. Removed HooksTab from main.py entirely.

3. **Standalone Projects main tab created**
   Projects is a subtab under Project Config only. Removed ProjectsTab from main.py main tab list.

4. **Standalone Model Config main tab created**
   Model Config belongs as subtab under User/Project Config. Removed ModelConfigTab from main.py main tab list.

5. **Skill Sources buttons (Add/Remove/Reset) separated from table by splitter**
   Buttons belong inside the same group as the table; splitter should resize the whole group. Removed inner splitter, placed buttons directly in the group layout below the table.

6. **Worktrees table columns not resizable**
   Per coding skill: never use setStretchLastSection or Stretch mode. All three columns now use Interactive mode with explicit initial widths; no setStretchLastSection call.

7. **Theme switching shows mixed old/new themes across the app until restart**
   Root cause: per-widget setStyleSheet() calls capture colors at construction time and override the global app stylesheet on theme change. Fixed by updating global QGroupBox style in generate_app_stylesheet() to use ACCENT_PRIMARY border, adding combobox-popup:0 to global QComboBox, and removing 33 stale QGroupBox and 9 QTabWidget per-widget stylesheets across all tabs.

8. **Preferences tab widgets showing different theme from other tabs (backup section)**
   Same cause as #7 — per-widget QGroupBox/QComboBox/QSpinBox/QTabWidget stylesheets in preferences_tab.py. All removed; global app stylesheet now handles them correctly on theme change.

9. **Project Config sub_tabs showing stale colors after theme change**
   self.sub_tabs.setStyleSheet(...) in project_config_tab.py captured colors at init. Removed per-widget stylesheet; inherits from global app stylesheet.

10. **Skill dialog missing 9 frontmatter fields (Review #23)**
    Added effort, paths, context, user-invocable, disable-model-invocation, agent, shell, hooks to both NewSkillDialog and EditSkillDialog. Fixed critical bug where EditSkillDialog discarded existing skill body on save.

11. **Model dropdowns showing outdated model names**
    Updated all model dropdowns and comparisons to current Claude 4.6 family: Sonnet 4.6, Opus 4.6, Haiku 4.5.

12. **Memory tab outdated/incorrect information**
    Rewrote overview HTML with correct memory hierarchy, auto memory system, /compact command, and storage paths. Added Projects subtab for browsing session JSONL files.

13. **No draggable dividers in settings panels**
    Added QSplitter(Vertical) in user_settings_subtab.py between form area and JSON preview. Added outer QSplitter in preferences_tab.py Skills subtab between directories group and sources group.

14. **About section missing dividers**
    Pending.

15. **Preferences backup section different theme from rest of app**
    Caused by per-widget QGroupBox.setStyleSheet() — fixed as part of #7/#8.
