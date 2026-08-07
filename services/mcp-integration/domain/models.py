"""Domain models for the MCP Integration service.

Defines the data structures used for Model Context Protocol server management,
tool discovery, and permission-gated tool execution.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class MCPTransport(StrEnum):
    """Supported transport protocols for MCP server connections.

    Determines how the MCP client communicates with an MCP server process.
    """

    STDIO = "stdio"
    SSE = "sse"
    WEBSOCKET = "websocket"


class ToolPermission(StrEnum):
    """Permission levels for MCP tool execution.

    Controls what operations a tool is allowed to perform,
    enabling fine-grained access control for external tool calls.
    """

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


@dataclass(frozen=True)
class MCPTool:
    """Represents a single tool exposed by an MCP server.

    Attributes:
        name: Unique name of the tool within its server.
        description: Human-readable description of what the tool does.
        input_schema: JSON Schema describing the tool's expected input.
        permissions: List of permissions required to invoke this tool.
        server_id: Identifier of the MCP server that hosts this tool.
    """

    name: str
    description: str
    input_schema: dict[str, Any]
    permissions: list[ToolPermission]
    server_id: str


@dataclass(frozen=True)
class MCPServer:
    """Represents a registered MCP server instance.

    Attributes:
        server_id: Unique identifier for this server registration.
        name: Human-readable name of the server.
        transport: The transport protocol used to communicate with this server.
        command: Shell command to start the server (for STDIO transport).
        url: URL endpoint for the server (for SSE/WebSocket transport).
        tools: List of tools discovered on this server.
    """

    server_id: str
    name: str
    transport: MCPTransport
    command: str | None = None
    url: str | None = None
    tools: list[MCPTool] = field(default_factory=list)


@dataclass(frozen=True)
class ToolCallResult:
    """Result of invoking an MCP tool.

    Attributes:
        tool_name: Name of the tool that was called.
        output: The output returned by the tool.
        success: Whether the tool call completed successfully.
        error: Error message if the call failed, None otherwise.
        duration_ms: Time taken to execute the tool call in milliseconds.
    """

    tool_name: str
    output: Any
    success: bool
    error: str | None = None
    duration_ms: float = 0.0
