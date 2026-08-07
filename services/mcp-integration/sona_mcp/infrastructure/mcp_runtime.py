"""MCP Runtime — top-level orchestrator for MCP Integration.

Implements the MCPManagerPort interface by composing all infrastructure
components: tool registry, discovery, invocation, security, sessions,
connections, circuit breakers, and metrics.
"""

from typing import Any

import structlog

from sona_mcp.application.ports import MCPManagerPort
from sona_mcp.domain.models import MCPServer, MCPTool, ToolCallResult
from sona_mcp.infrastructure.circuit_breaker import CircuitBreakerRegistry
from sona_mcp.infrastructure.connection_manager import ConnectionManager
from sona_mcp.infrastructure.metrics import MCPMetrics
from sona_mcp.infrastructure.prompt_manager import PromptManager
from sona_mcp.infrastructure.resource_manager import ResourceManager
from sona_mcp.infrastructure.security_manager import SecurityManager
from sona_mcp.infrastructure.session_manager import SessionManager
from sona_mcp.infrastructure.tool_discovery import ToolDiscovery
from sona_mcp.infrastructure.tool_invocation import ToolInvocationEngine
from sona_mcp.infrastructure.tool_registry import ToolRegistry

logger = structlog.get_logger()


class MCPRuntime(MCPManagerPort):
    """Full MCP runtime implementing the MCPManagerPort interface.

    Orchestrates all components for complete MCP server management,
    tool discovery, secure invocation, and monitoring.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        discovery: ToolDiscovery,
        invocation: ToolInvocationEngine,
        security_manager: SecurityManager,
        session_manager: SessionManager,
        connection_manager: ConnectionManager,
        circuit_breakers: CircuitBreakerRegistry,
        metrics: MCPMetrics,
        resource_manager: ResourceManager,
        prompt_manager: PromptManager,
    ) -> None:
        """Initialize the MCP runtime with all components.

        Args:
            registry: Tool registry for storing discovered tools.
            discovery: Tool discovery engine.
            invocation: Tool invocation engine.
            security_manager: Security policy manager.
            session_manager: Session lifecycle manager.
            connection_manager: Server connection manager.
            circuit_breakers: Per-tool circuit breaker registry.
            metrics: Metrics collector.
            resource_manager: MCP resource manager.
            prompt_manager: MCP prompt manager.
        """
        self._registry = registry
        self._discovery = discovery
        self._invocation = invocation
        self._security_manager = security_manager
        self._session_manager = session_manager
        self._connection_manager = connection_manager
        self._circuit_breakers = circuit_breakers
        self._metrics = metrics
        self._resource_manager = resource_manager
        self._prompt_manager = prompt_manager
        self._servers: dict[str, MCPServer] = {}

    @property
    def registry(self) -> ToolRegistry:
        """Access the tool registry."""
        return self._registry

    @property
    def security_manager(self) -> SecurityManager:
        """Access the security manager."""
        return self._security_manager

    @property
    def session_manager(self) -> SessionManager:
        """Access the session manager."""
        return self._session_manager

    @property
    def connection_manager(self) -> ConnectionManager:
        """Access the connection manager."""
        return self._connection_manager

    @property
    def circuit_breakers(self) -> CircuitBreakerRegistry:
        """Access the circuit breaker registry."""
        return self._circuit_breakers

    @property
    def metrics(self) -> MCPMetrics:
        """Access the metrics collector."""
        return self._metrics

    @property
    def resource_manager(self) -> ResourceManager:
        """Access the resource manager."""
        return self._resource_manager

    @property
    def prompt_manager(self) -> PromptManager:
        """Access the prompt manager."""
        return self._prompt_manager

    async def register_server(self, server: MCPServer) -> str:
        """Register a new MCP server and discover its tools.

        Args:
            server: The MCP server configuration to register.

        Returns:
            The server_id of the registered server.
        """
        self._servers[server.server_id] = server

        # Connect to the server
        await self._connection_manager.connect(server)

        # Discover tools
        await self._discovery.discover_from_server(server)

        # Register tool handlers if provided
        await logger.ainfo(
            "server_registered",
            server_id=server.server_id,
            name=server.name,
            tools_count=len(server.tools),
        )
        return server.server_id

    async def discover_tools(self, server_id: str) -> list[MCPTool]:
        """Discover all tools available on a registered MCP server.

        Args:
            server_id: Identifier of the server to query for tools.

        Returns:
            A list of MCPTool instances discovered on the server.
        """
        server = self._servers.get(server_id)
        if server is None:
            return []

        tools = await self._discovery.rediscover(server)
        await logger.ainfo(
            "tools_rediscovered",
            server_id=server_id,
            count=len(tools),
        )
        return tools

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any], user_id: str
    ) -> ToolCallResult:
        """Execute a tool call with full validation and protection.

        Checks circuit breaker, performs security validation, invokes
        the tool, and records metrics.

        Args:
            tool_name: Name of the tool to invoke.
            arguments: Arguments to pass to the tool.
            user_id: Identifier of the user requesting the tool call.

        Returns:
            A ToolCallResult with the output or error information.
        """
        # Check circuit breaker
        if not self._circuit_breakers.can_execute(tool_name):
            self._metrics.record_invocation(tool_name, False, 0.0)
            return ToolCallResult(
                tool_name=tool_name,
                output=None,
                success=False,
                error=f"Circuit breaker is open for tool '{tool_name}'",
            )

        # Invoke through the invocation engine
        result = await self._invocation.invoke(
            tool_name=tool_name,
            arguments=arguments,
            user_id=user_id,
        )

        # Update circuit breaker
        if result.success:
            self._circuit_breakers.record_success(tool_name)
        else:
            self._circuit_breakers.record_failure(tool_name)

        # Record server metrics
        tool = await self._registry.get(tool_name)
        if tool is not None:
            self._metrics.record_server_call(tool.server_id, result.success)

        return result

    async def list_servers(self) -> list[MCPServer]:
        """List all registered MCP servers.

        Returns:
            A list of all currently registered MCPServer instances.
        """
        return list(self._servers.values())

    async def health_check(self, server_id: str) -> bool:
        """Check the health/connectivity of a registered MCP server.

        Args:
            server_id: Identifier of the server to check.

        Returns:
            True if the server is healthy and responsive.
        """
        return await self._connection_manager.health_check(server_id)
