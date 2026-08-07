"""Memory relevance scoring models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RelevanceScore:
    """Composite relevance score for a memory entry.

    Combines multiple signals to produce a final ranking score.

    Attributes:
        memory_id: The ID of the scored memory entry.
        similarity: Vector similarity between query and memory (0-1).
        recency: Time decay factor, newer = higher (0-1).
        importance: Stored importance value of the memory (0-1).
        access_frequency: How often this memory has been accessed (0-1).
        combined: Weighted final score for ranking.
    """

    memory_id: str
    similarity: float = 0.0
    recency: float = 0.0
    importance: float = 0.0
    access_frequency: float = 0.0
    combined: float = 0.0
