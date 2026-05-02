# Remote Claude — Implementation Plan

## Goal

Allow Claude_DB to connect to remote Linux servers over SSH, scan their `~/.claude/`
directory structure, and work on them **in exactly the same way as the local system** —
same tabs, same editing, same capabilities, no artificial restrictions.

**Target systems**
| Label | User@Host | Key |
|-------|-----------|-----|
| Pi 1 | `pi@192.168.0.97` | `C:\Users\r_sta\.ssh\P16_id_rsa` |
| Pi 2 | `pi@192.168.0.169` | `C:\Users\r_sta\.ssh\P16_id_rsa` |
| QNAP | `rls1203@192.168.0.166` | `C:\Users\r_sta\.ssh\P16_id_rsa` |

---

## Critical Constraint — One SSH Session Per Server

**Exactly one `paramiko.SSHClient` instance is maintained per remote server.**
All file operations (SFTP reads, writes, directory listings) share that single
session. The session is opened when the user connects and kept alive with
paramiko's built-in keepalive mechanism (`transport.set_keepalive(30)`).
No new connections are opened per action, per tab, or per file operation.

If the session drops unexpectedly, the remote indicator switches to an error
state and the user must reconnect manually — no silent auto-reconnect that
creates hidden extra sessions.

---

## Architecture Overview

The current app hard-wires `Path` objects and local filesystem I/O throughout
`ConfigManager`, `project_scanner`, and many tabs. The cleanest approach that
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
                     │ delegates ALL file ops to:
          ┌──────────┴──────────┐
          │                     │
  ┌───────▼──────┐    ┌─────────▼──────────────────────┐
  │ LocalFS      │    │ RemoteFS (SFTP)                 │
  │ (thin Path   │    │ shares ONE SSHClient session    │
  │  wrapper)    │    │ TTL cache for reads             │
  └──────────────┘    └────────────────────────────────┘
```

A new **ServerContext** object (same pattern as `ProjectContext`) holds the
active server. When the user switches servers, a signal fires and all tabs
reload. When local is selected, `LocalFS` is used; when a remote server is
selected, `RemoteFS` backed by that server's single SSH session is used.

---

## New Dependency

```
paramiko >= 3.4
```

Add to `help/requirements.txt`. Paramiko handles SSH connections, SFTP file
transfers, and OpenSSH private key loading on Windows — no system SSH agent needed.

---

## New Modules

### `src/modules/remote/` package

#### `ssh_client.py`

Class `ManagedSSHClient`:
- Holds **one** `paramiko.SSHClient` and **one** `paramiko.SFTPClient`
- `connect(host, port, user, key_path)` — opens the session, calls
  `transport.set_keepalive(30)` immediately, opens the SFTP channel
- `disconnect()` — closes SFTP then SSH cleanly
- `is_connected() -> bool` — checks `transport.is_active()`
- `sftp` property — returns the shared `SFTPClient` (raises if not connected)
- `exec(cmd) -> tuple[str, str]` — runs a command on the existing session,
  returns (stdout, stderr)
- No reconnect-per-action; callers check `is_connected()` and handle errors
- `SSHConnectionError` custom exception for all failures

#### `remote_filesystem.py`

Class `RemoteFileSystem`:
- Takes a single `ManagedSSHClient` instance in its constructor
- All operations go through `client.sftp` (the shared SFTP channel)
- Implements the same subset of operations used by `ConfigManager` and
  `project_scanner`:
  - `exists(path)`, `is_dir(path)`, `is_file(path)`
  - `iterdir(path) -> list[str]` (returns child paths as strings)
  - `read_text(path) -> str`, `write_text(path, text)`
  - `read_bytes(path) -> bytes`
  - `stat(path)` (returns paramiko `SFTPAttributes`, exposes `.st_mtime`, `.st_size`)
  - `glob(path, pattern) -> list[str]`
  - `mkdir(path, parents=False, exist_ok=False)`
  - `unlink(path)`
- All reads cached in-memory with TTL (default 30 s, configurable per server)
- Cache is invalidated for a path on any write to that path
- Cache is fully cleared on disconnect or server switch

#### `local_filesystem.py`

Class `LocalFileSystem` — thin wrapper over `pathlib.Path`.
Identical interface to `RemoteFileSystem` so `ConfigManager` can use either
without branching.

#### `server_context.py`

Class `ServerContext(QObject)`:
- Signal `server_changed(server_cfg: dict | None)`
- `get_active() -> dict | None` — `None` means local
- `set_active(server_cfg)` — stores and emits signal
- `is_local() -> bool`
- `get_label() -> str` — `"Local"` or `"Pi 1 (pi@192.168.0.97)"`

#### `server_registry.py`

- Loads/saves server list from `config/config.json` under key `remote_servers`
- Each server entry: `{id, name, host, port, user, key_path, claude_dir}`
  - `claude_dir` defaults to `"$HOME/.claude"` (allows QNAP/Docker override)
- CRUD: `list_servers()`, `add_server(cfg)`, `update_server(id, cfg)`,
  `remove_server(id)`

---

## Changes to Existing Modules

### `utils/config_manager.py`

Refactor all direct `Path` file I/O calls to go through a `self._fs` object:

```python
# Before
content = Path(self.settings_file).read_text(encoding="utf-8")

# After
content = self._fs.read_text(self.settings_file)
```

Constructor gains `fs=None`:
- `fs=None` → `LocalFileSystem()`
- `fs=RemoteFileSystem(client)` → remote mode

`claude_dir` is kept as a plain string internally; `LocalFileSystem` resolves it
to a `Path`, `RemoteFileSystem` uses it as a POSIX path string.

**Scope:** ~80 lines touched, all mechanical. No tab API changes needed.

### `utils/project_scanner.py`

All public functions (`scan_projects`, `find_project_encoded_dir`,
`get_project_sessions`) get an optional `fs=None` parameter. When provided,
file operations go through it. `ConfigManager` passes `self._fs` through when
calling scanner functions.

### `main.py`

- Instantiate `ServerContext`; pass to all tab constructors that need it
- On `ServerContext.server_changed`:
  1. Disconnect previous `ManagedSSHClient` if any
  2. If remote: create new `ManagedSSHClient`, call `connect()`, create
     `RemoteFileSystem(client)`
  3. Rebuild `ConfigManager` with the new filesystem
  4. Call `reload()` on every data tab
- On app close: `disconnect()` the active client

---

## UI Changes

### 1. Remote mode indicator banner (PERSISTENT, always visible)

A **full-width colored strip** rendered between the main tab bar and the tab
content area. It is only visible when a remote server is active — completely
absent in local mode.

```
┌─────────────────────────────────────────────────────────────────────┐
│  📡  REMOTE: Pi 1 — pi@192.168.0.97  ●  Connected    [Disconnect]  │  ← amber/orange bar
└─────────────────────────────────────────────────────────────────────┘
```

States:
- **Connected** — amber/orange background, green dot `●`, label shows server name
- **Error / disconnected** — red background, red dot `●`, label shows error,
  button changes to `[Reconnect]`

This makes it impossible to confuse local and remote mode at a glance.

### 2. Server selector in toolbar

A `QComboBox` in the main toolbar listing `💻 Local` and all configured
servers. Selecting an entry triggers `ServerContext.server_changed`.
The box shows `💻 Local` when on local, `📡 Pi 1` (name only) when remote.

### 3. Remote Servers settings tab

A new tab under User Config (or a standalone top-level tab):

**Left panel — server list:**
- `QListWidget` with entries showing status dot (green/grey/red), name,
  and `user@host`
- Buttons: `Add`, `Edit`, `Remove`, `Connect`

**Right panel — server editor:**
- Display Name (e.g. `Pi 1`)
- Host / IP
- Port (default `22`)
- Username
- SSH Key Path (with file-picker `Browse…` button)
- Remote Claude Dir (default `$HOME/.claude`, editable for QNAP/Docker)
- SFTP Cache TTL in seconds (default `30`)
- `Test Connection` button — connects, runs `echo ok`, shows success/error inline

All fields saved to `config.json` under `remote_servers`.

### 4. Tab behaviour on server switch

Every data tab that already implements `refresh()` / `reload()` connects to
`ServerContext.server_changed`. Tabs that are purely static (Documentation,
About, CLI Reference) ignore the signal. No other tab changes are needed.

---

## Implementation Phases

### Phase 1 — Foundation (no UI, no breakage)

1. Add `paramiko` to `help/requirements.txt`
2. Create `src/modules/remote/` package with `__init__.py`
3. Implement `local_filesystem.py` and `remote_filesystem.py`
4. Implement `ssh_client.py` (`ManagedSSHClient` with keepalive)
5. Implement `server_registry.py` and `server_context.py`
6. Refactor `ConfigManager` to use `_fs` — verify local behaviour unchanged
7. Refactor `project_scanner.py` to accept `fs=` — verify local behaviour unchanged

### Phase 2 — Server management UI + connection plumbing

1. Build Remote Servers tab (list + editor + Test Connection)
2. Add server selector `QComboBox` to main toolbar
3. Add remote mode indicator banner to main window (hidden when local)
4. Wire `ServerContext.server_changed` → SSH connect/disconnect → ConfigManager
   rebuild → tab reload

### Phase 3 — Full remote mode (reads and writes, same as local)

1. Verify all tabs work correctly over SSH: Conversations, Project Memories,
   File History, Shell Snapshots, Projects, Settings, Hooks, Agents,
   Commands, CLAUDE.md, Permissions, MCP config, etc.
2. Fix any tab that bypasses `ConfigManager` and reads files directly
3. Handle SSH errors gracefully — show error in the banner, tab shows
   "Connection lost — reconnect using the toolbar" instead of crashing
4. Test on Pi 1 first, then Pi 2 and QNAP

### Phase 4 — Polish

1. Connection status polling — `QTimer` every 15 s calls `is_connected()`,
   updates banner dot without opening new connections
2. Cache clear on manual Refresh — toolbar Refresh button flushes `RemoteFS`
   TTL cache and triggers reload
3. Performance: for large JSONL files, read via `exec("tail -c 2097152 <file")`
   instead of full SFTP download
4. Store last-used server in `config.json`; auto-select (but do not auto-connect)
   on next app launch

---

## Technical Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| SSH library | `paramiko` | Pure Python, works on Windows without system OpenSSH, loads private keys directly |
| Sessions | One `ManagedSSHClient` per server, shared everywhere | User requirement; avoids connection overhead; keepalive prevents idle drop |
| File abstraction | Filesystem wrapper class | Only `ConfigManager` + `project_scanner` need changes; all tabs unchanged |
| Remote path type | POSIX `str` inside `RemoteFS`; `LocalFS` uses `Path` internally | Avoids Windows/POSIX confusion on paths; unified string API for callers |
| Caching | In-memory dict with TTL per path | SFTP round-trips ~5–20 ms; caching avoids hammering the Pi on every UI repaint |
| Remote = local | No read-only mode; all tabs work exactly as on local system | No artificial split; the filesystem abstraction makes this natural |
| Visual indication | Full-width persistent amber banner (hidden when local) | Impossible to miss; status and disconnect button in one place |
| Windows key format | `paramiko.RSAKey.from_private_key_file(key_path)` | Reads OpenSSH/PEM keys without system SSH agent |

---

## File Layout After Implementation

```
src/
├── modules/
│   └── remote/
│       ├── __init__.py
│       ├── ssh_client.py          ← ManagedSSHClient (one session + keepalive)
│       ├── local_filesystem.py    ← LocalFileSystem (Path wrapper)
│       ├── remote_filesystem.py   ← RemoteFileSystem (SFTP + TTL cache)
│       ├── server_context.py      ← ServerContext QObject + signal
│       └── server_registry.py     ← load/save server list
├── tabs/
│   └── remote_servers_tab.py      ← new settings tab
└── utils/
    ├── config_manager.py          ← _fs layer added (~80 lines changed)
    └── project_scanner.py         ← fs= optional param added

config/
└── config.json                    ← remote_servers key added
```

---

## Risk / Open Questions

- **QNAP / Docker**: Claude may run inside a Container Station container with a
  non-standard home directory. The per-server `claude_dir` override field handles this.
- **Large JSONL files**: Full SFTP download of a multi-MB session file is slow.
  Phase 4 addresses this with `exec("tail -c N <file")`.
- **Key passphrase**: `P16_id_rsa` is passphrase-free. If a future key has a
  passphrase, a prompt dialog will be needed — out of scope for now.
- **Concurrent writes**: If Claude is actively writing a JSONL while we read it
  over SFTP, we may get a partial read. Acceptable risk for a monitoring tool.
