"""
Terminal utilities — cross-platform functions for launching commands in a terminal.

Supports Windows, Linux, and macOS.
Terminal preference configurable via config["terminal"]["command"] (empty = auto-detect).
"""

import json
import logging
import platform
import shutil
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

_CONFIG_FILE = Path(__file__).parent.parent.parent / "config" / "config.json"


def _get_terminal_command() -> str:
    """Return user-configured terminal command, or empty string for auto-detect."""
    try:
        with open(_CONFIG_FILE) as f:
            cfg = json.load(f)
        return cfg.get("terminal", {}).get("command", "")
    except Exception:
        return ""


def _build_launch_args(command: str, title: str, cwd: str = None) -> list:
    """Build OS-specific argv list to run *command* in a new terminal window.

    Returns None if no usable terminal is found.
    """
    user_cmd = _get_terminal_command()
    system = platform.system()

    # ── User override ──────────────────────────────────────────────────────
    if user_cmd:
        # User provides full launch template, e.g. "xterm -e"
        return user_cmd.split() + [command]

    # ── Windows ────────────────────────────────────────────────────────────
    if system == "Windows":
        if shutil.which("wt"):
            args = ["wt", "-w", "0", "new-tab"]
            if title:
                args += ["--title", title]
            if cwd:
                args += ["-d", cwd]
            if shutil.which("pwsh"):
                args += ["pwsh", "-NoExit", "-Command", command]
            else:
                args += ["cmd", "/k", command]
            return args
        # Fallback: cmd in a new window
        return ["cmd", "/c", "start", "cmd", "/k", command]

    # ── macOS ──────────────────────────────────────────────────────────────
    if system == "Darwin":
        # Use osascript to open Terminal.app
        osa_cmd = f'tell application "Terminal" to do script "{command.replace(chr(34), chr(92)+chr(34))}"'
        return ["osascript", "-e", osa_cmd]

    # ── Linux ──────────────────────────────────────────────────────────────
    candidates = [
        ("gnome-terminal", ["gnome-terminal", "--title", title or "Terminal", "--", "bash", "-c",
                            f"{command}; exec bash"]),
        ("xterm",          ["xterm", "-title", title or "Terminal", "-e",
                            f"bash -c '{command}; exec bash'"]),
        ("konsole",        ["konsole", "--new-tab", "--title", title or "Terminal", "-e",
                            f"bash -c '{command}; exec bash'"]),
        ("kitty",          ["kitty", "--title", title or "Terminal",
                            "bash", "-c", f"{command}; exec bash"]),
        ("alacritty",      ["alacritty", "--title", title or "Terminal", "-e",
                            "bash", "-c", f"{command}; exec bash"]),
        ("xfce4-terminal", ["xfce4-terminal", "--title", title or "Terminal", "-e",
                            f"bash -c '{command}; exec bash'"]),
    ]
    for binary, args in candidates:
        if shutil.which(binary):
            return args

    return None


def run_in_terminal(
    command: str,
    title: str = "Command",
    parent_widget=None,
    show_error: bool = True,
    cwd: str = None,
) -> bool:
    """Run *command* in a new terminal window.

    Args:
        command:       Shell command to execute (e.g. 'claude plugin').
        title:         Window / tab title.
        parent_widget: Parent for error dialogs (optional).
        show_error:    Whether to show a QMessageBox on failure.
        cwd:           Working directory (optional).

    Returns:
        True if the terminal was launched successfully, False otherwise.
    """
    args = _build_launch_args(command, title, cwd)
    if not args:
        msg = "No usable terminal emulator found. Install xterm, gnome-terminal, or kitty."
        logger.error(msg)
        if show_error and parent_widget:
            QMessageBox.critical(parent_widget, "Terminal Error", msg)
        return False

    try:
        kwargs = {}
        if cwd:
            kwargs["cwd"] = cwd
        subprocess.Popen(args, **kwargs)
        logger.debug(f"Launched terminal: {args[0]!r} — {command!r}")
        return True
    except Exception as e:
        logger.error(f"Failed to launch terminal: {e}")
        if show_error and parent_widget:
            QMessageBox.critical(parent_widget, "Terminal Error", f"Failed to launch terminal:\n{e}")
        return False


def run_command_silent(
    command,
    timeout: int = 30,
    shell: bool = False,
) -> tuple[bool, str, str]:
    """Run *command* silently and capture output.

    Args:
        command: List or string command.
        timeout: Timeout in seconds.
        shell:   Use shell=True (default False).

    Returns:
        (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=shell,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return False, "", str(e)
