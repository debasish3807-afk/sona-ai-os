"""Dependency injection factory for Knowledge OS.

Creates fully-wired Knowledge OS runtime with all components.
"""

from sona_knowledge.infrastructure.chunking.recursive import RecursiveChunker
from sona_knowledge.infrastructure.citation_engine import CitationEngine
from sona_knowledge.infrastructure.embedding_service import EmbeddingService
from sona_knowledge.infrastructure.hybrid_search import HybridSearch
from sona_knowledge.infrastructure.incremental_indexer import IncrementalIndexer
from sona_knowledge.infrastructure.knowledge_manager import KnowledgeManager
from sona_knowledge.infrastructure.metadata_extractor import MetadataExtractor
from sona_knowledge.infrastructure.reranker import Reranker
from sona_knowledge.infrastructure.retriever import Retriever
from sona_knowledge.infrastructure.vector_store import VectorStore


def create_knowledge_manager(
    vector_size: int = 384,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    semantic_weight: float = 0.7,
    keyword_weight: float = 0.3,
) -> KnowledgeManager:
    """Create fully-wired Knowledge OS runtime.

    Args:
        vector_size: Dimensionality of embedding vectors.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Overlap between consecutive chunks.
        semantic_weight: Weight for semantic similarity in hybrid search.
        keyword_weight: Weight for keyword matching in hybrid search.

    Returns:
        A fully configured KnowledgeManager instance.
    """
    # Core services
    embedding_service = EmbeddingService(vector_size=vector_size)
    vector_store = VectorStore()
    retriever = Retriever(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )

    # Search and ranking
    hybrid_search = HybridSearch(
        semantic_weight=semantic_weight,
        keyword_weight=keyword_weight,
    )
    reranker = Reranker()
    citation_engine = CitationEngine()

    # Document processing
    metadata_extractor = MetadataExtractor()
    incremental_indexer = IncrementalIndexer()
    chunker = RecursiveChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    return KnowledgeManager(
        embedding_service=embedding_service,
        vector_store=vector_store,
        retriever=retriever,
        hybrid_search=hybrid_search,
        reranker=reranker,
        citation_engine=citation_engine,
        metadata_extractor=metadata_extractor,
        incremental_indexer=incremental_indexer,
        chunker=chunker,
    )
