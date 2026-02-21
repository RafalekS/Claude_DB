# ClaudeSync GUI Requirements Document

## Overview
A graphical user interface for the ClaudeSync command-line application using CustomTkinter framework. The GUI should provide access to all CLI commands and configuration options while maintaining a modern, user-friendly interface.

## Technical Specifications

### Framework & Dependencies
- Primary Framework: CustomTkinter
- Additional Dependencies:
  - CTkToolTip for tooltips
  - Standard Python libraries (logging, configparser, subprocess, etc.)

### Minimum Requirements
- Window Size: Minimum 800x600, resizable
- Python Version: Compatible with latest version
- Claude.ai Pro/Team Plan required

## Core Features

### Window Structure
1. Main Navigation:
   - Authentication Tab
   - Projects Tab
   - Sync Tab
   - Chat Tab
   - Configuration Tab
   - Logs Tab
   - Status Bar at bottom

2. Status Bar Information:
   - Connection status
   - Currently active project
   - Last sync time
   - Current operation status

### Authentication & Session Management
- Handle login/logout operations
- Track session expiry (1 week advance warning)
- Organization selection
- Store session information in config file

### Project Management
- Support all project operations:
  - Select/Create/List/Archive projects
  - File management
  - Submodule management
- Confirmation dialogs for dangerous operations

### Sync Functionality
- Preview files before sync (simple list view)
- Progress bar for sync operations
- Support all sync modes (normal, uberproject, category)
- Scheduler:
  - Daily and Weekly options
  - Time selection
  - Day selection for weekly schedule

### Chat Management
Support all chat operations:
- List chats
- Create chat
- Delete chats
- Send messages
- Sync chats
Basic interface only, no advanced chat features

### Configuration Management
- INI format config file (claudesync.conf)
- Apply button for saving changes
- Theme selection (default: dark-blue)
- All CLI config options accessible
- Category management

### Logging System
- GUI log viewer with:
  - Log level filtering (INFO, WARNING, ERROR)
  - Search functionality
  - Clear logs button
  - Export logs button
- File-based logging:
  - Rotating log files
  - Max 5MB per file
  - Keep 5 backup files
  - UTF-8 encoding

### Update Management
- Check for updates on startup
- Show progress while checking
- Silent check with notification if update available
- Option for automatic update
- Manual update option

### Error Handling
- Appropriate error dialogs
- Based on FAQ.md and Troubleshooting.md
- Detailed error logging

### UI/UX Features
- Tooltips on all interactive elements (using CTkToolTip)
- Confirmation dialogs for potentially dangerous operations
- Progress indicators for long-running operations
- Responsive layout that scales with window size

## Configuration File Structure
```ini
[General]
theme = dark-blue
language = en
first_run = true
min_width = 800
min_height = 600
log_level = INFO
log_file = claudesync.log

[Authentication]
session_key = 
session_expiry = 
active_provider = claude.ai
active_organization_id = 

[Project]
active_project_id = 
active_project_name = 
local_path = 

[Sync]
upload_delay = 0.5
max_file_size = 32768
two_way_sync = false
prune_remote_files = false

[Schedule]
enabled = false
frequency = daily
time = 00:00
days = 

[Categories]
# Will be populated with custom categories like:
# category_name = {"description": "desc", "patterns": ["pattern1", "pattern2"]}
```

## First Run Behavior
- Check/create configuration file
- Request necessary setup information
- Verify Claude.ai access
- Set initial configuration

## CLI Integration
- Support all CLI commands from quick-reference.md
- Handle command execution via subprocess
- Capture and display command output
- Error handling for failed commands

## Additional Notes
- OS native file dialogs for file/folder selection
- No keyboard shortcuts required
- Modern, clean interface design
- All widgets must be scalable with window resizing
