"""Sliding window text chunking strategy."""

import structlog

from sona_knowledge.infrastructure.chunking.base import TextChunker

logger = structlog.get_logger()


class SlidingWindowChunker(TextChunker):
    """Sliding window text chunker.

    Creates fixed-size windows of text with configurable overlap (stride).
    Provides consistent chunk sizes for uniform embedding quality.
    """

    def __init__(self, window_size: int = 512, stride: int = 256) -> None:
        """Initialize the sliding window chunker.

        Args:
            window_size: Size of each window in characters.
            stride: Step size between windows (window_size - overlap).
        """
        self._window_size = window_size
        self._stride = stride

    def chunk(self, text: str, **kwargs: object) -> list[str]:
        """Split text into fixed-size overlapping windows.

        Args:
            text: The text to chunk.
            **kwargs: Optional 'window_size' and 'stride' overrides.

        Returns:
            A list of text chunks.
        """
        window_size = int(kwargs.get("window_size", 0)) or self._window_size
        stride = int(kwargs.get("stride", 0)) or self._stride

        if not text.strip():
            return []

        # If text is shorter than window, return as single chunk
        if len(text) <= window_size:
            return [text.strip()] if text.strip() else []

        chunks: list[str] = []
        position = 0

        while position < len(text):
            end = position + window_size
            window = text[position:end].strip()
            if window:
                chunks.append(window)
            position += stride

            # Avoid creating tiny trailing chunks
            if position < len(text) and len(text) - position < stride // 2:
                # Include remaining text in last chunk
                remaining = text[position:].strip()
                if remaining and remaining != chunks[-1] if chunks else True:
                    chunks.append(remaining)
                break

        logger.debug(
            "sliding_window_chunking_complete",
            input_length=len(text),
            chunks_count=len(chunks),
            window_size=window_size,
            stride=stride,
        )
        return chunks
