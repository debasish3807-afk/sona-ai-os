"""Recursive text chunking strategy."""

import structlog

from sona_knowledge.infrastructure.chunking.base import TextChunker

logger = structlog.get_logger()


class RecursiveChunker(TextChunker):
    """Recursive text chunker.

    Splits text by progressively smaller separators (paragraphs, sentences,
    words) until the target chunk size is reached. Maintains overlap between
    consecutive chunks for context continuity.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50) -> None:
        """Initialize the recursive chunker.

        Args:
            chunk_size: Maximum number of characters per chunk.
            chunk_overlap: Number of characters to overlap between chunks.
        """
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._separators = ["\n\n", "\n", ". ", " "]

    def chunk(self, text: str, **kwargs: object) -> list[str]:
        """Split text recursively by paragraphs, sentences, then words.

        Args:
            text: The text to chunk.
            **kwargs: Optional 'chunk_size' and 'chunk_overlap' overrides.

        Returns:
            A list of text chunks.
        """
        chunk_size = int(kwargs.get("chunk_size", 0)) or self._chunk_size
        chunk_overlap = int(kwargs.get("chunk_overlap", 0)) or self._chunk_overlap

        if not text.strip():
            return []

        chunks = self._recursive_split(text, chunk_size, 0)
        # Apply overlap merging
        result = self._apply_overlap(chunks, chunk_overlap)

        logger.debug(
            "recursive_chunking_complete",
            input_length=len(text),
            chunks_count=len(result),
        )
        return result

    def _recursive_split(self, text: str, chunk_size: int, sep_idx: int) -> list[str]:
        """Recursively split text using separators at increasing granularity."""
        if len(text) <= chunk_size:
            return [text.strip()] if text.strip() else []

        if sep_idx >= len(self._separators):
            # Last resort: hard split by character count
            return self._hard_split(text, chunk_size)

        separator = self._separators[sep_idx]
        parts = text.split(separator)

        chunks: list[str] = []
        current = ""

        for part in parts:
            candidate = current + separator + part if current else part
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current.strip():
                    chunks.append(current.strip())
                # If single part exceeds chunk_size, split further
                if len(part) > chunk_size:
                    sub_chunks = self._recursive_split(part, chunk_size, sep_idx + 1)
                    chunks.extend(sub_chunks)
                    current = ""
                else:
                    current = part

        if current.strip():
            chunks.append(current.strip())

        return chunks

    def _hard_split(self, text: str, chunk_size: int) -> list[str]:
        """Hard-split text by character count when no separators work."""
        chunks: list[str] = []
        for i in range(0, len(text), chunk_size):
            chunk = text[i : i + chunk_size].strip()
            if chunk:
                chunks.append(chunk)
        return chunks

    def _apply_overlap(self, chunks: list[str], overlap: int) -> list[str]:
        """Apply overlap between consecutive chunks.

        Prepends the last `overlap` characters from the previous chunk
        to the beginning of the next chunk.
        """
        if overlap <= 0 or len(chunks) <= 1:
            return chunks

        result = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-overlap:]
            # Only add overlap if it doesn't duplicate the chunk start
            if not chunks[i].startswith(prev_tail):
                result.append(prev_tail + " " + chunks[i])
            else:
                result.append(chunks[i])

        return result
