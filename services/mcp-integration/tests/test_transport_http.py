"""Unit tests for HTTPTransport."""

import pytest

from sona_mcp.infrastructure.transport.http_transport import HTTPTransport


class TestHTTPTransportInit:
    def test_url_stored(self) -> None:
        transport = HTTPTransport("http://localhost:8080")
        assert transport.url == "http://localhost:8080"

    @pytest.mark.asyncio
    async def test_not_connected_initially(self) -> None:
        transport = HTTPTransport("http://localhost:8080")
        assert await transport.is_connected() is False


class TestHTTPTransportConnect:
    @pytest.mark.asyncio
    async def test_connect_to_nonexistent_server(self) -> None:
        transport = HTTPTransport("http://localhost:19999", timeout=0.5)
        result = await transport.connect()
        assert result is False

    @pytest.mark.asyncio
    async def test_not_connected_after_failed_connect(self) -> None:
        transport = HTTPTransport("http://localhost:19999", timeout=0.5)
        await transport.connect()
        assert await transport.is_connected() is False


class TestHTTPTransportDisconnect:
    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self) -> None:
        transport = HTTPTransport("http://localhost:8080")
        await transport.disconnect()  # Should not raise
        assert await transport.is_connected() is False


class TestHTTPTransportSendRequest:
    @pytest.mark.asyncio
    async def test_send_request_not_connected(self) -> None:
        transport = HTTPTransport("http://localhost:8080")
        with pytest.raises(ConnectionError):
            await transport.send_request("tools/list", {})


class TestHTTPTransportIsAbstract:
    def test_implements_base(self) -> None:
        from sona_mcp.infrastructure.transport.base import MCPTransportBase

        transport = HTTPTransport("http://example.com")
        assert isinstance(transport, MCPTransportBase)
