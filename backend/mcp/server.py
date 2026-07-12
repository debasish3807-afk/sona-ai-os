"""MCP Server — coordinates tool discovery, validation, and execution.

The MCPServer is the central entry point for the tool system. It:
    - Registers all tools at startup
    - Provides tool discovery (metadata listing)
    - Validates and executes tool calls
    - Manages sessions
    - Integrates with the AI Brain
"""

from __future__ import annotations

from typing import Any

from config.logging import get_logger
from mcp.session import MCPSessionManager
from tools.base import BaseTool, ToolResult
from tools.browser_tool import register_browser_tools
from tools.database_tool import register_database_tools
from tools.executor import ToolExecutor
from tools.filesystem_tool import register_filesystem_tools
from tools.git_tool import register_git_tools
from tools.github_tool import register_github_tools
from tools.permissions import ToolPermissions
from tools.python_tool import register_python_tools
from tools.registry import ToolRegistry
from tools.terminal_tool import register_terminal_tools

logger = get_logger(__name__)


class MCPServer:
    """MCP-compatible tool server.

    Manages the complete lifecycle of the tool system including
    registration, discovery, permission enforcement, execution,
    and session tracking.
    """

    def __init__(self, permissions: ToolPermissions | None = None) -> None:
        self._permissions = permissions or ToolPermissions()
        self._registry = ToolRegistry()
        self._executor = ToolExecutor(self._registry, self._permissions)
        self._sessions = MCPSessionManager()
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def registry(self) -> ToolRegistry:
        return self._registry

    @property
    def executor(self) -> ToolExecutor:
        return self._executor

    @property
    def sessions(self) -> MCPSessionManager:
        return self._sessions

    @property
    def permissions(self) -> ToolPermissions:
        return self._permissions

    def initialize(self) -> None:
        """Register all tools and initialize the server."""
        if self._initialized:
            return

        # Register all tool categories
        all_tools: list[BaseTool] = []
        all_tools.extend(register_filesystem_tools(self._permissions))
        all_tools.extend(register_terminal_tools(self._permissions))
        all_tools.extend(register_git_tools(self._permissions))
        all_tools.extend(register_github_tools())
        all_tools.extend(register_browser_tools(self._permissions))
        all_tools.extend(register_python_tools(self._permissions))
        all_tools.extend(register_database_tools(self._permissions))

        for tool in all_tools:
            self._registry.register(tool)

        self._initialized = True
        logger.info(
            "MCP server initialized",
            tools_registered=self._registry.tool_count,
            categories=len({t.category for t in all_tools}),
        )

    async def execute_tool(
        self,
        tool_name: str,
        params: dict[str, Any],
        session_id: str | None = None,
    ) -> ToolResult:
        """Execute a tool with session tracking.

        Args:
            tool_name: Name of the tool to execute.
            params: Tool parameters.
            session_id: Optional session for tracking.

        Returns:
            ToolResult from execution.
        """
        session = self._sessions.get_or_create(session_id)

        result = await self._executor.run(tool_name, **params)

        # Track in session
        session.record_execution(tool_name, result.success, result.duration_ms)

        return result

    def discover_tools(self) -> list[dict[str, Any]]:
        """Return tool metadata for AI discovery (MCP tools/list)."""
        return self._registry.to_schema()

    def get_tool_names(self) -> list[str]:
        """Get all registered tool names."""
        return self._registry.get_names()

    def get_status(self) -> dict[str, Any]:
        """Get MCP server status."""
        return {
            "initialized": self._initialized,
            "tools_registered": self._registry.tool_count,
            "active_sessions": self._sessions.active_count,
            "total_executions": self._executor.execution_count,
            "safe_mode": self._permissions.safe_mode,
            "workspace": self._permissions.workspace_root,
        }


# Global singleton
_mcp_server: MCPServer | None = None


def get_mcp_server() -> MCPServer:
    """Get the global MCP server instance."""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPServer()
        _mcp_server.initialize()
    return _mcp_server


def initialize_mcp_server(permissions: ToolPermissions | None = None) -> MCPServer:
    """Initialize the global MCP server with custom permissions."""
    global _mcp_server
    _mcp_server = MCPServer(permissions)
    _mcp_server.initialize()
    return _mcp_server
