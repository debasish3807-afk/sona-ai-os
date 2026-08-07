"""Base text chunker interface."""

from abc import ABC, abstractmethod


class TextChunker(ABC):
    """Abstract base class for text chunking strategies.

    Text chunkers split large documents into smaller chunks for embedding
    and retrieval. Different strategies offer trade-offs between chunk
    coherence, overlap, and size consistency.
    """

    @abstractmethod
    def chunk(self, text: str, **kwargs: object) -> list[str]:
        """Split text into chunks.

        Args:
            text: The text content to chunk.
            **kwargs: Strategy-specific parameters.

        Returns:
            A list of text chunks.
        """
        ...
