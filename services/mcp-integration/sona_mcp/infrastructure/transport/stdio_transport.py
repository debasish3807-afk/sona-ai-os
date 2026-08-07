"""STDIO-based MCP transport implementation.

Simulates communication with an MCP server process via stdin/stdout.
In production, this would spawn a subprocess and communicate via JSON-RPC
over the process's standard I/O streams.
"""

import asyncio
from typing import Any

import structlog

from sona_mcp.infrastructure.transport.base import MCPTransportBase

logger = structlog.get_logger()


class StdioTransport(MCPTransportBase):
    """STDIO transport for MCP server communication.

    Manages a simulated subprocess connection where requests are sent
    via stdin and responses received via stdout in JSON-RPC format.
    """

    def __init__(self, command: str) -> None:
        """Initialize the STDIO transport.

        Args:
            command: Shell command to start the MCP server process.
        """
        self._command = command
        self._connected = False
        self._request_id = 0
        self._process: asyncio.subprocess.Process | None = None

    @property
    def command(self) -> str:
        """The command used to spawn the MCP server process."""
        return self._command

    async def connect(self) -> bool:
        """Start the MCP server process and establish communication.

        Returns:
            True if the process started successfully.
        """
        try:
            self._process = await asyncio.create_subprocess_exec(
                *self._command.split(),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self._connected = True
            await logger.ainfo("stdio_transport_connected", command=self._command)
            return True
        except (OSError, ValueError) as e:
            await logger.aerror(
                "stdio_transport_connect_failed",
                command=self._command,
                error=str(e),
            )
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Terminate the MCP server process and clean up."""
        if self._process is not None:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except (ProcessLookupError, TimeoutError):
                if self._process is not None:
                    self._process.kill()
        self._connected = False
        self._process = None
        await logger.ainfo("stdio_transport_disconnected", command=self._command)

    async def send_request(self, method: str, params: dict[str, Any]) -> Any:
        """Send a JSON-RPC request over the process stdin.

        Args:
            method: The RPC method name.
            params: Request parameters.

        Returns:
            Parsed response from the server.

        Raises:
            ConnectionError: If not connected to the server.
        """
        if not self._connected or self._process is None:
            raise ConnectionError("STDIO transport is not connected")

        self._request_id += 1
        await logger.adebug(
            "stdio_request_sent",
            method=method,
            request_id=self._request_id,
        )

        # In a real implementation, this would write JSON-RPC to stdin
        # and read the response from stdout. For now, we return a
        # protocol-compliant empty result.
        return {"jsonrpc": "2.0", "id": self._request_id, "result": params}

    async def is_connected(self) -> bool:
        """Check if the transport process is still running.

        Returns:
            True if connected and process is alive.
        """
        if not self._connected or self._process is None:
            return False
        return self._process.returncode is None
