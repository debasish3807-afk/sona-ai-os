"""Memory summarization interface.

This module defines the summarization framework for generating concise
representations of memory content. Summarization is used during consolidation,
context assembly, and conversation history management to reduce token usage
while preserving key information.

Classes:
    SummaryLevel: Enumeration of summarization detail levels.
    SummaryConfig: Configuration for a summarization operation.
    MemorySummary: The result of a summarization operation.
    MemorySummarizer: Abstract interface for summarization operations.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from .types import MemoryEntry


class SummaryLevel(str, Enum):
    """Enumeration of summarization detail levels.

    Controls how much detail is preserved in the generated summary.

    Attributes:
        BRIEF: One or two sentences capturing the essential point.
        STANDARD: A paragraph with key details preserved.
        DETAILED: Multiple paragraphs with most context retained.
        COMPREHENSIVE: Full reconstruction with minimal information loss.
    """

    BRIEF = "brief"
    STANDARD = "standard"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


@dataclass(frozen=True, slots=True)
class SummaryConfig:
    """Configuration for a summarization operation.

    Controls the level of detail, token budget, and content preservation
    preferences for summary generation.

    Attributes:
        level: The desired summary detail level.
        max_tokens: Maximum token count for the generated summary.
        preserve_key_facts: Whether to explicitly extract and preserve key facts.
        include_timestamps: Whether to include temporal references in the summary.
        language: Target language for the summary (default: English).
        format_style: Output format ('prose', 'bullet_points', 'structured').
    """

    level: SummaryLevel = SummaryLevel.STANDARD
    max_tokens: int = 200
    preserve_key_facts: bool = True
    include_timestamps: bool = False
    language: str = "en"
    format_style: str = "prose"


@dataclass(frozen=True, slots=True)
class MemorySummary:
    """The result of a summarization operation.

    Contains the generated summary text along with metadata about
    the source material and generation process.

    Attributes:
        summary_id: Unique identifier for this summary (UUID4).
        content: The generated summary text.
        source_entry_ids: IDs of the memory entries that were summarized.
        level: The summary level that was applied.
        token_count: Actual token count of the generated summary.
        created_at: UTC timestamp when this summary was generated.
        key_facts: Optional list of extracted key facts.
        metadata: Additional metadata about the summarization process.
    """

    content: str
    source_entry_ids: list[str]
    level: SummaryLevel
    summary_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    token_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    key_facts: Optional[list[str]] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class MemorySummarizer(ABC):
    """Abstract interface for memory summarization operations.

    Implementations wrap LLM or other summarization capabilities to
    generate concise representations of memory content. Used during
    consolidation, context assembly, and conversation management.
    """

    @abstractmethod
    async def summarize(self, entry: MemoryEntry, config: Optional[SummaryConfig] = None) -> MemorySummary:
        """Generate a summary of a single memory entry.

        Args:
            entry: The memory entry to summarize.
            config: Optional configuration overrides (uses defaults if None).

        Returns:
            The generated memory summary.
        """
        ...

    @abstractmethod
    async def summarize_conversation(
        self, entries: list[MemoryEntry], config: Optional[SummaryConfig] = None
    ) -> MemorySummary:
        """Generate a summary of a conversation (multiple ordered entries).

        Optimized for conversation-style content where order and dialogue
        structure matters.

        Args:
            entries: Ordered list of conversation entries to summarize.
            config: Optional configuration overrides.

        Returns:
            The generated conversation summary.
        """
        ...

    @abstractmethod
    async def summarize_batch(
        self, entries: list[MemoryEntry], config: Optional[SummaryConfig] = None
    ) -> MemorySummary:
        """Generate a single summary covering multiple memory entries.

        Combines multiple entries into one coherent summary, useful for
        consolidation operations.

        Args:
            entries: List of memory entries to summarize together.
            config: Optional configuration overrides.

        Returns:
            The generated batch summary.
        """
        ...

    @abstractmethod
    async def extract_key_facts(self, entry: MemoryEntry) -> list[str]:
        """Extract key facts from a memory entry.

        Identifies and extracts discrete factual statements from the
        memory content for use in fact-based retrieval and knowledge graphs.

        Args:
            entry: The memory entry to extract facts from.

        Returns:
            List of extracted fact strings.
        """
        ...
