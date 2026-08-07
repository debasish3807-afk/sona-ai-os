"""Embedding service implementation.

Provides deterministic hash-based embeddings for local/testing use,
with cosine similarity computation.
"""

import hashlib
import math

from sona_memory.application.ports import EmbeddingPort

EMBEDDING_DIM = 128


def _hash_to_embedding(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """Generate a deterministic embedding from text using SHA-256 hashing.

    Produces a normalized unit vector for consistent cosine similarity.
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
    """
    if len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b, strict=True))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot / (mag_a * mag_b)


class EmbeddingService(EmbeddingPort):
    """Local deterministic embedding service.

    Generates consistent hash-based embeddings suitable for testing
    and development without requiring external API calls.
    """

    def __init__(self, dim: int = EMBEDDING_DIM) -> None:
        self._dim = dim

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._dim

    async def embed(self, text: str) -> list[float]:
        """Generate a deterministic embedding for a single text."""
        return _hash_to_embedding(text, self._dim)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate deterministic embeddings for multiple texts."""
        return [_hash_to_embedding(t, self._dim) for t in texts]
