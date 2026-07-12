"""Long-term memory - persistent user knowledge.

This module defines the long-term memory interface which manages persistent,
consolidated knowledge that has been deemed important enough to retain
indefinitely. Long-term memory entries have survived the consolidation process
and represent stable, high-value information.

Long-term memory corresponds to the cognitive concept of semantic and
episodic long-term storage - information that persists across sessions
and forms the basis of the system's accumulated knowledge.

Classes:
    LongTermConfig: Configuration for long-term memory behavior.
    LongTermMemory: Abstract interface extending MemoryStore for long-term memory.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass

from .base import MemoryStore
from .types import MemoryEntry


@dataclass(frozen=True, slots=True)
class LongTermConfig:
    """Configuration for long-term memory behavior.

    Controls capacity limits, consolidation scheduling, and importance
    decay parameters for long-term storage.

    Attributes:
        max_entries: Maximum number of entries in long-term memory.
        consolidation_interval_hours: How often to run consolidation (in hours).
        enable_decay: Whether to apply importance decay over time.
        decay_rate: Per-day decay rate for importance scores (0.0-1.0).
        min_importance_for_retention: Minimum importance to avoid cleanup.
        enable_knowledge_graph: Whether to maintain knowledge graph relationships.
    """

    max_entries: int = 100000
    consolidation_interval_hours: int = 24
    enable_decay: bool = True
    decay_rate: float = 0.001
    min_importance_for_retention: float = 0.1
    enable_knowledge_graph: bool = True


class LongTermMemory(MemoryStore):
    """Abstract interface for long-term memory operations.

    Extends the base MemoryStore with importance-based retrieval, topic
    search, consolidation of old entries, and knowledge graph access.
    """

    @abstractmethod
    async def get_by_importance(self, min_score: float = 0.5, limit: int = 50) -> list[MemoryEntry]:
        """Get entries above a minimum importance score.

        Retrieves the most important long-term memories, useful for
        providing high-value context to AI operations.

        Args:
            min_score: Minimum importance score threshold (0.0-1.0).
            limit: Maximum number of entries to return.

        Returns:
            List of entries meeting the importance threshold, ordered by score.
        """
        ...

    @abstractmethod
    async def get_by_topic(self, topic: str, limit: int = 20) -> list[MemoryEntry]:
        """Get entries related to a specific topic.

        Uses semantic matching to find memories relevant to the
        given topic string.

        Args:
            topic: The topic to search for.
            limit: Maximum number of entries to return.

        Returns:
            List of entries related to the topic, ordered by relevance.
        """
        ...

    @abstractmethod
    async def consolidate_old(self, older_than_days: int = 30) -> int:
        """Consolidate entries older than the specified age.

        Identifies entries older than the threshold and applies
        consolidation (summarization, merging, or archival).

        Args:
            older_than_days: Age threshold in days for consolidation.

        Returns:
            Number of entries that were consolidated.
        """
        ...

    @abstractmethod
    async def get_knowledge_graph_entries(self) -> list[MemoryEntry]:
        """Get all entries that are part of the knowledge graph.

        Returns entries that have relationships (semantic links, references,
        or explicit connections) to other entries.

        Returns:
            List of entries that participate in the knowledge graph.
        """
        ...
