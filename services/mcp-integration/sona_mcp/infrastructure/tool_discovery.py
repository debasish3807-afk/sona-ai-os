"""Tool discovery for MCP Integration.

Auto-discovers tools from registered MCP servers by querying their
tools/list endpoints. Servers declare their tools on registration.
"""

import structlog

from sona_mcp.domain.models import MCPServer, MCPTool
from sona_mcp.infrastructure.tool_registry import ToolRegistry

logger = structlog.get_logger()


class ToolDiscovery:
    """Discovers and registers tools from MCP servers.

    Queries each server's declared tools and registers them in the
    central tool registry. Supports re-discovery on reconnection.
    """

    def __init__(self, registry: ToolRegistry) -> None:
        """Initialize tool discovery with a registry.

        Args:
            registry: The ToolRegistry to register discovered tools into.
        """
        self._registry = registry
        self._discovered_servers: set[str] = set()

    async def discover_from_server(self, server: MCPServer) -> list[MCPTool]:
        """Discover and register all tools from an MCP server.

        Servers declare their tools in their MCPServer.tools list.
        Each tool is registered in the tool registry.

        Args:
            server: The MCP server to discover tools from.

        Returns:
            A list of discovered MCPTool instances.
        """
        tools = server.tools
        for tool in tools:
            await self._registry.register(tool)

        self._discovered_servers.add(server.server_id)
        await logger.ainfo(
            "tools_discovered",
            server_id=server.server_id,
            tools_count=len(tools),
            tool_names=[t.name for t in tools],
        )
        return tools

    async def rediscover(self, server: MCPServer) -> list[MCPTool]:
        """Re-discover tools from a server, replacing existing entries.

        Removes previously registered tools for this server and
        performs fresh discovery.

        Args:
            server: The MCP server to re-discover tools from.

        Returns:
            A list of newly discovered MCPTool instances.
        """
        # Remove old tools from this server
        existing = await self._registry.list_by_server(server.server_id)
        for tool in existing:
            await self._registry.unregister(tool.name)

        # Discover fresh
        return await self.discover_from_server(server)

    async def remove_server_tools(self, server_id: str) -> int:
        """Remove all tools associated with a server.

        Args:
            server_id: The server identifier whose tools should be removed.

        Returns:
            The number of tools removed.
        """
        tools = await self._registry.list_by_server(server_id)
        for tool in tools:
            await self._registry.unregister(tool.name)
        self._discovered_servers.discard(server_id)
        await logger.ainfo("server_tools_removed", server_id=server_id, removed_count=len(tools))
        return len(tools)

    def is_discovered(self, server_id: str) -> bool:
        """Check if a server has been discovered.

        Args:
            server_id: The server identifier to check.

        Returns:
            True if tools have been discovered from this server.
        """
        return server_id in self._discovered_servers

    @property
    def discovered_server_count(self) -> int:
        """Return the number of servers that have been discovered."""
        return len(self._discovered_servers)
