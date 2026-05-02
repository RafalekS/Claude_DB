"""
Worktrees Tab - Create, list, and remove git worktrees for isolated Claude Code work
"""

import logging
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QFileDialog
)
from PyQt6.QtCore import Qt

from utils import theme
from utils.ui_state_manager import UIStateManager

logger = logging.getLogger(__name__)

class NewWorktreeDialog(QDialog):
    """Dialog for creating a new git worktree"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Worktree")
        self.setMinimumWidth(480)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        form = QFormLayout()
        form.setSpacing(6)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("/path/to/worktree  or  ../feature-branch")

        browse_btn = QPushButton("Browse…")
        browse_btn.setStyleSheet(theme.get_button_neutral_style())
        browse_btn.clicked.connect(self._browse_path)
        path_row = QHBoxLayout()
        path_row.addWidget(self.path_edit)
        path_row.addWidget(browse_btn)

        self.branch_edit = QLineEdit()
        self.branch_edit.setPlaceholderText("branch-name  (leave blank to use detached HEAD)")

        self.new_branch_edit = QLineEdit()
        self.new_branch_edit.setPlaceholderText("new-branch-name  (leave blank to use existing branch)")

        form.addRow("Path:", path_row)
        form.addRow("Existing branch:", self.branch_edit)
        form.addRow("New branch (-b):", self.new_branch_edit)
        layout.addLayout(form)

        hint = QLabel(
            "Creates: <code>git worktree add &lt;path&gt; [-b &lt;new-branch&gt;] [&lt;branch&gt;]</code><br>"
            "Claude Code can operate in isolated worktrees via <code>isolation: \"worktree\"</code> in agents."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Worktree Parent Directory")
        if path:
            self.path_edit.setText(path)

    def get_data(self):
        return {
            "path": self.path_edit.text().strip(),
            "branch": self.branch_edit.text().strip(),
            "new_branch": self.new_branch_edit.text().strip(),
        }

class WorktreesTab(QWidget):
    """Tab for managing git worktrees used by Claude Code"""

    def __init__(self, config_manager, backup_manager, project_context=None):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self._project_context = project_context
        self.repo_root = self._find_repo_root()
        self.init_ui()
        if project_context:
            project_context.project_changed.connect(self._on_project_changed)
        self.refresh()

    def _on_project_changed(self, project_path) -> None:
        self.repo_root = self._find_repo_root()
        self.refresh()

    def _find_repo_root(self) -> Path | None:
        """Find the git repository root from the selected project (or cwd as fallback)."""
        start = None
        if self._project_context and self._project_context.has_project():
            p = self._project_context.get_project()
            if isinstance(p, Path):
                start = p
            else:
                return None  # remote project — git not supported
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True, text=True, timeout=5,
                cwd=start
            )
            if result.returncode == 0:
                return Path(result.stdout.strip())
        except Exception as e:
            logger.warning("Could not find git repo root: %s", e)
        return None

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(5)

        # Header
        header_row = QHBoxLayout()
        header = QLabel("Git Worktrees")
        header.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};"
        )
        self.repo_label = QLabel()
        self.repo_label.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        header_row.addWidget(header)
        header_row.addStretch()
        header_row.addWidget(self.repo_label)
        layout.addLayout(header_row)

        # Worktrees table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Path", "Branch", "Commit"])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        # Do NOT use setStretchLastSection — it locks the last column
        self.table.setColumnWidth(0, 300)
        self.table.setColumnWidth(1, 180)
        self.table.setColumnWidth(2, 120)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        UIStateManager.instance().restore_table_state("worktrees.table", self.table)
        UIStateManager.instance().connect_table("worktrees.table", self.table)
        layout.addWidget(self.table, 1)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(5)

        add_btn = QPushButton("➕ Add Worktree")
        add_btn.clicked.connect(self.add_worktree)

        remove_btn = QPushButton("🗑️ Remove")
        remove_btn.setStyleSheet(theme.get_button_danger_style())
        remove_btn.setToolTip("Remove selected worktree (git worktree remove)")
        remove_btn.clicked.connect(self.remove_worktree)

        prune_btn = QPushButton("✂️ Prune")
        prune_btn.setStyleSheet(theme.get_button_neutral_style())
        prune_btn.setToolTip("Prune stale worktree entries (git worktree prune)")
        prune_btn.clicked.connect(self.prune_worktrees)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet(theme.get_button_neutral_style())
        refresh_btn.clicked.connect(self.refresh)

        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addWidget(prune_btn)
        btn_row.addStretch()
        btn_row.addWidget(refresh_btn)
        layout.addLayout(btn_row)

        # Info footer
        tip = QLabel(
            "💡 <b>Worktrees</b> let Claude Code work in isolated branches simultaneously. "
            "Use <code>isolation: \"worktree\"</code> in an agent's frontmatter to automatically "
            "create and clean up a worktree for each agent run. "
            "The main worktree is always listed first and cannot be removed."
        )
        tip.setWordWrap(True)
        tip.setStyleSheet(
            f"color: {theme.FG_SECONDARY}; background: {theme.BG_MEDIUM}; "
            f"padding: 8px; border-radius: 3px; font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        layout.addWidget(tip)

    def refresh(self):
        if self.repo_root:
            self.repo_label.setText(f"Repo: {self.repo_root}")
        else:
            self.repo_label.setText("No git repository detected in current directory")

        self.table.setRowCount(0)
        worktrees = self._list_worktrees()
        for wt in worktrees:
            row = self.table.rowCount()
            self.table.insertRow(row)
            path_item = QTableWidgetItem(wt.get("path", ""))
            if wt.get("is_main"):
                path_item.setForeground(
                    __import__("PyQt6.QtGui", fromlist=["QColor"]).QColor(theme.ACCENT_PRIMARY)
                )
                path_item.setToolTip("Main worktree (cannot be removed)")
            self.table.setItem(row, 0, path_item)
            self.table.setItem(row, 1, QTableWidgetItem(wt.get("branch", "")))
            self.table.setItem(row, 2, QTableWidgetItem(wt.get("commit", "")[:12]))

    def _list_worktrees(self) -> list:
        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                capture_output=True, text=True, timeout=10,
                cwd=self.repo_root or Path.cwd()
            )
            if result.returncode != 0:
                return []
            return self._parse_worktree_list(result.stdout)
        except Exception as e:
            logger.warning("Could not list worktrees: %s", e)
            return []

    def _parse_worktree_list(self, output: str) -> list:
        worktrees = []
        current = {}
        first = True
        for line in output.splitlines():
            if line.startswith("worktree "):
                if current:
                    worktrees.append(current)
                current = {"path": line[9:], "is_main": first}
                first = False
            elif line.startswith("HEAD "):
                current["commit"] = line[5:]
            elif line.startswith("branch "):
                current["branch"] = line[7:].replace("refs/heads/", "")
            elif line == "bare":
                current["branch"] = "(bare)"
            elif line == "detached":
                current["branch"] = "(detached)"
        if current:
            worktrees.append(current)
        return worktrees

    def add_worktree(self):
        if not self.repo_root:
            QMessageBox.warning(self, "No Repository", "No git repository found in current directory.")
            return
        dlg = NewWorktreeDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        data = dlg.get_data()
        if not data["path"]:
            QMessageBox.warning(self, "Missing Path", "Worktree path is required.")
            return

        cmd = ["git", "worktree", "add"]
        if data["new_branch"]:
            cmd += ["-b", data["new_branch"]]
        cmd.append(data["path"])
        if data["branch"]:
            cmd.append(data["branch"])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
                cwd=self.repo_root
            )
            if result.returncode == 0:
                QMessageBox.information(self, "Created", f"Worktree created at:\n{data['path']}")
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", f"git worktree add failed:\n{result.stderr}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def remove_worktree(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Select a worktree to remove.")
            return

        path = self.table.item(row, 0).text()
        is_main = self.table.item(row, 0).toolTip() == "Main worktree (cannot be removed)"

        if is_main:
            QMessageBox.warning(self, "Cannot Remove", "The main worktree cannot be removed.")
            return

        reply = QMessageBox.question(
            self, "Remove Worktree",
            f"Remove worktree:\n{path}\n\nThe directory will be deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            result = subprocess.run(
                ["git", "worktree", "remove", path],
                capture_output=True, text=True, timeout=30,
                cwd=self.repo_root
            )
            if result.returncode == 0:
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", f"git worktree remove failed:\n{result.stderr}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def prune_worktrees(self):
        try:
            result = subprocess.run(
                ["git", "worktree", "prune"],
                capture_output=True, text=True, timeout=10,
                cwd=self.repo_root or Path.cwd()
            )
            if result.returncode == 0:
                self.refresh()
                QMessageBox.information(self, "Pruned", "Stale worktree entries removed.")
            else:
                QMessageBox.critical(self, "Error", f"git worktree prune failed:\n{result.stderr}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
