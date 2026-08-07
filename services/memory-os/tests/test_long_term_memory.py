"""Unit tests for long-term memory manager."""

import pytest

from sona_memory.domain.models import MemoryEntry, MemoryType
from sona_memory.infrastructure.embedding_service import EmbeddingService
from sona_memory.infrastructure.long_term_memory import LongTermMemory


def _make_entry(id: str, content: str = "test", importance: float = 0.5) -> MemoryEntry:
    return MemoryEntry(
        id=id, memory_type=MemoryType.LONG_TERM, content=content, importance=importance
    )


@pytest.fixture
def embedding_service() -> EmbeddingService:
    return EmbeddingService(dim=64)


@pytest.fixture
def ltm(embedding_service: EmbeddingService) -> LongTermMemory:
    return LongTermMemory(embedding_service=embedding_service)


class TestLongTermStore:
    """Tests for storing entries."""

    @pytest.mark.asyncio
    async def test_store_and_get(self, ltm: LongTermMemory) -> None:
        entry = _make_entry("m1", "important fact")
        await ltm.store("user1", entry)
        result = await ltm.get("user1", "m1")
        assert result is not None
        assert result.content == "important fact"

    @pytest.mark.asyncio
    async def test_store_generates_embedding(self, ltm: LongTermMemory) -> None:
        entry = _make_entry("m1", "no embedding yet")
        await ltm.store("user1", entry)
        result = await ltm.get("user1", "m1")
        assert result is not None
        assert result.embedding is not None
        assert len(result.embedding) == 64

    @pytest.mark.asyncio
    async def test_store_preserves_embedding(self, ltm: LongTermMemory) -> None:
        entry = MemoryEntry(
            id="m1",
            memory_type=MemoryType.LONG_TERM,
            content="test",
            embedding=[0.5] * 64,
        )
        await ltm.store("user1", entry)
        result = await ltm.get("user1", "m1")
        assert result is not None
        assert result.embedding == [0.5] * 64

    @pytest.mark.asyncio
    async def test_store_forces_long_term_type(self, ltm: LongTermMemory) -> None:
        entry = MemoryEntry(id="m1", memory_type=MemoryType.WORKING, content="test")
        await ltm.store("user1", entry)
        result = await ltm.get("user1", "m1")
        assert result is not None
        assert result.memory_type == MemoryType.LONG_TERM

    @pytest.mark.asyncio
    async def test_store_returns_id(self, ltm: LongTermMemory) -> None:
        result = await ltm.store("user1", _make_entry("m1"))
        assert result == "m1"


class TestLongTermSearch:
    """Tests for similarity search."""

    @pytest.mark.asyncio
    async def test_search_finds_similar(self, ltm: LongTermMemory) -> None:
        await ltm.store("user1", _make_entry("m1", "python programming language"))
        await ltm.store("user1", _make_entry("m2", "cooking recipes for dinner"))
        # Use same text to ensure self-similarity hits
        results = await ltm.search("user1", "python programming language")
        assert len(results) >= 1
        assert results[0][0].id == "m1"

    @pytest.mark.asyncio
    async def test_search_respects_top_k(self, ltm: LongTermMemory) -> None:
        for i in range(10):
            await ltm.store("user1", _make_entry(f"m{i}", f"content number {i}"))
        results = await ltm.search("user1", "content", top_k=3)
        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_search_empty_store(self, ltm: LongTermMemory) -> None:
        results = await ltm.search("user1", "anything")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_min_importance(self, ltm: LongTermMemory) -> None:
        await ltm.store("user1", _make_entry("low", "common fact", importance=0.2))
        await ltm.store("user1", _make_entry("high", "important fact", importance=0.9))
        results = await ltm.search("user1", "fact", min_importance=0.5)
        ids = [r[0].id for r in results]
        assert "low" not in ids

    @pytest.mark.asyncio
    async def test_search_returns_scores(self, ltm: LongTermMemory) -> None:
        await ltm.store("user1", _make_entry("m1", "hello world"))
        results = await ltm.search("user1", "hello world")
        assert len(results) > 0
        entry, score = results[0]
        assert isinstance(score, float)
        assert score > 0


class TestLongTermOperations:
    """Tests for remove, count, clear."""

    @pytest.mark.asyncio
    async def test_remove(self, ltm: LongTermMemory) -> None:
        await ltm.store("user1", _make_entry("m1"))
        assert await ltm.remove("user1", "m1") is True
        assert await ltm.get("user1", "m1") is None

    @pytest.mark.asyncio
    async def test_remove_nonexistent(self, ltm: LongTermMemory) -> None:
        assert await ltm.remove("user1", "m99") is False

    @pytest.mark.asyncio
    async def test_count(self, ltm: LongTermMemory) -> None:
        assert await ltm.count("user1") == 0
        await ltm.store("user1", _make_entry("m1"))
        assert await ltm.count("user1") == 1

    @pytest.mark.asyncio
    async def test_clear(self, ltm: LongTermMemory) -> None:
        await ltm.store("user1", _make_entry("m1"))
        await ltm.store("user1", _make_entry("m2"))
        count = await ltm.clear("user1")
        assert count == 2
        assert await ltm.count("user1") == 0

    @pytest.mark.asyncio
    async def test_get_all(self, ltm: LongTermMemory) -> None:
        await ltm.store("user1", _make_entry("m1"))
        await ltm.store("user1", _make_entry("m2"))
        results = await ltm.get_all("user1")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_unlimited_capacity(self, ltm: LongTermMemory) -> None:
        for i in range(100):
            await ltm.store("user1", _make_entry(f"m{i}", f"content {i}"))
        assert await ltm.count("user1") == 100
