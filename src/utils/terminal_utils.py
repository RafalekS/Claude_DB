"""
Terminal utilities - Reusable functions for launching commands in terminal
"""

import subprocess
from PyQt6.QtWidgets import QMessageBox


def run_in_terminal(command, title="Command", parent_widget=None, show_error=True, cwd=None):
    """
    Run a command in Windows Terminal with PowerShell 7

    Args:
        command: Command string to execute (e.g., 'claude plugin', 'npm install', 'git status')
        title: Window title for the terminal tab
        parent_widget: Parent widget for error dialogs (optional)
        show_error: Whether to show error dialog on failure (default: True)
        cwd: Working directory for the command (optional)

    Returns:
        True if successful, False if failed

    Example:
        run_in_terminal('claude plugin', 'Browse Plugins')
        run_in_terminal('npm install @anthropic-ai/claude-agent-sdk', 'Install SDK')
        run_in_terminal('claude /status', 'Project Status', cwd='C:\\Projects\\MyApp')
    """
    try:
        # Build command list
        cmd_list = [
            'wt.exe',
            '-w', '0',
            'new-tab',
            '--title', title
        ]

        # Add starting directory if provided
        if cwd:
            cmd_list.extend(['-d', cwd])

        # Add PowerShell command
        cmd_list.extend([
            'pwsh.exe',
            '-NoExit',
            '-Command', command
        ])

        # Use Windows Terminal with pwsh (PowerShell 7)
        # Use list form to avoid shell escaping issues
        subprocess.Popen(cmd_list)
        return True

    except Exception as e:
        if show_error and parent_widget:
            QMessageBox.critical(
                parent_widget,
                "Terminal Error",
                f"Failed to launch terminal:\n{str(e)}"
            )
        return False


def run_command_silent(command, timeout=30, shell=False):
    """
    Run a command silently and capture output

    Args:
        command: Command to run (list or string)
        timeout: Timeout in seconds (default: 30)
        shell: Whether to use shell=True (default: False)

    Returns:
        tuple: (success: bool, stdout: str, stderr: str)

    Example:
        success, out, err = run_command_silent(['claude.cmd', 'plugin', 'list'])
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
            shell=shell
        )

        return (result.returncode == 0, result.stdout, result.stderr)

    except subprocess.TimeoutExpired:
        return (False, "", f"Command timed out after {timeout} seconds")
    except Exception as e:
        return (False, "", str(e))
