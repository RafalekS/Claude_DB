"""
Configuration Manager - Handles reading and writing Claude Code configuration files
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages Claude Code configuration files"""

    def __init__(self):
        self.claude_dir = self.get_claude_dir()
        self.settings_file = self.claude_dir / "settings.json"
        self.mcp_file = self.claude_dir / ".mcp.json"  # Local scope
        self.mcp_user_file = self.claude_dir.parent / ".claude.json"  # User scope
        self.mcp_project_file = Path.cwd() / ".mcp.json"  # Project scope
        self.claude_md = self.claude_dir / "CLAUDE.md"
        self.agents_dir = self.claude_dir / "agents"
        self.commands_dir = self.claude_dir / "commands"
        self.hooks_dir = self.claude_dir / "hooks"

    @staticmethod
    def get_claude_dir() -> Path:
        """Get the Claude Code configuration directory"""
        home = Path.home()
        claude_dir = home / ".claude"

        if not claude_dir.exists():
            raise FileNotFoundError(
                f"Claude Code configuration directory not found: {claude_dir}\n"
                "Please ensure Claude Code is installed."
            )

        return claude_dir

    def read_json_file(self, file_path: Path) -> Dict:
        """Read and parse a JSON file"""
        try:
            if not file_path.exists():
                return {}

            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {str(e)}")
        except Exception as e:
            raise IOError(f"Error reading {file_path}: {str(e)}")

    def write_json_file(self, file_path: Path, data: Dict, indent: int = 2) -> None:
        """Write data to a JSON file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
        except Exception as e:
            raise IOError(f"Error writing {file_path}: {str(e)}")

    def read_text_file(self, file_path: Path) -> str:
        """Read a text file"""
        try:
            if not file_path.exists():
                return ""

            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Error reading {file_path}: {str(e)}")

    def write_text_file(self, file_path: Path, content: str) -> None:
        """Write content to a text file"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            raise IOError(f"Error writing {file_path}: {str(e)}")

    # Settings
    def get_settings(self) -> Dict:
        """Get Claude Code settings"""
        return self.read_json_file(self.settings_file)

    def save_settings(self, settings: Dict) -> None:
        """Save Claude Code settings"""
        self.write_json_file(self.settings_file, settings)

    # MCP Configuration
    def get_mcp_config(self, scope: str = "local") -> Dict:
        """Get MCP server configuration from specified scope

        Args:
            scope: "user", "local", or "project"
        """
        if scope == "user":
            return self.read_json_file(self.mcp_user_file)
        elif scope == "local":
            return self.read_json_file(self.mcp_file)
        elif scope == "project":
            return self.read_json_file(self.mcp_project_file)
        else:
            raise ValueError(f"Invalid scope: {scope}")

    def save_mcp_config(self, config: Dict, scope: str = "local") -> None:
        """Save MCP server configuration to specified scope

        Args:
            config: Configuration dictionary
            scope: "user", "local", or "project"
        """
        if scope == "user":
            self.write_json_file(self.mcp_user_file, config)
        elif scope == "local":
            self.write_json_file(self.mcp_file, config)
        elif scope == "project":
            self.write_json_file(self.mcp_project_file, config)
        else:
            raise ValueError(f"Invalid scope: {scope}")

    def get_mcp_file_path(self, scope: str = "local") -> Path:
        """Get the file path for specified MCP scope"""
        if scope == "user":
            return self.mcp_user_file
        elif scope == "local":
            return self.mcp_file
        elif scope == "project":
            return self.mcp_project_file
        else:
            raise ValueError(f"Invalid scope: {scope}")

    # Agents
    def list_agents(self) -> List[Path]:
        """List all agent files"""
        if not self.agents_dir.exists():
            return []

        agents = []
        for root, dirs, files in os.walk(self.agents_dir):
            for file in files:
                if file.endswith('.md'):
                    agents.append(Path(root) / file)
        return sorted(agents)

    def get_agent_content(self, agent_path: Path) -> str:
        """Get agent file content"""
        return self.read_text_file(agent_path)

    def save_agent(self, agent_path: Path, content: str) -> None:
        """Save agent file"""
        self.write_text_file(agent_path, content)

    # Commands
    def list_commands(self) -> List[Path]:
        """List all command files"""
        if not self.commands_dir.exists():
            return []

        commands = []
        for root, dirs, files in os.walk(self.commands_dir):
            for file in files:
                if file.endswith('.md'):
                    commands.append(Path(root) / file)
        return sorted(commands)

    def get_command_content(self, command_path: Path) -> str:
        """Get command file content"""
        return self.read_text_file(command_path)

    def save_command(self, command_path: Path, content: str) -> None:
        """Save command file"""
        self.write_text_file(command_path, content)

    # CLAUDE.md
    def get_claude_md(self) -> str:
        """Get CLAUDE.md content"""
        return self.read_text_file(self.claude_md)

    def save_claude_md(self, content: str) -> None:
        """Save CLAUDE.md content"""
        self.write_text_file(self.claude_md, content)

    # Search
    def search_in_files(self, query: str, file_type: str = 'all') -> List[Dict]:
        """Search for query in configuration files"""
        results = []
        query_lower = query.lower()

        # Search in agents
        if file_type in ['all', 'agents']:
            for agent_path in self.list_agents():
                content = self.get_agent_content(agent_path)
                if query_lower in content.lower():
                    results.append({
                        'type': 'agent',
                        'path': agent_path,
                        'name': agent_path.stem
                    })

        # Search in commands
        if file_type in ['all', 'commands']:
            for command_path in self.list_commands():
                content = self.get_command_content(command_path)
                if query_lower in content.lower():
                    results.append({
                        'type': 'command',
                        'path': command_path,
                        'name': command_path.stem
                    })

        # Search in settings
        if file_type in ['all', 'settings']:
            settings = self.get_settings()
            settings_str = json.dumps(settings, indent=2)
            if query_lower in settings_str.lower():
                results.append({
                    'type': 'settings',
                    'path': self.settings_file,
                    'name': 'settings.json'
                })

        return results
