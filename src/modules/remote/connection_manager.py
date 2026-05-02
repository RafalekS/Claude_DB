"""
ConnectionManager — manages the single active remote SSH connection.

At most one connection is active at any time.  connect() switches to a new
server (closing any previous session); disconnect() returns to local mode.
"""

import os

from .ssh_client import ManagedSSHClient, SSHConnectionError
from .filesystem import RemoteFileSystem


class ConnectionManager:
    """Manages the single active remote SSH connection."""

    def __init__(self):
        self._client: ManagedSSHClient | None = None
        self._fs: RemoteFileSystem | None = None
        self._active_cfg: dict | None = None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def connect(self, server_cfg: dict) -> None:
        """Open SSH connection described by server_cfg.  Closes any previous session.

        Raises SSHConnectionError on failure.
        """
        self.disconnect()

        host = server_cfg["host"]
        port = int(server_cfg.get("port", 22))
        user = server_cfg["user"]
        key_path = os.path.expanduser(os.path.expandvars(server_cfg["key_path"]))
        ttl = int(server_cfg.get("cache_ttl", 30))

        client = ManagedSSHClient()
        client.connect(host, port, user, key_path)   # raises SSHConnectionError on failure

        self._client = client
        self._fs = RemoteFileSystem(client, ttl=ttl)
        self._active_cfg = server_cfg

    def disconnect(self) -> None:
        """Close the active connection.  No-op if not connected."""
        if self._client is not None:
            try:
                self._client.disconnect()
            except Exception:
                pass
        self._client = None
        self._fs = None
        self._active_cfg = None

    # ── State ──────────────────────────────────────────────────────────────────

    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected()

    @property
    def fs(self) -> RemoteFileSystem | None:
        return self._fs

    @property
    def active_cfg(self) -> dict | None:
        return self._active_cfg

    # ── Remote path helpers ────────────────────────────────────────────────────

    def get_claude_dir(self) -> str | None:
        """Return the shell-expanded claude_dir for the active server.

        Runs `echo "<dir>"` on the remote to expand $HOME.  Falls back to
        manual substitution if the exec fails.
        """
        if self._active_cfg is None:
            return None
        raw = self._active_cfg.get("claude_dir", "$HOME/.claude")
        if self._client is not None and self._client.is_connected():
            try:
                stdout, _ = self._client.exec(f'echo "{raw}"')
                expanded = stdout.strip()
                if expanded:
                    return expanded
            except Exception:
                pass
        # Fallback: manual $HOME substitution
        user = self._active_cfg.get("user", "")
        return raw.replace("$HOME", f"/home/{user}")
