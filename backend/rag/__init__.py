"""RAG (Retrieval-Augmented Generation) engine.

Provides document ingestion, chunking, indexing, hybrid search,
and context building for knowledge-enhanced AI responses.
"""

from rag.engine import RAGEngine
from rag.ingestion import DocumentIngester, SupportedFileType
from rag.retrieval import HybridRetriever, RetrievalResult

__all__ = [
    "DocumentIngester",
    "HybridRetriever",
    "RAGEngine",
    "RetrievalResult",
    "SupportedFileType",
]
