"""Unit tests for memory consolidation service."""

import pytest

from sona_memory.domain.models import MemoryEntry, MemoryType
from sona_memory.infrastructure.consolidation import ConsolidationService
from sona_memory.infrastructure.embedding_service import EmbeddingService
from sona_memory.infrastructure.long_term_memory import LongTermMemory
from sona_memory.infrastructure.short_term_memory import ShortTermConfig, ShortTermMemory


def _make_entry(id: str, content: str = "test", importance: float = 0.8) -> MemoryEntry:
    return MemoryEntry(
        id=id,
        memory_type=MemoryType.SHORT_TERM,
        content=content,
        importance=importance,
    )


@pytest.fixture
def embedding_service() -> EmbeddingService:
    return EmbeddingService(dim=64)


@pytest.fixture
def short_term() -> ShortTermMemory:
    config = ShortTermConfig(consolidation_threshold=0.7)
    return ShortTermMemory(config=config)


@pytest.fixture
def long_term(embedding_service: EmbeddingService) -> LongTermMemory:
    return LongTermMemory(embedding_service=embedding_service)


@pytest.fixture
def consolidation(
    short_term: ShortTermMemory,
    long_term: LongTermMemory,
    embedding_service: EmbeddingService,
) -> ConsolidationService:
    return ConsolidationService(
        short_term=short_term,
        long_term=long_term,
        embedding_service=embedding_service,
    )


class TestConsolidateBasic:
    """Tests for basic consolidation behavior."""

    @pytest.mark.asyncio
    async def test_promotes_high_importance(
        self,
        short_term: ShortTermMemory,
        long_term: LongTermMemory,
        consolidation: ConsolidationService,
    ) -> None:
        await short_term.store("user1", _make_entry("m1", "important fact", importance=0.9))
        count = await consolidation.consolidate("user1")
        assert count == 1
        # Should be in long-term now
        assert await long_term.count("user1") == 1
        # Should be removed from short-term
        assert await short_term.count("user1") == 0

    @pytest.mark.asyncio
    async def test_does_not_promote_low_importance(
        self,
        short_term: ShortTermMemory,
        long_term: LongTermMemory,
        consolidation: ConsolidationService,
    ) -> None:
        await short_term.store("user1", _make_entry("m1", importance=0.3))
        count = await consolidation.consolidate("user1")
        assert count == 0
        assert await long_term.count("user1") == 0
        assert await short_term.count("user1") == 1

    @pytest.mark.asyncio
    async def test_consolidate_empty(self, consolidation: ConsolidationService) -> None:
        count = await consolidation.consolidate("user1")
        assert count == 0

    @pytest.mark.asyncio
    async def test_consolidate_multiple(
        self,
        short_term: ShortTermMemory,
        long_term: LongTermMemory,
        consolidation: ConsolidationService,
    ) -> None:
        await short_term.store("user1", _make_entry("m1", "fact1", importance=0.8))
        await short_term.store("user1", _make_entry("m2", "fact2", importance=0.9))
        await short_term.store("user1", _make_entry("m3", "low", importance=0.3))
        count = await consolidation.consolidate("user1")
        assert count == 2
        assert await long_term.count("user1") == 2
        assert await short_term.count("user1") == 1


class TestConsolidateDedup:
    """Tests for deduplication during consolidation."""

    @pytest.mark.asyncio
    async def test_dedup_against_existing(
        self,
        short_term: ShortTermMemory,
        long_term: LongTermMemory,
        consolidation: ConsolidationService,
    ) -> None:
        # First store in long-term
        lt_entry = MemoryEntry(
            id="existing",
            memory_type=MemoryType.LONG_TERM,
            content="same content here",
        )
        await long_term.store("user1", lt_entry)

        # Then try to consolidate identical content
        await short_term.store("user1", _make_entry("dup", "same content here", importance=0.8))
        count = await consolidation.consolidate("user1")
        # Should merge (not promote as new)
        assert count == 0
        assert await long_term.count("user1") == 1

    @pytest.mark.asyncio
    async def test_promotes_unique_content(
        self,
        short_term: ShortTermMemory,
        long_term: LongTermMemory,
        consolidation: ConsolidationService,
    ) -> None:
        lt_entry = MemoryEntry(
            id="existing",
            memory_type=MemoryType.LONG_TERM,
            content="original content",
        )
        await long_term.store("user1", lt_entry)

        await short_term.store(
            "user1", _make_entry("new", "completely different content", importance=0.8)
        )
        count = await consolidation.consolidate("user1")
        assert count == 1
        assert await long_term.count("user1") == 2


class TestMergeSimilar:
    """Tests for merging similar entries."""

    @pytest.mark.asyncio
    async def test_merge_similar_removes_duplicates(
        self,
        long_term: LongTermMemory,
        consolidation: ConsolidationService,
    ) -> None:
        # Store two identical entries
        await long_term.store(
            "user1",
            MemoryEntry(
                id="m1",
                memory_type=MemoryType.LONG_TERM,
                content="exact same text",
                importance=0.8,
            ),
        )
        await long_term.store(
            "user1",
            MemoryEntry(
                id="m2",
                memory_type=MemoryType.LONG_TERM,
                content="exact same text",
                importance=0.6,
            ),
        )
        merged = await consolidation.merge_similar("user1")
        assert merged == 1
        # Should keep the more important one
        remaining = await long_term.get_all("user1")
        assert len(remaining) == 1
        assert remaining[0].importance == 0.8

    @pytest.mark.asyncio
    async def test_merge_keeps_unique(
        self,
        long_term: LongTermMemory,
        consolidation: ConsolidationService,
    ) -> None:
        await long_term.store(
            "user1",
            MemoryEntry(
                id="m1",
                memory_type=MemoryType.LONG_TERM,
                content="python programming",
            ),
        )
        await long_term.store(
            "user1",
            MemoryEntry(
                id="m2",
                memory_type=MemoryType.LONG_TERM,
                content="cooking dinner tonight",
            ),
        )
        merged = await consolidation.merge_similar("user1")
        assert merged == 0


class TestComputeImportance:
    """Tests for importance computation."""

    @pytest.mark.asyncio
    async def test_base_importance(self, consolidation: ConsolidationService) -> None:
        entry = _make_entry("m1", importance=0.5)
        score = await consolidation.compute_importance(entry)
        assert score >= 0.5
        assert score <= 1.0

    @pytest.mark.asyncio
    async def test_long_content_boost(self, consolidation: ConsolidationService) -> None:
        short_entry = _make_entry("m1", "short", importance=0.5)
        long_entry = _make_entry("m2", "x" * 600, importance=0.5)
        short_score = await consolidation.compute_importance(short_entry)
        long_score = await consolidation.compute_importance(long_entry)
        assert long_score > short_score

    @pytest.mark.asyncio
    async def test_tags_boost(self, consolidation: ConsolidationService) -> None:
        no_tags = _make_entry("m1", importance=0.5)
        with_tags = MemoryEntry(
            id="m2",
            memory_type=MemoryType.SHORT_TERM,
            content="test",
            importance=0.5,
            tags=("important", "meeting"),
        )
        score_no = await consolidation.compute_importance(no_tags)
        score_tags = await consolidation.compute_importance(with_tags)
        assert score_tags > score_no

    @pytest.mark.asyncio
    async def test_importance_capped_at_one(self, consolidation: ConsolidationService) -> None:
        entry = MemoryEntry(
            id="m1",
            memory_type=MemoryType.SHORT_TERM,
            content="x" * 1000,
            importance=0.95,
            tags=("a", "b", "c", "d"),
            metadata={"key": "val"},
        )
        score = await consolidation.compute_importance(entry)
        assert score <= 1.0
