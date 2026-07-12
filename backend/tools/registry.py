"""Tool Registry — registers, discovers, and retrieves tools.

Maintains a catalog of all available tools with their metadata,
enabling the AI to discover and select appropriate tools.
"""

from __future__ import annotations

from typing import Any

from config.logging import get_logger
from tools.base import BaseTool, ToolCategory, ToolMetadata

logger = get_logger(__name__)


class ToolRegistry:
    """Central registry for all available tools.

    Supports:
        - Registration of tool instances
        - Lookup by name or category
        - Metadata discovery for AI tool selection
        - Tool listing for API endpoints
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    @property
    def tool_count(self) -> int:
        """Number of registered tools."""
        return len(self._tools)

    def register(self, tool: BaseTool) -> None:
        """Register a tool in the registry.

        Args:
            tool: The tool instance to register.
        """
        name = tool.metadata.name
        if name in self._tools:
            logger.warning("Tool already registered, overwriting", tool=name)
        self._tools[name] = tool
        logger.debug("Tool registered", tool=name, category=tool.category.value)

    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name.

        Args:
            name: The tool's registered name.

        Returns:
            The tool instance or None if not found.
        """
        return self._tools.get(name)

    def list_all(self) -> list[BaseTool]:
        """List all registered tools."""
        return list(self._tools.values())

    def list_by_category(self, category: ToolCategory) -> list[BaseTool]:
        """List tools filtered by category.

        Args:
            category: The category to filter by.

        Returns:
            List of tools in the specified category.
        """
        return [t for t in self._tools.values() if t.category == category]

    def get_metadata(self) -> list[ToolMetadata]:
        """Get metadata for all registered tools (for AI discovery)."""
        return [t.metadata for t in self._tools.values()]

    def get_names(self) -> list[str]:
        """Get all registered tool names."""
        return list(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def to_schema(self) -> list[dict[str, Any]]:
        """Export registry as JSON-serializable schema for API/MCP."""
        result: list[dict[str, Any]] = []
        for tool in self._tools.values():
            meta = tool.metadata
            result.append(
                {
                    "name": meta.name,
                    "description": meta.description,
                    "category": meta.category.value,
                    "dangerous": meta.dangerous,
                    "read_only": meta.read_only,
                    "parameters": [
                        {
                            "name": p.name,
                            "type": p.param_type,
                            "description": p.description,
                            "required": p.required,
                            "default": p.default,
                        }
                        for p in meta.parameters
                    ],
                }
            )
        return result
