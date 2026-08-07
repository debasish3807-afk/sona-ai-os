"""Unit tests for user memory manager."""

import pytest

from sona_memory.infrastructure.user_memory import UserMemory


class TestUserMemoryStore:
    """Tests for storing preferences."""

    @pytest.mark.asyncio
    async def test_set_and_get(self) -> None:
        um = UserMemory()
        await um.set_preference("user1", "language", "en")
        pref = await um.get_preference("user1", "language")
        assert pref is not None
        assert pref.value == "en"

    @pytest.mark.asyncio
    async def test_get_value(self) -> None:
        um = UserMemory()
        await um.set_preference("user1", "theme", "dark")
        value = await um.get_value("user1", "theme")
        assert value == "dark"

    @pytest.mark.asyncio
    async def test_get_value_default(self) -> None:
        um = UserMemory()
        value = await um.get_value("user1", "missing", default="fallback")
        assert value == "fallback"

    @pytest.mark.asyncio
    async def test_set_with_category(self) -> None:
        um = UserMemory()
        await um.set_preference("user1", "tz", "UTC", category="locale")
        pref = await um.get_preference("user1", "tz")
        assert pref is not None
        assert pref.category == "locale"

    @pytest.mark.asyncio
    async def test_set_with_confidence(self) -> None:
        um = UserMemory()
        await um.set_preference("user1", "name", "Alice", confidence=0.95)
        pref = await um.get_preference("user1", "name")
        assert pref is not None
        assert pref.confidence == 0.95

    @pytest.mark.asyncio
    async def test_set_with_source(self) -> None:
        um = UserMemory()
        await um.set_preference("user1", "mood", "happy", source="inferred")
        pref = await um.get_preference("user1", "mood")
        assert pref is not None
        assert pref.source == "inferred"

    @pytest.mark.asyncio
    async def test_overwrite_preference(self) -> None:
        um = UserMemory()
        await um.set_preference("user1", "color", "blue")
        await um.set_preference("user1", "color", "red")
        value = await um.get_value("user1", "color")
        assert value == "red"


class TestUserMemoryRetrieval:
    """Tests for retrieving preferences."""

    @pytest.mark.asyncio
    async def test_get_by_category(self) -> None:
        um = UserMemory()
        await um.set_preference("user1", "lang", "en", category="locale")
        await um.set_preference("user1", "theme", "dark", category="ui")
        await um.set_preference("user1", "tz", "UTC", category="locale")
        results = await um.get_by_category("user1", "locale")
        assert len(results) == 2
        keys = {p.key for p in results}
        assert "lang" in keys
        assert "tz" in keys

    @pytest.mark.asyncio
    async def test_get_all(self) -> None:
        um = UserMemory()
        await um.set_preference("user1", "a", 1)
        await um.set_preference("user1", "b", 2)
        all_prefs = await um.get_all("user1")
        assert len(all_prefs) == 2

    @pytest.mark.asyncio
    async def test_get_all_empty(self) -> None:
        um = UserMemory()
        assert await um.get_all("user1") == []

    @pytest.mark.asyncio
    async def test_has_preference(self) -> None:
        um = UserMemory()
        await um.set_preference("user1", "key1", "val")
        assert await um.has_preference("user1", "key1") is True
        assert await um.has_preference("user1", "no_key") is False

    @pytest.mark.asyncio
    async def test_get_keys(self) -> None:
        um = UserMemory()
        await um.set_preference("user1", "a", 1)
        await um.set_preference("user1", "b", 2)
        keys = await um.get_keys("user1")
        assert set(keys) == {"a", "b"}

    @pytest.mark.asyncio
    async def test_count(self) -> None:
        um = UserMemory()
        assert await um.count("user1") == 0
        await um.set_preference("user1", "k", "v")
        assert await um.count("user1") == 1


class TestUserMemoryDelete:
    """Tests for deleting preferences."""

    @pytest.mark.asyncio
    async def test_delete_preference(self) -> None:
        um = UserMemory()
        await um.set_preference("user1", "k", "v")
        assert await um.delete_preference("user1", "k") is True
        assert await um.get_preference("user1", "k") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self) -> None:
        um = UserMemory()
        assert await um.delete_preference("user1", "no") is False

    @pytest.mark.asyncio
    async def test_delete_by_category(self) -> None:
        um = UserMemory()
        await um.set_preference("user1", "a", 1, category="cat1")
        await um.set_preference("user1", "b", 2, category="cat1")
        await um.set_preference("user1", "c", 3, category="cat2")
        count = await um.delete_by_category("user1", "cat1")
        assert count == 2
        assert await um.count("user1") == 1

    @pytest.mark.asyncio
    async def test_clear(self) -> None:
        um = UserMemory()
        await um.set_preference("user1", "a", 1)
        await um.set_preference("user1", "b", 2)
        count = await um.clear("user1")
        assert count == 2
        assert await um.count("user1") == 0

    @pytest.mark.asyncio
    async def test_never_expires(self) -> None:
        """User memory should persist indefinitely."""
        um = UserMemory()
        await um.set_preference("user1", "permanent", "value")
        # No expiration mechanism — just verify it stays
        value = await um.get_value("user1", "permanent")
        assert value == "value"
