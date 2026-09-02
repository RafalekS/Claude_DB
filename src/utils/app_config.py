"""
Safe read/modify/write access to the app's config/config.json.

That one file holds unrelated things — remote_servers, tabs, preferences,
external_tools, claudekit_commands, github, mcp_search, last_server_id, … —
written by several different tabs. Every writer MUST read the whole file,
change only its own key, and write atomically, or one tab's save wipes
another tab's data (this is how the remote server list got lost).

Rules enforced here:
  * load() returns {} only when the file genuinely does not exist.
  * If the file exists but can't be parsed, load() raises ConfigError and
    first copies the bad file aside as config.json.corrupt-<timestamp> so a
    later blind write can't overwrite it with a partial document.
  * atomic_write() writes to a temp file in the same directory and renames.
  * update() = load + mutate-in-place + atomic_write, so a partial update
    never drops the keys it didn't touch, and fails loudly on a corrupt file
    instead of replacing it.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

# config/config.json at the project root: src/utils/ -> 2 parents -> src -> ..
CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "config.json"


class ConfigError(RuntimeError):
    """config.json exists but could not be read/parsed."""


def load(path: Path | str | None = None) -> dict:
    path = Path(path) if path is not None else CONFIG_PATH
    if not path.exists():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError, ValueError) as e:
        backup = path.with_name(f"{path.name}.corrupt-{time.strftime('%Y%m%d_%H%M%S')}")
        try:
            shutil.copy2(path, backup)
            logger.error("config.json is unreadable (%s); copied to %s", e, backup)
        except OSError:
            logger.error("config.json is unreadable (%s); could not back it up", e)
        raise ConfigError(f"{path} could not be read: {e}") from e
    if not isinstance(data, dict):
        raise ConfigError(f"{path} is not a JSON object")
    return data


def atomic_write(data: dict, path: Path | str | None = None) -> None:
    path = Path(path) if path is not None else CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.stem + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)          # atomic on POSIX and Windows
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def update(mutate: Callable[[dict], None], path: Path | str | None = None) -> dict:
    """Read the whole file, apply *mutate* in place, write it back atomically.

    Raises ConfigError if the file exists but is corrupt — the caller should
    surface that rather than write a fresh partial file over it.
    """
    data = load(path)
    mutate(data)
    atomic_write(data, path)
    return data
