"""
Lightweight YAML-frontmatter helpers shared by the agents / skills / commands tabs.

The GUI editors only ever change a handful of well-known single-line keys
(name, description, model, tools, …).  Claude Code frontmatter can also carry
multi-line block values (``hooks:``, ``mcpServers:``) and keys the GUI has no
field for (``permissionMode``, ``maxTurns``, ``skills``, ``when_to_use`` …).

``merge_frontmatter`` therefore does an in-place *text* merge: it rewrites only
the lines for the keys it is given and leaves every other line of the
frontmatter byte-for-byte untouched, so nothing is silently dropped on a
round-trip through the metadata dialog.
"""

from __future__ import annotations

import re
from typing import Dict, Optional, Tuple

_FM_RE = re.compile(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?(.*)$", re.DOTALL)


def split_frontmatter(content: str) -> Tuple[Optional[str], str]:
    """Return (frontmatter_text, body).

    ``frontmatter_text`` is ``None`` when the content has no ``---`` block.
    """
    if not content.startswith("---"):
        return None, content
    m = _FM_RE.match(content)
    if not m:
        return None, content
    return m.group(1), m.group(2)


def parse_simple(frontmatter_text: str) -> Dict[str, str]:
    """Parse top-level ``key: value`` pairs (single-line values only).

    Indented lines (block-value continuations) and list items are ignored, so
    the returned dict only carries the scalar keys the GUI knows how to edit.
    """
    out: Dict[str, str] = {}
    if not frontmatter_text:
        return out
    for line in frontmatter_text.splitlines():
        if not line or line[0] in (" ", "\t", "#", "-"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        if not key:
            continue
        out[key] = value.strip().strip('"').strip("'")
    return out


def _is_top_level_key_line(line: str, key: str) -> bool:
    return bool(re.match(rf"^{re.escape(key)}[ \t]*:", line))


def merge_frontmatter(content: str, updates: Dict[str, Optional[str]],
                      body: Optional[str] = None) -> str:
    """Apply ``updates`` to the frontmatter of ``content`` and return new content.

    * A value of ``None`` (or ``""``) removes that key's line.
    * An existing top-level ``key:`` line is replaced in place.
    * A new key is appended just before the closing ``---``.
    * Every other frontmatter line, including multi-line block values for keys
      not named in ``updates``, is preserved exactly.

    If ``body`` is given it replaces the existing body; otherwise the original
    body is kept.
    """
    fm_text, orig_body = split_frontmatter(content)
    new_body = orig_body if body is None else body

    fm_lines = fm_text.splitlines() if fm_text is not None else []

    for key, value in updates.items():
        remove = value is None or value == ""
        # Find an existing top-level line for this key.
        idx = next((i for i, ln in enumerate(fm_lines)
                    if _is_top_level_key_line(ln, key)), None)

        if remove:
            new_lines = []
        elif "\n" in str(value):
            # Block value: "key:" followed by the caller's already-indented text.
            new_lines = [f"{key}:", *str(value).splitlines()]
        else:
            new_lines = [f"{key}: {value}"]

        if idx is not None:
            # Drop the old key line plus any indented continuation lines.
            end = idx + 1
            while end < len(fm_lines) and fm_lines[end][:1] in (" ", "\t"):
                end += 1
            fm_lines[idx:end] = new_lines
        elif new_lines:
            fm_lines.extend(new_lines)

    fm_block = "\n".join(fm_lines)
    sep = "" if new_body.startswith("\n") else "\n"
    return f"---\n{fm_block}\n---\n{sep}{new_body}"
