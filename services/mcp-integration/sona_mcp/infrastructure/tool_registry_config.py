"""MCP Tool Registry configuration.

Controls which categories of tools are registered:
- Production tools: always available (calculate, current_time, echo)
- Demo tools: simulated implementations (read_file, web_fetch)

In production mode (default), demo tools are NOT registered.
Demo tools are explicitly enabled via SONA_MCP_DEMO_TOOLS_ENABLED=true.
"""

import os
from typing import Any

import structlog

from sona_mcp.domain.models import MCPServer, MCPTool, MCPTransport
from sona_mcp.infrastructure.builtin_tools import (
    BUILTIN_HANDLERS,
    BUILTIN_TOOLS,
    handle_calculate,
    handle_current_time,
    handle_echo,
)

logger = structlog.get_logger()

# Demo tool names — these use simulated/fake data and must not run in production
DEMO_TOOL_NAMES: frozenset[str] = frozenset({"read_file", "web_fetch"})

# Production tool names — safe, pure-logic tools with no simulated I/O
PRODUCTION_TOOL_NAMES: frozenset[str] = frozenset({"calculate", "current_time", "echo"})


def is_demo_tools_enabled() -> bool:
    """Check if demo tools are explicitly enabled via environment.

    Returns True only when SONA_MCP_DEMO_TOOLS_ENABLED is set to 'true' or '1'.
    Default (production): False.
    """
    val = os.environ.get("SONA_MCP_DEMO_TOOLS_ENABLED", "false").lower()
    return val in ("true", "1", "yes")


def get_production_tools() -> list[MCPTool]:
    """Return only production-safe tools (no simulated I/O)."""
    return [t for t in BUILTIN_TOOLS if t.name in PRODUCTION_TOOL_NAMES]


def get_demo_tools() -> list[MCPTool]:
    """Return demo/simulated tools (read_file, web_fetch)."""
    return [t for t in BUILTIN_TOOLS if t.name in DEMO_TOOL_NAMES]


def get_registered_tools() -> list[MCPTool]:
    """Return tools appropriate for the current environment.

    Production (default): only production tools.
    Demo mode (SONA_MCP_DEMO_TOOLS_ENABLED=true): production + demo tools.
    """
    tools = get_production_tools()
    if is_demo_tools_enabled():
        tools = tools + get_demo_tools()
        logger.warning(
            "mcp.demo_tools_enabled",
            message="Demo/simulated tools are enabled — not for production use",
            demo_tools=list(DEMO_TOOL_NAMES),
        )
    return tools


def get_registered_handlers() -> dict[str, Any]:
    """Return handlers appropriate for the current environment.

    Production (default): only production handlers.
    Demo mode: production + demo handlers.
    """
    prod_handlers = {
        "calculate": handle_calculate,
        "current_time": handle_current_time,
        "echo": handle_echo,
    }
    if is_demo_tools_enabled():
        return dict(BUILTIN_HANDLERS)  # All handlers including demo
    return prod_handlers


def get_registered_server() -> MCPServer:
    """Return the builtin server with appropriate tools registered."""
    tools = get_registered_tools()
    return MCPServer(
        server_id="builtin",
        name="Built-in Tools",
        transport=MCPTransport.STDIO,
        tools=tools,
    )
