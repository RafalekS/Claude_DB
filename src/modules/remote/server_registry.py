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

import json
import uuid
from pathlib import Path


_CONFIG_KEY = "remote_servers"

# Default path: config/config.json at the project root.
# src/modules/remote/ → 3 parents up → project root → config/config.json
_DEFAULT_CONFIG = Path(__file__).parent.parent.parent.parent / "config" / "config.json"


class ServerRegistry:

    def __init__(self, config_path: Path = _DEFAULT_CONFIG):
        self._path = Path(config_path)

    # ── Persistence ────────────────────────────────────────────────────────────

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        with open(self._path, encoding="utf-8") as f:
            return json.load(f)

    def _save(self, cfg: dict) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)

    # ── CRUD ───────────────────────────────────────────────────────────────────

    def list_servers(self) -> list[dict]:
        return self._load().get(_CONFIG_KEY, [])

    def add_server(self, server: dict) -> dict:
        if "id" not in server or not server["id"]:
            server = {**server, "id": uuid.uuid4().hex[:8]}
        server.setdefault("port", 22)
        server.setdefault("claude_dir", "$HOME/.claude")
        server.setdefault("cache_ttl", 30)
        cfg = self._load()
        servers = cfg.get(_CONFIG_KEY, [])
        servers.append(server)
        cfg[_CONFIG_KEY] = servers
        self._save(cfg)
        return server

    def update_server(self, server_id: str, updates: dict) -> None:
        cfg = self._load()
        servers = cfg.get(_CONFIG_KEY, [])
        for i, s in enumerate(servers):
            if s.get("id") == server_id:
                servers[i] = {**s, **updates}
                break
        cfg[_CONFIG_KEY] = servers
        self._save(cfg)

    def remove_server(self, server_id: str) -> None:
        cfg = self._load()
        servers = cfg.get(_CONFIG_KEY, [])
        cfg[_CONFIG_KEY] = [s for s in servers if s.get("id") != server_id]
        self._save(cfg)

    def get_server(self, server_id: str) -> dict | None:
        for s in self.list_servers():
            if s.get("id") == server_id:
                return s
        return None
