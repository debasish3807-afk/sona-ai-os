"""Abstract port interfaces for the MCP Integration service.

Defines the contracts that infrastructure adapters must implement
to provide MCP server management, tool discovery, and tool execution capabilities.
"""

from abc import ABC, abstractmethod
from typing import Any

from domain.models import MCPServer, MCPTool, ToolCallResult


class MCPManagerPort(ABC):
    """Primary port for MCP server and tool management.

    Defines the contract for registering MCP servers, discovering tools,
    and executing tool calls with permission gating. All concrete implementations
    (e.g., stdio-based, SSE-based) must satisfy this interface.
    """

    @abstractmethod
    async def register_server(self, server: MCPServer) -> str:
        """Register a new MCP server for tool discovery and execution.

        Args:
            server: The MCP server configuration to register.

        Returns:
            The server_id of the registered server.
        """
        ...

    @abstractmethod
    async def discover_tools(self, server_id: str) -> list[MCPTool]:
        """Discover all tools available on a registered MCP server.

        Args:
            server_id: Identifier of the server to query for tools.

        Returns:
            A list of MCPTool instances discovered on the server.
        """
        ...

    @abstractmethod
    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any], user_id: str
    ) -> ToolCallResult:
        """Execute a tool call on the appropriate MCP server.

        Permission checks are performed before execution based on the
        tool's required permissions and the user's granted permissions.

        Args:
            tool_name: Name of the tool to invoke.
            arguments: Arguments to pass to the tool.
            user_id: Identifier of the user requesting the tool call.

        Returns:
            A ToolCallResult with the output or error information.
        """
        ...

    @abstractmethod
    async def list_servers(self) -> list[MCPServer]:
        """List all registered MCP servers.

        Returns:
            A list of all currently registered MCPServer instances.
        """
        ...

    @abstractmethod
    async def health_check(self, server_id: str) -> bool:
        """Check the health/connectivity of a registered MCP server.

        Args:
            server_id: Identifier of the server to check.

        Returns:
            True if the server is healthy and responsive, False otherwise.
        """
        ...
