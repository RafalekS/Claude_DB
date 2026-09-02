"""Shared helpers for searching conversation transcripts.

Used by both conversation views:
  * tabs/project_conversations_subtab.py  (current project's sessions)
  * tabs/memory_tab.py                    (all projects)
"""

from __future__ import annotations

import re


def build_regex(term: str, whole_word: bool, match_case: bool) -> "re.Pattern | None":
    """Compile a search pattern for *term*.

    whole_word — require a non-word boundary on both sides (\\w-aware, so
                 "tor" does not match "storage" or "tornado").
    match_case — case-sensitive when True, otherwise IGNORECASE.
    Returns None for an empty term.
    """
    if not term:
        return None
    pat = re.escape(term)
    if whole_word:
        pat = rf"(?<!\w){pat}(?!\w)"
    return re.compile(pat, 0 if match_case else re.IGNORECASE)
