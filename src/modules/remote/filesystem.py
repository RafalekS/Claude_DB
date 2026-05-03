"""
Filesystem abstraction layer.

LocalFileSystem  — wraps pathlib.Path; behaviour identical to the existing code.
RemoteFileSystem — wraps paramiko SFTP via a ManagedSSHClient; TTL read cache.

Both expose the same interface so ConfigManager and project_scanner can use
either without branching.  All paths are accepted as str, Path, or RemotePath
and are converted to str internally.
"""

import fnmatch
import os
import shlex
import stat as _stat
import time
from pathlib import Path

from .remote_path import RemotePath
from .ssh_client import ManagedSSHClient


# ─── TTL read cache ───────────────────────────────────────────────────────────

class _Cache:
    """Simple TTL in-memory cache keyed by (operation, path_str) tuples."""

    def __init__(self, ttl: int = 30):
        self._ttl = ttl
        self._store: dict = {}

    def get(self, key: tuple):
        entry = self._store.get(key)
        if entry is None:
            return None, False
        val, exp = entry
        if time.monotonic() < exp:
            return val, True
        del self._store[key]
        return None, False

    def set(self, key: tuple, val) -> None:
        self._store[key] = (val, time.monotonic() + self._ttl)

    def invalidate(self, path_str: str) -> None:
        """Remove all cached entries for path_str and its parent directory."""
        parent = path_str.rsplit("/", 1)[0] if "/" in path_str else ""
        remove = [
            k for k in self._store
            if k[1] == path_str or k[1] == parent
        ]
        for k in remove:
            del self._store[k]

    def clear(self) -> None:
        self._store.clear()


# ─── Local filesystem ─────────────────────────────────────────────────────────

class LocalFileSystem:
    """Thin pathlib.Path wrapper.  Identical behaviour to the previous direct
    Path usage; exists so ConfigManager can use either filesystem uniformly."""

    # ── Query ──────────────────────────────────────────────────────────────────

    def exists(self, path) -> bool:
        return Path(str(path)).exists()

    def is_dir(self, path) -> bool:
        return Path(str(path)).is_dir()

    def is_file(self, path) -> bool:
        return Path(str(path)).is_file()

    def stat(self, path):
        return Path(str(path)).stat()

    # ── Read ───────────────────────────────────────────────────────────────────

    def read_text(self, path) -> str:
        return Path(str(path)).read_text(encoding="utf-8", errors="replace")

    def read_bytes(self, path) -> bytes:
        return Path(str(path)).read_bytes()

    def head_lines(self, path, n: int) -> str:
        """Return first n lines.  Reads the whole file locally (files are local)."""
        text = self.read_text(path)
        return "\n".join(text.splitlines()[:n])

    # ── Write ──────────────────────────────────────────────────────────────────

    def write_text(self, path, content: str) -> None:
        Path(str(path)).write_text(content, encoding="utf-8")

    def write_bytes(self, path, data: bytes) -> None:
        Path(str(path)).write_bytes(data)

    # ── Directory operations ───────────────────────────────────────────────────

    def iterdir(self, path) -> list[Path]:
        return list(Path(str(path)).iterdir())

    def glob(self, path, pattern: str) -> list[Path]:
        return list(Path(str(path)).glob(pattern))

    def walk(self, path):
        """Yield (root_str, dirnames, filenames) — same as os.walk."""
        for root, dirs, files in os.walk(str(path)):
            yield str(root), dirs, files

    def mkdir(self, path, parents: bool = False, exist_ok: bool = False) -> None:
        Path(str(path)).mkdir(parents=parents, exist_ok=exist_ok)

    def unlink(self, path) -> None:
        Path(str(path)).unlink()

    def rmtree(self, path) -> None:
        import shutil
        shutil.rmtree(str(path))

    # ── Path factory ───────────────────────────────────────────────────────────

    def join_path(self, root, name) -> Path:
        """Build a path by joining root with name."""
        return Path(str(root)) / str(name)

    def clear_cache(self) -> None:
        pass  # no-op; local filesystem has no cache


# ─── Remote filesystem (SFTP) ─────────────────────────────────────────────────

class RemoteFileSystem:
    """SFTP-backed filesystem.  All operations go through a single
    ManagedSSHClient session.  Reads are cached with a configurable TTL."""

    def __init__(self, client: ManagedSSHClient, ttl: int = 30):
        self._client = client
        self._cache = _Cache(ttl)

    # ── Internal helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _s(path) -> str:
        return str(path)

    def _sftp(self):
        return self._client.sftp  # raises SSHConnectionError if not connected

    # ── Query ──────────────────────────────────────────────────────────────────

    def exists(self, path) -> bool:
        p = self._s(path)
        cached, hit = self._cache.get(("stat", p))
        if hit:
            return cached is not None
        try:
            attrs = self._sftp().stat(p)
            self._cache.set(("stat", p), attrs)
            return True
        except FileNotFoundError:
            self._cache.set(("stat", p), None)
            return False

    def is_dir(self, path) -> bool:
        p = self._s(path)
        cached, hit = self._cache.get(("stat", p))
        if hit:
            return cached is not None and _stat.S_ISDIR(cached.st_mode)
        try:
            attrs = self._sftp().stat(p)
            self._cache.set(("stat", p), attrs)
            return _stat.S_ISDIR(attrs.st_mode)
        except Exception:
            return False

    def is_file(self, path) -> bool:
        p = self._s(path)
        cached, hit = self._cache.get(("stat", p))
        if hit:
            return cached is not None and _stat.S_ISREG(cached.st_mode)
        try:
            attrs = self._sftp().stat(p)
            self._cache.set(("stat", p), attrs)
            return _stat.S_ISREG(attrs.st_mode)
        except Exception:
            return False

    def stat(self, path):
        p = self._s(path)
        cached, hit = self._cache.get(("stat", p))
        if hit and cached is not None:
            return cached
        attrs = self._sftp().stat(p)
        self._cache.set(("stat", p), attrs)
        return attrs

    # ── Read ───────────────────────────────────────────────────────────────────

    def read_text(self, path) -> str:
        p = self._s(path)
        cached, hit = self._cache.get(("text", p))
        if hit:
            return cached
        with self._sftp().open(p, "rb") as f:
            content = f.read().decode("utf-8", errors="replace")
        self._cache.set(("text", p), content)
        return content

    def read_bytes(self, path) -> bytes:
        p = self._s(path)
        with self._sftp().open(p, "rb") as f:
            return f.read()

    def head_lines(self, path, n: int) -> str:
        """Efficient remote head via exec — avoids downloading the whole file."""
        p = self._s(path)
        stdout, _ = self._client.exec(f"head -n {n} {shlex.quote(p)}")
        return stdout

    # ── Write ──────────────────────────────────────────────────────────────────

    def write_text(self, path, content: str) -> None:
        p = self._s(path)
        self._cache.invalidate(p)
        # Ensure parent directory exists on the remote
        parent = p.rsplit("/", 1)[0]
        if parent:
            self._client.exec(f"mkdir -p {shlex.quote(parent)}")
        with self._sftp().open(p, "wb") as f:
            f.write(content.encode("utf-8"))

    def write_bytes(self, path, data: bytes) -> None:
        p = self._s(path)
        self._cache.invalidate(p)
        parent = p.rsplit("/", 1)[0]
        if parent:
            self._client.exec(f"mkdir -p {shlex.quote(parent)}")
        with self._sftp().open(p, "wb") as f:
            f.write(data)

    # ── Directory operations ───────────────────────────────────────────────────

    def iterdir(self, path) -> list[RemotePath]:
        p = self._s(path)
        cached, hit = self._cache.get(("dir", p))
        if hit:
            return cached
        attrs = self._sftp().listdir_attr(p)
        results = [RemotePath(p.rstrip("/") + "/" + a.filename) for a in attrs]
        # Also pre-populate stat cache for each entry
        for a in attrs:
            child_p = p.rstrip("/") + "/" + a.filename
            self._cache.set(("stat", child_p), a)
        self._cache.set(("dir", p), results)
        return results

    def glob(self, path, pattern: str) -> list[RemotePath]:
        p = self._s(path)
        if not self.exists(p):
            return []
        cached_dir, hit = self._cache.get(("dir", p))
        if not hit:
            # Populate dir cache via listdir_attr
            self.iterdir(p)
            cached_dir, _ = self._cache.get(("dir", p))
        if cached_dir is None:
            return []
        return [
            child for child in cached_dir
            if fnmatch.fnmatch(child.name, pattern)
        ]

    def walk(self, path):
        """Yield (root_str, dirnames, filenames) — same shape as os.walk."""
        stack = [self._s(path)]
        while stack:
            current = stack.pop()
            try:
                attrs = self._sftp().listdir_attr(current)
            except Exception as e:
                raise IOError(f"Cannot list remote directory {current}: {e}") from e
            dirs, files = [], []
            for a in attrs:
                if _stat.S_ISDIR(a.st_mode):
                    dirs.append(a.filename)
                    stack.append(current.rstrip("/") + "/" + a.filename)
                else:
                    files.append(a.filename)
            yield current, dirs, files

    def mkdir(self, path, parents: bool = False, exist_ok: bool = False) -> None:
        p = self._s(path)
        if parents or exist_ok:
            stdout, stderr = self._client.exec(f"mkdir -p {shlex.quote(p)}")
            if stderr.strip():
                raise IOError(f"mkdir -p {p}: {stderr.strip()}")
        else:
            stdout, stderr = self._client.exec(f"mkdir {shlex.quote(p)}")
            if stderr.strip():
                raise IOError(f"mkdir {p}: {stderr.strip()}")
        self._cache.invalidate(p)

    def unlink(self, path) -> None:
        p = self._s(path)
        self._sftp().remove(p)
        self._cache.invalidate(p)

    def rmtree(self, path) -> None:
        p = self._s(path)
        stdout, stderr = self._client.exec(f"rm -rf {shlex.quote(p)}")
        if stderr.strip():
            raise IOError(f"rm -rf {p}: {stderr.strip()}")
        self._cache.invalidate(p)

    # ── Path factory ───────────────────────────────────────────────────────────

    def join_path(self, root, name) -> RemotePath:
        return RemotePath(str(root)) / str(name)

    def clear_cache(self) -> None:
        self._cache.clear()
