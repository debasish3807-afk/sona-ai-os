"""Memory retrieval engine.

Orchestrates retrieval across all memory types, merging results
and applying unified ranking.
"""

import asyncio
from dataclasses import dataclass

import structlog

from sona_memory.domain.models import MemoryEntry, MemoryQuery, MemoryType
from sona_memory.domain.scoring import RelevanceScore
from sona_memory.infrastructure.conversation_memory import ConversationMemory
from sona_memory.infrastructure.embedding_service import EmbeddingService
from sona_memory.infrastructure.episodic_memory import EpisodicMemory
from sona_memory.infrastructure.long_term_memory import LongTermMemory
from sona_memory.infrastructure.ranking import MemoryRanker
from sona_memory.infrastructure.semantic_memory import SemanticMemory
from sona_memory.infrastructure.short_term_memory import ShortTermMemory
from sona_memory.infrastructure.working_memory import WorkingMemoryManager

logger = structlog.get_logger()


@dataclass
class RetrievalResult:
    """Result of a retrieval operation with scores."""

    entries: list[MemoryEntry]
    scores: list[RelevanceScore]


class RetrievalEngine:
    """Orchestrates retrieval across all memory subsystems.

    Queries appropriate memory stores based on the query parameters,
    merges results, applies unified ranking, and respects top_k limits.
    """

    def __init__(
        self,
        working_memory: WorkingMemoryManager,
        short_term_memory: ShortTermMemory,
        long_term_memory: LongTermMemory,
        episodic_memory: EpisodicMemory,
        semantic_memory: SemanticMemory,
        conversation_memory: ConversationMemory,
        embedding_service: EmbeddingService,
        ranker: MemoryRanker,
    ) -> None:
        self._working = working_memory
        self._short_term = short_term_memory
        self._long_term = long_term_memory
        self._episodic = episodic_memory
        self._semantic = semantic_memory
        self._conversation = conversation_memory
        self._embedding = embedding_service
        self._ranker = ranker

    async def retrieve(self, query: MemoryQuery) -> RetrievalResult:
        """Execute a retrieval across all relevant memory types.

        Args:
            query: The memory query with filters and parameters.

        Returns:
            RetrievalResult with ranked entries and scores.
        """
        # Determine which memory types to query
        types_to_query = query.memory_types or list(MemoryType)

        # Gather candidates from all relevant stores
        candidates: list[MemoryEntry] = []

        # Create tasks for parallel retrieval
        tasks: list[asyncio.Task[list[MemoryEntry]]] = []

        if MemoryType.WORKING in types_to_query:
            tasks.append(asyncio.create_task(self._get_working(query.user_id)))
        if MemoryType.SHORT_TERM in types_to_query:
            tasks.append(
                asyncio.create_task(self._get_short_term(query.user_id, query.min_importance))
            )
        if MemoryType.LONG_TERM in types_to_query:
            tasks.append(asyncio.create_task(self._get_long_term(query.user_id, query.query)))
        if MemoryType.EPISODIC in types_to_query:
            tasks.append(asyncio.create_task(self._get_episodic(query)))
        if MemoryType.SEMANTIC in types_to_query:
            tasks.append(asyncio.create_task(self._get_semantic(query.user_id, query.query)))

        # Await all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, list):
                candidates.extend(result)
            elif isinstance(result, Exception):
                logger.warning("retrieval_error", error=str(result))

        # Filter by min_importance
        if query.min_importance > 0:
            candidates = [e for e in candidates if e.importance >= query.min_importance]

        # Filter by time range
        if query.time_range:
            start, end = query.time_range
            candidates = [
                e for e in candidates if e.created_at is not None and start <= e.created_at <= end
            ]

        # Generate query embedding for ranking
        query_embedding = await self._embedding.embed(query.query) if query.query else None

        # Rank all candidates
        scores = self._ranker.rank(candidates, query_embedding=query_embedding)

        # Apply top_k
        top_scores = scores[: query.top_k]
        top_ids = {s.memory_id for s in top_scores}
        top_entries = [e for e in candidates if e.id in top_ids]

        # Sort entries to match score order
        id_to_entry = {e.id: e for e in top_entries}
        sorted_entries = [
            id_to_entry[s.memory_id] for s in top_scores if s.memory_id in id_to_entry
        ]

        return RetrievalResult(entries=sorted_entries, scores=top_scores)

    async def _get_working(self, user_id: str) -> list[MemoryEntry]:
        """Retrieve from working memory."""
        return await self._working.get_all(user_id)

    async def _get_short_term(self, user_id: str, min_importance: float) -> list[MemoryEntry]:
        """Retrieve from short-term memory."""
        return await self._short_term.get_by_importance(user_id, min_importance)

    async def _get_long_term(self, user_id: str, query_text: str) -> list[MemoryEntry]:
        """Retrieve from long-term memory using similarity search."""
        results = await self._long_term.search(user_id, query_text)
        return [entry for entry, _ in results]

    async def _get_episodic(self, query: MemoryQuery) -> list[MemoryEntry]:
        """Retrieve from episodic memory."""
        if query.time_range:
            start, end = query.time_range
            return await self._episodic.get_by_time_range(query.user_id, start, end)
        return await self._episodic.get_recent(query.user_id, limit=50)

    async def _get_semantic(self, user_id: str, query_text: str) -> list[MemoryEntry]:
        """Retrieve from semantic memory using similarity search."""
        results = await self._semantic.search(user_id, query_text)
        return [entry for entry, _ in results]
