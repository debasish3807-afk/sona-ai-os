"""Dependency injection factory for MCP Integration.

Creates a fully-wired MCPRuntime instance with all components
configured and built-in tools registered.
"""

from sona_mcp.infrastructure.builtin_tools import (
    BUILTIN_HANDLERS,
    BUILTIN_SERVER,
)
from sona_mcp.infrastructure.circuit_breaker import CircuitBreakerRegistry
from sona_mcp.infrastructure.connection_manager import ConnectionManager
from sona_mcp.infrastructure.mcp_runtime import MCPRuntime
from sona_mcp.infrastructure.metrics import MCPMetrics
from sona_mcp.infrastructure.prompt_manager import PromptManager
from sona_mcp.infrastructure.resource_manager import ResourceManager
from sona_mcp.infrastructure.security_manager import SecurityManager
from sona_mcp.infrastructure.session_manager import SessionManager
from sona_mcp.infrastructure.tool_discovery import ToolDiscovery
from sona_mcp.infrastructure.tool_invocation import ToolInvocationEngine
from sona_mcp.infrastructure.tool_registry import ToolRegistry


def create_mcp_runtime() -> MCPRuntime:
    """Create a fully-wired MCP runtime with built-in tools.

    Returns:
        A configured MCPRuntime instance ready for use.
    """
    # Core components
    registry = ToolRegistry()
    metrics = MCPMetrics()
    security_manager = SecurityManager()
    session_manager = SessionManager()
    connection_manager = ConnectionManager()
    circuit_breakers = CircuitBreakerRegistry()
    resource_manager = ResourceManager()
    prompt_manager = PromptManager()

    # Discovery and invocation
    discovery = ToolDiscovery(registry)
    invocation = ToolInvocationEngine(
        registry=registry,
        security_manager=security_manager,
        metrics=metrics,
    )

    # Register built-in tool handlers
    for tool_name, handler in BUILTIN_HANDLERS.items():
        invocation.register_handler(tool_name, handler)

    # Create runtime
    runtime = MCPRuntime(
        registry=registry,
        discovery=discovery,
        invocation=invocation,
        security_manager=security_manager,
        session_manager=session_manager,
        connection_manager=connection_manager,
        circuit_breakers=circuit_breakers,
        metrics=metrics,
        resource_manager=resource_manager,
        prompt_manager=prompt_manager,
    )

    return runtime


async def create_mcp_runtime_with_builtins() -> MCPRuntime:
    """Create an MCP runtime and register the built-in server.

    This is an async factory that also registers the built-in tools
    server, making all built-in tools immediately available.

    Returns:
        A configured MCPRuntime with built-in tools registered.
    """
    runtime = create_mcp_runtime()
    await runtime.register_server(BUILTIN_SERVER)
    return runtime
