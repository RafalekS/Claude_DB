"""
Shared utility for discovering Claude Code projects from ~/.claude/projects/

Primary strategy: read `cwd` from `attachment` entries inside JSONL session files.
This is always correct regardless of how hyphens appear in directory/file names.

Fallback strategy: decode the directory name heuristically (works for simple paths
with no hyphens, underscores, or spaces inside folder names).
"""

import json
from pathlib import Path

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


def _read_cwd_from_jsonl(project_dir: Path) -> Path | None:
    """
    Open the newest JSONL in project_dir and return the `cwd` from the first
    `attachment` entry that has one.  Reads at most 40 lines.
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
                    if i >= 40:
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


def find_project_encoded_dir(project_path: Path, projects_dir: Path | None = None) -> Path | None:
    """Return the ~/.claude/projects/<encoded>/ directory for a given project path."""
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


def get_project_sessions(project_path: Path, projects_dir: Path | None = None) -> list[dict]:
    """Return session info for a project, sorted newest first.

    Returns:
        list of {"uuid": str, "path": Path, "mtime": float}
    """
    encoded_dir = find_project_encoded_dir(project_path, projects_dir)
    if encoded_dir is None:
        return []
    sessions = []
    for jf in encoded_dir.glob("*.jsonl"):
        sessions.append({"uuid": jf.stem, "path": jf, "mtime": jf.stat().st_mtime})
    sessions.sort(key=lambda x: x["mtime"], reverse=True)
    return sessions


def scan_projects(projects_dir: Path | None = None) -> list[dict]:
    """
    Scan ~/.claude/projects/ and return decoded project entries.

    Returns:
        list of {"name": str, "path": Path, "sessions": int}
    """
    if projects_dir is None:
        projects_dir = CLAUDE_PROJECTS_DIR

    projects: list[dict] = []

    if not projects_dir.exists():
        return projects

    seen: set[Path] = set()
    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        project_path = _resolve_encoded_dir(project_dir)
        if project_path is None:
            continue

        # Deduplicate by resolved path (same project can have multiple encoded dirs
        # if the path was once different, e.g. after a rename)
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
