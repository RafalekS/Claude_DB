"""
MCP Configuration Validator for Windows
Validates .mcp.json files and auto-fixes Windows compatibility issues
"""

import json
import platform
from pathlib import Path
from typing import Dict, List, Tuple, Any


class MCPValidator:
    """Validates and fixes MCP server configurations for Windows"""

    # Commands that need cmd /c wrapper on Windows
    WINDOWS_WRAPPER_COMMANDS = {
        'npx', 'npm', 'node', 'uvx', 'uv', 'bunx', 'bun',
        'pnpm', 'yarn', 'python', 'python3', 'pip', 'pipx'
    }

    def __init__(self):
        self.is_windows = platform.system() == 'Windows'
        self.errors = []
        self.warnings = []
        self.fixes = []

    def validate_mcp_json(self, mcp_path: Path) -> Tuple[bool, List[str], List[str]]:
        """
        Validate .mcp.json file

        Returns:
            (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        if not mcp_path.exists():
            self.errors.append(f"File not found: {mcp_path}")
            return False, self.errors, self.warnings

        try:
            with open(mcp_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {e}")
            return False, self.errors, self.warnings

        # Check structure
        if 'mcpServers' not in config:
            self.errors.append("Missing 'mcpServers' key in root")
            return False, self.errors, self.warnings

        servers = config['mcpServers']
        if not isinstance(servers, dict):
            self.errors.append("'mcpServers' must be an object/dict")
            return False, self.errors, self.warnings

        # Validate each server
        for server_name, server_config in servers.items():
            self._validate_server(server_name, server_config)

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def _validate_server(self, name: str, config: Dict[str, Any]):
        """Validate individual server configuration"""
        # Check required fields
        if 'command' not in config:
            self.errors.append(f"Server '{name}': Missing 'command' field")
            return

        command = config['command']

        # Windows-specific validation
        if self.is_windows:
            if command in self.WINDOWS_WRAPPER_COMMANDS:
                if 'args' in config:
                    args = config['args']
                    if isinstance(args, list) and len(args) > 0:
                        # Check if first arg is '/c'
                        if args[0] != '/c':
                            self.warnings.append(
                                f"Server '{name}': Command '{command}' may not work on Windows. "
                                f"Consider using 'cmd' with '/c' wrapper."
                            )
                else:
                    self.warnings.append(
                        f"Server '{name}': Command '{command}' may not work on Windows. "
                        f"Consider using 'cmd' with '/c' wrapper."
                    )

    def auto_fix_windows(self, mcp_path: Path) -> Tuple[bool, str, List[str]]:
        """
        Auto-fix .mcp.json for Windows compatibility

        Returns:
            (success, fixed_json_string, fixes_applied)
        """
        self.fixes = []

        if not mcp_path.exists():
            return False, "", ["File not found"]

        try:
            with open(mcp_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            return False, "", [f"Invalid JSON: {e}"]

        if 'mcpServers' not in config:
            return False, "", ["Missing 'mcpServers' key"]

        servers = config['mcpServers']

        # Fix each server
        for server_name, server_config in servers.items():
            if self._fix_server(server_name, server_config):
                servers[server_name] = server_config

        # Return formatted JSON
        fixed_json = json.dumps(config, indent=2)
        return True, fixed_json, self.fixes

    def _fix_server(self, name: str, config: Dict[str, Any]) -> bool:
        """
        Fix individual server configuration for Windows

        Returns:
            True if fixes were applied
        """
        if not self.is_windows:
            return False

        if 'command' not in config:
            return False

        command = config['command']

        # Check if command needs cmd /c wrapper
        if command in self.WINDOWS_WRAPPER_COMMANDS:
            # Get existing args
            args = config.get('args', [])
            if not isinstance(args, list):
                args = []

            # Check if already wrapped
            if args and args[0] == '/c':
                return False  # Already fixed

            # Apply fix: wrap with cmd /c
            new_args = ['/c', command] + args
            config['command'] = 'cmd'
            config['args'] = new_args

            self.fixes.append(
                f"Server '{name}': Wrapped '{command}' with 'cmd /c'"
            )
            return True

        return False

    def get_validation_report(self, mcp_path: Path) -> str:
        """
        Generate human-readable validation report

        Returns:
            Formatted report string
        """
        is_valid, errors, warnings = self.validate_mcp_json(mcp_path)

        report = []
        report.append(f"MCP Configuration Validation Report")
        report.append(f"File: {mcp_path}")
        report.append(f"Platform: {platform.system()}")
        report.append("")

        if is_valid and not warnings:
            report.append("✅ Configuration is valid and Windows-compatible!")
        else:
            if errors:
                report.append(f"❌ Errors ({len(errors)}):")
                for error in errors:
                    report.append(f"  • {error}")
                report.append("")

            if warnings:
                report.append(f"⚠️  Warnings ({len(warnings)}):")
                for warning in warnings:
                    report.append(f"  • {warning}")
                report.append("")

        return "\n".join(report)

    def create_windows_template(self, server_type: str = 'npx') -> str:
        """
        Create Windows-compatible MCP server template

        Args:
            server_type: Type of server (npx, uvx, bunx)

        Returns:
            JSON template string
        """
        templates = {
            'npx': {
                "mcpServers": {
                    "example-server": {
                        "command": "cmd",
                        "args": [
                            "/c",
                            "npx",
                            "example-mcp-server@latest"
                        ],
                        "type": "stdio"
                    }
                }
            },
            'uvx': {
                "mcpServers": {
                    "example-server": {
                        "command": "cmd",
                        "args": [
                            "/c",
                            "uvx",
                            "example-mcp-server"
                        ],
                        "env": {
                            "EXAMPLE_VAR": "true"
                        }
                    }
                }
            },
            'bunx': {
                "mcpServers": {
                    "example-server": {
                        "command": "cmd",
                        "args": [
                            "/c",
                            "bunx",
                            "-y",
                            "@example/mcp-server"
                        ]
                    }
                }
            },
            'multi': {
                "mcpServers": {
                    "npx-server": {
                        "command": "cmd",
                        "args": [
                            "/c",
                            "npx",
                            "example-npx@latest",
                            "start"
                        ],
                        "type": "stdio"
                    },
                    "uvx-server": {
                        "command": "cmd",
                        "args": [
                            "/c",
                            "uvx",
                            "example-uvx-server"
                        ],
                        "env": {
                            "SERVER_ENABLED": "true"
                        }
                    },
                    "bunx-server": {
                        "command": "cmd",
                        "args": [
                            "/c",
                            "bunx",
                            "-y",
                            "@example/bunx-server"
                        ]
                    }
                }
            }
        }

        template = templates.get(server_type, templates['npx'])
        return json.dumps(template, indent=2)


# Convenience functions
def validate_mcp_file(mcp_path: Path) -> Tuple[bool, List[str], List[str]]:
    """Quick validation of MCP file"""
    validator = MCPValidator()
    return validator.validate_mcp_json(mcp_path)


def auto_fix_mcp_file(mcp_path: Path) -> Tuple[bool, str, List[str]]:
    """Quick auto-fix of MCP file"""
    validator = MCPValidator()
    return validator.auto_fix_windows(mcp_path)


def get_validation_report(mcp_path: Path) -> str:
    """Quick validation report"""
    validator = MCPValidator()
    return validator.get_validation_report(mcp_path)
