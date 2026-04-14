"""
Settings Manager - Centralized settings.json management
Prevents file conflicts by managing all settings.json read/write operations
"""

import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class SettingsManager(QObject):
    """Centralized manager for all settings.json files (User, Project Shared, Project Local)"""

    # Signals
    settings_changed = pyqtSignal(str, dict)  # (scope, new_settings)

    def __init__(self, user_settings_path: Path):
        super().__init__()
        self.user_settings_path = user_settings_path
        self._cache: Dict[str, Dict] = {}
        self._file_watchers: Dict[str, list] = {}

    def get_user_settings(self) -> Dict[str, Any]:
        """Get user settings from ~/.claude/settings.json"""
        return self._load_settings(self.user_settings_path)

    def get_project_settings(self, project_path: Path) -> Dict[str, Any]:
        """Get merged project settings (shared + local override)"""
        shared = self.get_project_shared_settings(project_path)
        local = self.get_project_local_settings(project_path)
        merged = shared.copy()
        merged.update(local)
        return merged

    def get_project_shared_settings(self, project_path: Path) -> Dict[str, Any]:
        """Get project shared settings from .claude/settings.json (team-shared, committed)"""
        return self._load_settings(project_path / ".claude" / "settings.json")

    def get_project_local_settings(self, project_path: Path) -> Dict[str, Any]:
        """Get project local settings from .claude/settings.local.json (user-specific, gitignored)"""
        return self._load_settings(project_path / ".claude" / "settings.local.json")

    def save_user_settings(self, settings: Dict[str, Any]) -> bool:
        """Save a full settings dict to ~/.claude/settings.json"""
        return self.save_settings(self.user_settings_path, settings)

    def update_user_setting(self, key: str, value: Any) -> bool:
        """Update a specific setting in user settings.json"""
        return self._update_setting(self.user_settings_path, key, value)

    def update_project_setting(
        self, project_path: Path, key: str, value: Any, local: bool = False
    ) -> bool:
        """Update a specific setting in project settings.json

        Args:
            project_path: Path to project folder
            key: Setting key (dot notation supported, e.g. "hooks.pre-commit")
            value: New value
            local: If True, update local settings; if False, update shared settings
        """
        if local:
            settings_path = project_path / ".claude" / "settings.local.json"
        else:
            settings_path = project_path / ".claude" / "settings.json"
        return self._update_setting(settings_path, key, value)

    def save_settings(self, path: Path, data: Dict[str, Any]) -> bool:
        """Save settings to file with atomic write (temp file + rename).

        Returns True on success, False otherwise.
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write: write to temp file first, then rename
            with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False,
                dir=path.parent, encoding='utf-8'
            ) as tmp_file:
                json.dump(data, tmp_file, indent=2)
                tmp_path = tmp_file.name

            shutil.move(tmp_path, path)

            cache_key = self._get_cache_key(path)
            self._cache[cache_key] = data.copy()

            self.settings_changed.emit(cache_key, data)
            self._notify_watchers(cache_key, data)

            return True

        except Exception as e:
            logger.error("Error saving settings to %s: %s", path, e)
            return False

    def watch_file(self, path: Path, callback: Callable[[Dict], None]) -> None:
        """Register a callback invoked (synchronously) whenever this file is saved."""
        cache_key = self._get_cache_key(path)
        self._file_watchers.setdefault(cache_key, []).append(callback)

    def clear_cache(self, path: Optional[Path] = None) -> None:
        """Clear cached settings.

        Args:
            path: Specific path to clear, or None to clear all.
        """
        if path:
            self._cache.pop(self._get_cache_key(path), None)
        else:
            self._cache.clear()

    # ── Private ──────────────────────────────────────────────────────────────

    def _load_settings(self, path: Path) -> Dict[str, Any]:
        """Load settings from file with caching (cache key derived from path)."""
        cache_key = self._get_cache_key(path)

        if cache_key in self._cache:
            return self._cache[cache_key].copy()

        if not path.exists():
            return {}

        try:
            with open(path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            self._cache[cache_key] = settings.copy()
            return settings
        except Exception as e:
            logger.error("Error loading settings from %s: %s", path, e)
            return {}

    def _update_setting(self, path: Path, key: str, value: Any) -> bool:
        """Update a single setting key (dot-notation supported) and save."""
        try:
            settings = self._load_settings(path)

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

            return self.save_settings(path, settings)

        except Exception as e:
            logger.error("Error updating setting %s in %s: %s", key, path, e)
            return False

    def _get_cache_key(self, path: Path) -> str:
        """Derive a stable cache key from a settings file path."""
        if path == self.user_settings_path:
            return "user"
        path_str = str(path.resolve())
        if "settings.local.json" in path_str:
            return f"project_local_{path.parent.parent}"
        if "settings.json" in path_str:
            return f"project_shared_{path.parent.parent}"
        return path_str

    def _notify_watchers(self, cache_key: str, settings: Dict[str, Any]) -> None:
        """Invoke registered watch_file callbacks synchronously."""
        for callback in self._file_watchers.get(cache_key, []):
            try:
                callback(settings)
            except Exception as e:
                logger.warning("Error in settings watcher callback: %s", e)
