"""
Config Sync Tab - GitHub configuration synchronization using git commands
"""

import os
import subprocess
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QMessageBox, QGroupBox, QLineEdit, QInputDialog, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import theme


class ConfigSyncTab(QWidget):
    """Tab for managing Claude Code configuration sync with GitHub via git"""

    def __init__(self, config_manager, backup_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager

        # Claude config directory (cross-platform)
        self.claude_dir = Path.home() / ".claude"

        self.init_ui()
        self.load_status()

    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        #header = QLabel("Configuration Sync XXX")
        #header.setStyleSheet(f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")
        #layout.addWidget(header)

        # Status Group
        status_group = self.create_status_group()
        layout.addWidget(status_group)

        # Actions Group
        actions_group = self.create_actions_group()
        layout.addWidget(actions_group)

        # Log viewer
        log_group = QGroupBox("Sync Log")
        log_group.setStyleSheet(theme.get_groupbox_style())
        log_layout = QVBoxLayout()

        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setStyleSheet(f"""
            QTextEdit {{
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: {theme.FONT_SIZE_SMALL}px;
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
                border: 1px solid {theme.BG_LIGHT};
                border-radius: 3px;
                padding: 8px;
            }}
        """)
        log_layout.addWidget(self.log_viewer)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group, 1)

    def create_status_group(self):
        """Create status display group"""
        group = QGroupBox("Sync Status")
        group.setStyleSheet(theme.get_groupbox_style())
        layout = QVBoxLayout()

        # Status labels
        self.repo_label = QLabel("Repository: Not configured")
        self.branch_label = QLabel("Branch: N/A")
        self.last_sync_label = QLabel("Last sync: Never")
        self.changes_label = QLabel("Local changes: N/A")

        for label in [self.repo_label, self.branch_label, self.last_sync_label, self.changes_label]:
            label.setStyleSheet(f"color: {theme.FG_PRIMARY}; font-size: {theme.FONT_SIZE_NORMAL}px; padding: 3px;")
            layout.addWidget(label)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Status")
        refresh_btn.setStyleSheet(theme.get_button_style())
        refresh_btn.setToolTip("Reload sync status from git repository")
        refresh_btn.clicked.connect(self.load_status)
        layout.addWidget(refresh_btn)

        group.setLayout(layout)
        return group

    def create_actions_group(self):
        """Create actions group"""
        group = QGroupBox("Sync Actions")
        group.setStyleSheet(theme.get_groupbox_style())
        layout = QVBoxLayout()

        # Initialize sync
        init_layout = QHBoxLayout()
        init_btn = QPushButton("🚀 Initialize Sync")
        init_btn.setStyleSheet(theme.get_button_style())
        init_btn.setToolTip("Set up GitHub sync repository")
        init_btn.clicked.connect(self.initialize_sync)
        init_layout.addWidget(init_btn)
        layout.addLayout(init_layout)

        # Pull/Push layout
        sync_layout = QHBoxLayout()

        pull_btn = QPushButton("📥 Pull from Remote")
        pull_btn.setStyleSheet(theme.get_button_style())
        pull_btn.setToolTip("Download latest config from GitHub")
        pull_btn.clicked.connect(self.pull_config)

        push_btn = QPushButton("📤 Push to Remote")
        push_btn.setStyleSheet(theme.get_button_style())
        push_btn.setToolTip("Upload local changes to GitHub")
        push_btn.clicked.connect(self.push_config)

        sync_layout.addWidget(pull_btn)
        sync_layout.addWidget(push_btn)
        layout.addLayout(sync_layout)

        group.setLayout(layout)
        return group

    def log(self, message):
        """Add message to log viewer"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_viewer.append(f"[{timestamp}] {message}")

    def run_git_command(self, args, check_repo=True):
        """
        Run git command in ~/.claude directory

        Args:
            args: List of git command arguments (e.g., ['status', '--porcelain'])
            check_repo: If True, check if directory is a git repo first

        Returns:
            (success: bool, output: str)
        """
        try:
            # Check if directory exists
            if not self.claude_dir.exists():
                return False, f"Directory {self.claude_dir} does not exist"

            # Check if it's a git repo (unless we're initializing)
            if check_repo and not (self.claude_dir / ".git").exists():
                return False, "Not a git repository. Please initialize sync first."

            # Build command
            cmd = ["git", "-C", str(self.claude_dir)] + args

            self.log(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                # Return both stderr and stdout (git sometimes uses stdout for errors)
                error_output = result.stderr.strip()
                if not error_output and result.stdout.strip():
                    error_output = result.stdout.strip()
                return False, error_output

        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def check_git_repo(self):
        """Check if ~/.claude is a git repository"""
        return (self.claude_dir / ".git").exists()

    def get_repo_info(self):
        """
        Get repository information

        Returns:
            dict with keys: remote, branch, modified, added, deleted
        """
        info = {
            "remote": None,
            "branch": None,
            "modified": [],
            "added": [],
            "deleted": []
        }

        if not self.check_git_repo():
            return info

        # Get remote URL
        success, output = self.run_git_command(["remote", "get-url", "origin"])
        if success:
            info["remote"] = output

        # Get current branch
        success, output = self.run_git_command(["branch", "--show-current"])
        if success:
            info["branch"] = output

        # Get status (porcelain format for parsing)
        success, output = self.run_git_command(["status", "--porcelain"])
        if success and output:
            for line in output.split('\n'):
                if not line:
                    continue
                status = line[:2]
                filename = line[3:]

                if status[0] in ['M', ' '] and status[1] == 'M':
                    info["modified"].append(filename)
                elif status[0] in ['A', '?']:
                    info["added"].append(filename)
                elif status[0] == 'D':
                    info["deleted"].append(filename)

        return info

    def load_status(self):
        """Load and display sync status"""
        self.log("Loading sync status...")

        if not self.check_git_repo():
            self.repo_label.setText("Repository: Not initialized")
            self.branch_label.setText("Branch: N/A")
            self.last_sync_label.setText("Last sync: Never")
            self.changes_label.setText("Local changes: N/A")
            self.log("❌ Not a git repository")
            return

        info = self.get_repo_info()

        # Update labels
        self.repo_label.setText(f"Repository: {info['remote'] or 'No remote configured'}")
        self.branch_label.setText(f"Branch: {info['branch'] or 'N/A'}")

        # Get last commit date
        success, output = self.run_git_command(["log", "-1", "--format=%ci"])
        if success and output:
            self.last_sync_label.setText(f"Last commit: {output}")
        else:
            self.last_sync_label.setText("Last commit: Never")

        # Update changes count
        modified = len(info["modified"])
        added = len(info["added"])
        deleted = len(info["deleted"])
        total = modified + added + deleted

        self.changes_label.setText(
            f"Local changes: {total} files ({modified} modified, {added} added, {deleted} deleted)"
        )

        self.log(f"✅ Status loaded: {total} local changes")

    def initialize_sync(self):
        """Initialize git repository and sync setup"""
        # Check if already initialized
        if self.check_git_repo():
            reply = QMessageBox.question(
                self,
                "Already Initialized",
                "Git repository already exists in ~/.claude\n\nRe-initialize? This will NOT delete existing files.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Get repository URL
        repo_url, ok = QInputDialog.getText(
            self,
            "Initialize Sync",
            "Enter GitHub repository URL:\n(e.g., git@github.com:username/claude-code-config.git)\n\nOr leave empty to just init locally:",
            QLineEdit.EchoMode.Normal,
            ""
        )

        if not ok:
            return

        # Confirmation
        reply = QMessageBox.question(
            self,
            "Confirm Initialization",
            f"Initialize git repository in ~/.claude?\n\n"
            f"Remote: {repo_url or 'None (local only)'}\n\n"
            "This will:\n"
            "• Initialize git repository\n"
            "• Add remote (if provided)\n"
            "• Create initial commit\n"
            "• Push to remote (if provided)\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self.log("Initializing git repository...")

        # Initialize git repo
        success, output = self.run_git_command(["init"], check_repo=False)
        if not success:
            self.log(f"❌ Failed to init: {output}")
            QMessageBox.critical(self, "Error", f"Failed to initialize:\n{output}")
            return

        self.log("✅ Git repository initialized")

        # Configure git user if not set (required for commits)
        success, output = self.run_git_command(["config", "user.name"], check_repo=False)
        if not success or not output:
            self.run_git_command(["config", "user.name", "Claude Code User"], check_repo=False)
            self.log("✅ Configured git user.name")

        success, output = self.run_git_command(["config", "user.email"], check_repo=False)
        if not success or not output:
            self.run_git_command(["config", "user.email", "claude-code@local"], check_repo=False)
            self.log("✅ Configured git user.email")

        # Add remote if provided
        if repo_url:
            # Remove existing origin if it exists
            self.run_git_command(["remote", "remove", "origin"])

            success, output = self.run_git_command(["remote", "add", "origin", repo_url])
            if not success:
                self.log(f"❌ Failed to add remote: {output}")
                QMessageBox.warning(self, "Warning", f"Failed to add remote:\n{output}\n\nRepository initialized locally only.")
            else:
                self.log(f"✅ Added remote: {repo_url}")

        # Create initial commit
        self.log("Creating initial commit...")
        success, output = self.run_git_command(["add", "."])
        if not success:
            self.log(f"❌ Failed to stage files: {output}")

        success, output = self.run_git_command(["commit", "-m", "Initial commit - Claude Code config"])
        if not success:
            if "nothing to commit" in output.lower() or "nothing added to commit" in output.lower():
                self.log("⚠️ No new files to commit (already committed)")
            else:
                self.log(f"❌ Failed to commit: {output if output else '(no error message)'}")
        else:
            self.log("✅ Initial commit created")

        # Push to remote if configured
        if repo_url:
            reply = QMessageBox.question(
                self,
                "Push to Remote?",
                "Push initial commit to remote?\n\nThis will upload your ~/.claude configuration to GitHub.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.log("Pushing to remote...")
                success, output = self.run_git_command(["push", "-u", "origin", "main"])
                if not success:
                    # Try master branch if main fails
                    success, output = self.run_git_command(["push", "-u", "origin", "master"])

                if success:
                    self.log("✅ Pushed to remote successfully")
                    QMessageBox.information(self, "Success", "Sync initialized and pushed to remote!")
                else:
                    self.log(f"❌ Push failed: {output}")
                    QMessageBox.warning(self, "Warning", f"Initialized locally but push failed:\n{output}")
            else:
                QMessageBox.information(self, "Success", "Sync initialized locally!")
        else:
            QMessageBox.information(self, "Success", "Git repository initialized locally!")

        self.load_status()

    def pull_config(self):
        """Pull configuration from remote"""
        if not self.check_git_repo():
            QMessageBox.warning(self, "Error", "Not initialized. Please initialize sync first.")
            return

        # Check if remote exists
        success, output = self.run_git_command(["remote", "get-url", "origin"])
        if not success:
            QMessageBox.warning(self, "Error", "No remote configured. Cannot pull.")
            return

        reply = QMessageBox.question(
            self,
            "Pull Configuration",
            "Pull latest configuration from GitHub?\n\n"
            "This will download and merge remote changes.\n"
            "Local changes will be preserved.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self.log("Pulling from remote...")

        # Get current branch
        success, branch = self.run_git_command(["branch", "--show-current"])
        if not success or not branch:
            branch = "main"
            self.log(f"⚠️ Could not detect branch, using: {branch}")

        # Pull
        success, output = self.run_git_command(["pull", "origin", branch])

        if success:
            self.log(f"✅ Pull successful:\n{output}")
            QMessageBox.information(self, "Success", "Configuration pulled successfully!")
            self.load_status()
        else:
            self.log(f"❌ Pull failed: {output}")
            QMessageBox.critical(self, "Pull Failed", f"Failed to pull:\n{output}")

    def push_config(self):
        """Push configuration to remote"""
        if not self.check_git_repo():
            QMessageBox.warning(self, "Error", "Not initialized. Please initialize sync first.")
            return

        # Check if remote exists
        success, output = self.run_git_command(["remote", "get-url", "origin"])
        if not success:
            QMessageBox.warning(self, "Error", "No remote configured. Cannot push.")
            return

        # Get current status
        self.log("Checking for local changes...")
        info = self.get_repo_info()

        modified = info["modified"]
        added = info["added"]
        deleted = info["deleted"]

        if not (modified or added or deleted):
            QMessageBox.information(self, "No Changes", "No local changes to push.")
            return

        # Show diff dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Review Changes Before Push")
        dialog.setMinimumSize(700, 500)

        layout = QVBoxLayout(dialog)

        info_label = QLabel(f"📝 {len(modified)} modified • ➕ {len(added)} added • ❌ {len(deleted)} deleted")
        info_label.setStyleSheet(f"font-size: {theme.FONT_SIZE_NORMAL}px; font-weight: bold; color: {theme.ACCENT_PRIMARY};")
        layout.addWidget(info_label)

        diff_viewer = QTextEdit()
        diff_viewer.setReadOnly(True)
        diff_viewer.setStyleSheet(f"""
            QTextEdit {{
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: {theme.FONT_SIZE_SMALL}px;
                background-color: {theme.BG_DARK};
                color: {theme.FG_PRIMARY};
            }}
        """)

        # Build diff text
        diff_text = ""
        if modified:
            diff_text += "🔄 MODIFIED FILES:\n"
            for file in modified:
                diff_text += f"  • {file}\n"
            diff_text += "\n"

        if added:
            diff_text += "➕ ADDED FILES:\n"
            for file in added:
                diff_text += f"  • {file}\n"
            diff_text += "\n"

        if deleted:
            diff_text += "❌ DELETED FILES:\n"
            for file in deleted:
                diff_text += f"  • {file}\n"
            diff_text += "\n"

        diff_viewer.setText(diff_text)
        layout.addWidget(diff_viewer)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        # Get commit message
        message, ok = QInputDialog.getText(
            self,
            "Push Configuration",
            "Enter commit message:",
            QLineEdit.EchoMode.Normal,
            "Update Claude Code configuration"
        )

        if not ok or not message.strip():
            return

        # Final confirmation
        reply = QMessageBox.question(
            self,
            "Confirm Push",
            f"Push local changes to GitHub?\n\nCommit message:\n{message}\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self.log("Staging changes...")

        # Stage all changes
        success, output = self.run_git_command(["add", "."])
        if not success:
            self.log(f"❌ Failed to stage: {output}")
            QMessageBox.critical(self, "Error", f"Failed to stage changes:\n{output}")
            return

        # Commit
        self.log("Committing...")
        success, output = self.run_git_command(["commit", "-m", message])
        if not success:
            if "nothing to commit" in output.lower() or "nothing added to commit" in output.lower():
                self.log("⚠️ Nothing to commit")
                QMessageBox.information(self, "No Changes", "No changes to commit.")
                return
            else:
                error_msg = output if output else "(no error message)"
                self.log(f"❌ Commit failed: {error_msg}")
                QMessageBox.critical(self, "Error", f"Failed to commit:\n{error_msg}")
                return

        self.log("✅ Committed successfully")

        # Push
        self.log("Pushing to remote...")
        success, branch = self.run_git_command(["branch", "--show-current"])
        if not success or not branch:
            branch = "main"

        success, output = self.run_git_command(["push", "origin", branch])

        if success:
            self.log(f"✅ Push successful:\n{output}")
            QMessageBox.information(self, "Success", "Configuration pushed successfully!")
            self.load_status()
        else:
            self.log(f"❌ Push failed: {output}")
            QMessageBox.critical(self, "Push Failed", f"Failed to push:\n{output}\n\nChanges are committed locally but not pushed.")
