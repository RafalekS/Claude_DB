"""
Configuration Manager — reads and writes Claude Code configuration files.

Accepts an optional FileSystem object (LocalFileSystem or RemoteFileSystem)
so the same code works against a local ~/.claude/ or a remote one over SFTP.
When no fs is provided, behaviour is identical to the original implementation.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages Claude Code configuration files (local or remote)."""

    def __init__(self, fs=None, claude_dir=None):
        """
        Args:
            fs:         FileSystem instance (LocalFileSystem or RemoteFileSystem).
                        None → LocalFileSystem() is used automatically.
            claude_dir: Path or RemotePath to the .claude directory.
                        None → detected from the local home directory.
        """
        if fs is None:
            from modules.remote.filesystem import LocalFileSystem
            self._fs = LocalFileSystem()
            self.claude_dir = self._get_local_claude_dir()
        else:
            self._fs = fs
            if claude_dir is None:
                raise ValueError("claude_dir is required when a remote fs is provided")
            # Accept str, Path, or RemotePath
            from modules.remote.remote_path import RemotePath
            self.claude_dir = (
                RemotePath(str(claude_dir))
                if not hasattr(claude_dir, "__truediv__")
                else claude_dir
            )

        self.settings_file      = self.claude_dir / "settings.json"
        self.mcp_user_file      = self.claude_dir.parent / ".claude.json"
        self.mcp_project_file   = Path.cwd() / ".mcp.json"   # always local
        self.claude_md          = self.claude_dir / "CLAUDE.md"
        self.claude_local_md    = self.claude_dir / "CLAUDE.local.md"
        self.agents_dir         = self.claude_dir / "agents"
        self.commands_dir       = self.claude_dir / "commands"
        self.skills_dir         = self.claude_dir / "skills"
        self.hooks_dir          = self.claude_dir / "hooks"

    @staticmethod
    def _get_local_claude_dir() -> Path:
        home = Path.home()
        claude_dir = home / ".claude"
        if not claude_dir.exists():
            raise FileNotFoundError(
                f"Claude Code configuration directory not found: {claude_dir}\n"
                "Please ensure Claude Code is installed."
            )
        return claude_dir

    # ── Low-level I/O (all go through self._fs) ───────────────────────────────

    def read_json_file(self, file_path) -> Dict:
        try:
            if not self._fs.exists(file_path):
                return {}
            content = self._fs.read_text(file_path)
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}") from e
        except Exception as e:
            raise IOError(f"Error reading {file_path}: {e}") from e

    def write_json_file(self, file_path, data: Dict, indent: int = 2) -> None:
        try:
            content = json.dumps(data, indent=indent, ensure_ascii=False)
            self._fs.write_text(file_path, content)
        except Exception as e:
            raise IOError(f"Error writing {file_path}: {e}") from e

    def read_text_file(self, file_path) -> str:
        try:
            if not self._fs.exists(file_path):
                return ""
            return self._fs.read_text(file_path)
        except Exception as e:
            raise IOError(f"Error reading {file_path}: {e}") from e

    def write_text_file(self, file_path, content: str) -> None:
        try:
            self._fs.mkdir(file_path.parent, parents=True, exist_ok=True)
            self._fs.write_text(file_path, content)
        except Exception as e:
            raise IOError(f"Error writing {file_path}: {e}") from e

    # ── Settings ───────────────────────────────────────────────────────────────

    def get_settings(self) -> Dict:
        return self.read_json_file(self.settings_file)

    def save_settings(self, settings: Dict) -> None:
        self.write_json_file(self.settings_file, settings)

    # ── MCP configuration ──────────────────────────────────────────────────────

    def get_mcp_config(self, scope: str = "user") -> Dict:
        if scope == "user":
            return self.read_json_file(self.mcp_user_file)
        elif scope == "project":
            return self.read_json_file(self.mcp_project_file)
        else:
            raise ValueError(f"Invalid MCP scope: {scope!r} (expected 'user' or 'project')")

    def save_mcp_config(self, config: Dict, scope: str = "user") -> None:
        if scope == "user":
            self.write_json_file(self.mcp_user_file, config)
        elif scope == "project":
            self.write_json_file(self.mcp_project_file, config)
        else:
            raise ValueError(f"Invalid MCP scope: {scope!r} (expected 'user' or 'project')")

    def get_mcp_file_path(self, scope: str = "user") -> Path:
        if scope == "user":
            return self.mcp_user_file
        elif scope == "project":
            return self.mcp_project_file
        else:
            raise ValueError(f"Invalid MCP scope: {scope!r} (expected 'user' or 'project')")

    # ── Agents ─────────────────────────────────────────────────────────────────

    def list_agents(self) -> list:
        if not self._fs.exists(self.agents_dir):
            return []
        agents = []
        for root, dirs, files in self._fs.walk(self.agents_dir):
            for file in files:
                if file.endswith(".md"):
                    agents.append(self._fs.join_path(root, file))
        return sorted(agents, key=str)

    def get_agent_content(self, agent_path) -> str:
        return self.read_text_file(agent_path)

    def save_agent(self, agent_path, content: str) -> None:
        self.write_text_file(agent_path, content)

    # ── Commands ───────────────────────────────────────────────────────────────

    def list_commands(self) -> list:
        if not self._fs.exists(self.commands_dir):
            return []
        commands = []
        for root, dirs, files in self._fs.walk(self.commands_dir):
            for file in files:
                if file.endswith(".md"):
                    commands.append(self._fs.join_path(root, file))
        return sorted(commands, key=str)

    def get_command_content(self, command_path) -> str:
        return self.read_text_file(command_path)

    def save_command(self, command_path, content: str) -> None:
        self.write_text_file(command_path, content)

    # ── Skills ─────────────────────────────────────────────────────────────────

    def list_skills(self) -> list:
        if not self._fs.exists(self.skills_dir):
            return []
        skills = []
        for root, dirs, files in self._fs.walk(self.skills_dir):
            for file in files:
                if file.endswith(".md"):
                    skills.append(self._fs.join_path(root, file))
        return sorted(skills, key=str)

    def list_skill_dirs(self) -> list:
        """Return immediate subdirectories of the skills directory."""
        if not self._fs.exists(self.skills_dir):
            return []
        return [p for p in self._fs.iterdir(self.skills_dir)
                if self._fs.is_dir(p)]

    def get_skill_content(self, skill_path) -> str:
        return self.read_text_file(skill_path)

    def save_skill(self, skill_path, content: str) -> None:
        self.write_text_file(skill_path, content)

    # ── CLAUDE.md ──────────────────────────────────────────────────────────────

    def get_claude_md(self) -> str:
        return self.read_text_file(self.claude_md)

    def save_claude_md(self, content: str) -> None:
        self.write_text_file(self.claude_md, content)

    def get_claude_local_md(self) -> str:
        if not self._fs.exists(self.claude_local_md):
            return ""
        return self.read_text_file(self.claude_local_md)

    def save_claude_local_md(self, content: str) -> None:
        self.write_text_file(self.claude_local_md, content)

    # ── Filesystem access ─────────────────────────────────────────────────────

    @property
    def fs(self):
        """Return the underlying filesystem (LocalFileSystem or RemoteFileSystem)."""
        return self._fs

    def clear_fs_cache(self) -> None:
        """Clear the filesystem read cache (no-op for local)."""
        self._fs.clear_cache()

    # ── Search ─────────────────────────────────────────────────────────────────

    def search_in_files(self, query: str, file_type: str = "all") -> List[Dict]:
        results = []
        query_lower = query.lower()

        if file_type in ("all", "agents"):
            for agent_path in self.list_agents():
                content = self.get_agent_content(agent_path)
                if query_lower in content.lower():
                    results.append({
                        "type": "agent",
                        "path": agent_path,
                        "name": getattr(agent_path, "stem", str(agent_path)),
                    })

        if file_type in ("all", "commands"):
            for command_path in self.list_commands():
                content = self.get_command_content(command_path)
                if query_lower in content.lower():
                    results.append({
                        "type": "command",
                        "path": command_path,
                        "name": getattr(command_path, "stem", str(command_path)),
                    })

        if file_type in ("all", "settings"):
            settings = self.get_settings()
            if query_lower in json.dumps(settings, indent=2).lower():
                results.append({
                    "type": "settings",
                    "path": self.settings_file,
                    "name": "settings.json",
                })

        return results


class ConfigManagerProxy:
    """Delegates all attribute access to the currently active ConfigManager.

    All tabs hold a reference to this proxy at startup.  When the user switches
    to a remote server, main calls set_delegate(remote_cm) and every subsequent
    tab call automatically hits the remote backend — no tab code needs to change.
    When returning to local, set_delegate(local_cm) restores local behaviour.
    """

    def __init__(self, initial_cm: ConfigManager):
        object.__setattr__(self, "_delegate", initial_cm)

    def set_delegate(self, cm: ConfigManager) -> None:
        object.__setattr__(self, "_delegate", cm)

    def get_delegate(self) -> ConfigManager:
        return object.__getattribute__(self, "_delegate")

    def __getattr__(self, name: str):
        delegate = object.__getattribute__(self, "_delegate")
        return getattr(delegate, name)

    def __setattr__(self, name: str, value) -> None:
        delegate = object.__getattribute__(self, "_delegate")
        setattr(delegate, name, value)
