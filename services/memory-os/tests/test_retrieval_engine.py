"""Unit tests for the retrieval engine."""

from datetime import UTC, datetime, timedelta

import pytest

from sona_memory.domain.models import MemoryEntry, MemoryQuery, MemoryType
from sona_memory.infrastructure.conversation_memory import ConversationMemory
from sona_memory.infrastructure.embedding_service import EmbeddingService
from sona_memory.infrastructure.episodic_memory import EpisodicMemory
from sona_memory.infrastructure.long_term_memory import LongTermMemory
from sona_memory.infrastructure.ranking import MemoryRanker
from sona_memory.infrastructure.retrieval_engine import RetrievalEngine
from sona_memory.infrastructure.semantic_memory import SemanticMemory
from sona_memory.infrastructure.short_term_memory import ShortTermMemory
from sona_memory.infrastructure.working_memory import WorkingMemoryManager


@pytest.fixture
def embedding_service() -> EmbeddingService:
    return EmbeddingService(dim=64)


@pytest.fixture
def engine(embedding_service: EmbeddingService) -> RetrievalEngine:
    return RetrievalEngine(
        working_memory=WorkingMemoryManager(),
        short_term_memory=ShortTermMemory(),
        long_term_memory=LongTermMemory(embedding_service=embedding_service),
        episodic_memory=EpisodicMemory(),
        semantic_memory=SemanticMemory(embedding_service=embedding_service),
        conversation_memory=ConversationMemory(),
        embedding_service=embedding_service,
        ranker=MemoryRanker(),
    )


class TestRetrievalBasic:
    """Tests for basic retrieval."""

    @pytest.mark.asyncio
    async def test_retrieve_from_working(self, engine: RetrievalEngine) -> None:
        entry = MemoryEntry(
            id="w1",
            memory_type=MemoryType.WORKING,
            content="in working",
            importance=0.5,
        )
        await engine._working.store("user1", entry)
        query = MemoryQuery(
            user_id="user1",
            query="working",
            memory_types=[MemoryType.WORKING],
        )
        result = await engine.retrieve(query)
        assert len(result.entries) >= 1

    @pytest.mark.asyncio
    async def test_retrieve_from_short_term(self, engine: RetrievalEngine) -> None:
        entry = MemoryEntry(
            id="st1",
            memory_type=MemoryType.SHORT_TERM,
            content="short term",
            importance=0.6,
        )
        await engine._short_term.store("user1", entry)
        query = MemoryQuery(
            user_id="user1",
            query="short",
            memory_types=[MemoryType.SHORT_TERM],
        )
        result = await engine.retrieve(query)
        assert len(result.entries) >= 1

    @pytest.mark.asyncio
    async def test_retrieve_from_long_term(self, engine: RetrievalEngine) -> None:
        entry = MemoryEntry(
            id="lt1",
            memory_type=MemoryType.LONG_TERM,
            content="python programming language",
        )
        await engine._long_term.store("user1", entry)
        query = MemoryQuery(
            user_id="user1",
            query="python programming language",
            memory_types=[MemoryType.LONG_TERM],
        )
        result = await engine.retrieve(query)
        assert len(result.entries) >= 1

    @pytest.mark.asyncio
    async def test_retrieve_empty(self, engine: RetrievalEngine) -> None:
        query = MemoryQuery(user_id="user1", query="nothing")
        result = await engine.retrieve(query)
        assert result.entries == []

    @pytest.mark.asyncio
    async def test_retrieve_respects_top_k(self, engine: RetrievalEngine) -> None:
        for i in range(10):
            entry = MemoryEntry(
                id=f"w{i}",
                memory_type=MemoryType.WORKING,
                content=f"entry {i}",
                importance=0.5,
            )
            await engine._working.store("user1", entry)
        query = MemoryQuery(
            user_id="user1",
            query="entry",
            top_k=3,
            memory_types=[MemoryType.WORKING],
        )
        result = await engine.retrieve(query)
        assert len(result.entries) <= 3


class TestRetrievalCrossType:
    """Tests for cross-type retrieval and merging."""

    @pytest.mark.asyncio
    async def test_merges_multiple_types(self, engine: RetrievalEngine) -> None:
        await engine._working.store(
            "user1",
            MemoryEntry(
                id="w1",
                memory_type=MemoryType.WORKING,
                content="working entry",
                importance=0.5,
            ),
        )
        await engine._short_term.store(
            "user1",
            MemoryEntry(
                id="st1",
                memory_type=MemoryType.SHORT_TERM,
                content="short entry",
                importance=0.6,
            ),
        )
        query = MemoryQuery(
            user_id="user1",
            query="entry",
            memory_types=[MemoryType.WORKING, MemoryType.SHORT_TERM],
            top_k=10,
        )
        result = await engine.retrieve(query)
        assert len(result.entries) == 2

    @pytest.mark.asyncio
    async def test_all_types_when_none_specified(self, engine: RetrievalEngine) -> None:
        await engine._working.store(
            "user1",
            MemoryEntry(
                id="w1",
                memory_type=MemoryType.WORKING,
                content="a",
                importance=0.5,
            ),
        )
        query = MemoryQuery(user_id="user1", query="a")
        result = await engine.retrieve(query)
        assert len(result.entries) >= 1


class TestRetrievalFiltering:
    """Tests for filtering during retrieval."""

    @pytest.mark.asyncio
    async def test_min_importance_filter(self, engine: RetrievalEngine) -> None:
        await engine._working.store(
            "user1",
            MemoryEntry(
                id="low",
                memory_type=MemoryType.WORKING,
                content="low",
                importance=0.1,
            ),
        )
        await engine._working.store(
            "user1",
            MemoryEntry(
                id="high",
                memory_type=MemoryType.WORKING,
                content="high",
                importance=0.9,
            ),
        )
        query = MemoryQuery(
            user_id="user1",
            query="test",
            min_importance=0.5,
            memory_types=[MemoryType.WORKING],
        )
        result = await engine.retrieve(query)
        ids = [e.id for e in result.entries]
        assert "low" not in ids

    @pytest.mark.asyncio
    async def test_time_range_filter(self, engine: RetrievalEngine) -> None:
        base = datetime(2024, 6, 1, tzinfo=UTC)
        await engine._working.store(
            "user1",
            MemoryEntry(
                id="old",
                memory_type=MemoryType.WORKING,
                content="old",
                importance=0.5,
                created_at=base - timedelta(days=30),
            ),
        )
        await engine._working.store(
            "user1",
            MemoryEntry(
                id="recent",
                memory_type=MemoryType.WORKING,
                content="recent",
                importance=0.5,
                created_at=base,
            ),
        )
        query = MemoryQuery(
            user_id="user1",
            query="test",
            time_range=(base - timedelta(days=1), base + timedelta(days=1)),
            memory_types=[MemoryType.WORKING],
        )
        result = await engine.retrieve(query)
        ids = [e.id for e in result.entries]
        assert "old" not in ids
        assert "recent" in ids


class TestRetrievalScores:
    """Tests for score generation."""

    @pytest.mark.asyncio
    async def test_scores_match_entries(self, engine: RetrievalEngine) -> None:
        await engine._working.store(
            "user1",
            MemoryEntry(
                id="w1",
                memory_type=MemoryType.WORKING,
                content="test",
                importance=0.7,
            ),
        )
        query = MemoryQuery(
            user_id="user1",
            query="test",
            memory_types=[MemoryType.WORKING],
        )
        result = await engine.retrieve(query)
        assert len(result.scores) == len(result.entries)
        if result.scores:
            assert result.scores[0].memory_id == result.entries[0].id
