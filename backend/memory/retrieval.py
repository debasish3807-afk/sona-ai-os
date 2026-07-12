"""Memory retrieval and search abstractions.

This module defines the retrieval framework for searching and accessing
memories across all storage backends. It supports multiple search strategies
including semantic (vector-based), keyword, hybrid, temporal, and graph-based
approaches.

Classes:
    SearchStrategy: Enumeration of available search approaches.
    RetrievalConfig: Configuration for a retrieval operation.
    RetrievalResult: Complete result set from a retrieval operation.
    MemoryRetriever: Abstract interface for memory search operations.
    EmbeddingProvider: Abstract interface for text embedding generation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from .types import MemoryEntry, MemoryQuery, MemorySearchResult, MemoryType


class SearchStrategy(str, Enum):
    """Enumeration of available memory search strategies.

    Attributes:
        SEMANTIC: Vector similarity search using embeddings.
        KEYWORD: Traditional keyword/text matching search.
        HYBRID: Combined semantic and keyword search with fusion.
        TEMPORAL: Time-based search with recency weighting.
        GRAPH: Graph traversal-based search following relationships.
    """

    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    TEMPORAL = "temporal"
    GRAPH = "graph"


@dataclass(frozen=True, slots=True)
class RetrievalConfig:
    """Configuration for a memory retrieval operation.

    Controls the search strategy, result limits, relevance thresholds,
    and post-processing options.

    Attributes:
        strategy: The search strategy to use.
        max_results: Maximum number of results to return.
        min_relevance: Minimum relevance score threshold (0.0-1.0).
        include_metadata: Whether to include full metadata in results.
        rerank: Whether to apply re-ranking to initial results.
        rerank_model: Optional model identifier for re-ranking.
        diversity_factor: Factor for result diversity (0.0 = most relevant, 1.0 = most diverse).
    """

    strategy: SearchStrategy = SearchStrategy.HYBRID
    max_results: int = 20
    min_relevance: float = 0.0
    include_metadata: bool = True
    rerank: bool = False
    rerank_model: Optional[str] = None
    diversity_factor: float = 0.0


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """Complete result set from a memory retrieval operation.

    Contains the matching entries along with metadata about the
    retrieval process (timing, candidate counts, strategy used).

    Attributes:
        entries: List of matching memory search results.
        query: The original query that produced these results.
        strategy_used: The search strategy that was applied.
        latency_ms: Time taken for the retrieval operation in milliseconds.
        total_candidates: Total number of candidates considered before filtering.
        metadata: Additional metadata about the retrieval process.
    """

    entries: list[MemorySearchResult]
    query: MemoryQuery
    strategy_used: SearchStrategy
    latency_ms: float = 0.0
    total_candidates: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class MemoryRetriever(ABC):
    """Abstract interface for memory search and retrieval operations.

    Implementations provide the search logic across different backends
    and strategies. The retriever is the primary entry point for finding
    relevant memories given a query.
    """

    @abstractmethod
    async def search(
        self, query: MemoryQuery, config: Optional[RetrievalConfig] = None
    ) -> RetrievalResult:
        """Execute a memory search with the given query and configuration.

        This is the primary search method that handles routing to the
        appropriate strategy based on the config.

        Args:
            query: The memory query parameters.
            config: Optional retrieval configuration (uses defaults if None).

        Returns:
            The complete retrieval result including entries and metadata.
        """
        ...

    @abstractmethod
    async def search_by_embedding(
        self,
        embedding: list[float],
        memory_types: Optional[list[MemoryType]] = None,
        max_results: int = 10,
        min_relevance: float = 0.0,
    ) -> list[MemorySearchResult]:
        """Search for memories by embedding vector similarity.

        Performs a direct vector similarity search against stored embeddings.

        Args:
            embedding: The query embedding vector.
            memory_types: Optional filter to specific memory types.
            max_results: Maximum number of results to return.
            min_relevance: Minimum similarity threshold.

        Returns:
            List of matching memory search results ordered by similarity.
        """
        ...

    @abstractmethod
    async def search_by_tags(
        self,
        tags: list[str],
        memory_types: Optional[list[MemoryType]] = None,
        max_results: int = 20,
    ) -> list[MemorySearchResult]:
        """Search for memories that have specific tags.

        Args:
            tags: Tag names to search for (entries must have at least one).
            memory_types: Optional filter to specific memory types.
            max_results: Maximum number of results to return.

        Returns:
            List of matching memory search results.
        """
        ...

    @abstractmethod
    async def search_temporal(
        self,
        start: datetime,
        end: datetime,
        memory_types: Optional[list[MemoryType]] = None,
        max_results: int = 50,
    ) -> list[MemorySearchResult]:
        """Search for memories within a time range.

        Args:
            start: Start of the time range (inclusive).
            end: End of the time range (inclusive).
            memory_types: Optional filter to specific memory types.
            max_results: Maximum number of results to return.

        Returns:
            List of matching memory search results ordered by time.
        """
        ...

    @abstractmethod
    async def get_related(
        self,
        entry_id: str,
        max_results: int = 10,
        min_relevance: float = 0.3,
    ) -> list[MemorySearchResult]:
        """Find memories related to a given entry.

        Uses the entry's content and metadata to find semantically
        or structurally related memories.

        Args:
            entry_id: The ID of the entry to find relations for.
            max_results: Maximum number of related entries to return.
            min_relevance: Minimum relevance threshold for relatedness.

        Returns:
            List of related memory search results.
        """
        ...

    @abstractmethod
    async def rerank(
        self,
        results: list[MemorySearchResult],
        query: str,
        max_results: Optional[int] = None,
    ) -> list[MemorySearchResult]:
        """Re-rank search results using a more sophisticated model.

        Takes initial retrieval results and re-orders them using
        a cross-encoder or other re-ranking model for improved accuracy.

        Args:
            results: The initial search results to re-rank.
            query: The original query text for re-ranking context.
            max_results: Optional limit on final results (None = keep all).

        Returns:
            Re-ranked list of memory search results.
        """
        ...


class EmbeddingProvider(ABC):
    """Abstract interface for text embedding generation.

    Implementations wrap embedding models (local or API-based) and
    provide a consistent interface for generating vector representations
    of text content.
    """

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text.

        Args:
            text: The text to embed.

        Returns:
            Dense vector representation of the text.
        """
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of texts.

        More efficient than individual calls for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors in the same order as inputs.
        """
        ...

    @abstractmethod
    async def get_dimensions(self) -> int:
        """Get the dimensionality of the embedding vectors.

        Returns:
            Number of dimensions in the embedding vector.
        """
        ...

    @abstractmethod
    async def get_model_id(self) -> str:
        """Get the identifier of the embedding model being used.

        Returns:
            Model identifier string (e.g., 'text-embedding-3-small').
        """
        ...
