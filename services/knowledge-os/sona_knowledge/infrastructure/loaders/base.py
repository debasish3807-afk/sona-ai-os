"""Base document loader interface."""

from abc import ABC, abstractmethod

from sona_knowledge.domain.models import Document


class DocumentLoader(ABC):
    """Abstract base class for document loaders.

    Each loader handles a specific document format or source type.
    """

    @abstractmethod
    async def load(self, source: str, **kwargs: object) -> Document:
        """Load a document from the given source.

        Args:
            source: Path, URL, or content string depending on loader type.
            **kwargs: Additional loader-specific parameters.

        Returns:
            A Document instance with extracted content and metadata.
        """
        ...

    @abstractmethod
    def supports(self, source: str) -> bool:
        """Check if this loader supports the given source.

        Args:
            source: Path, URL, or content string to check.

        Returns:
            True if this loader can handle the source.
        """
        ...
