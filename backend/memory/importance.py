"""Memory importance scoring system.

This module defines the importance scoring framework used to assign and
maintain relevance scores for memory entries. Importance scores drive
retention decisions, retrieval ranking, and eviction strategies.

The scoring system is factor-based, combining multiple signals (recency,
frequency, explicit user marking, etc.) into a composite score between
0.0 and 1.0.

Classes:
    ImportanceFactor: Enumeration of scoring factors.
    ImportanceScore: Computed importance score with factor breakdown.
    ImportanceScorer: Abstract interface for scoring memory entries.
    ImportanceDecayStrategy: Abstract interface for time-based score decay.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from .types import MemoryEntry


class ImportanceFactor(str, Enum):
    """Enumeration of factors contributing to importance scoring.

    Each factor represents a distinct signal that influences how important
    a memory is considered. The final score is a weighted combination.

    Attributes:
        RECENCY: How recently the memory was created or accessed.
        FREQUENCY: How often the memory has been accessed.
        RELEVANCE: Semantic relevance to current context or query.
        USER_EXPLICIT: Explicit user action (e.g., user marked as important).
        EMOTIONAL: Emotional salience or significance of the content.
        TASK_CRITICAL: Whether the memory is critical to an active task.
        REFERENCED: How often this memory is referenced by other memories.
    """

    RECENCY = "recency"
    FREQUENCY = "frequency"
    RELEVANCE = "relevance"
    USER_EXPLICIT = "user_explicit"
    EMOTIONAL = "emotional"
    TASK_CRITICAL = "task_critical"
    REFERENCED = "referenced"


@dataclass(frozen=True, slots=True)
class ImportanceScore:
    """Represents a computed importance score with factor breakdown.

    The importance score is a composite value derived from multiple
    weighted factors. The breakdown allows inspection of which signals
    contributed most to the final score.

    Attributes:
        score: Final composite importance score in range [0.0, 1.0].
        factors: Mapping of factor to its individual contribution (0.0-1.0).
        calculated_at: UTC timestamp when this score was computed.
        decay_rate: Rate at which this score decays over time (per hour).
        confidence: Confidence in the score accuracy (0.0-1.0).
    """

    score: float
    factors: dict[ImportanceFactor, float] = field(default_factory=dict)
    calculated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    decay_rate: float = 0.01
    confidence: float = 1.0

    def __post_init__(self) -> None:
        """Validate score bounds."""
        if not 0.0 <= self.score <= 1.0:
            object.__setattr__(self, "score", max(0.0, min(1.0, self.score)))


class ImportanceScorer(ABC):
    """Abstract interface for computing memory importance scores.

    Implementations of this interface provide the scoring logic that
    combines multiple factors into a final importance value. Different
    implementations may weight factors differently or use different
    aggregation strategies.
    """

    @abstractmethod
    async def score(self, entry: MemoryEntry) -> ImportanceScore:
        """Compute the importance score for a single memory entry.

        Args:
            entry: The memory entry to score.

        Returns:
            The computed importance score with factor breakdown.
        """
        ...

    @abstractmethod
    async def score_batch(self, entries: list[MemoryEntry]) -> list[ImportanceScore]:
        """Compute importance scores for a batch of memory entries.

        More efficient than calling score() individually for large batches
        as it allows for batch optimizations.

        Args:
            entries: The memory entries to score.

        Returns:
            List of importance scores in the same order as input entries.
        """
        ...

    @abstractmethod
    async def recalculate(self, entry: MemoryEntry, context: dict | None = None) -> ImportanceScore:
        """Recalculate the importance score with updated context.

        Used when the scoring context has changed (e.g., new access,
        new reference, task completion) and the score needs updating.

        Args:
            entry: The memory entry to re-score.
            context: Optional contextual information for scoring.

        Returns:
            The updated importance score.
        """
        ...

    @abstractmethod
    async def apply_decay(self, entry: MemoryEntry, elapsed_hours: float) -> float:
        """Apply time-based decay to an entry's importance score.

        Calculates the decayed score after a given time period has elapsed
        since the last calculation.

        Args:
            entry: The memory entry whose score should decay.
            elapsed_hours: Number of hours since last score calculation.

        Returns:
            The new decayed importance score value.
        """
        ...

    @abstractmethod
    async def get_threshold(self, memory_type: str | None = None) -> float:
        """Get the minimum importance threshold for retention.

        Entries below this threshold are candidates for eviction
        or consolidation.

        Args:
            memory_type: Optional memory type for type-specific thresholds.

        Returns:
            The minimum importance threshold value (0.0-1.0).
        """
        ...


class ImportanceDecayStrategy(ABC):
    """Abstract interface for time-based importance score decay.

    Implementations define how importance scores diminish over time,
    allowing different decay curves (linear, exponential, step, etc.)
    for different memory types or contexts.
    """

    @abstractmethod
    async def calculate_decay(
        self, current_score: float, elapsed_hours: float, decay_rate: float
    ) -> float:
        """Calculate the decayed score after a time interval.

        Args:
            current_score: The current importance score before decay.
            elapsed_hours: Hours elapsed since last calculation.
            decay_rate: The per-hour decay rate.

        Returns:
            The new score after decay is applied.
        """
        ...

    @abstractmethod
    async def should_expire(
        self, current_score: float, elapsed_hours: float, decay_rate: float, threshold: float
    ) -> bool:
        """Determine if an entry should be considered expired based on decay.

        Args:
            current_score: The current importance score.
            elapsed_hours: Hours elapsed since last calculation.
            decay_rate: The per-hour decay rate.
            threshold: The minimum score below which entry is expired.

        Returns:
            True if the decayed score would fall below the threshold.
        """
        ...
