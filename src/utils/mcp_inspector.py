"""
MCP Inspector utility for connecting to and querying MCP servers.

Adapted from an earlier mcp_client.py implementation.
"""

import asyncio
import os
from typing import Optional, List, Dict, Any
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPInspector:
    """MCP client for inspecting server capabilities and tools."""

    def __init__(self):
        """Initialize the MCP Inspector."""
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.server_name: Optional[str] = None

    async def connect_to_server(self, server_config: Dict[str, Any], server_name: str) -> None:
        """Connect to an MCP server using the provided configuration.

        Args:
            server_config: Dictionary containing 'command', 'args', and 'env'
            server_name: Name of the server for reference

        Raises:
            ValueError: If server config is invalid
            ConnectionError: If connection to server fails
        """
        self.server_name = server_name

        # Extract configuration
        command = server_config.get('command')
        args = server_config.get('args', [])
        env = server_config.get('env', {})

        if not command:
            raise ValueError("Server configuration must include 'command'")

        # Prepare environment variables (merge with current environment)
        server_env = os.environ.copy()
        if env:
            server_env.update(env)

        # Create server parameters
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=server_env
        )

        try:
            # Establish connection using stdio transport
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )

            read_stream, write_stream = stdio_transport

            # Create and initialize session
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            await self.session.initialize()

        except Exception as e:
            raise ConnectionError(f"Failed to connect to server '{server_name}': {e}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get list of all available tools from the connected server.

        Returns:
            List of tool dictionaries with name, description, and inputSchema

        Raises:
            RuntimeError: If not connected to a server
        """
        if not self.session:
            raise RuntimeError("Not connected to any server. Call connect_to_server first.")

        try:
            response = await self.session.list_tools()

            # Convert tools to dictionaries for easier handling
            tools = []
            for tool in response.tools:
                tool_dict = {
                    'name': tool.name,
                    'description': tool.description if hasattr(tool, 'description') else '',
                    'inputSchema': tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                }
                tools.append(tool_dict)

            return tools

        except Exception as e:
            raise RuntimeError(f"Failed to list tools: {e}")

    async def get_server_info(self) -> Dict[str, Any]:
        """Get server information.

        Returns:
            Dictionary with server information

        Raises:
            RuntimeError: If not connected to a server
        """
        if not self.session:
            raise RuntimeError("Not connected to any server")

        # Return basic info about the session
        return {
            'server_name': self.server_name,
            'connected': self.session is not None
        }

    async def disconnect(self) -> None:
        """Disconnect from the server and cleanup resources."""
        try:
            await self.exit_stack.aclose()
        except Exception as e:
            print(f"Warning: Error during disconnect: {e}")
        finally:
            self.session = None
            self.server_name = None

    async def __aenter__(self):
        """Support async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup when exiting async context."""
        await self.disconnect()


async def inspect_server(server_config: Dict[str, Any], server_name: str) -> List[Dict[str, Any]]:
    """Convenience function to inspect a server and get its tools.

    Args:
        server_config: Server configuration dictionary
        server_name: Name of the server

    Returns:
        List of tools from the server
    """
    async with MCPInspector() as inspector:
        await inspector.connect_to_server(server_config, server_name)
        tools = await inspector.list_tools()
        return tools
