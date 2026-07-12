"""Memory Engine for Sona AI OS.

This package provides a production-ready, multi-tiered memory system for the
Sona AI operating system. It implements a cognitive-inspired architecture with
working memory, short-term memory, long-term memory, episodic memory, semantic
memory, knowledge memory, conversation memory, and project memory.

The memory engine is completely self-contained with no external dependencies
on kernel, providers, or agents modules. It exposes abstract interfaces (ABCs)
that can be implemented by different storage backends.

Architecture:
    - types: Core type definitions (enums, dataclasses)
    - exceptions: Memory-specific exception hierarchy
    - events: Event system for reactive behavior
    - policies: Lifecycle and retention policy framework
    - importance: Importance scoring system
    - retrieval: Search and retrieval abstractions
    - consolidation: Memory consolidation and compression
    - summarizer: Content summarization interface
    - index: Memory indexing abstractions
    - state: System state management
    - metrics: Observability and metrics collection
    - base: Abstract memory store interface
    - working: Working memory (active session context)
    - short_term: Short-term memory (recent interactions)
    - long_term: Long-term memory (persistent knowledge)
    - episodic: Episodic memory (events and experiences)
    - semantic: Semantic memory (facts and relationships)
    - knowledge: Knowledge memory (documents and RAG)
    - conversation: Conversation memory (chat history)
    - project: Project memory (project-specific context)
    - session: Session memory (per-session state)
    - context: Memory context assembly for AI operations
    - registry: Memory store registration and discovery
    - factory: Memory store factory
    - manager: Top-level memory system orchestration

Usage:
    from backend.memory import (
        MemoryManager,
        MemoryEntry,
        MemoryType,
        MemoryScope,
        MemoryQuery,
    )

    # All interfaces are abstract - implement with your chosen backend.
"""

# --- Core Types ---
# --- Base Store ---
from .base import MemoryStore

# --- Consolidation ---
from .consolidation import (
    ConsolidationResult,
    ConsolidationStatus,
    ConsolidationStrategy,
    ConsolidationTask,
    MemoryConsolidator,
)

# --- Context Assembly ---
from .context import (
    AssembledMemoryContext,
    MemoryContextAssembler,
    MemoryContextConfig,
    MemoryContextEntry,
)
from .conversation import (
    Conversation,
    ConversationConfig,
    ConversationMemory,
    ConversationMessage,
)
from .episodic import Episode, EpisodicConfig, EpisodicMemory

# --- Events ---
from .events import MemoryEvent, MemoryEvents

# --- Exceptions ---
from .exceptions import (
    MemoryCapacityError,
    MemoryConsolidationError,
    MemoryError,
    MemoryExpirationError,
    MemoryImportExportError,
    MemoryIndexError,
    MemoryNotFoundError,
    MemoryPolicyViolation,
    MemoryRetrievalError,
    MemoryStorageError,
)

# --- Factory ---
from .factory import MemoryFactory

# --- Importance ---
from .importance import (
    ImportanceDecayStrategy,
    ImportanceFactor,
    ImportanceScore,
    ImportanceScorer,
)

# --- Index ---
from .index import (
    DistanceMetric,
    IndexConfig,
    IndexHealth,
    IndexManager,
    IndexStats,
    IndexType,
    MemoryIndex,
)
from .knowledge import (
    KnowledgeChunk,
    KnowledgeConfig,
    KnowledgeDocument,
    KnowledgeMemory,
)
from .long_term import LongTermConfig, LongTermMemory

# --- Manager ---
from .manager import MemoryManager, MemoryManagerConfig

# --- Metrics ---
from .metrics import (
    MemoryMetrics,
    MemoryOperation,
    MetricsCollector,
    OperationMetric,
)

# --- Policies ---
from .policies import (
    CapacityPolicy,
    ConsolidationPolicy,
    ConsolidationTrigger,
    EvictionStrategy,
    ExpiryAction,
    MemoryPolicySet,
    PinPolicy,
    PolicyEngine,
    PolicyViolation,
    RetentionPolicy,
)
from .project import ProjectConfig, ProjectContext, ProjectMemory

# --- Registry ---
from .registry import MemoryRegistry, MemoryStoreEntry

# --- Retrieval ---
from .retrieval import (
    EmbeddingProvider,
    MemoryRetriever,
    RetrievalConfig,
    RetrievalResult,
    SearchStrategy,
)
from .semantic import Fact, SemanticConfig, SemanticMemory, SemanticRelation
from .session import SessionMemory, SessionMemoryConfig, SessionState
from .short_term import ShortTermConfig, ShortTermMemory

# --- State ---
from .state import (
    MemoryStateManager,
    MemorySystemState,
    MemorySystemStatus,
)

# --- Summarizer ---
from .summarizer import (
    MemorySummarizer,
    MemorySummary,
    SummaryConfig,
    SummaryLevel,
)
from .types import (
    MemoryEntry,
    MemoryPriority,
    MemoryQuery,
    MemoryScope,
    MemorySearchResult,
    MemoryStats,
    MemoryTag,
    MemoryType,
)

# --- Memory Tier Stores ---
from .working import EvictionMode, WorkingMemory, WorkingMemoryConfig

__all__ = [
    # Core Types
    "MemoryScope",
    "MemoryType",
    "MemoryPriority",
    "MemoryTag",
    "MemoryEntry",
    "MemoryQuery",
    "MemorySearchResult",
    "MemoryStats",
    # Exceptions
    "MemoryError",
    "MemoryNotFoundError",
    "MemoryStorageError",
    "MemoryRetrievalError",
    "MemoryCapacityError",
    "MemoryExpirationError",
    "MemoryConsolidationError",
    "MemoryIndexError",
    "MemoryImportExportError",
    "MemoryPolicyViolation",
    # Events
    "MemoryEvents",
    "MemoryEvent",
    # Policies
    "ExpiryAction",
    "EvictionStrategy",
    "ConsolidationTrigger",
    "RetentionPolicy",
    "CapacityPolicy",
    "ConsolidationPolicy",
    "PinPolicy",
    "MemoryPolicySet",
    "PolicyViolation",
    "PolicyEngine",
    # Importance
    "ImportanceFactor",
    "ImportanceScore",
    "ImportanceScorer",
    "ImportanceDecayStrategy",
    # Retrieval
    "SearchStrategy",
    "RetrievalConfig",
    "RetrievalResult",
    "MemoryRetriever",
    "EmbeddingProvider",
    # Consolidation
    "ConsolidationStrategy",
    "ConsolidationStatus",
    "ConsolidationTask",
    "ConsolidationResult",
    "MemoryConsolidator",
    # Summarizer
    "SummaryLevel",
    "SummaryConfig",
    "MemorySummary",
    "MemorySummarizer",
    # Index
    "IndexType",
    "DistanceMetric",
    "IndexHealth",
    "IndexConfig",
    "IndexStats",
    "MemoryIndex",
    "IndexManager",
    # State
    "MemorySystemStatus",
    "MemorySystemState",
    "MemoryStateManager",
    # Metrics
    "MemoryOperation",
    "OperationMetric",
    "MemoryMetrics",
    "MetricsCollector",
    # Base Store
    "MemoryStore",
    # Working Memory
    "EvictionMode",
    "WorkingMemoryConfig",
    "WorkingMemory",
    # Short-Term Memory
    "ShortTermConfig",
    "ShortTermMemory",
    # Long-Term Memory
    "LongTermConfig",
    "LongTermMemory",
    # Episodic Memory
    "EpisodicConfig",
    "Episode",
    "EpisodicMemory",
    # Semantic Memory
    "SemanticConfig",
    "Fact",
    "SemanticRelation",
    "SemanticMemory",
    # Knowledge Memory
    "KnowledgeConfig",
    "KnowledgeDocument",
    "KnowledgeChunk",
    "KnowledgeMemory",
    # Conversation Memory
    "ConversationConfig",
    "ConversationMessage",
    "Conversation",
    "ConversationMemory",
    # Project Memory
    "ProjectConfig",
    "ProjectContext",
    "ProjectMemory",
    # Session Memory
    "SessionMemoryConfig",
    "SessionState",
    "SessionMemory",
    # Context Assembly
    "MemoryContextConfig",
    "MemoryContextEntry",
    "AssembledMemoryContext",
    "MemoryContextAssembler",
    # Registry
    "MemoryStoreEntry",
    "MemoryRegistry",
    # Factory
    "MemoryFactory",
    # Manager
    "MemoryManagerConfig",
    "MemoryManager",
]
