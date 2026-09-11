"""
Local disk cache for large remote files pulled over SFTP — session
transcripts, file-history backup snapshots, shell snapshots.

Several tabs (Conversations, File History, Shell Snapshots) each
independently re-read the SAME remote session .jsonl on every open/search,
even though it hasn't changed — a single long session can be 50-70 MB and
take real time over SFTP. This module caches by content identity instead of
by a time window:

  get_text(path, fs, mtime=...)  — for files that CAN change (session
      transcripts, memory .md). The cache filename embeds the remote mtime,
      so a changed file lands in a new cache entry, and every OTHER cached
      version of that same file is deleted right after — no TTL, no
      needless re-download of an unchanged file, no risk of serving stale
      content, and no unbounded growth from repeatedly-edited sessions.

  get_text_immutable(path, fs)   — for files that never change once written
      (a File History backup carries its version in the filename; a shell
      snapshot is a timestamped one-off). Cached by path alone — no mtime
      round trip needed since the content can't change.

Local mode (fs=None or a local fs) always reads straight from disk — no
caching needed there.
"""

from __future__ import annotations

import hashlib
import logging
import os
import tempfile
import time
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "cache" / "remote_files"
_ENV_VAR = "CLAUDE_DB_CACHE_DIR"

_DEFAULT_PRUNE_DAYS = 30
_CONFIG_KEY = "session_cache_prune_days"


def cache_dir() -> Path:
    override = os.environ.get(_ENV_VAR)
    base = Path(override).expanduser() if override else _DEFAULT_CACHE_DIR
    base.mkdir(parents=True, exist_ok=True)
    return base


def prune_days() -> int:
    """Days a cache entry may sit unread before prune_stale() removes it
    (default 30; configurable via config.json `session_cache_prune_days`,
    Preferences tab). 0 disables pruning."""
    try:
        from utils import app_config
        v = app_config.load().get(_CONFIG_KEY, _DEFAULT_PRUNE_DAYS)
        return max(0, int(v))
    except Exception:
        return _DEFAULT_PRUNE_DAYS


def set_prune_days(days: int) -> None:
    from utils import app_config
    app_config.update(lambda d: d.__setitem__(_CONFIG_KEY, max(0, int(days))))


def _is_remote(fs) -> bool:
    return fs is not None and getattr(fs, "_client", None) is not None


def identity_for(fs) -> str:
    """Stable per-server key so two servers' identically-named files don't collide."""
    client = getattr(fs, "_client", None)
    return getattr(client, "label", "") or "remote"


def _ident_prefix(identity: str) -> str:
    """Short, filename-safe prefix identifying the server — lets clear()
    scope to one server without needing a sidecar metadata file per entry."""
    return hashlib.sha1(identity.encode("utf-8")).hexdigest()[:10]


def _stable_stem(identity: str, remote_path: str) -> str:
    """Hash of (identity, path) alone — stable across edits, so every
    cached version of the same file shares this stem and differs only by
    the mtime suffix, making stale versions trivial to find and sweep."""
    body = hashlib.sha1(f"{identity}\x00{remote_path}".encode("utf-8")).hexdigest()
    return f"{_ident_prefix(identity)}_{body}"


def _versioned_path(identity: str, remote_path: str, mtime) -> Path:
    stem = _stable_stem(identity, remote_path)
    return cache_dir() / f"{stem}.{int(mtime or 0)}.cache"


def _immutable_path(identity: str, remote_path: str) -> Path:
    stem = _stable_stem(identity, remote_path)
    return cache_dir() / f"{stem}.immutable"


def _atomic_download(fs, path, dest: Path) -> bool:
    """Download *path* via *fs* straight to *dest*, atomically. Returns False
    (dest left untouched) on any failure so the caller can fall back."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=dest.parent, prefix=dest.stem + ".", suffix=".part")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        if hasattr(fs, "download_to"):
            fs.download_to(path, tmp)
        else:
            tmp.write_text(fs.read_text(path), encoding="utf-8")
        os.replace(tmp, dest)
        return True
    except Exception as e:
        logger.warning("cache download failed for %s: %s", path, e)
        try:
            tmp.unlink()
        except OSError:
            pass
        return False


def _touch(dest: Path) -> None:
    try:
        os.utime(dest, None)
    except OSError:
        pass


# ── Versioned (mtime-keyed) cache — for files that can change ─────────────────

def get_text(path, fs=None, *, mtime=None, force: bool = False) -> str:
    """Return the text of *path*, cached locally by (server, path, mtime)
    when remote. mtime should come from wherever the caller already listed
    this file (session scan, etc.) — no extra stat call is made here.
    """
    if not _is_remote(fs):
        if fs is not None:
            return fs.read_text(path)
        return Path(path).read_text(encoding="utf-8", errors="replace")

    ident = identity_for(fs)
    dest = _versioned_path(ident, str(path), mtime)

    if not force and dest.exists() and dest.stat().st_size > 0:
        _touch(dest)
        return dest.read_text(encoding="utf-8", errors="replace")

    if _atomic_download(fs, path, dest):
        _sweep_stale_versions(ident, str(path), keep=dest)
        return dest.read_text(encoding="utf-8", errors="replace")

    # Download failed — fall back to a direct (uncached) read.
    return fs.read_text(path)


def is_cached(path, fs, mtime) -> bool:
    if not _is_remote(fs):
        return False
    dest = _versioned_path(identity_for(fs), str(path), mtime)
    try:
        return dest.exists() and dest.stat().st_size > 0
    except OSError:
        return False


def _sweep_stale_versions(identity: str, remote_path: str, keep: Path) -> None:
    """Delete other cached versions of this same (identity, path) at a
    different (stale) mtime, so repeatedly editing a session doesn't grow
    the cache unboundedly."""
    stem = _stable_stem(identity, remote_path)
    for f in cache_dir().glob(f"{stem}.*.cache"):
        if f != keep:
            try:
                f.unlink()
            except OSError:
                pass


# ── Immutable cache — for files that never change once written ────────────────

def get_text_immutable(path, fs=None) -> str:
    """Return the text of *path*, cached locally forever (no freshness
    check — for files that are write-once by construction, e.g. a File
    History backup or a timestamped shell snapshot)."""
    if not _is_remote(fs):
        if fs is not None:
            return fs.read_text(path)
        return Path(path).read_text(encoding="utf-8", errors="replace")

    ident = identity_for(fs)
    dest = _immutable_path(ident, str(path))

    if dest.exists() and dest.stat().st_size > 0:
        _touch(dest)
        return dest.read_text(encoding="utf-8", errors="replace")

    if _atomic_download(fs, path, dest):
        return dest.read_text(encoding="utf-8", errors="replace")

    return fs.read_text(path)


# ── Maintenance ────────────────────────────────────────────────────────────────

def clear(identity: str | None = None) -> int:
    """Delete cached files — all of them, or just one server's (matched by
    its filename prefix). Returns files removed."""
    d = cache_dir()
    if not d.exists():
        return 0
    prefix = _ident_prefix(identity) + "_" if identity is not None else None
    removed = 0
    for f in d.iterdir():
        if not f.is_file():
            continue
        if prefix is not None and not f.name.startswith(prefix):
            continue
        try:
            f.unlink()
            removed += 1
        except OSError:
            pass
    return removed


def prune_stale(days: int | None = None) -> int:
    """Remove cache files not read (mtime, refreshed on every hit) in over
    *days* days. Disk hygiene, independent of the versioned cache's
    correctness — a session that's never reopened would otherwise sit
    cached forever. 0 disables pruning."""
    if days is None:
        days = prune_days()
    if days <= 0:
        return 0
    d = cache_dir()
    if not d.exists():
        return 0
    cutoff = time.time() - days * 86400
    removed = 0
    for f in d.iterdir():
        if not f.is_file():
            continue
        try:
            if f.stat().st_mtime < cutoff:
                f.unlink()
                removed += 1
        except OSError:
            pass
    return removed


def stats() -> dict:
    d = cache_dir()
    if not d.exists():
        return {"files": 0, "bytes": 0}
    files = [f for f in d.iterdir() if f.is_file()]
    return {"files": len(files), "bytes": sum(f.stat().st_size for f in files)}
