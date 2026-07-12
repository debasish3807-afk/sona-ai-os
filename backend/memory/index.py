"""Memory indexing abstractions.

This module defines the indexing framework for efficient memory retrieval.
Multiple index types are supported including vector (embedding), keyword,
graph, temporal, and tag-based indices. The IndexManager coordinates
multiple indices for comprehensive search coverage.

Classes:
    IndexType: Enumeration of available index types.
    DistanceMetric: Distance metrics for vector similarity.
    IndexHealth: Health status of an index.
    IndexConfig: Configuration for creating an index.
    IndexStats: Runtime statistics for an index.
    MemoryIndex: Abstract interface for a single index.
    IndexManager: Abstract interface for managing multiple indices.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .types import MemoryEntry, MemorySearchResult


class IndexType(str, Enum):
    """Enumeration of available index types.

    Attributes:
        VECTOR: Dense vector similarity index for semantic search.
        KEYWORD: Inverted index for keyword/text matching.
        GRAPH: Graph-based index for relationship traversal.
        TEMPORAL: Time-series index for temporal queries.
        TAG: Tag-based index for categorical filtering.
    """

    VECTOR = "vector"
    KEYWORD = "keyword"
    GRAPH = "graph"
    TEMPORAL = "temporal"
    TAG = "tag"


class DistanceMetric(str, Enum):
    """Distance metrics for vector similarity computation.

    Attributes:
        COSINE: Cosine similarity (angle-based).
        EUCLIDEAN: Euclidean (L2) distance.
        DOT_PRODUCT: Dot product similarity.
        MANHATTAN: Manhattan (L1) distance.
    """

    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"
    MANHATTAN = "manhattan"


class IndexHealth(str, Enum):
    """Health status of an index.

    Attributes:
        HEALTHY: Index is fully operational.
        DEGRADED: Index is operational but performance may be impacted.
        REBUILDING: Index is currently being rebuilt.
        CORRUPTED: Index is in an invalid state and needs rebuilding.
        UNAVAILABLE: Index is not accessible.
    """

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    REBUILDING = "rebuilding"
    CORRUPTED = "corrupted"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class IndexConfig:
    """Configuration for creating a memory index.

    Specifies the index type, dimensionality for vector indices,
    distance metric, and maintenance preferences.

    Attributes:
        index_type: The type of index to create.
        dimensions: Number of dimensions for vector indices (None for non-vector).
        distance_metric: Distance metric for vector similarity.
        auto_rebuild: Whether to automatically rebuild on detected degradation.
        rebuild_threshold: Number of operations before auto-rebuild triggers.
        index_id: Unique identifier for this index configuration.
    """

    index_type: IndexType
    dimensions: int | None = None
    distance_metric: DistanceMetric = DistanceMetric.COSINE
    auto_rebuild: bool = True
    rebuild_threshold: int = 10000
    index_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class IndexStats:
    """Runtime statistics for an index.

    Provides observability into index state including size, health,
    and maintenance history.

    Attributes:
        index_type: The type of this index.
        entry_count: Number of entries currently indexed.
        size_bytes: Estimated memory consumption in bytes.
        last_rebuilt: UTC timestamp of the last full rebuild.
        health: Current health status.
        avg_query_ms: Average query latency in milliseconds.
        total_queries: Total number of queries served.
        metadata: Additional index-specific statistics.
    """

    index_type: IndexType
    entry_count: int
    size_bytes: int
    last_rebuilt: datetime | None = None
    health: IndexHealth = IndexHealth.HEALTHY
    avg_query_ms: float = 0.0
    total_queries: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class MemoryIndex(ABC):
    """Abstract interface for a single memory index.

    Each index instance handles a single type of indexing (vector,
    keyword, etc.) and provides add/remove/search operations for
    that specific modality.
    """

    @abstractmethod
    async def add(self, entry: MemoryEntry) -> None:
        """Add a memory entry to this index.

        Args:
            entry: The memory entry to index.
        """
        ...

    @abstractmethod
    async def remove(self, entry_id: str) -> bool:
        """Remove a memory entry from this index.

        Args:
            entry_id: The ID of the entry to remove.

        Returns:
            True if the entry was found and removed, False otherwise.
        """
        ...

    @abstractmethod
    async def update(self, entry: MemoryEntry) -> None:
        """Update an existing entry in this index.

        If the entry doesn't exist, it will be added.

        Args:
            entry: The memory entry with updated content/metadata.
        """
        ...

    @abstractmethod
    async def search(
        self, query: str, max_results: int = 10, **kwargs: Any
    ) -> list[MemorySearchResult]:
        """Search this index for matching entries.

        Args:
            query: The search query (text for keyword, embedding for vector).
            max_results: Maximum number of results to return.
            **kwargs: Additional index-type-specific search parameters.

        Returns:
            List of matching memory search results.
        """
        ...

    @abstractmethod
    async def rebuild(self) -> None:
        """Fully rebuild this index from scratch.

        This operation may be expensive for large indices but ensures
        index integrity and optimal query performance.
        """
        ...

    @abstractmethod
    async def get_stats(self) -> IndexStats:
        """Get current statistics for this index.

        Returns:
            Index statistics including size, health, and query metrics.
        """
        ...

    @abstractmethod
    async def clear(self) -> None:
        """Remove all entries from this index.

        Resets the index to an empty state without changing configuration.
        """
        ...


class IndexManager(ABC):
    """Abstract interface for managing multiple memory indices.

    The IndexManager coordinates creation, access, and maintenance
    of all indices used by the memory system.
    """

    @abstractmethod
    async def create_index(self, config: IndexConfig) -> MemoryIndex:
        """Create a new index with the given configuration.

        Args:
            config: Configuration for the new index.

        Returns:
            The created index instance.
        """
        ...

    @abstractmethod
    async def get_index(self, index_type: IndexType) -> MemoryIndex | None:
        """Get an existing index by type.

        Args:
            index_type: The type of index to retrieve.

        Returns:
            The index instance, or None if no index of that type exists.
        """
        ...

    @abstractmethod
    async def list_indices(self) -> list[IndexStats]:
        """List all managed indices with their statistics.

        Returns:
            List of index statistics for all active indices.
        """
        ...

    @abstractmethod
    async def rebuild_all(self) -> dict[IndexType, bool]:
        """Rebuild all managed indices.

        Returns:
            Mapping of index type to rebuild success status.
        """
        ...

    @abstractmethod
    async def drop_index(self, index_type: IndexType) -> bool:
        """Remove and destroy an index.

        Args:
            index_type: The type of index to drop.

        Returns:
            True if the index was found and dropped, False otherwise.
        """
        ...
