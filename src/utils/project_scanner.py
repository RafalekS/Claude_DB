"""
Shared utility for discovering Claude Code projects from ~/.claude/projects/
"""

from pathlib import Path

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


def decode_project_directory_name(dir_name: str) -> Path | None:
    """
    Decode a ~/.claude/projects/ directory name back to a filesystem path.

    Linux encoding: path separators (/) become -, so /home/pi/myapp → -home-pi-myapp
    Windows encoding: drive letter separator is --, then / and backslash become -.
    Returns the decoded Path if it exists on disk, otherwise None.
    """
    # Linux: directory name starts with - (leading slash encoded as -)
    if dir_name.startswith("-") and "--" not in dir_name:
        # Replace all - with / and prepend nothing (the leading - is the root /)
        candidate = Path("/" + dir_name[1:].replace("-", "/"))
        if candidate.exists():
            return candidate

        # Some projects use _ in their actual name encoded as -; try mixed combos
        parts = dir_name[1:].split("-")
        for split_at in range(1, len(parts)):
            path_part = "/".join(parts[:split_at])
            name_variants = [
                "-".join(parts[split_at:]),
                "_".join(parts[split_at:]),
                ".".join(parts[split_at:]),
            ]
            for name in name_variants:
                candidate = Path(f"/{path_part}/{name}")
                if candidate.exists():
                    return candidate
        return None

    # Windows: look for -- as drive-letter separator
    idx = dir_name.find("--")
    if idx == -1:
        return None

    drive = dir_name[:idx]
    rest = dir_name[idx + 2 :]
    rest = rest.replace("--", "\x00BSDOT\x00")

    def _try(s: str) -> Path:
        return Path(f"{drive}:\\{s.replace('\x00BSDOT\x00', '\\.')}")

    for replacement in ("-", "\\"), (None, None):
        if replacement[0] is None:
            break
        candidate = _try(rest.replace(*replacement) if replacement[0] else rest)
        if candidate.exists():
            return candidate

    candidate = _try(rest.replace("-", "\\"))
    if candidate.exists():
        return candidate

    parts = rest.split("-")
    for split_at in range(1, len(parts)):
        path_part = "\\".join(parts[:split_at])
        name_variants = [
            "-".join(parts[split_at:]),
            "_".join(parts[split_at:]),
            ".".join(parts[split_at:]),
        ]
        for name in name_variants:
            candidate = _try(f"{path_part}\\{name}")
            if candidate.exists():
                return candidate

    return None


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

    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        project_path = decode_project_directory_name(project_dir.name)
        if project_path is not None:
            projects.append(
                {
                    "name": project_path.name,
                    "path": project_path,
                    "sessions": len(list(project_dir.glob("*.jsonl"))),
                }
            )

    projects.sort(key=lambda x: str(x["path"]).lower())
    return projects
