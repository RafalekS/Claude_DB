"""
Local disk cache for session/transcript text pulled from a remote server.

Searching the Conversations tab in remote mode re-reads every *.jsonl over
SFTP — a single long session can be 50-70 MB and take 30-45 s. These files
barely change once a session is idle, so we keep a copy on local disk for a
while (default 15 min) and serve reads from it.

Local mode reads straight from disk (no caching needed).
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# cache/ is gitignored at the project root.
_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "cache" / "sessions"

_DEFAULT_MINUTES = 15
_CONFIG_KEY = "session_cache_minutes"


def ttl_minutes() -> int:
    """Cache lifetime in minutes — configurable via config.json `session_cache_minutes`
    (Preferences tab). 0 disables the disk cache."""
    try:
        from utils import app_config
        v = app_config.load().get(_CONFIG_KEY, _DEFAULT_MINUTES)
        return max(0, int(v))
    except Exception:
        return _DEFAULT_MINUTES


def set_ttl_minutes(minutes: int) -> None:
    from utils import app_config
    app_config.update(lambda d: d.__setitem__(_CONFIG_KEY, max(0, int(minutes))))


def _is_remote(fs) -> bool:
    return fs is not None and getattr(fs, "_client", None) is not None


def identity_for(fs) -> str:
    """Stable per-server key so two servers' identically-named files don't collide."""
    client = getattr(fs, "_client", None)
    return getattr(client, "label", "") or "remote"


def _paths(identity: str, remote_path: str) -> tuple[Path, Path]:
    key = hashlib.sha1(f"{identity}\x00{remote_path}".encode("utf-8")).hexdigest()
    return _CACHE_DIR / f"{key}.txt", _CACHE_DIR / f"{key}.json"


def get_text(path, fs=None, *, ttl: int | None = None, force: bool = False) -> str:
    """Return the text of *path*.

    Remote fs: served from the local cache while it's fresh; otherwise
    downloaded once and cached. Local fs (or fs=None): read directly.
    ttl — seconds; None uses the configured ttl_minutes(). 0 disables caching.
    """
    if not _is_remote(fs):
        if fs is not None:
            return fs.read_text(path)
        return Path(path).read_text(encoding="utf-8", errors="replace")

    if ttl is None:
        ttl = ttl_minutes() * 60
    if ttl <= 0:
        return fs.read_text(path)

    ident = identity_for(fs)
    blob, meta = _paths(ident, str(path))

    if not force and blob.exists() and meta.exists():
        try:
            m = json.loads(meta.read_text(encoding="utf-8"))
            if m.get("expires", 0) > time.time():
                return blob.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass  # fall through and re-fetch

    text = fs.read_text(path)
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        blob.write_text(text, encoding="utf-8")
        meta.write_text(json.dumps({
            "identity": ident,
            "path": str(path),
            "fetched": time.time(),
            "expires": time.time() + ttl,
            "bytes": len(text.encode("utf-8")),
        }), encoding="utf-8")
    except Exception as e:
        logger.warning("session cache write failed for %s: %s", path, e)
    return text


def is_cached_fresh(path, fs) -> bool:
    if not _is_remote(fs):
        return False
    _blob, meta = _paths(identity_for(fs), str(path))
    try:
        return meta.exists() and json.loads(meta.read_text())["expires"] > time.time()
    except Exception:
        return False


def clear(identity: str | None = None) -> int:
    """Delete cached sessions (all, or one server's). Returns files removed."""
    if not _CACHE_DIR.exists():
        return 0
    removed = 0
    for meta in list(_CACHE_DIR.glob("*.json")):
        try:
            keep = identity is not None and json.loads(meta.read_text()).get("identity") != identity
        except Exception:
            keep = False
        if keep:
            continue
        blob = meta.with_suffix(".txt")
        for f in (meta, blob):
            try:
                f.unlink()
                removed += 1
            except OSError:
                pass
    return removed


def stats() -> dict:
    if not _CACHE_DIR.exists():
        return {"files": 0, "bytes": 0}
    blobs = list(_CACHE_DIR.glob("*.txt"))
    return {"files": len(blobs), "bytes": sum(f.stat().st_size for f in blobs)}
