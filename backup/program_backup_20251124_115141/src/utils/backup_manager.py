"""
Backup Manager - Handles backup and restore of Claude Code configuration files
"""

import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class BackupManager:
    """Manages backup and restore operations for Claude Code configurations"""

    def __init__(self, backup_dir: Optional[Path] = None):
        if backup_dir is None:
            # Use project backup directory
            self.backup_dir = Path(__file__).parent.parent.parent / "backup"
        else:
            self.backup_dir = backup_dir

        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.claude_dir = Path.home() / ".claude"

    def get_timestamp(self) -> str:
        """Generate timestamp for backup names"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def create_full_backup(self) -> Path:
        """Create a full backup of Claude Code configuration"""
        timestamp = self.get_timestamp()
        backup_name = f"claude_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name

        try:
            # Files to backup
            files_to_backup = [
                "settings.json",
                ".mcp.json",
                "CLAUDE.md",
                "config.json",
            ]

            # Directories to backup
            dirs_to_backup = [
                "agents",
                "commands",
                "hooks",
                "config",
                "prompt",
            ]

            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)

            # Backup individual files
            for file_name in files_to_backup:
                source = self.claude_dir / file_name
                if source.exists():
                    dest = backup_path / file_name
                    shutil.copy2(source, dest)

            # Backup directories
            for dir_name in dirs_to_backup:
                source = self.claude_dir / dir_name
                if source.exists():
                    dest = backup_path / dir_name
                    shutil.copytree(source, dest, dirs_exist_ok=True)

            # Create backup metadata
            metadata = {
                "timestamp": timestamp,
                "date": datetime.now().isoformat(),
                "source": str(self.claude_dir),
                "files_backed_up": [
                    f for f in files_to_backup
                    if (self.claude_dir / f).exists()
                ],
                "dirs_backed_up": [
                    d for d in dirs_to_backup
                    if (self.claude_dir / d).exists()
                ]
            }

            metadata_file = backup_path / "backup_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

            return backup_path

        except Exception as e:
            # Clean up partial backup
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise Exception(f"Backup failed: {str(e)}")

    def create_file_backup(self, file_path: Path) -> Path:
        """Create a backup of a single file before modification"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        timestamp = self.get_timestamp()
        relative_path = file_path.relative_to(self.claude_dir)

        # Create backup subdirectory structure
        backup_file_dir = self.backup_dir / f"file_backup_{timestamp}" / relative_path.parent
        backup_file_dir.mkdir(parents=True, exist_ok=True)

        backup_file_path = backup_file_dir / relative_path.name
        shutil.copy2(file_path, backup_file_path)

        return backup_file_path

    def list_backups(self) -> list:
        """List all available backups"""
        backups = []

        for item in self.backup_dir.iterdir():
            if item.is_dir() and item.name.startswith("claude_backup_"):
                metadata_file = item / "backup_metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    backups.append({
                        'path': item,
                        'name': item.name,
                        'metadata': metadata
                    })

        return sorted(backups, key=lambda x: x['name'], reverse=True)

    def restore_backup(self, backup_path: Path) -> None:
        """Restore configuration from backup"""
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        try:
            # Read backup metadata
            metadata_file = backup_path / "backup_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                metadata = {}

            # Restore files
            for item in backup_path.iterdir():
                if item.name == "backup_metadata.json":
                    continue

                dest = self.claude_dir / item.name

                if item.is_file():
                    shutil.copy2(item, dest)
                elif item.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest)

        except Exception as e:
            raise Exception(f"Restore failed: {str(e)}")

    def get_backup_size(self, backup_path: Path) -> int:
        """Get the size of a backup in bytes"""
        total_size = 0
        for item in backup_path.rglob('*'):
            if item.is_file():
                total_size += item.stat().st_size
        return total_size

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format size in bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
