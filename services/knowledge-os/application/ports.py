"""Abstract port interfaces for the Knowledge OS service.

Defines the contracts that infrastructure adapters must implement
to provide knowledge base management and document processing capabilities.
"""

from abc import ABC, abstractmethod

from domain.models import Document, DocumentChunk, DocumentType, RAGQuery, RAGResult


class KnowledgeBasePort(ABC):
    """Port for knowledge base management.

    Defines the contract for ingesting documents, querying knowledge bases
    using RAG pipelines, and managing knowledge base lifecycle operations.
    """

    @abstractmethod
    async def ingest(self, document: Document, kb_id: str) -> str:
        """Ingest a document into a knowledge base.

        Processes the document (chunking, embedding, indexing) and adds
        it to the specified knowledge base.

        Args:
            document: The document to ingest.
            kb_id: The target knowledge base identifier.

        Returns:
            The document ID confirming successful ingestion.
        """
        ...

    @abstractmethod
    async def query(self, rag_query: RAGQuery) -> RAGResult:
        """Query a knowledge base using the RAG pipeline.

        Performs embedding of the query, similarity search, optional
        re-ranking, and context assembly for LLM augmentation.

        Args:
            rag_query: The RAG query parameters.

        Returns:
            A RAGResult with relevant chunks and augmented context.
        """
        ...

    @abstractmethod
    async def list_knowledge_bases(self, user_id: str) -> list[dict]:
        """List available knowledge bases for a user.

        Args:
            user_id: The ID of the user whose knowledge bases to list.

        Returns:
            A list of dictionaries describing each knowledge base.
        """
        ...

    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """Remove a document from the knowledge base.

        Deletes the document and all associated chunks/embeddings.

        Args:
            document_id: The ID of the document to delete.

        Returns:
            True if the document was successfully deleted, False otherwise.
        """
        ...


class DocumentProcessorPort(ABC):
    """Port for document processing and chunking.

    Defines the contract for transforming raw documents into indexed
    chunks with embeddings suitable for similarity search.
    """

    @abstractmethod
    async def process(self, document: Document) -> list[DocumentChunk]:
        """Process a document into indexed chunks.

        Applies chunking strategy, generates embeddings for each chunk,
        and returns the list of processedDocumentChunks.

        Args:
            document: The document to process.

        Returns:
            A list of DocumentChunk instances with embeddings.
        """
        ...

    @abstractmethod
    async def extract_text(self, raw_content: bytes, doc_type: DocumentType) -> str:
        """Extract text from raw document content.

        Handles format-specific text extraction (e.g., PDF parsing,
        HTML stripping, code comment extraction).

        Args:
            raw_content: The raw bytes of the document.
            doc_type: The type of document to determine extraction strategy.

        Returns:
            The extracted text content as a string.
        """
        ...
