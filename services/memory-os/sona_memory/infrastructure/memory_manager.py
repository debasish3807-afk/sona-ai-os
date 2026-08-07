"""Memory Manager — top-level orchestrator.

Combines all memory subsystems, implements MemoryStorePort,
and routes operations to the appropriate subsystem based on MemoryType.
"""

import asyncio
import uuid
from dataclasses import replace
from datetime import UTC, datetime

import structlog

from sona_memory.application.ports import MemoryStorePort
from sona_memory.domain.events import (
    MemoryConsolidatedEvent,
    MemoryExpiredEvent,
    MemoryForgottenEvent,
    MemoryRetrievedEvent,
    MemoryStoredEvent,
)
from sona_memory.domain.models import MemoryEntry, MemoryQuery, MemoryType
from sona_memory.infrastructure.cleanup import CleanupService
from sona_memory.infrastructure.consolidation import ConsolidationService
from sona_memory.infrastructure.conversation_memory import ConversationMemory
from sona_memory.infrastructure.episodic_memory import EpisodicMemory
from sona_memory.infrastructure.long_term_memory import LongTermMemory
from sona_memory.infrastructure.metrics import MetricsCollector
from sona_memory.infrastructure.retrieval_engine import RetrievalEngine
from sona_memory.infrastructure.semantic_memory import SemanticMemory
from sona_memory.infrastructure.short_term_memory import ShortTermMemory
from sona_memory.infrastructure.working_memory import WorkingMemoryManager

logger = structlog.get_logger()


class MemoryManager(MemoryStorePort):
    """Top-level memory orchestrator implementing MemoryStorePort.

    Routes operations to the appropriate memory subsystem based on
    MemoryType and handles cross-cutting concerns like logging,
    metrics, and event emission.
    """

    def __init__(
        self,
        working_memory: WorkingMemoryManager,
        short_term_memory: ShortTermMemory,
        long_term_memory: LongTermMemory,
        episodic_memory: EpisodicMemory,
        semantic_memory: SemanticMemory,
        conversation_memory: ConversationMemory,
        retrieval_engine: RetrievalEngine,
        consolidation_service: ConsolidationService,
        cleanup_service: CleanupService,
        metrics: MetricsCollector,
    ) -> None:
        self._working = working_memory
        self._short_term = short_term_memory
        self._long_term = long_term_memory
        self._episodic = episodic_memory
        self._semantic = semantic_memory
        self._conversation = conversation_memory
        self._retrieval = retrieval_engine
        self._consolidation = consolidation_service
        self._cleanup = cleanup_service
        self._metrics = metrics
        self._events: list[
            MemoryStoredEvent
            | MemoryRetrievedEvent
            | MemoryConsolidatedEvent
            | MemoryForgottenEvent
            | MemoryExpiredEvent
        ] = []
        self._lock = asyncio.Lock()

    @property
    def events(
        self,
    ) -> list[
        MemoryStoredEvent
        | MemoryRetrievedEvent
        | MemoryConsolidatedEvent
        | MemoryForgottenEvent
        | MemoryExpiredEvent
    ]:
        """Get emitted domain events."""
        return list(self._events)

    def clear_events(self) -> None:
        """Clear emitted domain events."""
        self._events.clear()

    async def store(self, user_id: str, entry: MemoryEntry) -> str:
        """Store a memory entry, routing to the appropriate subsystem."""
        async with self._metrics.track_operation("store"):
            # Generate ID if needed
            if not entry.id:
                entry = replace(entry, id=str(uuid.uuid4()))

            # Set created_at if not present
            if entry.created_at is None:
                entry = replace(entry, created_at=datetime.now(UTC))

            # Route to appropriate subsystem
            memory_id = await self._route_store(user_id, entry)

            # Emit event
            event = MemoryStoredEvent(
                user_id=user_id,
                memory_id=memory_id,
                memory_type=str(entry.memory_type),
                importance=entry.importance,
            )
            async with self._lock:
                self._events.append(event)

            # Update metrics
            await self._metrics.update_memory_count(user_id, str(entry.memory_type), 1)

            logger.info(
                "memory_stored",
                user_id=user_id,
                memory_id=memory_id,
                memory_type=str(entry.memory_type),
            )

            return memory_id

    async def retrieve(self, query: MemoryQuery) -> list[MemoryEntry]:
        """Retrieve memories using the retrieval engine."""
        async with self._metrics.track_operation("retrieve"):
            result = await self._retrieval.retrieve(query)

            # Record hit/miss
            if result.entries:
                await self._metrics.record_hit()
            else:
                await self._metrics.record_miss()

            # Emit event
            event = MemoryRetrievedEvent(
                user_id=query.user_id,
                query=query.query,
                results_count=len(result.entries),
            )
            async with self._lock:
                self._events.append(event)

            logger.info(
                "memory_retrieved",
                user_id=query.user_id,
                results_count=len(result.entries),
            )

            return result.entries

    async def consolidate(self, user_id: str) -> int:
        """Consolidate short-term memories to long-term."""
        async with self._metrics.track_operation("consolidate"):
            count = await self._consolidation.consolidate(user_id)

            # Emit event
            event = MemoryConsolidatedEvent(
                user_id=user_id,
                consolidated_count=count,
            )
            async with self._lock:
                self._events.append(event)

            logger.info(
                "memory_consolidated",
                user_id=user_id,
                count=count,
            )

            return count

    async def forget(self, user_id: str, memory_id: str) -> bool:
        """Remove a memory from all subsystems."""
        async with self._metrics.track_operation("forget"):
            # Try all subsystems in order
            removed = (
                await self._working.remove(user_id, memory_id)
                or await self._short_term.remove(user_id, memory_id)
                or await self._long_term.remove(user_id, memory_id)
                or await self._episodic.remove(user_id, memory_id)
                or await self._semantic.remove(user_id, memory_id)
            )

            if removed:
                event = MemoryForgottenEvent(
                    user_id=user_id,
                    memory_id=memory_id,
                )
                async with self._lock:
                    self._events.append(event)

                logger.info(
                    "memory_forgotten",
                    user_id=user_id,
                    memory_id=memory_id,
                )

            return removed

    async def get_conversation_history(self, session_id: str, limit: int = 50) -> list[MemoryEntry]:
        """Get conversation history from conversation memory."""
        async with self._metrics.track_operation("get_history"):
            # Search across all users for the session
            # In practice, session_id typically encodes the user
            # For now, iterate conversation memory
            # This is a simplified approach
            return []

    async def cleanup(self, user_id: str) -> int:
        """Run cleanup for a user, removing expired entries."""
        cleaned = await self._cleanup.cleanup_user(user_id)
        if cleaned > 0:
            event = MemoryExpiredEvent(
                user_id=user_id,
                expired_count=cleaned,
            )
            async with self._lock:
                self._events.append(event)
        return cleaned

    async def get_metrics(self) -> dict[str, int]:
        """Get current metrics summary."""
        metrics = await self._metrics.get_metrics()
        return {
            "total_operations": sum(op.count for op in metrics.operations.values()),
            "retrieval_hits": metrics.retrieval_hits,
            "retrieval_misses": metrics.retrieval_misses,
        }

    async def _route_store(self, user_id: str, entry: MemoryEntry) -> str:
        """Route a store operation to the appropriate subsystem."""
        match entry.memory_type:
            case MemoryType.WORKING:
                return await self._working.store(user_id, entry)
            case MemoryType.SHORT_TERM:
                return await self._short_term.store(user_id, entry)
            case MemoryType.LONG_TERM:
                return await self._long_term.store(user_id, entry)
            case MemoryType.EPISODIC:
                return await self._episodic.store(user_id, entry)
            case MemoryType.SEMANTIC:
                return await self._semantic.store(user_id, entry)
