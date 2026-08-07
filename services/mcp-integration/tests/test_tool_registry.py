"""Unit tests for the ToolRegistry."""

import pytest

from sona_mcp.domain.models import MCPTool, ToolPermission
from sona_mcp.infrastructure.tool_registry import ToolRegistry


def _make_tool(
    name: str = "test_tool",
    server_id: str = "srv-1",
    permissions: list[ToolPermission] | None = None,
    description: str = "A test tool",
) -> MCPTool:
    return MCPTool(
        name=name,
        description=description,
        input_schema={"type": "object", "properties": {}},
        permissions=permissions or [ToolPermission.READ],
        server_id=server_id,
    )


class TestToolRegistryRegister:
    @pytest.mark.asyncio
    async def test_register_tool(self) -> None:
        registry = ToolRegistry()
        tool = _make_tool()
        await registry.register(tool)
        assert registry.count == 1

    @pytest.mark.asyncio
    async def test_register_multiple_tools(self) -> None:
        registry = ToolRegistry()
        await registry.register(_make_tool("tool1"))
        await registry.register(_make_tool("tool2"))
        assert registry.count == 2

    @pytest.mark.asyncio
    async def test_register_duplicate_increments_version(self) -> None:
        registry = ToolRegistry()
        await registry.register(_make_tool("tool1"))
        assert registry.get_version("tool1") == 1
        await registry.register(_make_tool("tool1"))
        assert registry.get_version("tool1") == 2

    @pytest.mark.asyncio
    async def test_register_emits_event(self) -> None:
        registry = ToolRegistry()
        await registry.register(_make_tool("tool1", server_id="srv-a"))
        events = registry.events
        assert len(events) == 1
        assert events[0].tool_name == "tool1"
        assert events[0].server_id == "srv-a"


class TestToolRegistryUnregister:
    @pytest.mark.asyncio
    async def test_unregister_existing(self) -> None:
        registry = ToolRegistry()
        await registry.register(_make_tool("tool1"))
        result = await registry.unregister("tool1")
        assert result is True
        assert registry.count == 0

    @pytest.mark.asyncio
    async def test_unregister_nonexistent(self) -> None:
        registry = ToolRegistry()
        result = await registry.unregister("missing")
        assert result is False

    @pytest.mark.asyncio
    async def test_unregister_clears_version(self) -> None:
        registry = ToolRegistry()
        await registry.register(_make_tool("tool1"))
        await registry.unregister("tool1")
        assert registry.get_version("tool1") == 0


class TestToolRegistryGet:
    @pytest.mark.asyncio
    async def test_get_existing(self) -> None:
        registry = ToolRegistry()
        tool = _make_tool("my_tool")
        await registry.register(tool)
        result = await registry.get("my_tool")
        assert result is not None
        assert result.name == "my_tool"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self) -> None:
        registry = ToolRegistry()
        result = await registry.get("missing")
        assert result is None


class TestToolRegistryList:
    @pytest.mark.asyncio
    async def test_list_all(self) -> None:
        registry = ToolRegistry()
        await registry.register(_make_tool("t1", server_id="s1"))
        await registry.register(_make_tool("t2", server_id="s2"))
        all_tools = await registry.list_all()
        assert len(all_tools) == 2

    @pytest.mark.asyncio
    async def test_list_by_server(self) -> None:
        registry = ToolRegistry()
        await registry.register(_make_tool("t1", server_id="s1"))
        await registry.register(_make_tool("t2", server_id="s1"))
        await registry.register(_make_tool("t3", server_id="s2"))
        s1_tools = await registry.list_by_server("s1")
        assert len(s1_tools) == 2

    @pytest.mark.asyncio
    async def test_list_by_server_empty(self) -> None:
        registry = ToolRegistry()
        result = await registry.list_by_server("missing")
        assert result == []


class TestToolRegistrySearch:
    @pytest.mark.asyncio
    async def test_search_by_capability(self) -> None:
        registry = ToolRegistry()
        await registry.register(_make_tool("reader", permissions=[ToolPermission.READ]))
        await registry.register(_make_tool("writer", permissions=[ToolPermission.WRITE]))
        readers = await registry.search_by_capability(ToolPermission.READ)
        assert len(readers) == 1
        assert readers[0].name == "reader"

    @pytest.mark.asyncio
    async def test_search_by_pattern(self) -> None:
        registry = ToolRegistry()
        await registry.register(_make_tool("read_file"))
        await registry.register(_make_tool("read_url"))
        await registry.register(_make_tool("write_file"))
        results = await registry.search_by_pattern("read_*")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_by_description(self) -> None:
        registry = ToolRegistry()
        await registry.register(_make_tool("t1", description="Read file contents"))
        await registry.register(_make_tool("t2", description="Write data to disk"))
        results = await registry.search_by_description("file")
        assert len(results) == 1
        assert results[0].name == "t1"

    @pytest.mark.asyncio
    async def test_search_by_description_case_insensitive(self) -> None:
        registry = ToolRegistry()
        await registry.register(_make_tool("t1", description="FETCH Data from API"))
        results = await registry.search_by_description("fetch")
        assert len(results) == 1


class TestToolRegistrySchema:
    @pytest.mark.asyncio
    async def test_get_tool_schema(self) -> None:
        registry = ToolRegistry()
        tool = MCPTool(
            name="tool1",
            description="test",
            input_schema={"type": "object", "properties": {"x": {"type": "string"}}},
            permissions=[ToolPermission.READ],
            server_id="s1",
        )
        await registry.register(tool)
        schema = registry.get_tool_schema("tool1")
        assert schema is not None
        assert "x" in schema["properties"]

    @pytest.mark.asyncio
    async def test_get_schema_missing(self) -> None:
        registry = ToolRegistry()
        assert registry.get_tool_schema("missing") is None
