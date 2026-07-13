"""Simple inverted index for fast memory search."""

from __future__ import annotations

import re

from config.logging import get_logger

logger = get_logger(__name__)


class MemoryIndex:
    """Simple inverted index for fast text search across memory stores."""

    def __init__(self) -> None:
        self._index: dict[str, set[str]] = {}
        self._documents: dict[str, set[str]] = {}
        self._tags: dict[str, set[str]] = {}

    def add(self, doc_id: str, content: str, tags: list[str] | None = None) -> None:
        """Add a document to the index.

        Args:
            doc_id: Unique document identifier.
            content: Text content to index.
            tags: Optional tags for the document.
        """
        tokens = self._tokenize(content)
        self._documents[doc_id] = tokens

        for token in tokens:
            if token not in self._index:
                self._index[token] = set()
            self._index[token].add(doc_id)

        if tags:
            self._tags[doc_id] = set(tags)
            for tag in tags:
                tag_lower = tag.lower()
                if tag_lower not in self._index:
                    self._index[tag_lower] = set()
                self._index[tag_lower].add(doc_id)

    def search(self, query: str, limit: int = 10) -> list[str]:
        """Search for documents matching query.

        Args:
            query: Search query string.
            limit: Maximum number of doc_ids to return.

        Returns:
            List of matching document IDs ranked by relevance.
        """
        tokens = self._tokenize(query)
        if not tokens:
            return []

        scores: dict[str, int] = {}
        for token in tokens:
            for doc_id in self._index.get(token, set()):
                scores[doc_id] = scores.get(doc_id, 0) + 1

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [doc_id for doc_id, _ in ranked[:limit]]

    def remove(self, doc_id: str) -> None:
        """Remove a document from the index.

        Args:
            doc_id: Document ID to remove.
        """
        tokens = self._documents.pop(doc_id, set())
        for token in tokens:
            if token in self._index:
                self._index[token].discard(doc_id)
                if not self._index[token]:
                    del self._index[token]

        tags = self._tags.pop(doc_id, set())
        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower in self._index:
                self._index[tag_lower].discard(doc_id)
                if not self._index[tag_lower]:
                    del self._index[tag_lower]

    @property
    def size(self) -> int:
        """Number of indexed documents."""
        return len(self._documents)

    def _tokenize(self, text: str) -> set[str]:
        """Tokenize text into lowercase words."""
        words = re.findall(r"\w+", text.lower())
        return {w for w in words if len(w) > 1}
