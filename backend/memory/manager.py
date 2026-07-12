"""Memory system manager - top-level orchestration.

This module defines the MemoryManager abstract base class which serves as
the top-level orchestration point for the entire memory engine. It coordinates
all sub-systems (stores, retrieval, consolidation, policies, metrics) and
provides a unified API for memory operations.

The MemoryManager is the primary entry point for external consumers of the
memory engine - all operations should flow through this interface.

Classes:
    MemoryManagerConfig: Configuration for the memory manager.
    MemoryManager: Abstract interface for top-level memory orchestration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .consolidation import MemoryConsolidator
from .context import AssembledMemoryContext, MemoryContextAssembler, MemoryContextConfig
from .conversation import ConversationMessage
from .importance import ImportanceScorer
from .knowledge import KnowledgeDocument
from .metrics import MetricsCollector
from .policies import MemoryPolicySet, PolicyEngine
from .registry import MemoryRegistry
from .retrieval import MemoryRetriever
from .state import MemoryStateManager
from .summarizer import MemorySummarizer
from .types import (
    MemoryEntry,
    MemoryQuery,
    MemoryScope,
    MemorySearchResult,
    MemoryStats,
    MemoryType,
)


@dataclass(frozen=True, slots=True)
class MemoryManagerConfig:
    """Configuration for the memory manager.

    Controls lifecycle behavior, background task scheduling, and
    feature toggles for the memory system.

    Attributes:
        auto_start: Whether to automatically initialize all stores on start.
        enable_consolidation: Whether to run automatic consolidation.
        enable_metrics: Whether to collect operation metrics.
        consolidation_interval_seconds: Seconds between consolidation runs.
        health_check_interval_seconds: Seconds between health checks.
        enable_policies: Whether to enforce retention/capacity policies.
        max_concurrent_operations: Maximum concurrent async operations.
        default_policy_set: Default policy set to apply.
    """

    auto_start: bool = True
    enable_consolidation: bool = True
    enable_metrics: bool = True
    consolidation_interval_seconds: int = 3600
    health_check_interval_seconds: int = 300
    enable_policies: bool = True
    max_concurrent_operations: int = 100
    default_policy_set: MemoryPolicySet | None = None


class MemoryManager(ABC):
    """Abstract interface for top-level memory system orchestration.

    The MemoryManager provides a unified API covering all memory operations
    and coordinates the underlying sub-systems. It manages lifecycle,
    delegates to appropriate stores, and enforces system-wide policies.

    Properties expose the sub-system components for advanced usage,
    while the method API provides convenience operations for common
    use cases.
    """

    # --- Properties for accessing sub-systems ---

    @property
    @abstractmethod
    def registry(self) -> MemoryRegistry:
        """Get the memory store registry."""
        ...

    @property
    @abstractmethod
    def retriever(self) -> MemoryRetriever:
        """Get the memory retriever."""
        ...

    @property
    @abstractmethod
    def consolidator(self) -> MemoryConsolidator:
        """Get the memory consolidator."""
        ...

    @property
    @abstractmethod
    def scorer(self) -> ImportanceScorer:
        """Get the importance scorer."""
        ...

    @property
    @abstractmethod
    def summarizer(self) -> MemorySummarizer:
        """Get the memory summarizer."""
        ...

    @property
    @abstractmethod
    def policy_engine(self) -> PolicyEngine:
        """Get the policy engine."""
        ...

    @property
    @abstractmethod
    def context_assembler(self) -> MemoryContextAssembler:
        """Get the context assembler."""
        ...

    @property
    @abstractmethod
    def metrics(self) -> MetricsCollector:
        """Get the metrics collector."""
        ...

    @property
    @abstractmethod
    def state_manager(self) -> MemoryStateManager:
        """Get the state manager."""
        ...

    # --- Lifecycle Operations ---

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the memory system and all sub-components.

        Starts all registered stores, indices, and background tasks.
        Must be called before any other operations.

        Raises:
            MemoryStorageError: If initialization fails.
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Gracefully shut down the memory system.

        Stops background tasks, flushes pending operations, and
        shuts down all stores in the correct order.
        """
        ...

    # --- Core Memory Operations ---

    @abstractmethod
    async def store(self, entry: MemoryEntry) -> str:
        """Store a memory entry in the appropriate store.

        Routes the entry to the correct store based on its memory_type,
        applies policies, updates indices, and emits events.

        Args:
            entry: The memory entry to store.

        Returns:
            The entry_id of the stored memory.
        """
        ...

    @abstractmethod
    async def get(self, entry_id: str, memory_type: MemoryType | None = None) -> MemoryEntry | None:
        """Retrieve a memory entry by ID.

        If memory_type is specified, searches only that store.
        Otherwise, searches all stores.

        Args:
            entry_id: The ID of the entry to retrieve.
            memory_type: Optional type hint for faster lookup.

        Returns:
            The memory entry if found, None otherwise.
        """
        ...

    @abstractmethod
    async def search(self, query: MemoryQuery) -> list[MemorySearchResult]:
        """Search across all memory stores.

        Delegates to the retriever for cross-store search with
        relevance ranking.

        Args:
            query: The search query parameters.

        Returns:
            List of matching results with relevance scores.
        """
        ...

    @abstractmethod
    async def delete(self, entry_id: str, memory_type: MemoryType | None = None) -> bool:
        """Delete a memory entry.

        Args:
            entry_id: The ID of the entry to delete.
            memory_type: Optional type hint for faster lookup.

        Returns:
            True if the entry was found and deleted.
        """
        ...

    # --- Context Operations ---

    @abstractmethod
    async def get_context_for_session(
        self, session_id: str, query: str, config: MemoryContextConfig | None = None
    ) -> AssembledMemoryContext:
        """Assemble memory context for a session.

        Combines working memory, relevant short-term and long-term memories,
        and knowledge into a token-budgeted context.

        Args:
            session_id: The session to assemble context for.
            query: Current query/input for relevance scoring.
            config: Optional assembly configuration.

        Returns:
            Assembled context ready for AI model input.
        """
        ...

    @abstractmethod
    async def get_relevant_context(
        self, query: str, config: MemoryContextConfig | None = None
    ) -> AssembledMemoryContext:
        """Get relevant memory context without session binding.

        Args:
            query: The query for relevance scoring.
            config: Optional assembly configuration.

        Returns:
            Assembled context based on query relevance.
        """
        ...

    # --- Conversation Operations ---

    @abstractmethod
    async def create_conversation(self, user_id: str, title: str | None = None) -> str:
        """Create a new conversation.

        Args:
            user_id: The user who owns the conversation.
            title: Optional conversation title.

        Returns:
            The conversation_id.
        """
        ...

    @abstractmethod
    async def add_message(self, conversation_id: str, message: ConversationMessage) -> None:
        """Add a message to a conversation.

        Args:
            conversation_id: The conversation to add the message to.
            message: The message to add.
        """
        ...

    @abstractmethod
    async def get_history(self, conversation_id: str, limit: int = 50) -> list[ConversationMessage]:
        """Get conversation message history.

        Args:
            conversation_id: The conversation to get history for.
            limit: Maximum number of messages to return.

        Returns:
            List of messages in chronological order.
        """
        ...

    # --- Knowledge Operations ---

    @abstractmethod
    async def ingest_document(self, document: KnowledgeDocument) -> str:
        """Ingest a document into knowledge memory.

        Args:
            document: The document to ingest.

        Returns:
            The doc_id of the ingested document.
        """
        ...

    @abstractmethod
    async def search_knowledge(self, query: str, max_results: int = 10) -> list[Any]:
        """Search the knowledge base.

        Args:
            query: The search query.
            max_results: Maximum number of results.

        Returns:
            List of relevant knowledge chunks.
        """
        ...

    # --- Management Operations ---

    @abstractmethod
    async def consolidate(self) -> dict[str, Any]:
        """Run memory consolidation across all stores.

        Returns:
            Summary of consolidation results.
        """
        ...

    @abstractmethod
    async def apply_policies(self) -> dict[str, Any]:
        """Apply all configured policies (retention, capacity, etc.).

        Returns:
            Summary of policy application results.
        """
        ...

    @abstractmethod
    async def get_stats(self) -> MemoryStats:
        """Get aggregate statistics for the entire memory system.

        Returns:
            Combined statistics across all stores.
        """
        ...

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Run a comprehensive health check on all components.

        Returns:
            Health status for each component.
        """
        ...

    @abstractmethod
    async def export_all(
        self,
        memory_types: list[MemoryType] | None = None,
        scope: MemoryScope | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """Export all memory entries for backup.

        Args:
            memory_types: Optional filter to specific types.
            scope: Optional filter to specific scope.

        Returns:
            Mapping of memory type name to serialized entries.
        """
        ...

    @abstractmethod
    async def import_all(self, data: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
        """Import memory entries from backup data.

        Args:
            data: Mapping of memory type name to serialized entries.

        Returns:
            Mapping of memory type name to number of entries imported.
        """
        ...
