"""Working memory - current session context buffer.

This module defines the working memory interface which manages the active
context for current operations. Working memory is the fastest-access tier,
holding information actively being used in the current session with strict
token budgets and automatic eviction.

Working memory corresponds to the cognitive concept of items currently
held in attention - it is limited in capacity, volatile, and serves as
the bridge between the user's current interaction and long-term storage.

Classes:
    EvictionMode: Strategy for evicting entries when at capacity.
    WorkingMemoryConfig: Configuration for working memory behavior.
    WorkingMemory: Abstract interface extending MemoryStore for working memory.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum

from .base import MemoryStore
from .types import MemoryEntry


class EvictionMode(str, Enum):
    """Strategy for evicting entries from working memory when at capacity.

    Attributes:
        FIFO: First-in, first-out - evict oldest entries first.
        IMPORTANCE: Evict lowest importance entries first.
        TOKEN_BUDGET: Evict entries that are least token-efficient.
        RELEVANCE: Evict entries least relevant to current context.
    """

    FIFO = "fifo"
    IMPORTANCE = "importance"
    TOKEN_BUDGET = "token_budget"
    RELEVANCE = "relevance"


@dataclass(frozen=True, slots=True)
class WorkingMemoryConfig:
    """Configuration for working memory behavior.

    Controls capacity limits, eviction behavior, and token budgeting
    for the working memory tier.

    Attributes:
        max_entries: Maximum number of entries held in working memory.
        max_tokens: Maximum total token count across all working memory entries.
        auto_evict: Whether to automatically evict when capacity is reached.
        eviction_strategy: Strategy for selecting entries to evict.
        preserve_pinned: Whether pinned entries are exempt from eviction.
        session_isolated: Whether working memory is isolated per session.
    """

    max_entries: int = 50
    max_tokens: int = 4096
    auto_evict: bool = True
    eviction_strategy: EvictionMode = EvictionMode.FIFO
    preserve_pinned: bool = True
    session_isolated: bool = True


class WorkingMemory(MemoryStore):
    """Abstract interface for working memory operations.

    Extends the base MemoryStore with session-aware context management,
    token budgeting, and trimming operations specific to working memory.

    Working memory provides the active context window for AI operations,
    managing what information is immediately available without requiring
    a search operation.
    """

    @abstractmethod
    async def get_context(self, session_id: str) -> list[MemoryEntry]:
        """Get all working memory entries for a specific session.

        Returns the current context buffer for the given session,
        ordered by relevance or insertion time.

        Args:
            session_id: The session identifier to get context for.

        Returns:
            List of memory entries in the session's working memory.
        """
        ...

    @abstractmethod
    async def add_to_context(self, session_id: str, entry: MemoryEntry) -> None:
        """Add a memory entry to a session's working memory context.

        If adding this entry would exceed capacity, auto-eviction may
        be triggered depending on configuration.

        Args:
            session_id: The session to add the entry to.
            entry: The memory entry to add to working memory.

        Raises:
            MemoryCapacityError: If capacity is exceeded and auto_evict is False.
        """
        ...

    @abstractmethod
    async def clear_context(self, session_id: str) -> None:
        """Clear all working memory entries for a specific session.

        Removes all entries from the session's working memory buffer.
        This is typically called when a session ends or is reset.

        Args:
            session_id: The session whose context should be cleared.
        """
        ...

    @abstractmethod
    async def get_token_count(self, session_id: str) -> int:
        """Get the total token count of a session's working memory.

        Args:
            session_id: The session to count tokens for.

        Returns:
            Total estimated token count across all entries in the session.
        """
        ...

    @abstractmethod
    async def trim_to_budget(self, session_id: str, max_tokens: int) -> int:
        """Trim working memory to fit within a token budget.

        Removes entries (per eviction strategy) until the total token
        count is within the specified budget.

        Args:
            session_id: The session to trim.
            max_tokens: The target maximum token count.

        Returns:
            Number of entries that were removed to meet the budget.
        """
        ...
