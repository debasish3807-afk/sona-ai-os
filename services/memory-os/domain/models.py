"""Domain models for the Memory OS service.

Defines the data structures used by the Memory OS for memory storage,
retrieval, consolidation, and querying across multiple memory types.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class MemoryType(StrEnum):
    """Types of memory supported by the Memory OS.

    Each type corresponds to a different temporal and semantic
    memory category with distinct storage and retrieval characteristics.
    """

    WORKING = "working"
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


@dataclass(frozen=True)
class MemoryEntry:
    """A single memory entry stored in the Memory OS.

    Attributes:
        id: Unique identifier for the memory entry.
        memory_type: Classification of the memory type.
        content: The textual content of the memory.
        embedding: Optional vector embedding for similarity search.
        metadata: Optional additional metadata about the memory.
        importance: Importance score (0.0 to 1.0), used for consolidation and eviction.
        created_at: Timestamp when the memory was created.
        expires_at: Optional expiration timestamp for time-limited memories.
        tags: Categorical tags for filtering and organization.
    """

    id: str
    memory_type: MemoryType
    content: str
    embedding: list[float] | None = None
    metadata: dict | None = None
    importance: float = 0.5
    created_at: datetime | None = None
    expires_at: datetime | None = None
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class MemoryQuery:
    """Query parameters for retrieving memories from the Memory OS.

    Attributes:
        user_id: The user whose memories to search.
        query: The search query text for similarity matching.
        memory_types: Optional filter by memory types (None means all types).
        top_k: Maximum number of results to return.
        min_importance: Minimum importance score threshold.
        time_range: Optional time range filter as (start, end) tuple.
    """

    user_id: str
    query: str
    memory_types: list[MemoryType] | None = None
    top_k: int = 10
    min_importance: float = 0.0
    time_range: tuple[datetime, datetime] | None = None
