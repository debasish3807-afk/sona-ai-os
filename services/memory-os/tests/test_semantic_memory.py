"""Unit tests for semantic memory manager."""

import pytest

from sona_memory.domain.models import MemoryEntry, MemoryType
from sona_memory.infrastructure.embedding_service import EmbeddingService
from sona_memory.infrastructure.semantic_memory import SemanticConfig, SemanticMemory


def _make_entry(
    id: str, content: str = "fact", importance: float = 0.5, tags: tuple[str, ...] = ()
) -> MemoryEntry:
    return MemoryEntry(
        id=id,
        memory_type=MemoryType.SEMANTIC,
        content=content,
        importance=importance,
        tags=tags,
    )


@pytest.fixture
def embedding_service() -> EmbeddingService:
    return EmbeddingService(dim=64)


@pytest.fixture
def sm(embedding_service: EmbeddingService) -> SemanticMemory:
    return SemanticMemory(embedding_service=embedding_service)


class TestSemanticStore:
    """Tests for storing semantic memories."""

    @pytest.mark.asyncio
    async def test_store_and_get(self, sm: SemanticMemory) -> None:
        entry = _make_entry("s1", "Python is a programming language")
        await sm.store("user1", entry)
        result = await sm.get("user1", "s1")
        assert result is not None
        assert result.content == "Python is a programming language"

    @pytest.mark.asyncio
    async def test_store_generates_embedding(self, sm: SemanticMemory) -> None:
        entry = _make_entry("s1", "factual knowledge")
        await sm.store("user1", entry)
        result = await sm.get("user1", "s1")
        assert result is not None
        assert result.embedding is not None
        assert len(result.embedding) == 64

    @pytest.mark.asyncio
    async def test_store_sets_high_importance(self, sm: SemanticMemory) -> None:
        entry = _make_entry("s1")  # default importance 0.5
        await sm.store("user1", entry)
        result = await sm.get("user1", "s1")
        assert result is not None
        assert result.importance == 0.8  # default semantic importance

    @pytest.mark.asyncio
    async def test_store_forces_semantic_type(self, sm: SemanticMemory) -> None:
        entry = MemoryEntry(id="s1", memory_type=MemoryType.WORKING, content="fact")
        await sm.store("user1", entry)
        result = await sm.get("user1", "s1")
        assert result is not None
        assert result.memory_type == MemoryType.SEMANTIC

    @pytest.mark.asyncio
    async def test_store_returns_id(self, sm: SemanticMemory) -> None:
        result = await sm.store("user1", _make_entry("s1"))
        assert result == "s1"

    @pytest.mark.asyncio
    async def test_deduplication(self, embedding_service: EmbeddingService) -> None:
        config = SemanticConfig(dedup_threshold=0.99)
        sm = SemanticMemory(embedding_service=embedding_service, config=config)
        # Store same content twice
        await sm.store("user1", _make_entry("s1", "exact same content"))
        await sm.store("user1", _make_entry("s2", "exact same content"))
        # Should not duplicate
        assert await sm.count("user1") == 1


class TestSemanticSearch:
    """Tests for similarity-based retrieval."""

    @pytest.mark.asyncio
    async def test_search_finds_relevant(self, sm: SemanticMemory) -> None:
        await sm.store("user1", _make_entry("s1", "earth orbits the sun"))
        await sm.store("user1", _make_entry("s2", "water boils at 100 degrees"))
        results = await sm.search("user1", "earth orbits the sun")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_respects_top_k(self, sm: SemanticMemory) -> None:
        for i in range(10):
            await sm.store("user1", _make_entry(f"s{i}", f"fact number {i}"))
        results = await sm.search("user1", "fact", top_k=3)
        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_search_empty(self, sm: SemanticMemory) -> None:
        results = await sm.search("user1", "anything")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_min_importance(self, sm: SemanticMemory) -> None:
        await sm.store("user1", _make_entry("low", "low fact", importance=0.2))
        await sm.store("user1", _make_entry("high", "high fact", importance=0.9))
        results = await sm.search("user1", "fact", min_importance=0.5)
        ids = [r[0].id for r in results]
        assert "low" not in ids


class TestSemanticOperations:
    """Tests for various operations."""

    @pytest.mark.asyncio
    async def test_get_by_tags(self, sm: SemanticMemory) -> None:
        await sm.store("user1", _make_entry("s1", "python fact", tags=("programming",)))
        await sm.store("user1", _make_entry("s2", "cooking fact", tags=("food",)))
        results = await sm.get_by_tags("user1", {"programming"})
        assert len(results) == 1
        assert results[0].id == "s1"

    @pytest.mark.asyncio
    async def test_remove(self, sm: SemanticMemory) -> None:
        await sm.store("user1", _make_entry("s1"))
        assert await sm.remove("user1", "s1") is True
        assert await sm.get("user1", "s1") is None

    @pytest.mark.asyncio
    async def test_remove_nonexistent(self, sm: SemanticMemory) -> None:
        assert await sm.remove("user1", "s99") is False

    @pytest.mark.asyncio
    async def test_count(self, sm: SemanticMemory) -> None:
        assert await sm.count("user1") == 0
        await sm.store("user1", _make_entry("s1", "unique content"))
        assert await sm.count("user1") == 1

    @pytest.mark.asyncio
    async def test_clear(self, sm: SemanticMemory) -> None:
        await sm.store("user1", _make_entry("s1", "unique1"))
        await sm.store("user1", _make_entry("s2", "unique2"))
        count = await sm.clear("user1")
        assert count == 2
        assert await sm.count("user1") == 0

    @pytest.mark.asyncio
    async def test_get_all(self, sm: SemanticMemory) -> None:
        await sm.store("user1", _make_entry("s1", "fact1"))
        await sm.store("user1", _make_entry("s2", "fact2"))
        results = await sm.get_all("user1")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_no_temporal_decay(self, sm: SemanticMemory) -> None:
        """Semantic memory should persist without expiration."""
        entry = _make_entry("s1", "permanent fact")
        await sm.store("user1", entry)
        result = await sm.get("user1", "s1")
        assert result is not None
