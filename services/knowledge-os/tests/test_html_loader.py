"""Tests for the HTML document loader."""

import pytest

from sona_knowledge.domain.models import DocumentType
from sona_knowledge.infrastructure.loaders.html_loader import HTMLLoader


@pytest.fixture
def loader() -> HTMLLoader:
    return HTMLLoader()


class TestHTMLLoader:
    """Tests for HTMLLoader."""

    @pytest.mark.asyncio
    async def test_load_basic_html(self, loader: HTMLLoader) -> None:
        html = "<html><body><p>Hello world</p></body></html>"
        doc = await loader.load(html)
        assert "Hello world" in doc.content
        assert doc.doc_type == DocumentType.HTML

    @pytest.mark.asyncio
    async def test_strips_html_tags(self, loader: HTMLLoader) -> None:
        html = "<p>First</p><p>Second</p>"
        doc = await loader.load(html)
        assert "<p>" not in doc.content
        assert "First" in doc.content
        assert "Second" in doc.content

    @pytest.mark.asyncio
    async def test_extracts_title_from_title_tag(self, loader: HTMLLoader) -> None:
        html = "<html><head><title>My Page</title></head><body>Content</body></html>"
        doc = await loader.load(html)
        assert doc.title == "My Page"

    @pytest.mark.asyncio
    async def test_extracts_title_from_h1(self, loader: HTMLLoader) -> None:
        html = "<html><body><h1>Heading</h1><p>Content</p></body></html>"
        doc = await loader.load(html)
        assert doc.title == "Heading"

    @pytest.mark.asyncio
    async def test_custom_title_overrides(self, loader: HTMLLoader) -> None:
        html = "<html><head><title>Original</title></head><body>X</body></html>"
        doc = await loader.load(html, title="Custom")
        assert doc.title == "Custom"

    @pytest.mark.asyncio
    async def test_removes_script_tags(self, loader: HTMLLoader) -> None:
        html = "<p>Text</p><script>alert('xss')</script><p>More</p>"
        doc = await loader.load(html)
        assert "alert" not in doc.content
        assert "Text" in doc.content
        assert "More" in doc.content

    @pytest.mark.asyncio
    async def test_removes_style_tags(self, loader: HTMLLoader) -> None:
        html = "<p>Text</p><style>.cls{color:red}</style>"
        doc = await loader.load(html)
        assert "color" not in doc.content
        assert "Text" in doc.content

    @pytest.mark.asyncio
    async def test_decodes_html_entities(self, loader: HTMLLoader) -> None:
        html = "<p>A &amp; B &lt; C &gt; D</p>"
        doc = await loader.load(html)
        assert "A & B" in doc.content
        assert "< C >" in doc.content

    @pytest.mark.asyncio
    async def test_metadata_has_word_count(self, loader: HTMLLoader) -> None:
        html = "<p>one two three</p>"
        doc = await loader.load(html)
        assert doc.metadata is not None
        assert doc.metadata["word_count"] >= 3

    @pytest.mark.asyncio
    async def test_metadata_has_original_length(self, loader: HTMLLoader) -> None:
        html = "<p>content</p>"
        doc = await loader.load(html)
        assert doc.metadata is not None
        assert doc.metadata["original_length"] == len(html)

    def test_supports_html_extension(self, loader: HTMLLoader) -> None:
        assert loader.supports("page.html") is True
        assert loader.supports("page.htm") is True

    def test_supports_doctype(self, loader: HTMLLoader) -> None:
        assert loader.supports("<!DOCTYPE html><html>...") is True

    def test_supports_html_tag(self, loader: HTMLLoader) -> None:
        assert loader.supports("<html><body>test</body></html>") is True

    def test_does_not_support_plain_text(self, loader: HTMLLoader) -> None:
        assert loader.supports("Just text") is False

    @pytest.mark.asyncio
    async def test_normalizes_whitespace(self, loader: HTMLLoader) -> None:
        html = "<p>  Lots   of    spaces  </p>"
        doc = await loader.load(html)
        assert "  " not in doc.content
