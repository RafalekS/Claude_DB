"""
ServerRegistry — persists the list of remote servers in config/config.json
under the key "remote_servers".

Each server entry:
    {
        "id":         str   — short unique id (8 hex chars)
        "name":       str   — display label, e.g. "Pi 1"
        "host":       str   — IP or hostname
        "port":       int   — SSH port, default 22
        "user":       str   — SSH username
        "key_path":   str   — path to private key file
        "claude_dir": str   — remote ~/.claude path, default "$HOME/.claude"
        "cache_ttl":  int   — SFTP read cache TTL in seconds, default 30
    }
"""

import uuid
from pathlib import Path

from utils import app_config


_CONFIG_KEY = "remote_servers"

# Default path: config/config.json at the project root.
_DEFAULT_CONFIG = app_config.CONFIG_PATH


class ServerRegistry:

    def __init__(self, config_path: Path = _DEFAULT_CONFIG):
        self._path = Path(config_path)

    # ── CRUD ───────────────────────────────────────────────────────────────────
    # Every mutation goes through app_config.update() which reads the whole
    # config.json, changes only "remote_servers", and writes it back
    # atomically — so this can never wipe tabs/preferences/etc., and it fails
    # loudly instead of writing a partial file if config.json is corrupt.

    def list_servers(self) -> list[dict]:
        try:
            return list(app_config.load(self._path).get(_CONFIG_KEY, []))
        except app_config.ConfigError:
            return []

    def add_server(self, server: dict) -> dict:
        if "id" not in server or not server["id"]:
            server = {**server, "id": uuid.uuid4().hex[:8]}
        server.setdefault("port", 22)
        server.setdefault("claude_dir", "$HOME/.claude")
        server.setdefault("cache_ttl", 30)
        app_config.update(
            lambda d: d.setdefault(_CONFIG_KEY, []).append(server), self._path)
        return server

    def update_server(self, server_id: str, updates: dict) -> None:
        def _mut(d: dict):
            servers = d.setdefault(_CONFIG_KEY, [])
            for i, s in enumerate(servers):
                if s.get("id") == server_id:
                    servers[i] = {**s, **updates}
                    break
        app_config.update(_mut, self._path)

    def remove_server(self, server_id: str) -> None:
        app_config.update(
            lambda d: d.__setitem__(
                _CONFIG_KEY,
                [s for s in d.get(_CONFIG_KEY, []) if s.get("id") != server_id]),
            self._path)

    def get_server(self, server_id: str) -> dict | None:
        for s in self.list_servers():
            if s.get("id") == server_id:
                return s
        return None
