"""Tests for the Markdown document loader."""

import pytest

from sona_knowledge.domain.models import DocumentType
from sona_knowledge.infrastructure.loaders.markdown_loader import MarkdownLoader


@pytest.fixture
def loader() -> MarkdownLoader:
    return MarkdownLoader()


class TestMarkdownLoader:
    """Tests for MarkdownLoader."""

    @pytest.mark.asyncio
    async def test_load_basic_markdown(self, loader: MarkdownLoader) -> None:
        md = "# Hello\n\nThis is a paragraph."
        doc = await loader.load(md)
        assert doc.content == md
        assert doc.doc_type == DocumentType.MARKDOWN

    @pytest.mark.asyncio
    async def test_extracts_title_from_h1(self, loader: MarkdownLoader) -> None:
        md = "# My Document\n\nContent here."
        doc = await loader.load(md)
        assert doc.title == "My Document"

    @pytest.mark.asyncio
    async def test_custom_title_overrides(self, loader: MarkdownLoader) -> None:
        md = "# Original Title\n\nContent."
        doc = await loader.load(md, title="Custom Title")
        assert doc.title == "Custom Title"

    @pytest.mark.asyncio
    async def test_extracts_headings_metadata(self, loader: MarkdownLoader) -> None:
        md = "# Title\n## Section 1\n### Subsection\n## Section 2"
        doc = await loader.load(md)
        assert doc.metadata is not None
        headings = doc.metadata["headings"]
        assert len(headings) == 4
        assert headings[0] == {"level": 1, "text": "Title"}
        assert headings[1] == {"level": 2, "text": "Section 1"}
        assert headings[2] == {"level": 3, "text": "Subsection"}

    @pytest.mark.asyncio
    async def test_word_count_in_metadata(self, loader: MarkdownLoader) -> None:
        md = "# Title\n\nOne two three four."
        doc = await loader.load(md)
        assert doc.metadata is not None
        # word count includes all words (Title + One two three four.)
        assert doc.metadata["word_count"] == 6

    @pytest.mark.asyncio
    async def test_load_with_doc_id(self, loader: MarkdownLoader) -> None:
        doc = await loader.load("# Doc", doc_id="md-001")
        assert doc.id == "md-001"

    @pytest.mark.asyncio
    async def test_load_without_heading(self, loader: MarkdownLoader) -> None:
        md = "Just plain text in a markdown file."
        doc = await loader.load(md)
        assert doc.title == "Just plain text in a markdown file."

    @pytest.mark.asyncio
    async def test_load_with_source_url(self, loader: MarkdownLoader) -> None:
        doc = await loader.load("# Doc", source_url="https://github.com/readme.md")
        assert doc.source_url == "https://github.com/readme.md"

    @pytest.mark.asyncio
    async def test_empty_markdown(self, loader: MarkdownLoader) -> None:
        doc = await loader.load("")
        assert doc.content == ""
        assert doc.title == "Untitled Markdown"

    def test_supports_md_extension(self, loader: MarkdownLoader) -> None:
        assert loader.supports("readme.md") is True

    def test_supports_h1_prefix(self, loader: MarkdownLoader) -> None:
        assert loader.supports("# Title") is True

    def test_does_not_support_plain_text(self, loader: MarkdownLoader) -> None:
        assert loader.supports("Just text") is False

    @pytest.mark.asyncio
    async def test_multiple_h1_headings(self, loader: MarkdownLoader) -> None:
        md = "# First\n# Second\n# Third"
        doc = await loader.load(md)
        assert doc.title == "First"  # First H1 wins
