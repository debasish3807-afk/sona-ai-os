"""Embedding providers for semantic memory."""

from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod

from config.logging import get_logger

logger = get_logger(__name__)

DIMENSION = 128


class EmbeddingProvider(ABC):
    """Abstract base for embedding providers."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text."""

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple texts."""


class SimpleEmbedding(EmbeddingProvider):
    """TF-IDF-like local embedding for development (no API needed).

    Produces deterministic 128-dimensional vectors from text using
    character-level hashing. Suitable for development and testing.
    """

    def __init__(self, dimension: int = DIMENSION) -> None:
        self._dimension = dimension

    async def embed(self, text: str) -> list[float]:
        """Generate a hash-based embedding vector."""
        return self._compute_vector(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple texts."""
        return [self._compute_vector(t) for t in texts]

    def _compute_vector(self, text: str) -> list[float]:
        """Compute a deterministic vector from text using hashing."""
        text = text.lower().strip()
        vector = [0.0] * self._dimension

        words = text.split()
        for i, word in enumerate(words):
            digest = hashlib.sha256(word.encode()).hexdigest()
            for j in range(self._dimension):
                char_idx = j % len(digest)
                value = int(digest[char_idx], 16) / 15.0
                weight = 1.0 / (1.0 + i * 0.1)
                vector[j] += value * weight

        magnitude = math.sqrt(sum(v * v for v in vector))
        if magnitude > 0:
            vector = [v / magnitude for v in vector]

        return vector
