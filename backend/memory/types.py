"""Shared type definitions for the memory engine.

This module defines the core data structures and enumerations used throughout
the memory engine. All types are fully typed using Python 3.12 type annotations
and leverage dataclasses for structured data representation.

Types defined:
    - MemoryScope: Defines the visibility/access scope of a memory entry.
    - MemoryType: Categorizes memory entries by their temporal/semantic nature.
    - MemoryPriority: Priority levels for memory retention and retrieval ordering.
    - MemoryTag: Metadata tag attached to memory entries for categorization.
    - MemoryEntry: The primary data structure representing a single memory.
    - MemoryQuery: Parameters for searching/filtering memory entries.
    - MemorySearchResult: A single result from a memory search operation.
    - MemoryStats: Aggregate statistics about the memory system state.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, IntEnum
from typing import Any


class MemoryScope(str, Enum):
    """Defines the visibility and access scope of a memory entry.

    Memory scopes determine which contexts can access a particular memory:
        - GLOBAL: Accessible across all users and sessions.
        - USER: Scoped to a specific user across all their sessions.
        - SESSION: Limited to the current active session.
        - PROJECT: Associated with a specific project context.
        - CONVERSATION: Bound to a specific conversation thread.
    """

    GLOBAL = "global"
    USER = "user"
    SESSION = "session"
    PROJECT = "project"
    CONVERSATION = "conversation"


class MemoryType(str, Enum):
    """Categorizes memory entries by their temporal and semantic nature.

    Memory types represent different cognitive memory models:
        - WORKING: Active, in-use context for the current operation.
        - SHORT_TERM: Recent interactions retained for hours or days.
        - LONG_TERM: Persistent knowledge retained indefinitely.
        - EPISODIC: Specific events and experiences with temporal context.
        - SEMANTIC: Facts, concepts, and their relationships.
        - KNOWLEDGE: External documents and knowledge base content.
        - PROJECT: Project-specific context and conventions.
        - CONVERSATION: Chat history and dialogue context.
    """

    WORKING = "working"
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    KNOWLEDGE = "knowledge"
    PROJECT = "project"
    CONVERSATION = "conversation"


class MemoryPriority(IntEnum):
    """Priority levels for memory retention and retrieval ordering.

    Lower values indicate higher priority. Used by eviction strategies
    and retrieval ranking to determine which memories to keep or surface first.

    Attributes:
        CRITICAL: Must never be evicted (priority 0).
        HIGH: Important memories retained preferentially (priority 10).
        NORMAL: Standard priority for most memories (priority 50).
        LOW: Candidates for early eviction (priority 90).
        EXPENDABLE: Can be evicted at any time (priority 100).
    """

    CRITICAL = 0
    HIGH = 10
    NORMAL = 50
    LOW = 90
    EXPENDABLE = 100


@dataclass(frozen=True, slots=True)
class MemoryTag:
    """A metadata tag attached to memory entries for categorization and filtering.

    Tags enable flexible, user-defined categorization of memories beyond
    the built-in type and scope hierarchies.

    Attributes:
        name: The tag identifier (e.g., 'important', 'code-review').
        category: Optional grouping category for the tag (e.g., 'workflow', 'topic').
        metadata: Additional key-value metadata associated with this tag.
    """

    name: str
    category: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MemoryEntry:
    """The primary data structure representing a single memory in the system.

    A MemoryEntry encapsulates all information about a stored memory including
    its content, type classification, importance scoring, embedding vector for
    semantic search, and lifecycle metadata.

    Attributes:
        entry_id: Unique identifier for this memory entry (UUID4).
        memory_type: The type classification of this memory.
        scope: The visibility scope of this memory.
        content: The actual memory content (text, structured data, etc.).
        embedding: Optional dense vector representation for semantic search.
        importance_score: Numeric importance score in range [0.0, 1.0].
        tags: List of metadata tags for categorization.
        created_at: UTC timestamp when this memory was first stored.
        updated_at: UTC timestamp of the most recent modification.
        accessed_at: UTC timestamp of the most recent read access.
        metadata: Arbitrary key-value metadata for extensibility.
        pinned: Whether this memory is pinned (exempt from eviction).
        expires_at: Optional UTC timestamp after which this memory expires.
        user_id: Optional user identifier for user-scoped memories.
        session_id: Optional session identifier for session-scoped memories.
        source: Optional provenance information about where this memory came from.
        token_count: Optional estimated token count of the content.
        access_count: Number of times this memory has been retrieved.
        priority: The retention priority level of this memory.
    """

    memory_type: MemoryType
    scope: MemoryScope
    content: str
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    embedding: list[float] | None = None
    importance_score: float = 0.5
    tags: list[MemoryTag] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    accessed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)
    pinned: bool = False
    expires_at: datetime | None = None
    user_id: str | None = None
    session_id: str | None = None
    source: str | None = None
    token_count: int | None = None
    access_count: int = 0
    priority: MemoryPriority = MemoryPriority.NORMAL


@dataclass(frozen=True, slots=True)
class MemoryQuery:
    """Parameters for searching and filtering memory entries.

    Encapsulates all query parameters including text-based search,
    type/scope filters, tag matching, importance thresholds, and
    result limits.

    Attributes:
        query_text: The natural language search query.
        memory_types: Optional filter to specific memory types.
        scope_filter: Optional filter to specific scopes.
        tags_filter: Optional filter requiring specific tags.
        min_importance: Minimum importance score threshold (0.0-1.0).
        max_results: Maximum number of results to return.
        include_expired: Whether to include expired entries in results.
        user_id: Optional filter for user-scoped entries.
        session_id: Optional filter for session-scoped entries.
        time_range_start: Optional start of time range filter.
        time_range_end: Optional end of time range filter.
        include_embeddings: Whether to include embedding vectors in results.
    """

    query_text: str
    memory_types: list[MemoryType] | None = None
    scope_filter: list[MemoryScope] | None = None
    tags_filter: list[str] | None = None
    min_importance: float = 0.0
    max_results: int = 20
    include_expired: bool = False
    user_id: str | None = None
    session_id: str | None = None
    time_range_start: datetime | None = None
    time_range_end: datetime | None = None
    include_embeddings: bool = False


@dataclass(frozen=True, slots=True)
class MemorySearchResult:
    """A single result from a memory search operation.

    Wraps a MemoryEntry with relevance scoring and match classification
    metadata from the retrieval process.

    Attributes:
        entry: The matched memory entry.
        relevance_score: Relevance score in range [0.0, 1.0], higher is more relevant.
        match_type: The type of match that produced this result (e.g., 'semantic', 'keyword', 'exact').
        highlights: Optional list of text snippets showing match context.
    """

    entry: MemoryEntry
    relevance_score: float
    match_type: str
    highlights: list[str] | None = None


@dataclass(frozen=True, slots=True)
class MemoryStats:
    """Aggregate statistics about the memory system state.

    Provides a snapshot of the memory system's current resource utilization,
    entry distribution, and temporal bounds.

    Attributes:
        total_entries: Total number of memory entries across all types/scopes.
        by_type: Count of entries broken down by MemoryType.
        by_scope: Count of entries broken down by MemoryScope.
        total_size_bytes: Estimated total storage size in bytes.
        oldest_entry: Timestamp of the oldest entry in the system.
        newest_entry: Timestamp of the newest entry in the system.
        pinned_count: Number of currently pinned entries.
        expired_count: Number of expired but not yet cleaned entries.
    """

    total_entries: int
    by_type: dict[MemoryType, int]
    by_scope: dict[MemoryScope, int]
    total_size_bytes: int
    oldest_entry: datetime | None = None
    newest_entry: datetime | None = None
    pinned_count: int = 0
    expired_count: int = 0
