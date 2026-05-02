# Remote Claude — Implementation Plan

## Goal

Allow Claude_DB to connect to remote Linux servers over SSH, scan their `~/.claude/`
directory structure, and present the same tabs and editing capabilities as for the
local machine.

**Target systems**
| Label | User@Host | Key |
|-------|-----------|-----|
| Pi 1 (local dev Pi) | `pi@192.168.0.97` | `C:\Users\r_sta\.ssh\P16_id_rsa` |
| Pi 2 | `pi@192.168.0.169` | `C:\Users\r_sta\.ssh\P16_id_rsa` |
| QNAP | `rls1203@192.168.0.166` | `C:\Users\r_sta\.ssh\P16_id_rsa` |

---

## Architecture Overview

The current app hard-wires `Path` objects and local filesystem I/O throughout
`ConfigManager`, `project_scanner`, and many tabs.  The cleanest approach that
avoids rewriting every tab is a **pluggable filesystem layer**:

```
┌─────────────────────────────────────────────────────┐
│                  Existing Tabs                       │
│  (unchanged API — still call config_manager.*)       │
└────────────────────┬────────────────────────────────┘
                     │
           ┌─────────▼──────────┐
           │   ConfigManager    │  ← same interface as today
           │  (refactored I/O)  │
           └─────────┬──────────┘
                     │ delegates file ops to:
          ┌──────────┴──────────┐
          │                     │
  ┌───────▼──────┐    ┌─────────▼────────┐
  │ LocalFS      │    │ RemoteFS (SFTP)   │
  │ (thin Path   │    │ paramiko-based;   │
  │  wrapper)    │    │ TTL cache         │
  └──────────────┘    └──────────────────┘
```

A new **ServerContext** object (parallel to `ProjectContext`) holds the active
server. When the user switches servers, a signal fires and all tabs reload — the
same pattern already used for project switching.

---

## New Dependency

```
paramiko >= 3.4
```

Add to `requirements.txt` / `help/requirements.txt`. Paramiko handles SSH
connections, SFTP file transfers, and OpenSSH private key loading on Windows.

---

## New Modules

### `modules/remote/` package

#### `ssh_client.py`
- Class `SSHClient` wrapping `paramiko.SSHClient`
- Methods: `connect()`, `disconnect()`, `is_alive()`, `exec_command(cmd)`,
  `get_sftp()` (returns cached `paramiko.SFTPClient`)
- Reconnects automatically on stale connection
- Loads OpenSSH private key from configured path
- Raises `SSHConnectionError` (custom exception) on failure

#### `remote_filesystem.py`
- Class `RemoteFileSystem`
- Mirrors the subset of `pathlib.Path` operations used by `ConfigManager`
  and `project_scanner`: `exists()`, `is_dir()`, `is_file()`, `iterdir()`,
  `read_text()`, `write_text()`, `read_bytes()`, `stat()`, `glob()`,
  `mkdir(parents, exist_ok)`, `unlink()`
- All reads cached with TTL (configurable, default 30 s)
- Cache invalidated on any write to the same path
- Thread-safe (reads happen on Qt main thread; keep it simple for now)

#### `local_filesystem.py`
- Class `LocalFileSystem` — thin wrapper over `pathlib.Path`
- Same interface as `RemoteFileSystem` so code can use either interchangeably

#### `server_context.py`
- Class `ServerContext(QObject)` with signal `server_changed(server_config: dict)`
- `get_active()` → returns current server dict or `None` for local
- `set_active(server_config)` → emits signal
- `is_local()` → bool

#### `server_registry.py`
- Loads/saves server list from `config/config.json` under key `remote_servers`
- Each entry: `{name, host, port, user, key_path, enabled}`
- CRUD: `list_servers()`, `add_server()`, `update_server()`, `remove_server()`

### `modules/remote/__init__.py`

---

## Changes to Existing Modules

### `utils/config_manager.py`

Refactor all `Path.read_text()`, `Path.write_text()`, `open()`, `Path.exists()`,
`Path.iterdir()`, `Path.glob()` calls to go through a `FileSystem` object stored
as `self._fs`.

Constructor gains an optional `fs=None` parameter:
- `fs=None` → uses `LocalFileSystem()`
- `fs=RemoteFileSystem(ssh_client, remote_home)` → remote mode

`claude_dir` becomes a virtual path object provided by the filesystem layer
(a plain `str` on remote, a `Path` on local) — or we keep it as a `str` and let
the filesystem resolve it.

**Estimated changes:** ~80 lines touched, mostly mechanical substitutions.
No tab changes needed if the interface stays identical.

### `utils/project_scanner.py`

`scan_projects()`, `find_project_encoded_dir()`, `get_project_sessions()` all
use `Path.iterdir()`, `Path.glob()`, and `open()`.

Add an optional `fs=None` parameter to each public function.  When `fs` is
provided (remote), use it instead of direct `Path` calls.  `ConfigManager`
passes its `_fs` when calling scanner functions.

### `main.py`

- Instantiate `ServerContext` and pass to tab constructors that need it
- On `ServerContext.server_changed`: reconnect SSH, rebuild `RemoteFileSystem`,
  rebuild `ConfigManager` with new fs, call `reload_all()` on each tab
- Add `SSHClient` lifecycle management (connect on server select,
  disconnect on server change or app close)

---

## UI Changes

### New tab: Remote Servers (in Settings or as top-level tab)

**Server list panel** (left):
- `QListWidget` showing servers with status dot (green = connected,
  grey = not connected, red = error)
- Buttons: Add, Edit, Remove, Test Connection
- "Local" entry always present at top and cannot be deleted

**Server editor panel** (right):
- Fields: Display name, Host/IP, Port (default 22), Username, SSH key path
  (file-picker button), Optional: remote claude dir override (default `~/.claude`)
- "Test Connection" button — attempts SSH and reports success or error message

**Active server indicator** in the main window title bar or status bar:
`Claude_DB — pi@192.168.0.97` or `Claude_DB — Local`

### Server selector widget (persistent, top of window)

A compact `QComboBox` or `QToolButton` menu in the toolbar area showing
`📡 pi@192.168.0.97 ▾` (or `💻 Local`). Switching triggers `ServerContext.server_changed`.

### Tab behaviour on server switch

All tabs that currently show Claude data call `refresh()` / `reload()` when
`ServerContext.server_changed` fires. Tabs that are purely informational
(Documentation, About) ignore the signal.

Remote editing confirmation: tabs that write files show a yellow info banner
`"Editing on remote: pi@192.168.0.97"` above the editor to prevent accidental
remote changes. Writes go via SFTP.

---

## Implementation Phases

### Phase 1 — Foundation (no UI yet)

1. Add `paramiko` to requirements
2. Implement `local_filesystem.py` and `remote_filesystem.py`
3. Implement `ssh_client.py` with connect / disconnect / exec / sftp
4. Refactor `ConfigManager` to use `_fs` layer (keep all existing tests green)
5. Refactor `project_scanner.py` to accept optional `fs` parameter
6. Add `server_registry.py` (read/write from config.json)
7. Add `server_context.py` (QObject with signal)

### Phase 2 — Remote server management UI

1. Build **Remote Servers** settings tab with list + editor
2. Wire "Test Connection" button
3. Add active-server indicator to main window toolbar
4. Wire `ServerContext.server_changed` → rebuild ConfigManager + reload tabs

### Phase 3 — Read-only remote browsing

1. Verify all read tabs (Conversations, Project Memories, File History,
   Shell Snapshots, Projects list, Settings viewer) work correctly over SSH
2. Add TTL cache controls (cache duration in Remote Servers settings)
3. Add "remote" badge / banner to UI when a remote server is active
4. Handle connection errors gracefully (show error in each tab, retry button)

### Phase 4 — Remote editing

1. Enable writes for: CLAUDE.md, settings.json, hooks, permissions, agents,
   commands, MCP config
2. Add "Editing on remote" warning banner on all editor tabs
3. Confirm-before-save dialog for remote writes (optional, configurable)
4. Test all write paths on Pi 1 first, then Pi 2 and QNAP

### Phase 5 — Polish

1. SSH keepalive (send keepalive packets every 30 s to prevent idle timeout)
2. Connection status polling (background QTimer, updates status dot)
3. Cached directory listing with manual Refresh button
4. Performance: stream large JSONL files in chunks rather than full SFTP download
5. Store last-used server in config so it reconnects on next app launch

---

## Technical Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| SSH library | `paramiko` | Pure Python, works on Windows without system OpenSSH, loads private keys directly, proven in production |
| File abstraction | Filesystem wrapper class | Avoids rewriting every tab; only `ConfigManager` and `project_scanner` need changes |
| Remote path type | `str` everywhere inside filesystem layer; expose same `Path`-like API | Remote paths are POSIX strings; wrapping avoids Windows/POSIX confusion |
| Caching | In-memory dict with TTL | SFTP round-trips are ~5–20 ms each; caching avoids hammering the Pi |
| Thread model | All SSH on Qt main thread for now | Simpler; SFTP reads on a Raspberry Pi over LAN are fast enough; revisit if UI freezes become a problem |
| Write confirmation | Warning banner (not blocking dialog) | Less friction for quick edits; user can see they're on remote at a glance |
| Windows key format | paramiko `RSAKey.from_private_key_file()` | Reads OpenSSH/PEM format keys on Windows without needing system SSH agent |

---

## File Layout After Implementation

```
src/
├── modules/
│   └── remote/
│       ├── __init__.py
│       ├── ssh_client.py
│       ├── local_filesystem.py
│       ├── remote_filesystem.py
│       ├── server_context.py
│       └── server_registry.py
├── tabs/
│   └── remote_servers_tab.py       ← new tab
└── utils/
    ├── config_manager.py           ← _fs layer added
    └── project_scanner.py          ← fs= param added

config/
└── config.json                     ← remote_servers key added
```

---

## Risk / Open Questions

- **QNAP SSH**: Container Station may run Claude inside a Docker container with
  a different home directory. May need a configurable `remote_claude_dir` override
  per server (already planned in server config).
- **Large JSONL files**: Session files can be many MB. Full SFTP download for
  every conversation load may be slow. Phase 5 will address streaming.
- **Concurrent access**: If Claude is actively writing to a JSONL file while we
  read it over SFTP, we may get a partial read. Low-risk for read-only browsing.
- **Key passphrase**: `P16_id_rsa` appears to be passphrase-free (used in
  automated contexts). If a future key has a passphrase, we'll need a
  passphrase prompt dialog.
