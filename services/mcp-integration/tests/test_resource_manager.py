"""Unit tests for ResourceManager."""

import pytest

from sona_mcp.infrastructure.resource_manager import (
    MCPResource,
    ResourceContent,
    ResourceManager,
)


def _make_resource(
    uri: str = "file:///tmp/test.txt",
    name: str = "test.txt",
    server_id: str = "srv-1",
) -> MCPResource:
    return MCPResource(
        uri=uri,
        name=name,
        description="A test file",
        mime_type="text/plain",
        server_id=server_id,
    )


class TestResourceRegistration:
    @pytest.mark.asyncio
    async def test_register_resource(self) -> None:
        mgr = ResourceManager()
        await mgr.register_resource(_make_resource())
        assert mgr.resource_count == 1

    @pytest.mark.asyncio
    async def test_register_multiple(self) -> None:
        mgr = ResourceManager()
        await mgr.register_resource(_make_resource("file:///a", "a"))
        await mgr.register_resource(_make_resource("file:///b", "b"))
        assert mgr.resource_count == 2

    @pytest.mark.asyncio
    async def test_unregister_resource(self) -> None:
        mgr = ResourceManager()
        await mgr.register_resource(_make_resource())
        result = await mgr.unregister_resource("file:///tmp/test.txt")
        assert result is True
        assert mgr.resource_count == 0

    @pytest.mark.asyncio
    async def test_unregister_nonexistent(self) -> None:
        mgr = ResourceManager()
        result = await mgr.unregister_resource("missing")
        assert result is False


class TestResourceLookup:
    @pytest.mark.asyncio
    async def test_get_resource(self) -> None:
        mgr = ResourceManager()
        await mgr.register_resource(_make_resource())
        res = await mgr.get_resource("file:///tmp/test.txt")
        assert res is not None
        assert res.name == "test.txt"

    @pytest.mark.asyncio
    async def test_get_missing(self) -> None:
        mgr = ResourceManager()
        res = await mgr.get_resource("missing")
        assert res is None

    @pytest.mark.asyncio
    async def test_list_all_resources(self) -> None:
        mgr = ResourceManager()
        await mgr.register_resource(_make_resource("file:///a", "a"))
        await mgr.register_resource(_make_resource("file:///b", "b"))
        resources = await mgr.list_resources()
        assert len(resources) == 2

    @pytest.mark.asyncio
    async def test_list_by_server(self) -> None:
        mgr = ResourceManager()
        await mgr.register_resource(_make_resource("file:///a", "a", "s1"))
        await mgr.register_resource(_make_resource("file:///b", "b", "s2"))
        s1_res = await mgr.list_resources(server_id="s1")
        assert len(s1_res) == 1
        assert s1_res[0].name == "a"


class TestResourceReading:
    @pytest.mark.asyncio
    async def test_read_resource(self) -> None:
        mgr = ResourceManager()
        await mgr.register_resource(_make_resource())
        content = await mgr.read_resource("file:///tmp/test.txt")
        assert content is not None
        assert "test.txt" in content.content

    @pytest.mark.asyncio
    async def test_read_missing(self) -> None:
        mgr = ResourceManager()
        content = await mgr.read_resource("missing")
        assert content is None

    @pytest.mark.asyncio
    async def test_read_uses_cache(self) -> None:
        mgr = ResourceManager()
        await mgr.register_resource(_make_resource())
        c1 = await mgr.read_resource("file:///tmp/test.txt")
        c2 = await mgr.read_resource("file:///tmp/test.txt")
        assert c1 is c2  # Same object from cache


class TestResourceCache:
    @pytest.mark.asyncio
    async def test_cache_content(self) -> None:
        mgr = ResourceManager()
        content = ResourceContent(uri="file:///custom", content="custom data")
        await mgr.cache_content("file:///custom", content)
        assert mgr.cache_size == 1

    @pytest.mark.asyncio
    async def test_invalidate_specific(self) -> None:
        mgr = ResourceManager()
        await mgr.register_resource(_make_resource())
        await mgr.read_resource("file:///tmp/test.txt")
        assert mgr.cache_size == 1
        await mgr.invalidate_cache("file:///tmp/test.txt")
        assert mgr.cache_size == 0

    @pytest.mark.asyncio
    async def test_invalidate_all(self) -> None:
        mgr = ResourceManager()
        await mgr.register_resource(_make_resource("file:///a", "a"))
        await mgr.register_resource(_make_resource("file:///b", "b"))
        await mgr.read_resource("file:///a")
        await mgr.read_resource("file:///b")
        await mgr.invalidate_cache()
        assert mgr.cache_size == 0


class TestResourceServerCleanup:
    @pytest.mark.asyncio
    async def test_remove_server_resources(self) -> None:
        mgr = ResourceManager()
        await mgr.register_resource(_make_resource("file:///a", "a", "s1"))
        await mgr.register_resource(_make_resource("file:///b", "b", "s1"))
        await mgr.register_resource(_make_resource("file:///c", "c", "s2"))
        removed = await mgr.remove_server_resources("s1")
        assert removed == 2
        assert mgr.resource_count == 1
