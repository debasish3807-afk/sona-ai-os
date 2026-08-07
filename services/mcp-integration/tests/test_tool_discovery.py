"""Unit tests for ToolDiscovery."""

import pytest

from sona_mcp.domain.models import MCPServer, MCPTool, MCPTransport, ToolPermission
from sona_mcp.infrastructure.tool_discovery import ToolDiscovery
from sona_mcp.infrastructure.tool_registry import ToolRegistry


def _make_server(server_id: str = "srv-1", tools: list[MCPTool] | None = None) -> MCPServer:
    if tools is None:
        tools = [
            MCPTool(
                name="tool_a",
                description="Tool A",
                input_schema={},
                permissions=[ToolPermission.READ],
                server_id=server_id,
            ),
            MCPTool(
                name="tool_b",
                description="Tool B",
                input_schema={},
                permissions=[ToolPermission.WRITE],
                server_id=server_id,
            ),
        ]
    return MCPServer(
        server_id=server_id,
        name=f"Server {server_id}",
        transport=MCPTransport.STDIO,
        tools=tools,
    )


class TestToolDiscovery:
    @pytest.mark.asyncio
    async def test_discover_from_server(self) -> None:
        registry = ToolRegistry()
        discovery = ToolDiscovery(registry)
        server = _make_server()
        tools = await discovery.discover_from_server(server)
        assert len(tools) == 2
        assert registry.count == 2

    @pytest.mark.asyncio
    async def test_is_discovered_after_discovery(self) -> None:
        registry = ToolRegistry()
        discovery = ToolDiscovery(registry)
        server = _make_server("srv-x")
        assert discovery.is_discovered("srv-x") is False
        await discovery.discover_from_server(server)
        assert discovery.is_discovered("srv-x") is True

    @pytest.mark.asyncio
    async def test_discovered_server_count(self) -> None:
        registry = ToolRegistry()
        discovery = ToolDiscovery(registry)
        await discovery.discover_from_server(_make_server("s1"))
        await discovery.discover_from_server(_make_server("s2"))
        assert discovery.discovered_server_count == 2

    @pytest.mark.asyncio
    async def test_rediscover_replaces_tools(self) -> None:
        registry = ToolRegistry()
        discovery = ToolDiscovery(registry)
        server = _make_server("srv-1")
        await discovery.discover_from_server(server)
        assert registry.count == 2

        # Rediscover with different tools
        new_tool = MCPTool(
            name="tool_c",
            description="Tool C",
            input_schema={},
            permissions=[ToolPermission.READ],
            server_id="srv-1",
        )
        new_server = MCPServer(
            server_id="srv-1",
            name="Server srv-1",
            transport=MCPTransport.STDIO,
            tools=[new_tool],
        )
        tools = await discovery.rediscover(new_server)
        assert len(tools) == 1
        assert registry.count == 1
        assert (await registry.get("tool_c")) is not None

    @pytest.mark.asyncio
    async def test_remove_server_tools(self) -> None:
        registry = ToolRegistry()
        discovery = ToolDiscovery(registry)
        await discovery.discover_from_server(_make_server("srv-1"))
        removed = await discovery.remove_server_tools("srv-1")
        assert removed == 2
        assert registry.count == 0
        assert discovery.is_discovered("srv-1") is False

    @pytest.mark.asyncio
    async def test_remove_nonexistent_server(self) -> None:
        registry = ToolRegistry()
        discovery = ToolDiscovery(registry)
        removed = await discovery.remove_server_tools("missing")
        assert removed == 0

    @pytest.mark.asyncio
    async def test_discover_empty_server(self) -> None:
        registry = ToolRegistry()
        discovery = ToolDiscovery(registry)
        server = _make_server("srv-empty", tools=[])
        tools = await discovery.discover_from_server(server)
        assert len(tools) == 0
        assert registry.count == 0

    @pytest.mark.asyncio
    async def test_discover_multiple_servers_isolated(self) -> None:
        registry = ToolRegistry()
        discovery = ToolDiscovery(registry)
        s1_tools = [
            MCPTool(
                name="s1_tool",
                description="",
                input_schema={},
                permissions=[ToolPermission.READ],
                server_id="s1",
            )
        ]
        s2_tools = [
            MCPTool(
                name="s2_tool",
                description="",
                input_schema={},
                permissions=[ToolPermission.READ],
                server_id="s2",
            )
        ]
        await discovery.discover_from_server(_make_server("s1", s1_tools))
        await discovery.discover_from_server(_make_server("s2", s2_tools))
        assert registry.count == 2
        s1_result = await registry.list_by_server("s1")
        assert len(s1_result) == 1
        assert s1_result[0].name == "s1_tool"
