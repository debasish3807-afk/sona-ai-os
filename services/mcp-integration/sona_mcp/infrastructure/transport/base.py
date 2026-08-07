"""Abstract base class for MCP transport implementations.

All transport adapters must implement this interface to provide
communication with MCP servers regardless of the underlying protocol.
"""

from abc import ABC, abstractmethod
from typing import Any


class MCPTransportBase(ABC):
    """Abstract base for all MCP transport implementations.

    Provides the contract for connecting to, disconnecting from,
    and communicating with MCP server processes.
    """

    @abstractmethod
    async def connect(self) -> bool:
        """Establish a connection to the MCP server.

        Returns:
            True if the connection was established successfully.
        """
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection to the MCP server."""
        ...

    @abstractmethod
    async def send_request(self, method: str, params: dict[str, Any]) -> Any:
        """Send a JSON-RPC request to the MCP server.

        Args:
            method: The RPC method name (e.g., 'tools/list', 'tools/call').
            params: Parameters to include in the request.

        Returns:
            The response data from the server.
        """
        ...

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check whether the transport is currently connected.

        Returns:
            True if connected, False otherwise.
        """
        ...
