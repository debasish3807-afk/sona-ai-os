"""Dependency injection / factory for Memory OS.

Provides factory functions to create fully-wired Memory Manager
instances with all subsystems configured.
"""

from sona_memory.infrastructure.cleanup import CleanupConfig, CleanupService
from sona_memory.infrastructure.consolidation import ConsolidationConfig, ConsolidationService
from sona_memory.infrastructure.conversation_memory import ConversationConfig, ConversationMemory
from sona_memory.infrastructure.embedding_service import EmbeddingService
from sona_memory.infrastructure.episodic_memory import EpisodicConfig, EpisodicMemory
from sona_memory.infrastructure.long_term_memory import LongTermConfig, LongTermMemory
from sona_memory.infrastructure.memory_manager import MemoryManager
from sona_memory.infrastructure.metrics import MetricsCollector
from sona_memory.infrastructure.ranking import MemoryRanker, RankingWeights
from sona_memory.infrastructure.retrieval_engine import RetrievalEngine
from sona_memory.infrastructure.semantic_memory import SemanticConfig, SemanticMemory
from sona_memory.infrastructure.short_term_memory import ShortTermConfig, ShortTermMemory
from sona_memory.infrastructure.working_memory import WorkingMemoryConfig, WorkingMemoryManager


def create_memory_manager(
    *,
    working_config: WorkingMemoryConfig | None = None,
    short_term_config: ShortTermConfig | None = None,
    long_term_config: LongTermConfig | None = None,
    episodic_config: EpisodicConfig | None = None,
    semantic_config: SemanticConfig | None = None,
    conversation_config: ConversationConfig | None = None,
    consolidation_config: ConsolidationConfig | None = None,
    cleanup_config: CleanupConfig | None = None,
    ranking_weights: RankingWeights | None = None,
    embedding_dim: int = 128,
) -> MemoryManager:
    """Create a fully-wired Memory Manager with all subsystems.

    All parameters are optional and use sensible defaults.

    Returns:
        A configured MemoryManager ready for use.
    """
    # Core services
    embedding_service = EmbeddingService(dim=embedding_dim)
    metrics = MetricsCollector()
    ranker = MemoryRanker(weights=ranking_weights)

    # Memory subsystems
    working_memory = WorkingMemoryManager(config=working_config)
    short_term = ShortTermMemory(config=short_term_config)
    long_term = LongTermMemory(
        embedding_service=embedding_service,
        config=long_term_config,
    )
    episodic = EpisodicMemory(config=episodic_config)
    semantic = SemanticMemory(
        embedding_service=embedding_service,
        config=semantic_config,
    )
    conversation = ConversationMemory(config=conversation_config)

    # Retrieval engine
    retrieval_engine = RetrievalEngine(
        working_memory=working_memory,
        short_term_memory=short_term,
        long_term_memory=long_term,
        episodic_memory=episodic,
        semantic_memory=semantic,
        conversation_memory=conversation,
        embedding_service=embedding_service,
        ranker=ranker,
    )

    # Consolidation and cleanup
    consolidation = ConsolidationService(
        short_term=short_term,
        long_term=long_term,
        embedding_service=embedding_service,
        config=consolidation_config,
    )
    cleanup = CleanupService(
        working_memory=working_memory,
        short_term=short_term,
        config=cleanup_config,
    )

    # Assemble
    return MemoryManager(
        working_memory=working_memory,
        short_term_memory=short_term,
        long_term_memory=long_term,
        episodic_memory=episodic,
        semantic_memory=semantic,
        conversation_memory=conversation,
        retrieval_engine=retrieval_engine,
        consolidation_service=consolidation,
        cleanup_service=cleanup,
        metrics=metrics,
    )
