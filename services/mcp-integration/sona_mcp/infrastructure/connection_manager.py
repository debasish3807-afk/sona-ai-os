"""Connection management for MCP Integration.

Manages connections to MCP servers with lifecycle management,
connection pooling, auto-reconnect, and health monitoring.
"""

import time
from dataclasses import dataclass, field
from enum import StrEnum

import structlog

from sona_mcp.domain.events import ServerConnectedEvent, ServerDisconnectedEvent
from sona_mcp.domain.models import MCPServer
from sona_mcp.infrastructure.transport.base import MCPTransportBase

logger = structlog.get_logger()


class ConnectionState(StrEnum):
    """States a server connection can be in."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class ServerConnection:
    """Tracks the state of a connection to an MCP server.

    Attributes:
        server: The MCP server configuration.
        transport: The transport adapter used for communication.
        state: Current connection state.
        connected_at: When the connection was established.
        reconnect_attempts: Number of reconnect attempts made.
        last_health_check: When the last health check was performed.
        healthy: Whether the last health check passed.
    """

    server: MCPServer
    transport: MCPTransportBase | None = None
    state: ConnectionState = ConnectionState.DISCONNECTED
    connected_at: float | None = None
    reconnect_attempts: int = 0
    last_health_check: float | None = None
    healthy: bool = False
    _failure_count: int = field(default=0, init=False)


class ConnectionManager:
    """Manages connections to MCP servers.

    Provides connect/disconnect lifecycle, connection pooling,
    auto-reconnect on failure, and health monitoring.
    """

    def __init__(
        self,
        max_reconnect_attempts: int = 3,
        health_check_interval: float = 60.0,
    ) -> None:
        """Initialize the connection manager.

        Args:
            max_reconnect_attempts: Max auto-reconnect attempts before failing.
            health_check_interval: Seconds between health checks.
        """
        self._connections: dict[str, ServerConnection] = {}
        self._max_reconnect_attempts = max_reconnect_attempts
        self._health_check_interval = health_check_interval
        self._events: list[ServerConnectedEvent | ServerDisconnectedEvent] = []

    @property
    def events(self) -> list[ServerConnectedEvent | ServerDisconnectedEvent]:
        """Return collected domain events and clear the buffer."""
        events = list(self._events)
        self._events.clear()
        return events

    async def connect(self, server: MCPServer, transport: MCPTransportBase | None = None) -> bool:
        """Establish a connection to an MCP server.

        Args:
            server: The server to connect to.
            transport: Optional transport adapter to use.

        Returns:
            True if the connection was established successfully.
        """
        conn = ServerConnection(server=server, transport=transport)
        conn.state = ConnectionState.CONNECTING

        if transport is not None:
            success = await transport.connect()
            if success:
                conn.state = ConnectionState.CONNECTED
                conn.connected_at = time.monotonic()
                conn.healthy = True
                self._events.append(
                    ServerConnectedEvent(
                        server_id=server.server_id,
                        tools_count=len(server.tools),
                    )
                )
            else:
                conn.state = ConnectionState.FAILED
        else:
            # No transport = simulated connection (e.g., built-in tools)
            conn.state = ConnectionState.CONNECTED
            conn.connected_at = time.monotonic()
            conn.healthy = True
            self._events.append(
                ServerConnectedEvent(
                    server_id=server.server_id,
                    tools_count=len(server.tools),
                )
            )

        self._connections[server.server_id] = conn
        await logger.ainfo(
            "server_connection_state",
            server_id=server.server_id,
            state=conn.state.value,
        )
        return conn.state == ConnectionState.CONNECTED

    async def disconnect(self, server_id: str, reason: str = "") -> bool:
        """Disconnect from an MCP server.

        Args:
            server_id: The server to disconnect from.
            reason: Reason for disconnection.

        Returns:
            True if disconnected successfully, False if not found.
        """
        conn = self._connections.get(server_id)
        if conn is None:
            return False

        if conn.transport is not None:
            await conn.transport.disconnect()

        conn.state = ConnectionState.DISCONNECTED
        conn.healthy = False
        self._events.append(ServerDisconnectedEvent(server_id=server_id, reason=reason))
        await logger.ainfo("server_disconnected", server_id=server_id, reason=reason)
        return True

    async def reconnect(self, server_id: str) -> bool:
        """Attempt to reconnect to a disconnected server.

        Args:
            server_id: The server to reconnect to.

        Returns:
            True if reconnection succeeded.
        """
        conn = self._connections.get(server_id)
        if conn is None:
            return False

        if conn.reconnect_attempts >= self._max_reconnect_attempts:
            conn.state = ConnectionState.FAILED
            await logger.awarn("max_reconnect_attempts_reached", server_id=server_id)
            return False

        conn.state = ConnectionState.RECONNECTING
        conn.reconnect_attempts += 1

        if conn.transport is not None:
            success = await conn.transport.connect()
            if success:
                conn.state = ConnectionState.CONNECTED
                conn.connected_at = time.monotonic()
                conn.reconnect_attempts = 0
                conn.healthy = True
                self._events.append(
                    ServerConnectedEvent(
                        server_id=server_id,
                        tools_count=len(conn.server.tools),
                    )
                )
                return True
            conn.state = ConnectionState.FAILED
            return False
        # Simulated reconnect succeeds
        conn.state = ConnectionState.CONNECTED
        conn.connected_at = time.monotonic()
        conn.reconnect_attempts = 0
        conn.healthy = True
        return True

    async def health_check(self, server_id: str) -> bool:
        """Perform a health check on a server connection.

        Args:
            server_id: The server to check.

        Returns:
            True if the server is healthy.
        """
        conn = self._connections.get(server_id)
        if conn is None:
            return False

        conn.last_health_check = time.monotonic()

        if conn.state != ConnectionState.CONNECTED:
            conn.healthy = False
            return False

        if conn.transport is not None:
            conn.healthy = await conn.transport.is_connected()
        else:
            conn.healthy = True

        return conn.healthy

    async def get_connection(self, server_id: str) -> ServerConnection | None:
        """Get the connection object for a server.

        Args:
            server_id: The server identifier.

        Returns:
            The ServerConnection if it exists, None otherwise.
        """
        return self._connections.get(server_id)

    async def is_connected(self, server_id: str) -> bool:
        """Check if a server is currently connected.

        Args:
            server_id: The server to check.

        Returns:
            True if the server is in CONNECTED state.
        """
        conn = self._connections.get(server_id)
        if conn is None:
            return False
        return conn.state == ConnectionState.CONNECTED

    async def list_connected(self) -> list[str]:
        """List all currently connected server IDs.

        Returns:
            A list of server_id strings for connected servers.
        """
        return [
            sid
            for sid, conn in self._connections.items()
            if conn.state == ConnectionState.CONNECTED
        ]

    @property
    def connection_count(self) -> int:
        """Return the total number of tracked connections."""
        return len(self._connections)
