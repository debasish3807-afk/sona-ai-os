"""Retriever for Knowledge OS.

Retrieves relevant chunks from the vector store based on query embeddings.
"""

import structlog

from sona_knowledge.infrastructure.embedding_service import EmbeddingService
from sona_knowledge.infrastructure.vector_store import SearchResult, VectorStore

logger = structlog.get_logger()


class Retriever:
    """Retrieves relevant document chunks from the vector store.

    Embeds the query and performs similarity search against stored vectors,
    filtering by minimum similarity threshold.
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
    ) -> None:
        """Initialize the retriever.

        Args:
            embedding_service: Service for generating query embeddings.
            vector_store: Store containing document chunk vectors.
        """
        self._embedding_service = embedding_service
        self._vector_store = vector_store

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.0,
        kb_id: str | None = None,
    ) -> list[SearchResult]:
        """Retrieve relevant chunks for a query.

        Args:
            query: The search query text.
            top_k: Maximum number of results to return.
            min_similarity: Minimum similarity score threshold.
            kb_id: Optional knowledge base ID to filter results.

        Returns:
            List of SearchResult sorted by descending similarity.
        """
        query_embedding = await self._embedding_service.embed(query)

        metadata_filter = None
        if kb_id:
            metadata_filter = {"kb_id": kb_id}

        results = await self._vector_store.search(
            query_vector=query_embedding,
            top_k=top_k,
            min_score=min_similarity,
            metadata_filter=metadata_filter,
        )

        logger.info(
            "retrieval_complete",
            query_length=len(query),
            results_count=len(results),
            top_score=results[0].score if results else 0.0,
        )

        return results
