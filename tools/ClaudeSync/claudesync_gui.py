#!/usr/bin/env python3
import configparser
import json
import logging
import os
import subprocess
import sys
import tkinter as tk
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from tkinter import filedialog
from typing import Any, Dict, List, Optional, Tuple

import CTkToolTip
import customtkinter
from PIL import Image

# Configure customtkinter appearance
customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")


class ConfigHandler:
    """Handles all configuration file operations"""

    def __init__(self, config_file: str = "claudesync.conf"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_or_create_config()

    def load_or_create_config(self) -> None:
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self._create_default_config()

    def _create_default_config(self) -> None:
        self.config["General"] = {
            "theme": "dark-blue",
            "language": "en",
            "first_run": "true",
            "min_width": "800",
            "min_height": "600",
            "log_level": "INFO",
            "log_file": "claudesync.log",
        }

        self.config["Authentication"] = {
            "session_key": "",
            "session_expiry": "",
            "active_provider": "claude.ai",
            "active_organization_id": "",
        }

        self.config["Project"] = {
            "active_project_id": "",
            "active_project_name": "",
            "local_path": "",
        }

        self.config["Sync"] = {
            "upload_delay": "0.5",
            "max_file_size": "32768",
            "two_way_sync": "false",
            "prune_remote_files": "false",
        }

        self.config["Schedule"] = {
            "enabled": "false",
            "frequency": "daily",
            "time": "00:00",
            "days": "",
        }

        self.config["Categories"] = {}

        self.save()

    def save(self) -> None:
        with open(self.config_file, "w") as configfile:
            self.config.write(configfile)

    def get(self, section: str, key: str, fallback: Any = None) -> str:
        return self.config.get(section, key, fallback=fallback)

    def set(self, section: str, key: str, value: str) -> None:
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))


class LogHandler:
    """Handles application logging"""

    def __init__(self, log_file: str = "claudesync.log"):
        self.logger = logging.getLogger("ClaudeSync")
        self.logger.setLevel(logging.INFO)

        # File Handler
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 5MB
        )
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(file_handler)

        # Store logs for GUI display
        self.log_queue: List[str] = []
        self.max_queue_size = 1000

    def add_gui_handler(self, callback):
        """Add handler for GUI updates"""

        class GUIHandler(logging.Handler):
            def emit(self_handler, record):
                log_entry = self_handler.format(record)
                callback(log_entry)
                self.log_queue.append(log_entry)
                if len(self.log_queue) > self.max_queue_size:
                    self.log_queue.pop(0)

        gui_handler = GUIHandler()
        gui_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(gui_handler)

    def log(self, level: str, message: str) -> None:
        level_map = {
            "INFO": self.logger.info,
            "WARNING": self.logger.warning,
            "ERROR": self.logger.error,
            "DEBUG": self.logger.debug,
        }
        if level.upper() in level_map:
            level_map[level.upper()](message)


class CommandExecutor:
    """Handles CLI command execution"""

    def __init__(self, logger: LogHandler):
        self.logger = logger

    def execute(self, command: List[str]) -> Tuple[int, str, str]:
        try:
            self.logger.log("DEBUG", f"Executing command: {' '.join(command)}")
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                self.logger.log("ERROR", f"Command failed: {stderr}")
            else:
                self.logger.log("DEBUG", f"Command successful: {stdout}")

            return process.returncode, stdout, stderr
        except Exception as e:
            self.logger.log("ERROR", f"Command execution error: {str(e)}")
            return -1, "", str(e)


class StatusBar(customtkinter.CTkFrame):
    """Status bar for displaying application state"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.status = {
            "Connection": "Disconnected",
            "Project": "None",
            "Last Sync": "Never",
            "Status": "Ready",
        }

        self.labels = {}
        for i, (key, value) in enumerate(self.status.items()):
            self.labels[key] = customtkinter.CTkLabel(
                self, text=f"{key}: {value}", width=150
            )
            self.labels[key].grid(row=0, column=i, padx=5, pady=2, sticky="w")

        self.grid_columnconfigure(len(self.status) - 1, weight=1)

    def update_status(self, key: str, value: str) -> None:
        if key in self.labels:
            self.status[key] = value
            self.labels[key].configure(text=f"{key}: {value}")


class ConfirmDialog(customtkinter.CTkToplevel):
    """Dialog for confirming dangerous operations"""

    def __init__(self, parent, title: str, message: str):
        super().__init__(parent)

        self.title(title)
        self.result = False

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Layout
        self.geometry("300x150")

        label = customtkinter.CTkLabel(self, text=message, wraplength=250)
        label.pack(pady=20, padx=20)

        button_frame = customtkinter.CTkFrame(self)
        button_frame.pack(fill="x", padx=20, pady=10)

        yes_button = customtkinter.CTkButton(
            button_frame, text="Yes", command=self.yes_click
        )
        yes_button.pack(side="left", padx=10)

        no_button = customtkinter.CTkButton(
            button_frame, text="No", command=self.no_click
        )
        no_button.pack(side="right", padx=10)

        self.wait_window()

    def yes_click(self):
        self.result = True
        self.destroy()

    def no_click(self):
        self.result = False
        self.destroy()


class UpdateCheckDialog(customtkinter.CTkToplevel):
    """Dialog for update checking"""

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Checking for Updates")
        self.geometry("300x100")

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        self.label = customtkinter.CTkLabel(self, text="Checking for updates...")
        self.label.pack(pady=20)

        self.progress = customtkinter.CTkProgressBar(self)
        self.progress.pack(padx=20, pady=10)
        self.progress.start()

    def update_status(self, message: str):
        self.label.configure(text=message)

    def done(self):
        self.progress.stop()
        self.destroy()


# --- END OF PART 1 --- CONTINUE WITH PART 2 BELOW ---


class ClaudeSyncGUI(customtkinter.CTk):
    """Main application window"""

    def __init__(self):
        super().__init__()

        # Initialize components
        self.config = ConfigHandler()
        self.logger = LogHandler()
        self.command_executor = CommandExecutor(self.logger)

        # Window setup
        self.title("ClaudeSync GUI")
        self.geometry(
            f"{self.config.get('General',
    'min_width')}x{self.config.get('General',
     'min_height')}"
        )
        self.minsize(
            width=int(self.config.get("General", "min_width")),
            height=int(self.config.get("General", "min_height")),
        )

        # Initialize GUI elements
        self.setup_gui()

        # First run check
        if self.config.get("General", "first_run") == "true":
            self.first_run_setup()

        # Check session expiry
        self.check_session_expiry()

        # Check for updates
        self.check_for_updates()

    def setup_gui(self):
        """Setup main GUI elements"""
        # Main container
        self.main_container = customtkinter.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        # Tab view
        self.tab_view = customtkinter.CTkTabview(self.main_container)
        self.tab_view.pack(fill="both", expand=True)

        # Add tabs
        self.tab_view.add("Authentication")
        self.tab_view.add("Projects")
        self.tab_view.add("Sync")
        self.tab_view.add("Chat")
        self.tab_view.add("Configuration")
        self.tab_view.add("Logs")

        # Setup each tab
        self.setup_auth_tab()
        self.setup_projects_tab()
        self.setup_sync_tab()
        self.setup_chat_tab()
        self.setup_config_tab()
        self.setup_logs_tab()

        # Status bar
        self.status_bar = StatusBar(self)
        self.status_bar.pack(fill="x", padx=10, pady=10)

    def setup_auth_tab(self):
        """Setup Authentication tab"""
        tab = self.tab_view.tab("Authentication")

        # Login frame
        login_frame = customtkinter.CTkFrame(tab)
        login_frame.pack(padx=20, pady=20, fill="x")

        # Session key entry
        session_key_label = customtkinter.CTkLabel(login_frame, text="Session Key:")
        session_key_label.grid(row=0, column=0, padx=10, pady=10)

        self.session_key_entry = customtkinter.CTkEntry(
            login_frame, width=300, show="*"
        )
        self.session_key_entry.grid(row=0, column=1, padx=10, pady=10)
        CTkToolTip.CTkToolTip(
            self.session_key_entry, message="Enter your Claude.ai session key"
        )

        # Login button
        login_button = customtkinter.CTkButton(
            login_frame, text="Login", command=self.handle_login
        )
        login_button.grid(row=0, column=2, padx=10, pady=10)

        # Organization selection
        org_frame = customtkinter.CTkFrame(tab)
        org_frame.pack(padx=20, pady=20, fill="x")

        org_label = customtkinter.CTkLabel(org_frame, text="Organization:")
        org_label.grid(row=0, column=0, padx=10, pady=10)

        self.org_dropdown = customtkinter.CTkOptionMenu(
            org_frame,
            values=["No organizations found"],
            command=self.handle_org_selection,
        )
        self.org_dropdown.grid(row=0, column=1, padx=10, pady=10)

    # --- END OF PART 2 --- CONTINUE WITH PART 3 BELOW ---

    def setup_projects_tab(self):
        """Setup Projects tab"""
        tab = self.tab_view.tab("Projects")

        # Project list frame
        list_frame = customtkinter.CTkFrame(tab)
        list_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Project selection
        select_label = customtkinter.CTkLabel(list_frame, text="Select Project:")
        select_label.pack(padx=10, pady=5)

        self.project_list = customtkinter.CTkTextbox(list_frame, height=200)
        self.project_list.pack(padx=10, pady=5, fill="both", expand=True)

        # Buttons frame
        button_frame = customtkinter.CTkFrame(tab)
        button_frame.pack(padx=20, pady=10, fill="x")

        create_button = customtkinter.CTkButton(
            button_frame, text="Create Project", command=self.create_project
        )
        create_button.pack(side="left", padx=5)

        archive_button = customtkinter.CTkButton(
            button_frame, text="Archive Project", command=self.archive_project
        )
        archive_button.pack(side="left", padx=5)

        refresh_button = customtkinter.CTkButton(
            button_frame, text="Refresh List", command=self.refresh_projects
        )
        refresh_button.pack(side="left", padx=5)

    def setup_sync_tab(self):
        """Setup Sync tab"""
        tab = self.tab_view.tab("Sync")

        # Sync options frame
        options_frame = customtkinter.CTkFrame(tab)
        options_frame.pack(padx=20, pady=20, fill="x")

        # Sync mode selection
        mode_label = customtkinter.CTkLabel(options_frame, text="Sync Mode:")
        mode_label.grid(row=0, column=0, padx=10, pady=10)

        self.sync_mode = customtkinter.CTkOptionMenu(
            options_frame,
            values=["Normal", "Uberproject", "Category"],
            command=self.handle_sync_mode_change,
        )
        self.sync_mode.grid(row=0, column=1, padx=10, pady=10)

        # Category selection (initially hidden)
        self.category_frame = customtkinter.CTkFrame(options_frame)
        self.category_dropdown = customtkinter.CTkOptionMenu(
            self.category_frame, values=["No categories"]
        )

        # Preview frame
        preview_frame = customtkinter.CTkFrame(tab)
        preview_frame.pack(padx=20, pady=10, fill="both", expand=True)

        preview_label = customtkinter.CTkLabel(preview_frame, text="Files to Sync:")
        preview_label.pack(padx=10, pady=5)

        self.preview_list = customtkinter.CTkTextbox(preview_frame)
        self.preview_list.pack(padx=10, pady=5, fill="both", expand=True)

        # Scheduler frame
        scheduler_frame = customtkinter.CTkFrame(tab)
        scheduler_frame.pack(padx=20, pady=10, fill="x")

        # Schedule enable switch
        self.schedule_switch = customtkinter.CTkSwitch(
            scheduler_frame, text="Enable Scheduling", command=self.toggle_scheduler
        )
        self.schedule_switch.grid(row=0, column=0, padx=10, pady=10)

        # Frequency selection
        self.frequency_dropdown = customtkinter.CTkOptionMenu(
            scheduler_frame,
            values=["Daily", "Weekly"],
            command=self.handle_frequency_change,
        )
        self.frequency_dropdown.grid(row=0, column=1, padx=10, pady=10)

        # Time selection
        time_label = customtkinter.CTkLabel(scheduler_frame, text="Time:")
        time_label.grid(row=0, column=2, padx=5, pady=10)

        self.time_entry = customtkinter.CTkEntry(scheduler_frame, width=100)
        self.time_entry.grid(row=0, column=3, padx=5, pady=10)
        self.time_entry.insert(0, "00:00")

        # Days selection (for weekly schedule)
        self.days_frame = customtkinter.CTkFrame(scheduler_frame)
        self.day_vars = {}
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            var = customtkinter.StringVar(value="0")
            checkbox = customtkinter.CTkCheckBox(
                self.days_frame, text=day, variable=var
            )
            checkbox.grid(row=0, column=i, padx=5, pady=5)
            self.day_vars[day] = var

        # Sync button
        sync_button = customtkinter.CTkButton(
            tab, text="Start Sync", command=self.start_sync
        )
        sync_button.pack(padx=20, pady=20)

        # Progress bar
        self.sync_progress = customtkinter.CTkProgressBar(tab)
        self.sync_progress.pack(padx=20, pady=10, fill="x")
        self.sync_progress.set(0)

    def setup_chat_tab(self):
        """Setup Chat tab"""
        tab = self.tab_view.tab("Chat")

        # Chat list frame
        list_frame = customtkinter.CTkFrame(tab)
        list_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Chat selection
        select_label = customtkinter.CTkLabel(list_frame, text="Select Chat:")
        select_label.pack(padx=10, pady=5)

        self.chat_list = customtkinter.CTkTextbox(list_frame, height=200)
        self.chat_list.pack(padx=10, pady=5, fill="both", expand=True)

        # Buttons frame
        button_frame = customtkinter.CTkFrame(tab)
        button_frame.pack(padx=20, pady=10, fill="x")

        create_button = customtkinter.CTkButton(
            button_frame, text="Create Chat", command=self.create_chat
        )
        create_button.pack(side="left", padx=5)

        delete_button = customtkinter.CTkButton(
            button_frame, text="Delete Chat", command=self.delete_chat
        )
        delete_button.pack(side="left", padx=5)

        sync_button = customtkinter.CTkButton(
            button_frame, text="Sync Chats", command=self.sync_chats
        )
        sync_button.pack(side="left", padx=5)

        # Message frame
        message_frame = customtkinter.CTkFrame(tab)
        message_frame.pack(padx=20, pady=10, fill="x")

        self.message_entry = customtkinter.CTkEntry(
            message_frame, placeholder_text="Enter message..."
        )
        self.message_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)

        send_button = customtkinter.CTkButton(
            message_frame, text="Send", command=self.send_message
        )
        send_button.pack(side="right", padx=5, pady=5)

    # --- END OF PART 3 --- CONTINUE WITH PART 4 BELOW ---

    def setup_config_tab(self):
        """Setup Configuration tab"""
        tab = self.tab_view.tab("Configuration")

        # Create scrollable frame
        config_frame = customtkinter.CTkScrollableFrame(tab)
        config_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Theme selection
        theme_label = customtkinter.CTkLabel(config_frame, text="Theme:")
        theme_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.theme_dropdown = customtkinter.CTkOptionMenu(
            config_frame,
            values=["blue", "dark-blue", "green"],
            command=self.change_theme,
        )
        self.theme_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.theme_dropdown.set(self.config.get("General", "theme"))

        # Sync settings
        upload_delay_label = customtkinter.CTkLabel(config_frame, text="Upload Delay:")
        upload_delay_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.upload_delay_entry = customtkinter.CTkEntry(config_frame)
        self.upload_delay_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        self.upload_delay_entry.insert(0, self.config.get("Sync", "upload_delay"))

        max_file_size_label = customtkinter.CTkLabel(
            config_frame, text="Max File Size (bytes):"
        )
        max_file_size_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        self.max_file_size_entry = customtkinter.CTkEntry(config_frame)
        self.max_file_size_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        self.max_file_size_entry.insert(0, self.config.get("Sync", "max_file_size"))

        # Sync options
        self.two_way_sync_var = customtkinter.StringVar(
            value=self.config.get("Sync", "two_way_sync")
        )
        two_way_sync_check = customtkinter.CTkCheckBox(
            config_frame, text="Two-way Sync", variable=self.two_way_sync_var
        )
        two_way_sync_check.grid(
            row=3, column=0, columnspan=2, padx=10, pady=10, sticky="w"
        )

        self.prune_remote_var = customtkinter.StringVar(
            value=self.config.get("Sync", "prune_remote_files")
        )
        prune_remote_check = customtkinter.CTkCheckBox(
            config_frame, text="Prune Remote Files", variable=self.prune_remote_var
        )
        prune_remote_check.grid(
            row=4, column=0, columnspan=2, padx=10, pady=10, sticky="w"
        )

        # Category management
        category_label = customtkinter.CTkLabel(config_frame, text="Categories:")
        category_label.grid(
            row=5, column=0, columnspan=2, padx=10, pady=(20, 10), sticky="w"
        )

        # Category list
        self.category_list = customtkinter.CTkTextbox(config_frame, height=100)
        self.category_list.grid(
            row=6, column=0, columnspan=2, padx=10, pady=5, sticky="ew"
        )

        # Category buttons
        category_button_frame = customtkinter.CTkFrame(config_frame)
        category_button_frame.grid(
            row=7, column=0, columnspan=2, padx=10, pady=10, sticky="ew"
        )

        add_category_button = customtkinter.CTkButton(
            category_button_frame, text="Add Category", command=self.add_category
        )
        add_category_button.pack(side="left", padx=5)

        remove_category_button = customtkinter.CTkButton(
            category_button_frame, text="Remove Category", command=self.remove_category
        )
        remove_category_button.pack(side="left", padx=5)

        # Save button
        save_button = customtkinter.CTkButton(
            config_frame, text="Apply Changes", command=self.save_config
        )
        save_button.grid(row=8, column=0, columnspan=2, padx=10, pady=20)

    def setup_logs_tab(self):
        """Setup Logs tab"""
        tab = self.tab_view.tab("Logs")

        # Log level selection
        level_frame = customtkinter.CTkFrame(tab)
        level_frame.pack(padx=20, pady=10, fill="x")

        level_label = customtkinter.CTkLabel(level_frame, text="Log Level:")
        level_label.pack(side="left", padx=10)

        self.log_level = customtkinter.CTkOptionMenu(
            level_frame,
            values=["INFO", "WARNING", "ERROR", "DEBUG"],
            command=self.change_log_level,
        )
        self.log_level.pack(side="left", padx=10)

        # Search frame
        search_frame = customtkinter.CTkFrame(tab)
        search_frame.pack(padx=20, pady=10, fill="x")

        self.search_entry = customtkinter.CTkEntry(
            search_frame, placeholder_text="Search logs..."
        )
        self.search_entry.pack(side="left", padx=10, pady=10, fill="x", expand=True)

        search_button = customtkinter.CTkButton(
            search_frame, text="Search", command=self.search_logs
        )
        search_button.pack(side="right", padx=10, pady=10)

        # Log display
        self.log_display = customtkinter.CTkTextbox(tab)
        self.log_display.pack(padx=20, pady=10, fill="both", expand=True)

        # Buttons frame
        button_frame = customtkinter.CTkFrame(tab)
        button_frame.pack(padx=20, pady=10, fill="x")

        clear_button = customtkinter.CTkButton(
            button_frame, text="Clear Logs", command=self.clear_logs
        )
        clear_button.pack(side="left", padx=5)

        export_button = customtkinter.CTkButton(
            button_frame, text="Export Logs", command=self.export_logs
        )
        export_button.pack(side="left", padx=5)

        # Initialize log handler
        self.logger.add_gui_handler(self.update_log_display)

    def update_log_display(self, message: str):
        """Update log display with new message"""
        self.log_display.insert("end", message + "\n")
        self.log_display.see("end")

    # --- END OF PART 4 --- CONTINUE WITH FINAL PART BELOW ---

    def first_run_setup(self):
        """Handle first run setup"""
        dialog = customtkinter.CTkInputDialog(
            text="Please enter your Claude.ai session key:", title="First Run Setup"
        )
        session_key = dialog.get_input()
        if session_key:
            self.config.set("Authentication", "session_key", session_key)
            self.config.set("General", "first_run", "false")
            self.config.save()
            self.session_key_entry.insert(0, session_key)
            self.handle_login()

    def check_session_expiry(self):
        """Check if session key is near expiration"""
        expiry_str = self.config.get("Authentication", "session_expiry")
        if expiry_str:
            expiry = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
            warning_threshold = expiry - timedelta(days=7)
            if datetime.now() >= warning_threshold:
                self.show_warning(
                    "Session Expiring",
                    f"Your session key will expire on {expiry.strftime('%Y-%m-%d')}. Please update it soon.",
                )

    def check_for_updates(self):
        """Check for application updates"""
        dialog = UpdateCheckDialog(self)

        try:
            # Execute update check command
            returncode, stdout, stderr = self.command_executor.execute(
                ["claudesync", "upgrade", "--check"]
            )

            if returncode == 0 and "upgrade available" in stdout.lower():
                dialog.update_status("Update available!")
                if self.show_confirm(
                    "Update Available", "Would you like to update now?"
                ):
                    self.perform_update()
            else:
                dialog.update_status("No updates available")
                self.after(2000, dialog.done)

        except Exception as e:
            dialog.update_status(f"Update check failed: {str(e)}")
            self.after(2000, dialog.done)

    def perform_update(self):
        """Perform application update"""
        returncode, stdout, stderr = self.command_executor.execute(
            ["claudesync", "upgrade"]
        )
        if returncode == 0:
            self.show_info(
                "Update Complete",
                "Application has been updated successfully. Please restart the application.",
            )
        else:
            self.show_error("Update Failed", f"Failed to update: {stderr}")

    def handle_login(self):
        """Handle login attempt"""
        session_key = self.session_key_entry.get()
        if not session_key:
            self.show_error("Login Error", "Please enter a session key")
            return

        # Save session key
        self.config.set("Authentication", "session_key", session_key)
        self.config.save()

        # Attempt login
        returncode, stdout, stderr = self.command_executor.execute(
            ["claudesync", "auth", "login", "--provider", "claude.ai"]
        )

        if returncode == 0:
            self.status_bar.update_status("Connection", "Connected")
            self.load_organizations()
        else:
            self.show_error("Login Failed", f"Failed to login: {stderr}")

    def load_organizations(self):
        """Load available organizations"""
        returncode, stdout, stderr = self.command_executor.execute(
            ["claudesync", "organization", "ls"]
        )

        if returncode == 0:
            orgs = [line.strip() for line in stdout.split("\n") if line.strip()]
            if orgs:
                self.org_dropdown.configure(values=orgs)
                self.org_dropdown.set(orgs[0])

    def handle_org_selection(self, org: str):
        """Handle organization selection"""
        returncode, stdout, stderr = self.command_executor.execute(
            ["claudesync", "organization", "set", org]
        )

        if returncode == 0:
            self.config.set("Authentication", "active_organization_id", org)
            self.config.save()
            self.refresh_projects()

    def refresh_projects(self):
        """Refresh project list"""
        returncode, stdout, stderr = self.command_executor.execute(
            ["claudesync", "project", "ls", "-a"]
        )

        if returncode == 0:
            self.project_list.delete("0.0", "end")
            self.project_list.insert("0.0", stdout)

    def create_project(self):
        """Create new project"""
        name_dialog = customtkinter.CTkInputDialog(
            text="Enter project name:", title="Create Project"
        )
        project_name = name_dialog.get_input()

        if project_name:
            path_dialog = customtkinter.CTkInputDialog(
                text="Enter project path:", title="Create Project"
            )
            project_path = path_dialog.get_input()

            if project_path:
                returncode, stdout, stderr = self.command_executor.execute(
                    [
                        "claudesync",
                        "project",
                        "create",
                        "--name",
                        project_name,
                        "--path",
                        project_path,
                    ]
                )

                if returncode == 0:
                    self.refresh_projects()
                else:
                    self.show_error(
                        "Project Creation Failed", f"Failed to create project: {stderr}"
                    )

    def archive_project(self):
        """Archive selected project"""
        if self.show_confirm(
            "Archive Project", "Are you sure you want to archive this project?"
        ):
            returncode, stdout, stderr = self.command_executor.execute(
                ["claudesync", "project", "archive"]
            )

            if returncode == 0:
                self.refresh_projects()
            else:
                self.show_error(
                    "Archive Failed", f"Failed to archive project: {stderr}"
                )

    def handle_sync_mode_change(self, mode: str):
        """Handle sync mode change"""
        if mode == "Category":
            self.category_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
            self.load_categories()
        else:
            self.category_frame.grid_forget()

    def load_categories(self):
        """Load available categories"""
        if "Categories" in self.config.config:
            categories = list(self.config.config["Categories"].keys())
            if categories:
                self.category_dropdown.configure(values=categories)
                self.category_dropdown.set(categories[0])

    def toggle_scheduler(self):
        """Toggle scheduler settings"""
        enabled = self.schedule_switch.get()
        self.frequency_dropdown.configure(state="normal" if enabled else "disabled")
        self.time_entry.configure(state="normal" if enabled else "disabled")

        if enabled and self.frequency_dropdown.get() == "Weekly":
            self.days_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=10)
        else:
            self.days_frame.grid_forget()

    def handle_frequency_change(self, frequency: str):
        """Handle schedule frequency change"""
        if frequency == "Weekly" and self.schedule_switch.get():
            self.days_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=10)
        else:
            self.days_frame.grid_forget()

    def start_sync(self):
        """Start sync operation"""
        # Get files to sync
        self.preview_sync()

        if not self.show_confirm("Start Sync", "Do you want to proceed with the sync?"):
            return

        self.sync_progress.set(0)
        self.sync_progress.start()

        # Prepare sync command
        cmd = ["claudesync", "push"]
        mode = self.sync_mode.get()

        if mode == "Uberproject":
            cmd.append("--uberproject")
        elif mode == "Category":
            cmd.extend(["--category", self.category_dropdown.get()])

        # Execute sync
        returncode, stdout, stderr = self.command_executor.execute(cmd)

        self.sync_progress.stop()

        if returncode == 0:
            self.sync_progress.set(1)
            self.status_bar.update_status(
                "Last Sync", datetime.now().strftime("%Y-%m-%d %H:%M")
            )
            self.show_info("Sync Complete", "Files synchronized successfully")
        else:
            self.sync_progress.set(0)
            self.show_error("Sync Failed", f"Failed to sync: {stderr}")

    def preview_sync(self):
        """Preview files to be synced"""
        cmd = ["claudesync", "project", "file", "ls"]
        returncode, stdout, stderr = self.command_executor.execute(cmd)

        if returncode == 0:
            self.preview_list.delete("0.0", "end")
            self.preview_list.insert("0.0", stdout)

    def create_chat(self):
        """Create new chat"""
        name_dialog = customtkinter.CTkInputDialog(
            text="Enter chat name:", title="Create Chat"
        )
        chat_name = name_dialog.get_input()

        if chat_name:
            returncode, stdout, stderr = self.command_executor.execute(
                ["claudesync", "chat", "init", "--name", chat_name]
            )

            if returncode == 0:
                self.refresh_chats()
            else:
                self.show_error(
                    "Chat Creation Failed", f"Failed to create chat: {stderr}"
                )

    def delete_chat(self):
        """Delete selected chat"""
        if self.show_confirm(
            "Delete Chat", "Are you sure you want to delete this chat?"
        ):
            returncode, stdout, stderr = self.command_executor.execute(
                ["claudesync", "chat", "rm"]
            )

            if returncode == 0:
                self.refresh_chats()
            else:
                self.show_error("Delete Failed", f"Failed to delete chat: {stderr}")

    def sync_chats(self):
        """Sync chats"""
        returncode, stdout, stderr = self.command_executor.execute(
            ["claudesync", "chat", "pull"]
        )

        if returncode == 0:
            self.refresh_chats()
        else:
            self.show_error("Sync Failed", f"Failed to sync chats: {stderr}")

    def refresh_chats(self):
        """Refresh chat list"""
        returncode, stdout, stderr = self.command_executor.execute(
            ["claudesync", "chat", "ls"]
        )

        if returncode == 0:
            self.chat_list.delete("0.0", "end")
            self.chat_list.insert("0.0", stdout)

    def send_message(self):
        """Send chat message"""
        message = self.message_entry.get()
        if message:
            returncode, stdout, stderr = self.command_executor.execute(
                ["claudesync", "chat", "message", message]
            )

            if returncode == 0:
                self.message_entry.delete(0, "end")
                self.refresh_chats()
            else:
                self.show_error("Send Failed", f"Failed to send message: {stderr}")

    def change_theme(self, theme: str):
        """Change application theme"""
        customtkinter.set_default_color_theme(theme)
        self.config.set("General", "theme", theme)
        self.config.save()

    def add_category(self):
        """Add new category"""
        name_dialog = customtkinter.CTkInputDialog(
            text="Enter category name:", title="Add Category"
        )
        name = name_dialog.get_input()

        if name:
            desc_dialog = customtkinter.CTkInputDialog(
                text="Enter category description:", title="Add Category"
            )
            desc = desc_dialog.get_input()

            if desc:
                pattern_dialog = customtkinter.CTkInputDialog(
                    text="Enter file patterns (comma-separated):", title="Add Category"
                )
                patterns = pattern_dialog.get_input()

                if patterns:
                    category_data = {
                        "description": desc,
                        "patterns": [p.strip() for p in patterns.split(",")],
                    }
                    self.config.set("Categories", name, json.dumps(category_data))
                    self.config.save()
                    self.refresh_categories()

    def remove_category(self):
        """Remove selected category"""
        if "Categories" in self.config.config:
            categories = list(self.config.config["Categories"].keys())
            if categories:
                dialog = customtkinter.CTkInputDialog(
                    text="Select category to remove:", title="Remove Category"
                )
                category = dialog.get_input()

                if category in categories:
                    if self.show_confirm(
                        "Remove Category",
                        f"Are you sure you want to remove category '{category}'?",
                    ):
                        self.config.config.remove_option("Categories", category)
                        self.config.save()
                        self.refresh_categories()

    def refresh_categories(self):
        """Refresh category list display"""
        if "Categories" in self.config.config:
            self.category_list.delete("0.0", "end")
            for name, data_str in self.config.config["Categories"].items():
                data = json.loads(data_str)
                self.category_list.insert("end", f"Name: {name}\n")
                self.category_list.insert(
                    "end", f"Description: {data['description']}\n"
                )
                self.category_list.insert(
                    "end", f"Patterns: {', '.join(data['patterns'])}\n\n"
                )

    def save_config(self):
        """Save configuration changes"""
        # Save sync settings
        self.config.set("Sync", "upload_delay", self.upload_delay_entry.get())
        self.config.set("Sync", "max_file_size", self.max_file_size_entry.get())
        self.config.set("Sync", "two_way_sync", self.two_way_sync_var.get())
        self.config.set("Sync", "prune_remote_files", self.prune_remote_var.get())

        # Save scheduler settings
        self.config.set("Schedule", "enabled", str(self.schedule_switch.get()))
        self.config.set("Schedule", "frequency", self.frequency_dropdown.get())
        self.config.set("Schedule", "time", self.time_entry.get())

        if self.frequency_dropdown.get() == "Weekly":
            selected_days = [
                day for day, var in self.day_vars.items() if var.get() == "1"
            ]
            self.config.set("Schedule", "days", ",".join(selected_days))

        self.config.save()
        self.show_info("Configuration", "Settings saved successfully")

    def change_log_level(self, level: str):
        """Change logging level"""
        self.logger.logger.setLevel(getattr(logging, level))
        self.config.set("General", "log_level", level)
        self.config.save()

    def search_logs(self):
        """Search logs for text"""
        search_text = self.search_entry.get()
        if search_text:
            self.log_display.delete("0.0", "end")
            for log in self.logger.log_queue:
                if search_text.lower() in log.lower():
                    self.log_display.insert("end", log + "\n")

    def clear_logs(self):
        """Clear log display"""
        if self.show_confirm("Clear Logs", "Are you sure you want to clear the logs?"):
            self.log_display.delete("0.0", "end")
            self.logger.log_queue.clear()

    def export_logs(self):
        """Export logs to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("All files", "*.*")],
        )
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.log_display.get("0.0", "end"))
                self.show_info("Export Complete", "Logs exported successfully")
            except Exception as e:
                self.show_error("Export Failed", f"Failed to export logs: {str(e)}")

    def show_error(self, title: str, message: str):
        """Show error dialog"""
        dialog = customtkinter.CTkInputDialog(text=message, title=title)

    def show_warning(self, title: str, message: str):
        """Show warning dialog"""
        dialog = customtkinter.CTkInputDialog(text=message, title=title)

    def show_info(self, title: str, message: str):
        """Show info dialog"""
        dialog = customtkinter.CTkInputDialog(text=message, title=title)

    def show_confirm(self, title: str, message: str) -> bool:
        """Show confirmation dialog"""
        dialog = ConfirmDialog(self, title, message)
        return dialog.result


if __name__ == "__main__":
    app = ClaudeSyncGUI()
    app.mainloop()
