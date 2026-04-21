# TODO

## #1 — Project Config: replace text field with project dropdown
- [x] Extract scan_projects / decode_project_directory_name to shared utility (utils/project_scanner.py)
- [x] Replace read-only QLineEdit in ProjectConfigTab header with QComboBox
  - Scanned projects as dropdown items
  - Browse still works; custom folders added at bottom with separator
  - 🔄 Refresh button added
  - Selecting from combo sets project_context
- [x] ProjectsTab: remove its own "Select Project" group; receive project_context and use it
- [x] ProjectsTab: add more Execute Commands buttons based on documentation/commands reference

## Codebase Cleanup (from audit)
- [ ] Extract duplicate hooks tree/add_hook logic (3× duplication across hook subtabs)
- [ ] Extract duplicate add_permission logic (3× duplication across permission subtabs)
- [ ] Fix 3× `# TODO: Save to settings file` stubs in permissions_tab.py
- [ ] Consolidate identical cache management in mcp_search_client.py and github_client.py
- [ ] Centralise hardcoded timeout values in config
- [ ] Consider splitting large files: preferences_tab.py (~1902 lines), mcp_tab.py (~1786 lines)
