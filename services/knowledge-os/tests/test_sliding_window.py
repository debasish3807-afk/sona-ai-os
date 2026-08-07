"""Tests for sliding window text chunking."""

import pytest

from sona_knowledge.infrastructure.chunking.sliding_window import SlidingWindowChunker


@pytest.fixture
def chunker() -> SlidingWindowChunker:
    return SlidingWindowChunker(window_size=100, stride=50)


class TestSlidingWindowChunker:
    """Tests for SlidingWindowChunker."""

    def test_short_text_single_chunk(self, chunker: SlidingWindowChunker) -> None:
        chunks = chunker.chunk("Short text.")
        assert len(chunks) == 1
        assert chunks[0] == "Short text."

    def test_empty_text_returns_empty(self, chunker: SlidingWindowChunker) -> None:
        chunks = chunker.chunk("")
        assert chunks == []

    def test_whitespace_only_returns_empty(self, chunker: SlidingWindowChunker) -> None:
        chunks = chunker.chunk("   \n   ")
        assert chunks == []

    def test_splits_by_window_size(self) -> None:
        chunker = SlidingWindowChunker(window_size=50, stride=50)
        text = "A" * 150
        chunks = chunker.chunk(text)
        assert len(chunks) == 3

    def test_overlap_between_windows(self) -> None:
        chunker = SlidingWindowChunker(window_size=100, stride=50)
        text = "A" * 200
        chunks = chunker.chunk(text)
        assert len(chunks) >= 3
        # With stride=50 and window=100, overlap is 50 chars

    def test_window_size_respected(self) -> None:
        chunker = SlidingWindowChunker(window_size=80, stride=40)
        text = "X" * 300
        chunks = chunker.chunk(text)
        for chunk in chunks:
            assert len(chunk) <= 80

    def test_override_window_size(self, chunker: SlidingWindowChunker) -> None:
        text = "Y" * 300
        chunks_default = chunker.chunk(text)
        chunks_small = chunker.chunk(text, window_size=50, stride=25)
        assert len(chunks_small) >= len(chunks_default)

    def test_stride_equals_window_no_overlap(self) -> None:
        chunker = SlidingWindowChunker(window_size=50, stride=50)
        text = "ABCDE" * 30  # 150 chars
        chunks = chunker.chunk(text)
        # Non-overlapping windows
        assert len(chunks) == 3

    def test_stride_half_window_gives_overlap(self) -> None:
        chunker = SlidingWindowChunker(window_size=100, stride=50)
        text = "Z" * 200
        chunks = chunker.chunk(text)
        # 200 chars, stride 50: positions 0, 50, 100, 150
        assert len(chunks) >= 3

    def test_preserves_all_content(self) -> None:
        chunker = SlidingWindowChunker(window_size=50, stride=25)
        text = "Hello World " * 10
        chunks = chunker.chunk(text)
        # All characters should appear in at least one chunk
        combined = "".join(chunks)
        for char in text.strip():
            assert char in combined

    def test_no_empty_chunks(self) -> None:
        chunker = SlidingWindowChunker(window_size=30, stride=15)
        text = "Content " * 20
        chunks = chunker.chunk(text)
        for chunk in chunks:
            assert chunk.strip() != ""

    def test_large_document(self) -> None:
        chunker = SlidingWindowChunker(window_size=200, stride=100)
        text = "Word " * 500  # 2500 chars
        chunks = chunker.chunk(text)
        assert len(chunks) > 10
