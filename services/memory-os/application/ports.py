"""Abstract port interfaces for the Memory OS service.

Defines the contracts that infrastructure adapters must implement
to provide memory storage, retrieval, consolidation, and embedding
generation capabilities.
"""

from abc import ABC, abstractmethod

from domain.models import MemoryEntry, MemoryQuery


class MemoryStorePort(ABC):
    """Port for memory storage operations.

    Infrastructure adapters implement this port to provide persistent
    memory storage using vector databases, caches, or other backends.
    """

    @abstractmethod
    async def store(self, user_id: str, entry: MemoryEntry) -> str:
        """Store a memory entry for a user.

        Args:
            user_id: The user who owns this memory.
            entry: The memory entry to store.

        Returns:
            The unique identifier of the stored memory.
        """
        ...

    @abstractmethod
    async def retrieve(self, query: MemoryQuery) -> list[MemoryEntry]:
        """Retrieve memories matching the query.

        Performs similarity search and/or filtering based on the
        query parameters (type, importance, time range).

        Args:
            query: The memory query specifying search criteria.

        Returns:
            A list of matching memory entries, ordered by relevance.
        """
        ...

    @abstractmethod
    async def consolidate(self, user_id: str) -> int:
        """Consolidate short-term memories into long-term storage.

        Analyzes short-term memories and promotes important ones
        to long-term storage, potentially merging related memories.

        Args:
            user_id: The user whose memories to consolidate.

        Returns:
            The number of memories consolidated.
        """
        ...

    @abstractmethod
    async def forget(self, user_id: str, memory_id: str) -> bool:
        """Remove a specific memory entry.

        Args:
            user_id: The user who owns the memory.
            memory_id: The identifier of the memory to remove.

        Returns:
            True if the memory was successfully removed, False otherwise.
        """
        ...

    @abstractmethod
    async def get_conversation_history(self, session_id: str, limit: int = 50) -> list[MemoryEntry]:
        """Get recent conversation history for a session.

        Retrieves the most recent conversation turns stored as
        working/short-term memories for a given session.

        Args:
            session_id: The session identifier to retrieve history for.
            limit: Maximum number of entries to return (default 50).

        Returns:
            A list of memory entries representing the conversation history.
        """
        ...


class EmbeddingPort(ABC):
    """Port for generating vector embeddings for memory entries.

    Infrastructure adapters implement this port to generate
    embedding vectors used for similarity-based memory retrieval.
    """

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text.

        Args:
            text: The text content to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple texts.

        More efficient than calling embed() multiple times when
        processing batches of memory entries.

        Args:
            texts: A list of text strings to embed.

        Returns:
            A list of embedding vectors, one per input text.
        """
        ...
