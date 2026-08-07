"""Tests for the PDF document loader."""

import pytest

from sona_knowledge.domain.models import DocumentType
from sona_knowledge.infrastructure.loaders.pdf_loader import PDFLoader


@pytest.fixture
def loader() -> PDFLoader:
    return PDFLoader()


class TestPDFLoader:
    """Tests for PDFLoader."""

    @pytest.mark.asyncio
    async def test_load_basic_content(self, loader: PDFLoader) -> None:
        content = "Chapter 1: Introduction\n\nThis is the first chapter."
        doc = await loader.load(content)
        assert doc.content == content
        assert doc.doc_type == DocumentType.PDF

    @pytest.mark.asyncio
    async def test_extracts_title_from_first_line(self, loader: PDFLoader) -> None:
        content = "Document Title Here\n\nBody content follows."
        doc = await loader.load(content)
        assert doc.title == "Document Title Here"

    @pytest.mark.asyncio
    async def test_custom_title_overrides(self, loader: PDFLoader) -> None:
        doc = await loader.load("content", title="My PDF")
        assert doc.title == "My PDF"

    @pytest.mark.asyncio
    async def test_custom_doc_id(self, loader: PDFLoader) -> None:
        doc = await loader.load("content", doc_id="pdf-001")
        assert doc.id == "pdf-001"

    @pytest.mark.asyncio
    async def test_metadata_has_page_count(self, loader: PDFLoader) -> None:
        # Short content = 1 page
        doc = await loader.load("Short content")
        assert doc.metadata is not None
        assert doc.metadata["page_count"] >= 1

    @pytest.mark.asyncio
    async def test_metadata_has_word_count(self, loader: PDFLoader) -> None:
        doc = await loader.load("one two three four five")
        assert doc.metadata is not None
        assert doc.metadata["word_count"] == 5

    @pytest.mark.asyncio
    async def test_long_content_multiple_pages(self, loader: PDFLoader) -> None:
        # 10000 characters ~= 3+ pages
        content = "word " * 2000
        doc = await loader.load(content)
        assert doc.metadata is not None
        assert doc.metadata["page_count"] > 1

    @pytest.mark.asyncio
    async def test_with_source_url(self, loader: PDFLoader) -> None:
        doc = await loader.load("content", source_url="https://example.com/doc.pdf")
        assert doc.source_url == "https://example.com/doc.pdf"

    @pytest.mark.asyncio
    async def test_empty_content(self, loader: PDFLoader) -> None:
        doc = await loader.load("")
        assert doc.content == ""
        assert doc.title == "Untitled PDF"

    def test_supports_pdf_extension(self, loader: PDFLoader) -> None:
        assert loader.supports("document.pdf") is True

    def test_supports_pdf_magic(self, loader: PDFLoader) -> None:
        assert loader.supports("%PDF-1.5 binary content") is True

    def test_does_not_support_txt(self, loader: PDFLoader) -> None:
        assert loader.supports("document.txt") is False

    @pytest.mark.asyncio
    async def test_custom_page_count(self, loader: PDFLoader) -> None:
        doc = await loader.load("content", page_count=10)
        assert doc.metadata is not None
        assert doc.metadata["page_count"] == 10
