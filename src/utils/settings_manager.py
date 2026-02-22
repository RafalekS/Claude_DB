"""
Settings Manager - Centralized settings.json management
Prevents file conflicts by managing all settings.json read/write operations
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from PyQt6.QtCore import QObject, pyqtSignal
import tempfile
import shutil


class SettingsManager(QObject):
    """Centralized manager for all settings.json files (User, Project Shared, Project Local)"""

    # Signals
    settings_changed = pyqtSignal(str, dict)  # (scope, new_settings)

    def __init__(self, user_settings_path: Path):
        super().__init__()
        self.user_settings_path = user_settings_path
        self._cache = {}  # Cache settings in memory to reduce I/O
        self._file_watchers = {}  # Callbacks for external file changes

    def get_user_settings(self) -> Dict[str, Any]:
        """Get user settings from ~/.claude/settings.json"""
        return self._load_settings(self.user_settings_path, "user")

    def get_project_settings(self, project_path: Path) -> Dict[str, Any]:
        """Get merged project settings (shared + local override)"""
        shared = self.get_project_shared_settings(project_path)
        local = self.get_project_local_settings(project_path)

        # Merge: local overrides shared
        merged = shared.copy()
        merged.update(local)
        return merged

    def get_project_shared_settings(self, project_path: Path) -> Dict[str, Any]:
        """Get project shared settings from .claude/settings.json (team-shared, committed)"""
        settings_path = project_path / ".claude" / "settings.json"
        return self._load_settings(settings_path, f"project_shared_{project_path}")

    def get_project_local_settings(self, project_path: Path) -> Dict[str, Any]:
        """Get project local settings from .claude/settings.local.json (user-specific, gitignored)"""
        settings_path = project_path / ".claude" / "settings.local.json"
        return self._load_settings(settings_path, f"project_local_{project_path}")

    def save_user_settings(self, settings: Dict[str, Any]) -> bool:
        """Save a full settings dict to ~/.claude/settings.json"""
        return self.save_settings(self.user_settings_path, settings)

    def update_user_setting(self, key: str, value: Any) -> bool:
        """Update a specific setting in user settings.json"""
        return self._update_setting(self.user_settings_path, key, value, "user")

    def update_project_setting(self, project_path: Path, key: str, value: Any, local: bool = False) -> bool:
        """Update a specific setting in project settings.json

        Args:
            project_path: Path to project folder
            key: Setting key (can be nested using dot notation, e.g., "hooks.pre-commit")
            value: New value
            local: If True, update local settings; if False, update shared settings
        """
        if local:
            settings_path = project_path / ".claude" / "settings.local.json"
            cache_key = f"project_local_{project_path}"
        else:
            settings_path = project_path / ".claude" / "settings.json"
            cache_key = f"project_shared_{project_path}"

        return self._update_setting(settings_path, key, value, cache_key)

    def save_settings(self, path: Path, data: Dict[str, Any]) -> bool:
        """Save settings to file with atomic write (temp file + rename)

        Args:
            path: Path to settings file
            data: Settings dictionary to save

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write: write to temp file first, then rename
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False,
                                            dir=path.parent, encoding='utf-8') as tmp_file:
                json.dump(data, tmp_file, indent=2)
                tmp_path = tmp_file.name

            # Rename temp file to target (atomic on most filesystems)
            shutil.move(tmp_path, path)

            # Update cache
            cache_key = self._get_cache_key(path)
            self._cache[cache_key] = data.copy()

            # Emit signal
            self.settings_changed.emit(cache_key, data)

            return True

        except Exception as e:
            print(f"Error saving settings to {path}: {e}")
            return False

    def watch_file(self, path: Path, callback: Callable[[Dict], None]):
        """Register callback for when settings file changes externally

        Args:
            path: Path to watch
            callback: Function to call with new settings when file changes
        """
        cache_key = self._get_cache_key(path)
        if cache_key not in self._file_watchers:
            self._file_watchers[cache_key] = []
        self._file_watchers[cache_key].append(callback)

    def clear_cache(self, path: Optional[Path] = None):
        """Clear cached settings

        Args:
            path: Specific path to clear, or None to clear all
        """
        if path:
            cache_key = self._get_cache_key(path)
            self._cache.pop(cache_key, None)
        else:
            self._cache.clear()

    # Private methods

    def _load_settings(self, path: Path, cache_key: str) -> Dict[str, Any]:
        """Load settings from file with caching"""
        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key].copy()

        # Load from file
        if not path.exists():
            return {}

        try:
            with open(path, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            # Cache result
            self._cache[cache_key] = settings.copy()
            return settings

        except Exception as e:
            print(f"Error loading settings from {path}: {e}")
            return {}

    def _update_setting(self, path: Path, key: str, value: Any, cache_key: str) -> bool:
        """Update a specific setting in a settings file

        Supports nested keys using dot notation (e.g., "hooks.pre-commit")
        """
        try:
            # Load current settings
            settings = self._load_settings(path, cache_key)

            # Handle nested keys (e.g., "hooks.pre-commit")
            if '.' in key:
                keys = key.split('.')
                current = settings
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value
            else:
                settings[key] = value

            # Save settings
            return self.save_settings(path, settings)

        except Exception as e:
            print(f"Error updating setting {key} in {path}: {e}")
            return False

    def _get_cache_key(self, path: Path) -> str:
        """Get cache key for a settings file path"""
        path_str = str(path.resolve())

        # Generate descriptive cache keys
        if path == self.user_settings_path:
            return "user"
        elif "settings.local.json" in path_str:
            return f"project_local_{path.parent.parent}"
        elif "settings.json" in path_str:
            return f"project_shared_{path.parent.parent}"
        else:
            return path_str

    def _notify_watchers(self, cache_key: str, settings: Dict[str, Any]):
        """Notify registered watchers of settings changes"""
        if cache_key in self._file_watchers:
            for callback in self._file_watchers[cache_key]:
                try:
                    callback(settings)
                except Exception as e:
                    print(f"Error in settings watcher callback: {e}")
