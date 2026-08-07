"""Unit tests for StdioTransport."""

import pytest

from sona_mcp.infrastructure.transport.stdio_transport import StdioTransport


class TestStdioTransportInit:
    def test_command_stored(self) -> None:
        transport = StdioTransport("echo hello")
        assert transport.command == "echo hello"

    def test_initially_disconnected(self) -> None:
        _ = StdioTransport("echo hello")
        # Can't call is_connected synchronously, test via connect

    @pytest.mark.asyncio
    async def test_not_connected_initially(self) -> None:
        transport = StdioTransport("echo hello")
        assert await transport.is_connected() is False


class TestStdioTransportConnect:
    @pytest.mark.asyncio
    async def test_connect_simple_command(self) -> None:
        transport = StdioTransport("cat")
        result = await transport.connect()
        assert result is True
        await transport.disconnect()

    @pytest.mark.asyncio
    async def test_connect_invalid_command(self) -> None:
        transport = StdioTransport("/nonexistent/binary/xyz123")
        result = await transport.connect()
        assert result is False

    @pytest.mark.asyncio
    async def test_is_connected_after_connect(self) -> None:
        transport = StdioTransport("cat")
        await transport.connect()
        assert await transport.is_connected() is True
        await transport.disconnect()


class TestStdioTransportDisconnect:
    @pytest.mark.asyncio
    async def test_disconnect(self) -> None:
        transport = StdioTransport("cat")
        await transport.connect()
        await transport.disconnect()
        assert await transport.is_connected() is False

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self) -> None:
        transport = StdioTransport("echo test")
        await transport.disconnect()  # Should not raise


class TestStdioTransportSendRequest:
    @pytest.mark.asyncio
    async def test_send_request_connected(self) -> None:
        transport = StdioTransport("cat")
        await transport.connect()
        result = await transport.send_request("tools/list", {"key": "val"})
        assert result is not None
        assert "result" in result
        await transport.disconnect()

    @pytest.mark.asyncio
    async def test_send_request_not_connected(self) -> None:
        transport = StdioTransport("echo test")
        with pytest.raises(ConnectionError):
            await transport.send_request("tools/list", {})

    @pytest.mark.asyncio
    async def test_send_request_increments_id(self) -> None:
        transport = StdioTransport("cat")
        await transport.connect()
        r1 = await transport.send_request("method1", {})
        r2 = await transport.send_request("method2", {})
        assert r1["id"] != r2["id"]
        await transport.disconnect()
