"""Vector database layer — embedding storage and semantic search.

Provides an abstract vector store interface with an in-process
FAISS-like implementation for development and testing.
"""

from vector.embeddings import EmbeddingEngine, chunk_text
from vector.memory_store import InMemoryVectorStore
from vector.store import SearchResult, VectorRecord, VectorStore

__all__ = [
    "EmbeddingEngine",
    "InMemoryVectorStore",
    "SearchResult",
    "VectorRecord",
    "VectorStore",
    "chunk_text",
]
