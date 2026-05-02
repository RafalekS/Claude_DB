"""
ServerDialog — Add / Edit a remote server configuration.
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QPushButton, QDialogButtonBox, QFileDialog, QHBoxLayout, QLabel,
)
from PyQt6.QtCore import Qt
from utils import theme


class ServerDialog(QDialog):
    """Form dialog for adding or editing a remote server entry."""

    def __init__(self, parent=None, server: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Add Server" if server is None else "Edit Server")
        self.setMinimumWidth(480)
        self._init_ui(server or {})

    def _init_ui(self, srv: dict) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        lbl_style = f"color: {theme.FG_PRIMARY};"

        def _label(text):
            l = QLabel(text)
            l.setStyleSheet(lbl_style)
            return l

        # Name
        self._name = QLineEdit(srv.get("name", ""))
        self._name.setPlaceholderText("e.g. Pi 1")
        form.addRow(_label("Display name:"), self._name)

        # Host
        self._host = QLineEdit(srv.get("host", ""))
        self._host.setPlaceholderText("IP address or hostname")
        form.addRow(_label("Host:"), self._host)

        # Port
        self._port = QSpinBox()
        self._port.setRange(1, 65535)
        self._port.setValue(int(srv.get("port", 22)))
        form.addRow(_label("Port:"), self._port)

        # User
        self._user = QLineEdit(srv.get("user", ""))
        self._user.setPlaceholderText("SSH username")
        form.addRow(_label("Username:"), self._user)

        # Key path  (line edit + Browse button)
        key_row = QHBoxLayout()
        self._key_path = QLineEdit(srv.get("key_path", ""))
        self._key_path.setPlaceholderText("Path to private key file")
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_key)
        key_row.addWidget(self._key_path, 1)
        key_row.addWidget(browse_btn)
        form.addRow(_label("Private key:"), key_row)

        # Claude dir
        self._claude_dir = QLineEdit(srv.get("claude_dir", "$HOME/.claude"))
        form.addRow(_label("Claude dir:"), self._claude_dir)

        # Cache TTL
        self._cache_ttl = QSpinBox()
        self._cache_ttl.setRange(5, 3600)
        self._cache_ttl.setSuffix(" s")
        self._cache_ttl.setValue(int(srv.get("cache_ttl", 30)))
        form.addRow(_label("Cache TTL:"), self._cache_ttl)

        layout.addLayout(form)

        # OK / Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_key(self) -> None:
        start = os.path.expanduser("~/.ssh")
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Private Key", start, "All files (*)"
        )
        if path:
            self._key_path.setText(path)

    def _validate_and_accept(self) -> None:
        if not self._host.text().strip():
            self._host.setFocus()
            return
        if not self._user.text().strip():
            self._user.setFocus()
            return
        if not self._key_path.text().strip():
            self._key_path.setFocus()
            return
        self.accept()

    def get_server(self) -> dict:
        """Return the server dict from the form (no id — caller adds it)."""
        return {
            "name":       self._name.text().strip() or self._host.text().strip(),
            "host":       self._host.text().strip(),
            "port":       self._port.value(),
            "user":       self._user.text().strip(),
            "key_path":   self._key_path.text().strip(),
            "claude_dir": self._claude_dir.text().strip() or "$HOME/.claude",
            "cache_ttl":  self._cache_ttl.value(),
        }
