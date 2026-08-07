"""Tool registry for MCP Integration.

Stores all discovered tools, supports registration, unregistration,
search by name/server/capability, and version tracking.
"""

import fnmatch
from typing import Any

import structlog

from sona_mcp.domain.events import ToolRegisteredEvent
from sona_mcp.domain.models import MCPTool, ToolPermission

logger = structlog.get_logger()


class ToolRegistry:
    """Central registry for all MCP tools.

    Provides registration, lookup, search, and version tracking
    for tools discovered across all connected MCP servers.
    """

    def __init__(self) -> None:
        """Initialize an empty tool registry."""
        self._tools: dict[str, MCPTool] = {}
        self._versions: dict[str, int] = {}
        self._events: list[ToolRegisteredEvent] = []

    @property
    def events(self) -> list[ToolRegisteredEvent]:
        """Return collected domain events and clear the buffer."""
        events = list(self._events)
        self._events.clear()
        return events

    async def register(self, tool: MCPTool) -> None:
        """Register a tool in the registry.

        If a tool with the same name already exists, it is replaced
        and the version counter is incremented.

        Args:
            tool: The MCPTool to register.
        """
        if tool.name in self._tools:
            self._versions[tool.name] = self._versions.get(tool.name, 1) + 1
        else:
            self._versions[tool.name] = 1

        self._tools[tool.name] = tool
        self._events.append(ToolRegisteredEvent(tool_name=tool.name, server_id=tool.server_id))
        await logger.ainfo(
            "tool_registered",
            tool_name=tool.name,
            server_id=tool.server_id,
            version=self._versions[tool.name],
        )

    async def unregister(self, tool_name: str) -> bool:
        """Remove a tool from the registry.

        Args:
            tool_name: Name of the tool to remove.

        Returns:
            True if the tool was removed, False if not found.
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            del self._versions[tool_name]
            await logger.ainfo("tool_unregistered", tool_name=tool_name)
            return True
        return False

    async def get(self, tool_name: str) -> MCPTool | None:
        """Get a tool by its name.

        Args:
            tool_name: Name of the tool to retrieve.

        Returns:
            The MCPTool if found, None otherwise.
        """
        return self._tools.get(tool_name)

    async def list_all(self) -> list[MCPTool]:
        """List all registered tools.

        Returns:
            A list of all tools in the registry.
        """
        return list(self._tools.values())

    async def list_by_server(self, server_id: str) -> list[MCPTool]:
        """List all tools belonging to a specific server.

        Args:
            server_id: The server identifier to filter by.

        Returns:
            A list of tools from the specified server.
        """
        return [t for t in self._tools.values() if t.server_id == server_id]

    async def search_by_capability(self, permission: ToolPermission) -> list[MCPTool]:
        """Search for tools that require a specific permission.

        Args:
            permission: The permission to filter by.

        Returns:
            A list of tools requiring the given permission.
        """
        return [t for t in self._tools.values() if permission in t.permissions]

    async def search_by_pattern(self, pattern: str) -> list[MCPTool]:
        """Search for tools matching a glob pattern.

        Args:
            pattern: A glob pattern to match against tool names.

        Returns:
            A list of tools whose names match the pattern.
        """
        return [t for t in self._tools.values() if fnmatch.fnmatch(t.name, pattern)]

    async def search_by_description(self, keyword: str) -> list[MCPTool]:
        """Search for tools whose description contains a keyword.

        Args:
            keyword: A keyword to search for in descriptions.

        Returns:
            A list of tools with matching descriptions.
        """
        keyword_lower = keyword.lower()
        return [t for t in self._tools.values() if keyword_lower in t.description.lower()]

    def get_version(self, tool_name: str) -> int:
        """Get the current version number of a tool.

        Args:
            tool_name: Name of the tool.

        Returns:
            The version number, or 0 if not registered.
        """
        return self._versions.get(tool_name, 0)

    def get_tool_schema(self, tool_name: str) -> dict[str, Any] | None:
        """Get the input schema for a tool.

        Args:
            tool_name: Name of the tool.

        Returns:
            The input schema dict, or None if not found.
        """
        tool = self._tools.get(tool_name)
        return tool.input_schema if tool else None

    @property
    def count(self) -> int:
        """Return the total number of registered tools."""
        return len(self._tools)
