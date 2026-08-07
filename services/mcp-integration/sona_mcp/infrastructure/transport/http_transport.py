"""HTTP-based MCP transport implementation.

Provides communication with MCP servers over HTTP using JSON-RPC.
Supports both standard HTTP request/response and SSE-based streaming.
"""

from typing import Any

import httpx
import structlog

from sona_mcp.infrastructure.transport.base import MCPTransportBase

logger = structlog.get_logger()


class HTTPTransport(MCPTransportBase):
    """HTTP transport for MCP server communication.

    Communicates with MCP servers via HTTP POST requests carrying
    JSON-RPC payloads. Manages an httpx async client for connection pooling.
    """

    def __init__(self, url: str, timeout: float = 30.0) -> None:
        """Initialize the HTTP transport.

        Args:
            url: Base URL of the MCP server.
            timeout: Request timeout in seconds.
        """
        self._url = url
        self._timeout = timeout
        self._connected = False
        self._request_id = 0
        self._client: httpx.AsyncClient | None = None

    @property
    def url(self) -> str:
        """The base URL of the MCP server."""
        return self._url

    async def connect(self) -> bool:
        """Establish an HTTP connection to the MCP server.

        Creates an httpx async client and verifies connectivity.

        Returns:
            True if the connection was established successfully.
        """
        try:
            self._client = httpx.AsyncClient(
                base_url=self._url,
                timeout=self._timeout,
            )
            # Verify server is reachable
            response = await self._client.get("/health")
            self._connected = response.status_code == 200
            await logger.ainfo(
                "http_transport_connected",
                url=self._url,
                status=response.status_code,
            )
            return self._connected
        except (httpx.HTTPError, httpx.ConnectError) as e:
            await logger.aerror(
                "http_transport_connect_failed",
                url=self._url,
                error=str(e),
            )
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Close the HTTP client and release resources."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        self._connected = False
        await logger.ainfo("http_transport_disconnected", url=self._url)

    async def send_request(self, method: str, params: dict[str, Any]) -> Any:
        """Send a JSON-RPC request over HTTP POST.

        Args:
            method: The RPC method name.
            params: Request parameters.

        Returns:
            Parsed JSON response from the server.

        Raises:
            ConnectionError: If not connected.
            httpx.HTTPError: If the request fails.
        """
        if not self._connected or self._client is None:
            raise ConnectionError("HTTP transport is not connected")

        self._request_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }

        await logger.adebug(
            "http_request_sent",
            method=method,
            request_id=self._request_id,
            url=self._url,
        )

        response = await self._client.post("/rpc", json=payload)
        response.raise_for_status()
        return response.json()

    async def is_connected(self) -> bool:
        """Check if the HTTP connection is active.

        Performs a lightweight health check to verify connectivity.

        Returns:
            True if connected and server is responsive.
        """
        if not self._connected or self._client is None:
            return False
        try:
            response = await self._client.get("/health")
            return response.status_code == 200
        except (httpx.HTTPError, httpx.ConnectError):
            self._connected = False
            return False
