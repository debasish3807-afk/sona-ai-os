"""Short-term memory - recent interactions (hours/days).

This module defines the short-term memory interface which manages recently
acquired information that hasn't yet been consolidated into long-term storage.
Short-term memory bridges the gap between volatile working memory and
persistent long-term memory.

Entries in short-term memory represent recent interactions, decisions, and
context from the past hours or days. They are candidates for promotion to
long-term memory or consolidation.

Classes:
    ShortTermConfig: Configuration for short-term memory behavior.
    ShortTermMemory: Abstract interface extending MemoryStore for short-term memory.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from .base import MemoryStore
from .types import MemoryEntry, MemoryScope


class ShortTermConfig:
    """Configuration for short-term memory behavior.

    Controls retention duration, capacity limits, and automatic
    consolidation triggers.

    Attributes:
        max_age_hours: Maximum age in hours before entries become consolidation candidates.
        max_entries: Maximum number of entries in short-term memory.
        auto_consolidate: Whether to automatically consolidate older entries.
        consolidation_threshold: Number of entries that triggers auto-consolidation.
        promote_threshold: Importance score above which entries auto-promote to long-term.
        default_scope: Default scope for new short-term entries.
    """

    def __init__(
        self,
        max_age_hours: int = 72,
        max_entries: int = 1000,
        auto_consolidate: bool = True,
        consolidation_threshold: int = 100,
        promote_threshold: float = 0.8,
        default_scope: MemoryScope = MemoryScope.SESSION,
    ) -> None:
        """Initialize short-term memory configuration.

        Args:
            max_age_hours: Maximum age in hours before consolidation.
            max_entries: Maximum number of entries.
            auto_consolidate: Whether to auto-consolidate.
            consolidation_threshold: Entry count trigger for consolidation.
            promote_threshold: Importance score for auto-promotion.
            default_scope: Default scope for new entries.
        """
        self.max_age_hours = max_age_hours
        self.max_entries = max_entries
        self.auto_consolidate = auto_consolidate
        self.consolidation_threshold = consolidation_threshold
        self.promote_threshold = promote_threshold
        self.default_scope = default_scope


class ShortTermMemory(MemoryStore):
    """Abstract interface for short-term memory operations.

    Extends the base MemoryStore with temporal retrieval, session-based
    access, promotion to long-term storage, and expiration management.
    """

    @abstractmethod
    async def get_recent(
        self,
        scope: Optional[MemoryScope] = None,
        hours: int = 24,
        limit: int = 50,
    ) -> list[MemoryEntry]:
        """Get the most recent entries within a time window.

        Args:
            scope: Optional scope filter.
            hours: Number of hours to look back.
            limit: Maximum number of entries to return.

        Returns:
            List of recent memory entries ordered by recency.
        """
        ...

    @abstractmethod
    async def get_by_session(
        self, session_id: str, limit: int = 50
    ) -> list[MemoryEntry]:
        """Get all short-term memory entries from a specific session.

        Args:
            session_id: The session identifier to filter by.
            limit: Maximum number of entries to return.

        Returns:
            List of memory entries from the specified session.
        """
        ...

    @abstractmethod
    async def promote_to_long_term(self, entry_id: str) -> bool:
        """Promote a short-term memory entry to long-term storage.

        Marks the entry for migration to long-term memory. The actual
        migration may be immediate or deferred depending on implementation.

        Args:
            entry_id: The ID of the entry to promote.

        Returns:
            True if the entry was found and promoted, False otherwise.
        """
        ...

    @abstractmethod
    async def get_expiring(self, within_hours: int = 4) -> list[MemoryEntry]:
        """Get entries that will expire within the specified time window.

        Useful for identifying entries that need attention before they
        are automatically cleaned up.

        Args:
            within_hours: Number of hours to look ahead for expiring entries.

        Returns:
            List of entries that will expire within the time window.
        """
        ...
