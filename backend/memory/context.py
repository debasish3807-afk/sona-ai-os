"""Memory context assembly for AI operations.

This module defines the context assembly framework which combines memories
from multiple tiers (working, short-term, long-term, knowledge) into a
unified context suitable for AI model input. The assembler manages token
budgets, relevance filtering, and source diversity.

Context assembly is the critical bridge between stored memories and AI
operations - it determines what the model "knows" for any given interaction.

Classes:
    MemoryContextConfig: Configuration for context assembly.
    MemoryContextEntry: A single entry in an assembled context.
    AssembledMemoryContext: Complete assembled context ready for AI input.
    MemoryContextAssembler: Abstract interface for context assembly operations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from .types import MemoryType


@dataclass(frozen=True, slots=True)
class MemoryContextConfig:
    """Configuration for context assembly operations.

    Controls which memory tiers to include, token budgets, relevance
    thresholds, and diversity settings.

    Attributes:
        max_tokens: Maximum total token count for the assembled context.
        include_working: Whether to include working memory entries.
        include_short_term: Whether to include short-term memory entries.
        include_long_term: Whether to include long-term memory entries.
        include_knowledge: Whether to include knowledge base entries.
        include_conversation: Whether to include conversation history.
        relevance_threshold: Minimum relevance score for inclusion (0.0-1.0).
        max_entries: Maximum number of entries in the assembled context.
        diversity_factor: Factor for source diversity (0.0 = pure relevance, 1.0 = max diversity).
        recency_boost: Boost factor for more recent entries (0.0 = no boost).
    """

    max_tokens: int = 4096
    include_working: bool = True
    include_short_term: bool = True
    include_long_term: bool = True
    include_knowledge: bool = True
    include_conversation: bool = True
    relevance_threshold: float = 0.3
    max_entries: int = 50
    diversity_factor: float = 0.2
    recency_boost: float = 0.1


@dataclass(frozen=True, slots=True)
class MemoryContextEntry:
    """A single entry in an assembled context.

    Represents one piece of memory content that has been selected for
    inclusion in the AI context, with metadata about its source and relevance.

    Attributes:
        source_type: The memory type this entry came from.
        content: The text content to include in context.
        relevance: Relevance score for this entry relative to the query.
        token_count: Estimated token count of this entry's content.
        entry_id: The original memory entry ID for traceability.
        metadata: Additional context about this entry.
    """

    source_type: MemoryType
    content: str
    relevance: float
    token_count: int
    entry_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AssembledMemoryContext:
    """Complete assembled context ready for AI model input.

    Contains the selected memory entries along with assembly metadata
    for debugging and optimization.

    Attributes:
        entries: Ordered list of context entries to provide to the model.
        total_tokens: Total token count across all entries.
        sources_queried: List of memory types that were queried during assembly.
        assembly_time_ms: Time taken to assemble the context in milliseconds.
        truncated: Whether the context was truncated to fit token budget.
        metadata: Additional assembly metadata.
    """

    entries: list[MemoryContextEntry]
    total_tokens: int
    sources_queried: list[MemoryType]
    assembly_time_ms: float = 0.0
    truncated: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class MemoryContextAssembler(ABC):
    """Abstract interface for memory context assembly operations.

    Implementations coordinate retrieval from multiple memory tiers,
    apply relevance scoring and diversity, and trim the result to
    fit within the configured token budget.
    """

    @abstractmethod
    async def assemble(
        self,
        session_id: str,
        query: str,
        config: MemoryContextConfig | None = None,
    ) -> AssembledMemoryContext:
        """Assemble a complete context for an AI operation.

        Queries multiple memory tiers, scores results by relevance,
        applies diversity and recency factors, and trims to budget.

        Args:
            session_id: The session to assemble context for.
            query: The query or current user input for relevance scoring.
            config: Optional assembly configuration (uses defaults if None).

        Returns:
            The assembled context with entries and metadata.
        """
        ...

    @abstractmethod
    async def get_relevant_memories(
        self,
        query: str,
        memory_types: list[MemoryType] | None = None,
        limit: int = 20,
    ) -> list[MemoryContextEntry]:
        """Get relevant memories from specified tiers without full assembly.

        A lighter-weight operation that retrieves relevant entries
        without the full assembly pipeline (no token budgeting).

        Args:
            query: The query for relevance scoring.
            memory_types: Optional filter to specific memory types.
            limit: Maximum number of entries to return.

        Returns:
            List of relevant memory context entries.
        """
        ...

    @abstractmethod
    async def estimate_tokens(self, content: str) -> int:
        """Estimate the token count of a text string.

        Args:
            content: The text content to estimate tokens for.

        Returns:
            Estimated token count.
        """
        ...

    @abstractmethod
    async def trim_context(
        self, context: AssembledMemoryContext, max_tokens: int
    ) -> AssembledMemoryContext:
        """Trim an assembled context to fit within a token budget.

        Removes lower-relevance entries until the total token count
        is within the specified budget.

        Args:
            context: The assembled context to trim.
            max_tokens: The target maximum token count.

        Returns:
            A new trimmed context with entries removed as needed.
        """
        ...
