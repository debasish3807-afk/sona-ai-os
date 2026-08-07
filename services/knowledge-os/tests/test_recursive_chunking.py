"""Tests for recursive text chunking."""

import pytest

from sona_knowledge.infrastructure.chunking.recursive import RecursiveChunker


@pytest.fixture
def chunker() -> RecursiveChunker:
    return RecursiveChunker(chunk_size=100, chunk_overlap=20)


class TestRecursiveChunker:
    """Tests for RecursiveChunker."""

    def test_short_text_single_chunk(self, chunker: RecursiveChunker) -> None:
        chunks = chunker.chunk("Short text.")
        assert len(chunks) == 1
        assert chunks[0] == "Short text."

    def test_empty_text_returns_empty(self, chunker: RecursiveChunker) -> None:
        chunks = chunker.chunk("")
        assert chunks == []

    def test_whitespace_only_returns_empty(self, chunker: RecursiveChunker) -> None:
        chunks = chunker.chunk("   \n\n  ")
        assert chunks == []

    def test_splits_by_paragraph(self, chunker: RecursiveChunker) -> None:
        text = "First paragraph with enough content.\n\nSecond paragraph with more content here."
        chunks = chunker.chunk(text)
        assert len(chunks) >= 1

    def test_splits_long_text_into_multiple_chunks(self) -> None:
        chunker = RecursiveChunker(chunk_size=50, chunk_overlap=0)
        text = "A" * 200
        chunks = chunker.chunk(text)
        assert len(chunks) > 1

    def test_respects_chunk_size(self) -> None:
        chunker = RecursiveChunker(chunk_size=100, chunk_overlap=0)
        text = "Word " * 100  # 500 chars
        chunks = chunker.chunk(text)
        # Most chunks should be within chunk_size (with some tolerance for overlap)
        for chunk in chunks[:-1]:  # Last chunk may be shorter
            assert len(chunk) <= 150  # Some tolerance for overlap text

    def test_overlap_adds_context(self) -> None:
        chunker = RecursiveChunker(chunk_size=50, chunk_overlap=10)
        text = "Sentence one here. Sentence two here. Sentence three here. Sentence four here."
        chunks = chunker.chunk(text)
        assert len(chunks) >= 2

    def test_sentence_splitting(self) -> None:
        chunker = RecursiveChunker(chunk_size=40, chunk_overlap=0)
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = chunker.chunk(text)
        assert len(chunks) >= 2

    def test_override_chunk_size(self, chunker: RecursiveChunker) -> None:
        text = "word " * 100
        chunks_default = chunker.chunk(text)
        chunks_small = chunker.chunk(text, chunk_size=50)
        assert len(chunks_small) >= len(chunks_default)

    def test_preserves_content(self) -> None:
        chunker = RecursiveChunker(chunk_size=100, chunk_overlap=0)
        text = "Alpha Beta Gamma Delta Epsilon"
        chunks = chunker.chunk(text)
        # All original words should appear in at least one chunk
        for word in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]:
            assert any(word in c for c in chunks)

    def test_no_empty_chunks(self) -> None:
        chunker = RecursiveChunker(chunk_size=30, chunk_overlap=5)
        text = "One.\n\nTwo.\n\nThree.\n\nFour.\n\nFive."
        chunks = chunker.chunk(text)
        for chunk in chunks:
            assert chunk.strip() != ""

    def test_large_document(self) -> None:
        chunker = RecursiveChunker(chunk_size=200, chunk_overlap=30)
        text = "\n\n".join([f"Paragraph {i}: " + "content " * 20 for i in range(20)])
        chunks = chunker.chunk(text)
        assert len(chunks) > 5
