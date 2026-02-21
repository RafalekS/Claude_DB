"""
Project Context Manager - Centralized project folder selection and state
Manages current project path and provides helper methods for project-specific paths
"""

from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


class ProjectContext(QObject):
    """Manages current project context and provides helper methods for project paths"""

    # Signals
    project_changed = pyqtSignal(Path)  # Emits when project folder changes

    def __init__(self):
        super().__init__()
        self._current_project: Optional[Path] = None

    def set_project(self, path: Path) -> bool:
        """Set current project path

        Args:
            path: Path to project folder

        Returns:
            True if valid project path, False otherwise
        """
        if not path or not path.exists():
            return False

        # Validate it's a directory
        if not path.is_dir():
            return False

        # Store project path
        self._current_project = path

        # Emit signal
        self.project_changed.emit(path)

        return True

    def get_project(self) -> Optional[Path]:
        """Get current project path

        Returns:
            Current project path or None if not set
        """
        return self._current_project

    def has_project(self) -> bool:
        """Check if project is set

        Returns:
            True if project path is set, False otherwise
        """
        return self._current_project is not None

    def validate_claude_folder(self) -> bool:
        """Check if current project has .claude folder

        Returns:
            True if .claude folder exists, False otherwise
        """
        if not self._current_project:
            return False

        claude_folder = self._current_project / ".claude"
        return claude_folder.exists() and claude_folder.is_dir()

    def ensure_claude_folder(self) -> bool:
        """Ensure .claude folder exists, create if needed

        Returns:
            True if folder exists or was created, False on error
        """
        if not self._current_project:
            return False

        try:
            claude_folder = self._current_project / ".claude"
            claude_folder.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating .claude folder: {e}")
            return False

    # Path helper methods

    def get_claude_folder(self) -> Optional[Path]:
        """Get .claude folder path

        Returns:
            Path to .claude folder or None if project not set
        """
        if not self._current_project:
            return None
        return self._current_project / ".claude"

    def get_agents_folder(self) -> Optional[Path]:
        """Get agents folder path (.claude/agents/)

        Returns:
            Path to agents folder or None if project not set
        """
        claude_folder = self.get_claude_folder()
        return claude_folder / "agents" if claude_folder else None

    def get_commands_folder(self) -> Optional[Path]:
        """Get commands folder path (.claude/commands/)

        Returns:
            Path to commands folder or None if project not set
        """
        claude_folder = self.get_claude_folder()
        return claude_folder / "commands" if claude_folder else None

    def get_skills_folder(self) -> Optional[Path]:
        """Get skills folder path (.claude/skills/)

        Returns:
            Path to skills folder or None if project not set
        """
        claude_folder = self.get_claude_folder()
        return claude_folder / "skills" if claude_folder else None

    def get_plugins_folder(self) -> Optional[Path]:
        """Get plugins folder path (.claude/plugins/)

        Returns:
            Path to plugins folder or None if project not set
        """
        claude_folder = self.get_claude_folder()
        return claude_folder / "plugins" if claude_folder else None

    def get_mcp_file(self) -> Optional[Path]:
        """Get MCP config file path (<project>/.mcp.json)

        Returns:
            Path to .mcp.json or None if project not set
        """
        if not self._current_project:
            return None
        return self._current_project / ".mcp.json"

    def get_settings_file(self) -> Optional[Path]:
        """Get project settings file path (.claude/settings.json - shared, committed)

        Returns:
            Path to settings.json or None if project not set
        """
        claude_folder = self.get_claude_folder()
        return claude_folder / "settings.json" if claude_folder else None

    def get_local_settings_file(self) -> Optional[Path]:
        """Get project local settings file path (.claude/settings.local.json - user-specific, gitignored)

        Returns:
            Path to settings.local.json or None if project not set
        """
        claude_folder = self.get_claude_folder()
        return claude_folder / "settings.local.json" if claude_folder else None

    def get_sessions_folder(self) -> Optional[Path]:
        """Get sessions folder path (.claude/sessions/)

        Returns:
            Path to sessions folder or None if project not set
        """
        claude_folder = self.get_claude_folder()
        return claude_folder / "sessions" if claude_folder else None

    def get_cache_folder(self) -> Optional[Path]:
        """Get cache folder path (.claude/cache/)

        Returns:
            Path to cache folder or None if project not set
        """
        claude_folder = self.get_claude_folder()
        return claude_folder / "cache" if claude_folder else None

    def clear_project(self):
        """Clear current project (reset to None)"""
        old_project = self._current_project
        self._current_project = None

        # Emit signal with None to notify listeners
        if old_project:
            self.project_changed.emit(None)

    def __str__(self) -> str:
        """String representation of current project"""
        if self._current_project:
            return f"ProjectContext({self._current_project})"
        return "ProjectContext(No project set)"

    def __repr__(self) -> str:
        """Debug representation"""
        return self.__str__()
