"""
ServerContext — tracks which server (local or remote) is currently active.

Pattern mirrors ProjectContext: a QObject with a pyqtSignal that all data
tabs connect to.  When the user switches servers, the signal fires and every
tab reloads.

None means "local machine".
A dict means a remote server entry from ServerRegistry.
"""

from PyQt6.QtCore import QObject, pyqtSignal


class ServerContext(QObject):
    """Holds the currently active server and notifies tabs on change."""

    server_changed = pyqtSignal(object)   # emits dict | None

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active: dict | None = None  # None = local

    # ── Accessors ─────────────────────────────────────────────────────────────

    def get_active(self) -> dict | None:
        return self._active

    def set_active(self, server_cfg: dict | None) -> None:
        self._active = server_cfg
        self.server_changed.emit(server_cfg)

    def is_local(self) -> bool:
        return self._active is None

    def has_server(self) -> bool:
        return self._active is not None

    def get_label(self) -> str:
        """Human-readable label for display in the UI."""
        if self._active is None:
            return "Local"
        name = self._active.get("name", "")
        host = self._active.get("host", "")
        user = self._active.get("user", "")
        if name:
            return f"{name} ({user}@{host})" if host else name
        return f"{user}@{host}" if host else "Remote"
