"""
RemoteServersTab — manage remote server list and connect/disconnect.
"""

import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QAbstractItemView, QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor

from utils import theme

logger = logging.getLogger(__name__)


# ── Background connect thread ──────────────────────────────────────────────────

class _ConnectThread(QThread):
    succeeded = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, conn_manager, server_cfg, parent=None):
        super().__init__(parent)
        self._conn = conn_manager
        self._cfg = server_cfg

    def run(self):
        try:
            self._conn.connect(self._cfg)
            self.succeeded.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


# ── Tab widget ─────────────────────────────────────────────────────────────────

class RemoteServersTab(QWidget):
    """UI for managing remote server connections."""

    def __init__(self, server_registry, connection_manager, server_context, parent=None):
        super().__init__(parent)
        self._registry = server_registry
        self._conn = connection_manager
        self._ctx = server_context
        self._connect_thread: _ConnectThread | None = None
        self._init_ui()
        self._refresh_table()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("Remote Servers")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")
        layout.addWidget(title)

        # Server table
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Name", "Host", "User", "Port"])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self._table.setColumnWidth(2, 100)
        self._table.setColumnWidth(3, 60)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.itemSelectionChanged.connect(self._update_buttons)
        layout.addWidget(self._table, 1)

        # CRUD buttons
        crud_row = QHBoxLayout()
        self._add_btn = QPushButton("Add Server")
        self._edit_btn = QPushButton("Edit")
        self._remove_btn = QPushButton("Remove")
        self._add_btn.clicked.connect(self._add_server)
        self._edit_btn.clicked.connect(self._edit_server)
        self._remove_btn.clicked.connect(self._remove_server)
        crud_row.addWidget(self._add_btn)
        crud_row.addWidget(self._edit_btn)
        crud_row.addWidget(self._remove_btn)
        crud_row.addStretch()
        layout.addLayout(crud_row)

        # Connect / Disconnect buttons
        conn_row = QHBoxLayout()
        self._connect_btn = QPushButton("Connect to Selected")
        self._connect_btn.setStyleSheet(
            f"QPushButton {{ background: {theme.ACCENT_PRIMARY}; color: #000; font-weight: bold; }}"
            f"QPushButton:disabled {{ background: {theme.BG_MEDIUM}; color: {theme.FG_SECONDARY}; }}"
        )
        self._disconnect_btn = QPushButton("Disconnect (go local)")
        self._connect_btn.clicked.connect(self._connect)
        self._disconnect_btn.clicked.connect(self._disconnect)
        conn_row.addWidget(self._connect_btn)
        conn_row.addWidget(self._disconnect_btn)
        conn_row.addStretch()
        layout.addLayout(conn_row)

        # Status label
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-style: italic;")
        self._status_lbl.setWordWrap(True)
        layout.addWidget(self._status_lbl)

        self._update_buttons()

        # Keep status label in sync when server changes externally (e.g. top-bar Disconnect)
        self._ctx.server_changed.connect(self._on_ctx_server_changed)

    # ── Table population ───────────────────────────────────────────────────────

    def _refresh_table(self) -> None:
        servers = self._registry.list_servers()
        active_id = (self._ctx.get_active() or {}).get("id")

        self._table.setRowCount(len(servers))
        for row, srv in enumerate(servers):
            sid = srv.get("id", "")
            is_active = sid == active_id

            name_text = srv.get("name", "") + (" ✓" if is_active else "")
            items = [
                QTableWidgetItem(name_text),
                QTableWidgetItem(srv.get("host", "")),
                QTableWidgetItem(srv.get("user", "")),
                QTableWidgetItem(str(srv.get("port", 22))),
            ]
            for col, item in enumerate(items):
                item.setData(Qt.ItemDataRole.UserRole, sid)
                if is_active:
                    item.setForeground(QColor("#E8A000"))
                self._table.setItem(row, col, item)

        self._update_buttons()

    def _selected_server_id(self) -> str | None:
        rows = self._table.selectedItems()
        if not rows:
            return None
        return rows[0].data(Qt.ItemDataRole.UserRole)

    def _selected_server(self) -> dict | None:
        sid = self._selected_server_id()
        if sid is None:
            return None
        return self._registry.get_server(sid)

    def _update_buttons(self) -> None:
        has_selection = self._selected_server_id() is not None
        is_busy = self._connect_thread is not None and self._connect_thread.isRunning()
        active = self._ctx.get_active()
        selected_is_active = has_selection and (
            active is not None and active.get("id") == self._selected_server_id()
        )

        self._edit_btn.setEnabled(has_selection and not is_busy)
        self._remove_btn.setEnabled(has_selection and not selected_is_active and not is_busy)
        self._connect_btn.setEnabled(has_selection and not is_busy and not selected_is_active)
        self._disconnect_btn.setEnabled(active is not None and not is_busy)

    # ── CRUD actions ──────────────────────────────────────────────────────────

    def _add_server(self) -> None:
        from dialogs.server_dialog import ServerDialog
        dlg = ServerDialog(self)
        if dlg.exec() == ServerDialog.DialogCode.Accepted:
            self._registry.add_server(dlg.get_server())
            self._refresh_table()

    def _edit_server(self) -> None:
        srv = self._selected_server()
        if srv is None:
            return
        from dialogs.server_dialog import ServerDialog
        dlg = ServerDialog(self, server=srv)
        if dlg.exec() == ServerDialog.DialogCode.Accepted:
            data = dlg.get_server()
            self._registry.update_server(srv["id"], data)
            # If we just edited the active server, refresh banner label via context
            active = self._ctx.get_active()
            if active is not None and active.get("id") == srv["id"]:
                updated = self._registry.get_server(srv["id"])
                self._ctx.set_active(updated)
            self._refresh_table()

    def _remove_server(self) -> None:
        srv = self._selected_server()
        if srv is None:
            return
        name = srv.get("name") or srv.get("host", "")
        reply = QMessageBox.question(
            self, "Remove Server",
            f"Remove '{name}' from the server list?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._registry.remove_server(srv["id"])
            self._refresh_table()

    # ── Connect / Disconnect ───────────────────────────────────────────────────

    def _connect(self) -> None:
        srv = self._selected_server()
        if srv is None:
            return
        label = srv.get("name") or srv.get("host", "")
        self._status_lbl.setText(f"Connecting to {label}…")
        self._status_lbl.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-style: italic;")
        self._update_buttons()

        self._connect_thread = _ConnectThread(self._conn, srv, self)
        self._connect_thread.succeeded.connect(lambda: self._on_connect_ok(srv))
        self._connect_thread.failed.connect(self._on_connect_fail)
        self._connect_thread.start()

    def _on_connect_ok(self, srv: dict) -> None:
        self._connect_thread = None
        self._ctx.set_active(srv)
        label = self._ctx.get_label()
        self._status_lbl.setText(f"Connected to {label}")
        self._status_lbl.setStyleSheet("color: #6A9A6A;")
        self._refresh_table()
        logger.info("Connected to remote server: %s", label)

    def _on_connect_fail(self, error: str) -> None:
        self._connect_thread = None
        self._status_lbl.setText(f"Connection failed: {error}")
        self._status_lbl.setStyleSheet("color: #E05252;")
        self._update_buttons()
        logger.error("SSH connect failed: %s", error)

    def _on_ctx_server_changed(self, server_cfg) -> None:
        """Handle server context changes triggered externally (e.g. top-bar Disconnect button)."""
        if server_cfg is None:
            self._status_lbl.setText("Disconnected — using local machine.")
            self._status_lbl.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-style: italic;")
        self._refresh_table()

    def _disconnect(self) -> None:
        self._conn.disconnect()
        self._ctx.set_active(None)
        # _on_ctx_server_changed fires via server_changed signal — no need to repeat here
        logger.info("Disconnected from remote server, back to local mode")
