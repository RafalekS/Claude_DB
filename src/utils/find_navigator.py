"""FindNavigator — shared in-document find for the conversation viewers.

Both conversation views (tabs/project_conversations_subtab.py and
tabs/memory_tab.py) drop a huge transcript into a read-only QPlainTextEdit
and need the same thing on top of it: highlight every match, Prev / Next,
an "n / m" counter, and centre-on-match. This is that, once.
"""

from __future__ import annotations

from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import QTextEdit

from utils import theme
from utils.transcript_search import build_regex


class FindNavigator:
    def __init__(self, viewer, label=None, prev_btn=None, next_btn=None):
        self._viewer = viewer
        self._label = label
        self._prev_btn = prev_btn
        self._next_btn = next_btn
        self._spans: list[tuple[int, int]] = []
        self._idx = -1
        self._term = ""

    # ── public API ──────────────────────────────────────────────────────────
    @property
    def count(self) -> int:
        return len(self._spans)

    @property
    def index(self) -> int:
        return self._idx

    def search(self, term: str, whole_word: bool, match_case: bool) -> None:
        self._term = term
        rx = build_regex(term, whole_word, match_case)
        body = self._viewer.toPlainText()
        self._spans = [(m.start(), m.end()) for m in rx.finditer(body)] if rx else []
        self._idx = -1
        self._highlight()
        self._update_label()
        self._update_buttons()
        if self._spans:
            self.goto(0)

    def clear(self) -> None:
        self._term = ""
        self._spans = []
        self._idx = -1
        self._viewer.setExtraSelections([])
        self._update_label()
        self._update_buttons()

    def goto(self, idx: int) -> None:
        if not self._spans:
            return
        self._idx = idx % len(self._spans)
        a, b = self._spans[self._idx]
        cur = self._viewer.textCursor()
        cur.setPosition(a)
        cur.setPosition(b, QTextCursor.MoveMode.KeepAnchor)
        self._viewer.setTextCursor(cur)
        self._viewer.centerCursor()
        self._update_label()

    def next(self) -> None:
        if self._spans:
            self.goto(self._idx + 1)

    def prev(self) -> None:
        if self._spans:
            self.goto(self._idx - 1)

    # ── internals ───────────────────────────────────────────────────────────
    def _highlight(self) -> None:
        sels = []
        if self._spans:
            fmt = QTextCharFormat()
            fmt.setBackground(QColor(theme.WARNING_COLOR))
            fmt.setForeground(QColor(theme.BG_DARK))
            doc = self._viewer.document()
            for a, b in self._spans:
                cur = QTextCursor(doc)
                cur.setPosition(a)
                cur.setPosition(b, QTextCursor.MoveMode.KeepAnchor)
                sel = QTextEdit.ExtraSelection()
                sel.cursor = cur
                sel.format = fmt
                sels.append(sel)
        self._viewer.setExtraSelections(sels)

    def _update_label(self) -> None:
        if self._label is None:
            return
        n = len(self._spans)
        if n == 0:
            self._label.setText("no matches" if self._term else "")
        else:
            cur = self._idx + 1 if self._idx >= 0 else 0
            self._label.setText(f"{cur} / {n}")

    def _update_buttons(self) -> None:
        on = bool(self._spans)
        if self._prev_btn is not None:
            self._prev_btn.setEnabled(on)
        if self._next_btn is not None:
            self._next_btn.setEnabled(on)
