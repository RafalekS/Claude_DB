"""
UI state manager — persists QTableWidget column widths, sort order,
and QListWidget scroll positions between tab switches and app restarts.

Usage:
    from utils.ui_state_manager import UIStateManager
    mgr = UIStateManager.instance()
    mgr.restore_table_state("mcp.servers_table", self.table)
    # ... later, on column resize or app close:
    mgr.save_table_state("mcp.servers_table", self.table)
"""

import json
import logging
from pathlib import Path
from PyQt6.QtWidgets import QTableWidget, QListWidget
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)

_STATE_FILE = Path(__file__).parent.parent.parent / "config" / "ui_state.json"


class UIStateManager:
    """Singleton that saves/restores table and list widget state."""

    _instance: "UIStateManager | None" = None

    @classmethod
    def instance(cls) -> "UIStateManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._state: dict = {}
        self._load()

    # ── Persistence ────────────────────────────────────────────────────────

    def _load(self) -> None:
        try:
            if _STATE_FILE.exists():
                with open(_STATE_FILE, encoding="utf-8") as f:
                    self._state = json.load(f)
                logger.debug(f"Loaded UI state ({len(self._state)} entries)")
        except Exception as e:
            logger.warning(f"Could not load UI state from {_STATE_FILE}: {e}")
            self._state = {}

    def save(self) -> None:
        """Flush in-memory state to disk. Call on app close and after column resize."""
        try:
            _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save UI state to {_STATE_FILE}: {e}")

    # ── Tables ─────────────────────────────────────────────────────────────

    def save_table_state(self, table_id: str, table: QTableWidget) -> None:
        """Save column widths and sort order for a table.

        Args:
            table_id: Unique string key e.g. "mcp.servers_table"
            table: The QTableWidget to save state from
        """
        header = table.horizontalHeader()
        widths = [table.columnWidth(i) for i in range(table.columnCount())]
        sort_col = header.sortIndicatorSection()
        sort_order = header.sortIndicatorOrder().value  # int
        self._state[table_id] = {
            "widths": widths,
            "sort_col": sort_col,
            "sort_order": sort_order,
        }
        self.save()

    def restore_table_state(self, table_id: str, table: QTableWidget) -> None:
        """Restore column widths and sort order for a table.

        Args:
            table_id: Same key used in save_table_state
            table: The QTableWidget to restore state to
        """
        data = self._state.get(table_id)
        if not data:
            return
        widths: list = data.get("widths", [])
        for i, w in enumerate(widths):
            if i < table.columnCount() and isinstance(w, int) and w > 0:
                table.setColumnWidth(i, w)
        sort_col: int = data.get("sort_col", 0)
        sort_order = Qt.SortOrder(data.get("sort_order", Qt.SortOrder.AscendingOrder.value))
        if 0 <= sort_col < table.columnCount():
            table.sortItems(sort_col, sort_order)

    def connect_table(self, table_id: str, table: QTableWidget) -> None:
        """Auto-save on every column resize. Call once after table is populated.

        Args:
            table_id: Same key used in save/restore
            table: The QTableWidget to monitor
        """
        table.horizontalHeader().sectionResized.connect(
            lambda _idx, _old, _new: self.save_table_state(table_id, table)
        )

    # ── Lists ──────────────────────────────────────────────────────────────

    def save_list_state(self, list_id: str, widget: QListWidget) -> None:
        """Save scroll position for a list widget."""
        vbar = widget.verticalScrollBar()
        scroll = vbar.value() if vbar else 0
        self._state[list_id] = {"scroll": scroll}
        self.save()

    def restore_list_state(self, list_id: str, widget: QListWidget) -> None:
        """Restore scroll position for a list widget."""
        data = self._state.get(list_id)
        if not data:
            return
        vbar = widget.verticalScrollBar()
        if vbar:
            vbar.setValue(data.get("scroll", 0))
