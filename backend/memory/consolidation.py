"""Memory consolidation and compression.

This module defines the consolidation framework for merging, summarizing,
and compressing memory entries to manage growth and improve long-term
retrieval quality. Consolidation transforms many granular memories into
fewer, denser representations.

Classes:
    ConsolidationStrategy: Enumeration of consolidation approaches.
    ConsolidationStatus: Status tracking for consolidation tasks.
    ConsolidationTask: Definition of a pending consolidation operation.
    ConsolidationResult: Outcome of a completed consolidation operation.
    MemoryConsolidator: Abstract interface for consolidation operations.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from .types import MemoryEntry, MemoryType


class ConsolidationStrategy(str, Enum):
    """Enumeration of available consolidation strategies.

    Attributes:
        SUMMARIZE: Generate a natural language summary of entries.
        MERGE: Combine multiple entries into a single comprehensive entry.
        ARCHIVE: Move entries to cold storage with minimal processing.
        COMPRESS: Reduce token count while preserving key information.
        DISTILL: Extract and retain only the most important facts.
    """

    SUMMARIZE = "summarize"
    MERGE = "merge"
    ARCHIVE = "archive"
    COMPRESS = "compress"
    DISTILL = "distill"


class ConsolidationStatus(str, Enum):
    """Status of a consolidation task.

    Attributes:
        PENDING: Task is queued but not yet started.
        RUNNING: Task is currently executing.
        COMPLETED: Task finished successfully.
        FAILED: Task encountered an error and did not complete.
        CANCELLED: Task was cancelled before completion.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class ConsolidationTask:
    """Definition of a pending or active consolidation operation.

    A consolidation task encapsulates the parameters for consolidating
    a set of source entries into a target representation.

    Attributes:
        task_id: Unique identifier for this task (UUID4).
        source_entries: List of memory entry IDs to consolidate.
        strategy: The consolidation strategy to apply.
        target_type: The memory type of the resulting consolidated entry.
        status: Current status of this task.
        created_at: UTC timestamp when this task was created.
        started_at: UTC timestamp when execution began (None if not started).
        completed_at: UTC timestamp when execution finished (None if not done).
        metadata: Additional task metadata.
    """

    source_entries: list[str]
    strategy: ConsolidationStrategy
    target_type: MemoryType = MemoryType.LONG_TERM
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: ConsolidationStatus = ConsolidationStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ConsolidationResult:
    """Outcome of a completed consolidation operation.

    Contains the result of processing including the new consolidated
    entry (if successful), counts of processed and removed entries,
    and a summary of what was done.

    Attributes:
        task_id: The ID of the task that produced this result.
        success: Whether the consolidation completed successfully.
        consolidated_entry: The new consolidated memory entry (None on failure).
        entries_processed: Number of source entries that were processed.
        entries_removed: Number of source entries that were removed after consolidation.
        summary: Human-readable summary of the consolidation outcome.
        error: Error message if the consolidation failed.
        duration_ms: Time taken for the consolidation in milliseconds.
    """

    task_id: str
    success: bool
    consolidated_entry: MemoryEntry | None = None
    entries_processed: int = 0
    entries_removed: int = 0
    summary: str = ""
    error: str | None = None
    duration_ms: float = 0.0


class MemoryConsolidator(ABC):
    """Abstract interface for memory consolidation operations.

    Implementations handle the actual logic of merging, summarizing,
    or compressing memory entries according to the specified strategy.
    """

    @abstractmethod
    async def consolidate(
        self, task: ConsolidationTask, entries: list[MemoryEntry]
    ) -> ConsolidationResult:
        """Execute a single consolidation task.

        Takes a set of source entries and produces a consolidated result
        according to the task's strategy and configuration.

        Args:
            task: The consolidation task definition.
            entries: The actual memory entries to consolidate.

        Returns:
            The consolidation result including the new entry if successful.
        """
        ...

    @abstractmethod
    async def consolidate_batch(
        self, tasks: list[ConsolidationTask], entries_map: dict[str, list[MemoryEntry]]
    ) -> list[ConsolidationResult]:
        """Execute multiple consolidation tasks in batch.

        More efficient than individual calls when multiple consolidation
        operations need to be performed.

        Args:
            tasks: List of consolidation task definitions.
            entries_map: Mapping of task_id to the entries for that task.

        Returns:
            List of consolidation results in the same order as input tasks.
        """
        ...

    @abstractmethod
    async def should_consolidate(
        self, entries: list[MemoryEntry], strategy: ConsolidationStrategy
    ) -> bool:
        """Determine whether a set of entries should be consolidated.

        Evaluates whether the given entries meet the criteria for
        consolidation (e.g., sufficient count, age, redundancy).

        Args:
            entries: Candidate entries for consolidation.
            strategy: The strategy that would be applied.

        Returns:
            True if consolidation is recommended.
        """
        ...

    @abstractmethod
    async def get_candidates(
        self,
        memory_type: MemoryType,
        max_age_hours: float | None = None,
        min_count: int = 5,
    ) -> list[list[str]]:
        """Identify groups of entries that are candidates for consolidation.

        Analyzes stored memories to find clusters that would benefit
        from consolidation.

        Args:
            memory_type: The memory type to find candidates in.
            max_age_hours: Optional maximum age filter in hours.
            min_count: Minimum number of entries in a candidate group.

        Returns:
            List of entry ID groups, where each group is a consolidation candidate.
        """
        ...

    @abstractmethod
    async def estimate_savings(
        self, entries: list[MemoryEntry], strategy: ConsolidationStrategy
    ) -> dict[str, Any]:
        """Estimate the storage savings from consolidating entries.

        Args:
            entries: The entries that would be consolidated.
            strategy: The strategy that would be applied.

        Returns:
            Dictionary with estimated savings including:
                - entries_reduction: Number of entries that would be removed.
                - size_reduction_bytes: Estimated byte savings.
                - token_reduction: Estimated token count reduction.
        """
        ...
