"""Tests for the plain text document loader."""

import pytest

from sona_knowledge.domain.models import DocumentType
from sona_knowledge.infrastructure.loaders.text_loader import TextLoader


@pytest.fixture
def loader() -> TextLoader:
    return TextLoader()


class TestTextLoader:
    """Tests for TextLoader."""

    @pytest.mark.asyncio
    async def test_load_simple_text(self, loader: TextLoader) -> None:
        doc = await loader.load("Hello, world! This is a test document.")
        assert doc.content == "Hello, world! This is a test document."
        assert doc.doc_type == DocumentType.TEXT

    @pytest.mark.asyncio
    async def test_load_with_title(self, loader: TextLoader) -> None:
        doc = await loader.load("Some content", title="My Title")
        assert doc.title == "My Title"

    @pytest.mark.asyncio
    async def test_load_with_doc_id(self, loader: TextLoader) -> None:
        doc = await loader.load("content", doc_id="custom-id")
        assert doc.id == "custom-id"

    @pytest.mark.asyncio
    async def test_load_generates_uuid(self, loader: TextLoader) -> None:
        doc = await loader.load("content")
        assert len(doc.id) > 0

    @pytest.mark.asyncio
    async def test_load_extracts_title_from_first_line(self, loader: TextLoader) -> None:
        doc = await loader.load("First Line Title\nSecond line content")
        assert doc.title == "First Line Title"

    @pytest.mark.asyncio
    async def test_load_metadata_has_word_count(self, loader: TextLoader) -> None:
        doc = await loader.load("one two three four five")
        assert doc.metadata is not None
        assert doc.metadata["word_count"] == 5

    @pytest.mark.asyncio
    async def test_load_with_source_url(self, loader: TextLoader) -> None:
        doc = await loader.load("content", source_url="https://example.com/file.txt")
        assert doc.source_url == "https://example.com/file.txt"

    @pytest.mark.asyncio
    async def test_load_multiline_text(self, loader: TextLoader) -> None:
        text = "Line 1\nLine 2\nLine 3"
        doc = await loader.load(text)
        assert doc.content == text

    @pytest.mark.asyncio
    async def test_load_empty_text(self, loader: TextLoader) -> None:
        doc = await loader.load("")
        assert doc.content == ""

    def test_supports_txt_extension(self, loader: TextLoader) -> None:
        assert loader.supports("document.txt") is True

    def test_supports_plain_text(self, loader: TextLoader) -> None:
        assert loader.supports("Just some text content") is True

    def test_does_not_support_html(self, loader: TextLoader) -> None:
        assert loader.supports("<!DOCTYPE html>") is False

    def test_does_not_support_markdown_heading(self, loader: TextLoader) -> None:
        assert loader.supports("# Heading") is False
