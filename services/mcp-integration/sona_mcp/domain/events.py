"""Domain events for the MCP Integration service.

Events are emitted when significant state changes occur in the MCP runtime,
such as tool registration, invocation, failures, and server connectivity changes.
"""

from dataclasses import dataclass

from sona_shared.domain.primitives import DomainEvent


@dataclass(frozen=True)
class ToolRegisteredEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when a new tool is registered in the tool registry."""

    tool_name: str = ""
    server_id: str = ""


@dataclass(frozen=True)
class ToolInvokedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted after a tool call completes (success or failure)."""

    tool_name: str = ""
    user_id: str = ""
    success: bool = True
    duration_ms: float = 0.0


@dataclass(frozen=True)
class ToolFailedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when a tool call fails with an error."""

    tool_name: str = ""
    error: str = ""


@dataclass(frozen=True)
class ServerConnectedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when an MCP server connection is established."""

    server_id: str = ""
    tools_count: int = 0


@dataclass(frozen=True)
class ServerDisconnectedEvent(DomainEvent):  # type: ignore[misc]
    """Emitted when an MCP server is disconnected."""

    server_id: str = ""
    reason: str = ""
