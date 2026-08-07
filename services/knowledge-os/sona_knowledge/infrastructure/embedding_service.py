"""Embedding service for Knowledge OS.

Provides deterministic hash-based embeddings for testing and development,
with the same interface suitable for real embedding providers.
"""

import hashlib
import math

import structlog

logger = structlog.get_logger()

EMBEDDING_DIM = 384


def _hash_to_embedding(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """Generate a deterministic embedding from text using SHA-256 hashing.

    Produces a normalized unit vector for consistent cosine similarity.

    Args:
        text: Input text to embed.
        dim: Dimensionality of the output vector.

    Returns:
        A normalized list of floats representing the embedding.
    """
    raw: list[float] = []
    chunk_idx = 0
    while len(raw) < dim:
        hash_input = f"{text}:{chunk_idx}".encode()
        digest = hashlib.sha256(hash_input).hexdigest()
        for i in range(0, len(digest), 8):
            if len(raw) >= dim:
                break
            val = int(digest[i : i + 8], 16)
            raw.append((val / 0xFFFFFFFF) * 2 - 1)
        chunk_idx += 1

    # Normalize to unit vector
    magnitude = math.sqrt(sum(x * x for x in raw))
    if magnitude > 0:
        return [x / magnitude for x in raw]
    return [0.0] * dim


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Returns a value between -1 and 1, where 1 means identical direction.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        Cosine similarity score.
    """
    if len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b, strict=True))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot / (mag_a * mag_b)


class EmbeddingService:
    """Local deterministic embedding service.

    Generates consistent hash-based embeddings suitable for testing
    and development without requiring external API calls.
    """

    def __init__(self, vector_size: int = EMBEDDING_DIM) -> None:
        """Initialize embedding service.

        Args:
            vector_size: Dimensionality of generated embeddings.
        """
        self._dim = vector_size

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._dim

    async def embed(self, text: str) -> list[float]:
        """Generate a deterministic embedding for a single text.

        Args:
            text: Input text to embed.

        Returns:
            A normalized embedding vector.
        """
        return _hash_to_embedding(text, self._dim)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate deterministic embeddings for multiple texts.

        Args:
            texts: List of input texts to embed.

        Returns:
            List of normalized embedding vectors.
        """
        logger.debug("embedding_batch", count=len(texts))
        return [_hash_to_embedding(t, self._dim) for t in texts]
