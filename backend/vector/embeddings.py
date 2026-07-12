"""Embedding engine — text chunking and embedding generation.

Provides text chunking with overlap and a lightweight local
embedding generator for development. In production, use
OpenAI or provider embeddings via the provider system.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TextChunk:
    """A chunk of text with position metadata."""

    content: str
    chunk_index: int
    start_char: int
    end_char: int
    token_estimate: int


def estimate_tokens(text: str) -> int:
    """Estimate token count (~4 chars per token)."""
    return max(1, len(text) // 4)


def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
    min_chunk_size: int = 50,
) -> list[TextChunk]:
    """Split text into overlapping chunks by token estimate.

    Args:
        text: The text to chunk.
        chunk_size: Target tokens per chunk.
        chunk_overlap: Overlap tokens between chunks.
        min_chunk_size: Minimum chunk size (skip smaller).

    Returns:
        List of TextChunks.
    """
    if not text.strip():
        return []

    # Convert token sizes to character estimates
    char_size = chunk_size * 4
    char_overlap = chunk_overlap * 4
    min_chars = min_chunk_size * 4

    chunks: list[TextChunk] = []
    start = 0
    idx = 0

    while start < len(text):
        end = min(start + char_size, len(text))

        # Try to break at sentence/paragraph boundary
        if end < len(text):
            for sep in ("\n\n", "\n", ". ", "! ", "? ", "; "):
                break_pos = text.rfind(sep, start + min_chars, end)
                if break_pos > start:
                    end = break_pos + len(sep)
                    break

        chunk_content = text[start:end].strip()
        if len(chunk_content) >= min_chars:
            chunks.append(
                TextChunk(
                    content=chunk_content,
                    chunk_index=idx,
                    start_char=start,
                    end_char=end,
                    token_estimate=estimate_tokens(chunk_content),
                )
            )
            idx += 1

        # Advance start position with overlap, ensuring forward progress
        new_start = end - char_overlap
        if new_start <= start:
            new_start = end  # Force forward progress
        start = new_start
        if start >= len(text) - min_chars:
            break

    return chunks


class EmbeddingEngine:
    """Generates embeddings for text chunks.

    Uses a deterministic hash-based embedding for development.
    In production, connect to OpenAI/Ollama embedding APIs.
    """

    def __init__(self, dimensions: int = 384) -> None:
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_text(self, text: str) -> list[float]:
        """Generate a deterministic embedding for text.

        Uses SHA-256 hash expanded to target dimensions.
        Produces consistent embeddings for the same input.
        Semantically similar texts will NOT be close — this is
        for development/testing only. Use provider embeddings
        for semantic search in production.
        """
        hash_bytes = hashlib.sha256(text.lower().strip().encode()).digest()
        # Expand hash to fill dimensions
        values: list[float] = []
        for i in range(self._dimensions):
            byte_idx = i % len(hash_bytes)
            # Combine byte position with index for more variance
            raw = hash_bytes[byte_idx] ^ (i & 0xFF)
            values.append((raw / 255.0) * 2 - 1)  # Normalize to [-1, 1]

        # Normalize to unit vector
        norm = math.sqrt(sum(v * v for v in values))
        if norm > 0:
            values = [v / norm for v in values]
        return values

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        return [self.embed_text(t) for t in texts]
