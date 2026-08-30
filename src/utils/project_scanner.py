"""
Shared utility for discovering Claude Code projects from ~/.claude/projects/

Primary strategy: read `cwd` from `attachment` entries inside JSONL session files.
This is always correct regardless of how hyphens appear in directory/file names.

Fallback strategy: decode the directory name heuristically (works for simple paths
with no hyphens, underscores, or spaces inside folder names).

All public functions accept an optional `fs` parameter (LocalFileSystem or
RemoteFileSystem).  When fs=None the original local-only code paths run
unchanged; when fs is provided all I/O goes through fs.* methods.
"""

import json
from pathlib import Path

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


# ── Local helpers ──────────────────────────────────────────────────────────────

def _read_cwd_from_jsonl(project_dir: Path) -> Path | None:
    """
    Open the newest JSONL in project_dir and return the `cwd` from the first
    entry that has one.  Reads at most 120 lines (a current session writes a
    block of metadata entries — last-prompt, mode, permission-mode,
    bridge-session, ai-title — before the first message that carries `cwd`).
    """
    jsonl_files = sorted(
        project_dir.glob("*.jsonl"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    for jf in jsonl_files:
        try:
            with open(jf, encoding="utf-8", errors="replace") as fh:
                for i, raw in enumerate(fh):
                    if i >= 120:  # new sessions write more metadata before the first message
                        break
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        entry = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    cwd = entry.get("cwd")
                    if cwd and isinstance(cwd, str):
                        p = Path(cwd)
                        # Return the path even if it doesn't currently exist
                        # (remote machine, unmounted drive, etc.)
                        return p
        except Exception:
            continue
    return None


def decode_project_directory_name(dir_name: str) -> Path | None:
    """
    Heuristic fallback: decode a ~/.claude/projects/ directory name.

    Linux encoding:  /home/pi/myapp  →  -home-pi-myapp
    Windows encoding: C:\\Scripts\\app →  C--Scripts-app

    Only returns a Path if it exists on disk.  Many paths with hyphens or
    underscores in component names cannot be decoded reliably this way;
    use _read_cwd_from_jsonl() as the primary source.
    """
    # Linux: starts with single - (root / encoded as -)
    if dir_name.startswith("-") and "--" not in dir_name:
        candidate = Path("/" + dir_name[1:].replace("-", "/"))
        if candidate.exists():
            return candidate
        # Try last component with _ or . in place of -
        parts = dir_name[1:].split("-")
        for split_at in range(1, len(parts)):
            path_part = "/".join(parts[:split_at])
            for sep in ("-", "_", "."):
                candidate = Path(f"/{path_part}/{sep.join(parts[split_at:])}")
                if candidate.exists():
                    return candidate
        return None

    # Windows: C-- prefix
    idx = dir_name.find("--")
    if idx == -1:
        return None
    drive = dir_name[:idx]
    rest = dir_name[idx + 2:]

    def _win(s: str) -> Path:
        return Path(f"{drive}:\\{s}")

    candidate = _win(rest.replace("-", "\\"))
    if candidate.exists():
        return candidate

    parts = rest.split("-")
    for split_at in range(1, len(parts)):
        path_part = "\\".join(parts[:split_at])
        for sep in ("-", "_", "."):
            candidate = _win(f"{path_part}\\{sep.join(parts[split_at:])}")
            if candidate.exists():
                return candidate
    return None


def _resolve_encoded_dir(project_dir: Path) -> Path | None:
    """
    Return the filesystem path for an encoded project directory, using JSONL
    cwd as the primary source and name-decode as fallback.
    """
    cwd = _read_cwd_from_jsonl(project_dir)
    if cwd is not None:
        return cwd
    return decode_project_directory_name(project_dir.name)


# ── Remote helpers ─────────────────────────────────────────────────────────────

def _read_cwd_from_jsonl_fs(project_dir, fs) -> str | None:
    """
    Remote variant of _read_cwd_from_jsonl.  Returns the cwd string
    (not a Path) because the path belongs to the remote machine.
    Uses fs.head_lines() to avoid downloading entire JSONL files.
    """
    try:
        jsonl_files = fs.glob(project_dir, "*.jsonl")
    except Exception:
        return None

    def _mtime(p):
        try:
            return fs.stat(p).st_mtime
        except Exception:
            return 0

    jsonl_files = sorted(jsonl_files, key=_mtime, reverse=True)

    for jf in jsonl_files:
        try:
            lines_text = fs.head_lines(jf, 120)
        except Exception:
            continue
        for raw in lines_text.splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue
            cwd = entry.get("cwd")
            if cwd and isinstance(cwd, str):
                return cwd
    return None


def _resolve_encoded_dir_fs(project_dir, fs) -> str | None:
    """Remote variant of _resolve_encoded_dir.  Returns cwd as str."""
    cwd = _read_cwd_from_jsonl_fs(project_dir, fs)
    if cwd is not None:
        return cwd
    dir_name = str(project_dir).rstrip("/").rsplit("/", 1)[-1]
    decoded = decode_project_directory_name(dir_name)
    return str(decoded) if decoded is not None else None


# ── Public API ─────────────────────────────────────────────────────────────────

def find_project_encoded_dir(project_path, projects_dir=None, fs=None):
    """Return the ~/.claude/projects/<encoded>/ directory for a given project path.

    Local mode (fs=None): project_path is a Path; returns a Path.
    Remote mode (fs provided): project_path is a str (cwd on remote); returns a
    RemotePath to the encoded directory, or None.
    """
    if fs is None:
        # ── Local ─────────────────────────────────────────────────────────────
        if projects_dir is None:
            projects_dir = CLAUDE_PROJECTS_DIR
        if not projects_dir.exists():
            return None
        try:
            target = project_path.resolve()
        except Exception:
            target = project_path

        try:
            for pdir in projects_dir.iterdir():
                if not pdir.is_dir():
                    continue
                decoded = _resolve_encoded_dir(pdir)
                if decoded is None:
                    continue
                try:
                    if decoded.resolve() == target:
                        return pdir
                except Exception:
                    if decoded == project_path:
                        return pdir
        except Exception:
            pass
        return None

    else:
        # ── Remote ────────────────────────────────────────────────────────────
        if projects_dir is None:
            raise ValueError("projects_dir is required in remote mode")
        try:
            entries = fs.iterdir(projects_dir)
        except Exception:
            return None
        target_str = str(project_path).rstrip("/")
        for pdir in entries:
            if not fs.is_dir(pdir):
                continue
            cwd = _resolve_encoded_dir_fs(pdir, fs)
            if cwd is not None and cwd.rstrip("/") == target_str:
                return pdir
        return None


def get_project_sessions(project_path, projects_dir=None, fs=None) -> list[dict]:
    """Return session info for a project, sorted newest first.

    Local mode (fs=None):
        project_path  — Path to the decoded project directory
        Returns list of {"uuid": str, "path": Path, "mtime": float}

    Remote mode (fs provided):
        project_path  — RemotePath to the *encoded* project directory
                        (the projects/<encoded>/ dir, not the cwd).
                        Pass the encoded_dir returned by scan_projects().
        Returns list of {"uuid": str, "path": RemotePath, "mtime": float}
    """
    if fs is None:
        # ── Local ─────────────────────────────────────────────────────────────
        encoded_dir = find_project_encoded_dir(project_path, projects_dir)
        if encoded_dir is None:
            return []
        sessions = []
        for jf in encoded_dir.glob("*.jsonl"):
            sessions.append({"uuid": jf.stem, "path": jf, "mtime": jf.stat().st_mtime})
        sessions.sort(key=lambda x: x["mtime"], reverse=True)
        return sessions

    else:
        # ── Remote ────────────────────────────────────────────────────────────
        # project_path is the cwd str / RemotePath — same convention as local.
        # Find the encoded directory first, then list its JSONL files.
        if projects_dir is None:
            raise ValueError("projects_dir is required in remote mode")
        encoded_dir = find_project_encoded_dir(project_path, projects_dir, fs)
        if encoded_dir is None:
            return []
        try:
            jsonl_files = fs.glob(encoded_dir, "*.jsonl")
        except Exception:
            return []
        sessions = []
        for jf in jsonl_files:
            try:
                mtime = fs.stat(jf).st_mtime
            except Exception:
                mtime = 0
            uuid = jf.stem if hasattr(jf, "stem") else str(jf).rsplit("/", 1)[-1].rsplit(".", 1)[0]
            sessions.append({"uuid": uuid, "path": jf, "mtime": mtime})
        sessions.sort(key=lambda x: x["mtime"], reverse=True)
        return sessions


def scan_projects(projects_dir=None, fs=None) -> list[dict]:
    """
    Scan ~/.claude/projects/ and return decoded project entries.

    Local mode (fs=None):
        Returns list of {"name": str, "path": Path, "sessions": int}

    Remote mode (fs provided):
        projects_dir must be provided (a RemotePath).
        Returns list of {
            "name":        str,
            "path":        str,          # cwd string on the remote machine
            "sessions":    int,
            "encoded_dir": RemotePath,   # projects/<encoded>/ on the remote
        }
    """
    if fs is None:
        # ── Local ─────────────────────────────────────────────────────────────
        if projects_dir is None:
            projects_dir = CLAUDE_PROJECTS_DIR

        projects: list[dict] = []

        if not projects_dir.exists():
            return projects

        seen: set = set()
        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue

            project_path = _resolve_encoded_dir(project_dir)
            if project_path is None:
                continue

            try:
                key = project_path.resolve()
            except Exception:
                key = project_path
            if key in seen:
                continue
            seen.add(key)

            projects.append({
                "name": project_path.name,
                "path": project_path,
                "sessions": len(list(project_dir.glob("*.jsonl"))),
            })

        projects.sort(key=lambda x: str(x["path"]).lower())
        return projects

    else:
        # ── Remote ────────────────────────────────────────────────────────────
        if projects_dir is None:
            raise ValueError("projects_dir is required in remote mode")

        projects: list[dict] = []

        if not fs.exists(projects_dir):
            return projects

        seen: set[str] = set()
        try:
            entries = fs.iterdir(projects_dir)
        except Exception:
            return projects

        for project_dir in entries:
            if not fs.is_dir(project_dir):
                continue

            cwd_str = _resolve_encoded_dir_fs(project_dir, fs)
            if cwd_str is None:
                continue

            key = cwd_str.rstrip("/")
            if key in seen:
                continue
            seen.add(key)

            try:
                jsonl_files = fs.glob(project_dir, "*.jsonl")
                session_count = len(jsonl_files)
            except Exception:
                session_count = 0

            name = key.rsplit("/", 1)[-1] or key

            projects.append({
                "name":        name,
                "path":        key,
                "sessions":    session_count,
                "encoded_dir": project_dir,
            })

        projects.sort(key=lambda x: str(x["path"]).lower())
        return projects
