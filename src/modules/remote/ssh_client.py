"""
ManagedSSHClient — one SSH session per remote server.

A single paramiko.SSHClient is opened on connect() and reused for all
operations: SFTP file transfers and exec_command() calls all go through
this one session.  Keepalive is enabled immediately after connect so the
connection survives idle periods.

No automatic reconnection — callers check is_connected() and surface any
connection errors to the user via the UI.
"""

import paramiko


class SSHConnectionError(Exception):
    """Raised when the SSH session cannot be established or has dropped."""


class ManagedSSHClient:
    """One persistent SSH session with a shared SFTP channel."""

    def __init__(self):
        self._ssh: paramiko.SSHClient | None = None
        self._sftp: paramiko.SFTPClient | None = None
        self._label: str = ""          # "user@host" for display

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def connect(self, host: str, port: int, user: str, key_path: str = "",
                password: str = "", keepalive: int = 30) -> None:
        """Open SSH session.  Closes any previous session first.

        Auth priority: key_path (if non-empty) → password (if non-empty).
        At least one must be provided.

        Args:
            host:       IP address or hostname
            port:       SSH port (usually 22)
            user:       SSH username
            key_path:   path to private key file (OpenSSH or PEM format); takes priority
            password:   SSH password; used only when key_path is empty
            keepalive:  keepalive interval in seconds (default 30)
        """
        self.disconnect()

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs: dict = dict(
            hostname=host,
            port=port,
            username=user,
            allow_agent=False,
            look_for_keys=False,
            timeout=15,
        )
        if key_path:
            connect_kwargs["key_filename"] = key_path
        elif password:
            connect_kwargs["password"] = password
        else:
            raise SSHConnectionError(
                f"No authentication provided for {user}@{host} — supply a key file or password"
            )

        try:
            ssh.connect(**connect_kwargs)
        except Exception as e:
            raise SSHConnectionError(
                f"Cannot connect to {user}@{host}:{port} — {e}"
            ) from e

        transport = ssh.get_transport()
        if transport is None:
            ssh.close()
            raise SSHConnectionError(f"SSH transport unavailable for {user}@{host}")

        transport.set_keepalive(keepalive)

        try:
            sftp = ssh.open_sftp()
        except Exception as e:
            ssh.close()
            raise SSHConnectionError(
                f"Cannot open SFTP channel on {user}@{host} — {e}"
            ) from e

        self._ssh = ssh
        self._sftp = sftp
        self._label = f"{user}@{host}"

    def disconnect(self) -> None:
        """Close SFTP channel then SSH session."""
        if self._sftp is not None:
            try:
                self._sftp.close()
            except Exception:
                pass
            self._sftp = None
        if self._ssh is not None:
            try:
                self._ssh.close()
            except Exception:
                pass
            self._ssh = None
        self._label = ""

    def is_connected(self) -> bool:
        """Return True if the session is alive."""
        if self._ssh is None:
            return False
        t = self._ssh.get_transport()
        return t is not None and t.is_active()

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def sftp(self) -> paramiko.SFTPClient:
        """The shared SFTP channel.  Raises SSHConnectionError if not connected."""
        if not self.is_connected() or self._sftp is None:
            raise SSHConnectionError(
                f"Not connected{' to ' + self._label if self._label else ''}"
            )
        return self._sftp

    @property
    def label(self) -> str:
        """Display label, e.g. 'pi@192.168.0.97'."""
        return self._label

    # ── Command execution ─────────────────────────────────────────────────────

    def exec(self, command: str) -> tuple[str, str]:
        """Execute a shell command on the remote host.

        Opens a new channel within the existing session (not a new connection).

        Returns:
            (stdout_text, stderr_text)
        """
        if not self.is_connected():
            raise SSHConnectionError(
                f"Not connected{' to ' + self._label if self._label else ''}"
            )
        _, stdout, stderr = self._ssh.exec_command(command)  # type: ignore[union-attr]
        return (
            stdout.read().decode("utf-8", errors="replace"),
            stderr.read().decode("utf-8", errors="replace"),
        )
