"""Unit tests for ConnectionManager."""

import pytest

from sona_mcp.domain.models import MCPServer, MCPTransport
from sona_mcp.infrastructure.connection_manager import (
    ConnectionManager,
    ConnectionState,
)


def _make_server(server_id: str = "srv-1") -> MCPServer:
    return MCPServer(
        server_id=server_id,
        name=f"Server {server_id}",
        transport=MCPTransport.STDIO,
    )


class TestConnectionConnect:
    @pytest.mark.asyncio
    async def test_connect_without_transport(self) -> None:
        mgr = ConnectionManager()
        result = await mgr.connect(_make_server())
        assert result is True

    @pytest.mark.asyncio
    async def test_connect_sets_state(self) -> None:
        mgr = ConnectionManager()
        await mgr.connect(_make_server("srv-1"))
        conn = await mgr.get_connection("srv-1")
        assert conn is not None
        assert conn.state == ConnectionState.CONNECTED

    @pytest.mark.asyncio
    async def test_connect_emits_event(self) -> None:
        mgr = ConnectionManager()
        await mgr.connect(_make_server("srv-1"))
        events = mgr.events
        assert len(events) == 1
        assert events[0].server_id == "srv-1"

    @pytest.mark.asyncio
    async def test_is_connected(self) -> None:
        mgr = ConnectionManager()
        await mgr.connect(_make_server("srv-1"))
        assert await mgr.is_connected("srv-1") is True

    @pytest.mark.asyncio
    async def test_is_not_connected(self) -> None:
        mgr = ConnectionManager()
        assert await mgr.is_connected("missing") is False


class TestConnectionDisconnect:
    @pytest.mark.asyncio
    async def test_disconnect(self) -> None:
        mgr = ConnectionManager()
        await mgr.connect(_make_server("srv-1"))
        result = await mgr.disconnect("srv-1", reason="shutdown")
        assert result is True

    @pytest.mark.asyncio
    async def test_disconnect_sets_state(self) -> None:
        mgr = ConnectionManager()
        await mgr.connect(_make_server("srv-1"))
        await mgr.disconnect("srv-1")
        conn = await mgr.get_connection("srv-1")
        assert conn is not None
        assert conn.state == ConnectionState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_disconnect_emits_event(self) -> None:
        mgr = ConnectionManager()
        await mgr.connect(_make_server("srv-1"))
        _ = mgr.events  # clear connect event
        await mgr.disconnect("srv-1", reason="done")
        events = mgr.events
        assert len(events) == 1
        assert events[0].reason == "done"

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent(self) -> None:
        mgr = ConnectionManager()
        result = await mgr.disconnect("missing")
        assert result is False


class TestConnectionReconnect:
    @pytest.mark.asyncio
    async def test_reconnect_simulated(self) -> None:
        mgr = ConnectionManager()
        await mgr.connect(_make_server("srv-1"))
        await mgr.disconnect("srv-1")
        result = await mgr.reconnect("srv-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_reconnect_max_attempts(self) -> None:
        mgr = ConnectionManager(max_reconnect_attempts=0)
        await mgr.connect(_make_server("srv-1"))
        await mgr.disconnect("srv-1")
        result = await mgr.reconnect("srv-1")
        assert result is False

    @pytest.mark.asyncio
    async def test_reconnect_nonexistent(self) -> None:
        mgr = ConnectionManager()
        result = await mgr.reconnect("missing")
        assert result is False


class TestConnectionHealth:
    @pytest.mark.asyncio
    async def test_health_check_connected(self) -> None:
        mgr = ConnectionManager()
        await mgr.connect(_make_server("srv-1"))
        assert await mgr.health_check("srv-1") is True

    @pytest.mark.asyncio
    async def test_health_check_disconnected(self) -> None:
        mgr = ConnectionManager()
        await mgr.connect(_make_server("srv-1"))
        await mgr.disconnect("srv-1")
        assert await mgr.health_check("srv-1") is False

    @pytest.mark.asyncio
    async def test_health_check_missing(self) -> None:
        mgr = ConnectionManager()
        assert await mgr.health_check("missing") is False


class TestConnectionListing:
    @pytest.mark.asyncio
    async def test_list_connected(self) -> None:
        mgr = ConnectionManager()
        await mgr.connect(_make_server("s1"))
        await mgr.connect(_make_server("s2"))
        await mgr.disconnect("s1")
        connected = await mgr.list_connected()
        assert connected == ["s2"]

    @pytest.mark.asyncio
    async def test_connection_count(self) -> None:
        mgr = ConnectionManager()
        await mgr.connect(_make_server("s1"))
        await mgr.connect(_make_server("s2"))
        assert mgr.connection_count == 2
