"""Tests for workspace content extractors."""

import pytest

from sona_research.domain.workspace_models import DocumentFormat
from sona_research.infrastructure.workspace.extractors import ContentExtractors


class TestMarkdownExtraction:
    @pytest.mark.asyncio
    async def test_strips_headers(self) -> None:
        text = await ContentExtractors.extract("# Hello\n## World", DocumentFormat.MARKDOWN)
        assert "#" not in text
        assert "Hello" in text
        assert "World" in text

    @pytest.mark.asyncio
    async def test_strips_bold(self) -> None:
        text = await ContentExtractors.extract("**bold text**", DocumentFormat.MARKDOWN)
        assert "**" not in text
        assert "bold text" in text

    @pytest.mark.asyncio
    async def test_strips_links(self) -> None:
        text = await ContentExtractors.extract(
            "[click](http://example.com)", DocumentFormat.MARKDOWN
        )
        assert "click" in text
        assert "http://example.com" not in text

    @pytest.mark.asyncio
    async def test_strips_code_blocks(self) -> None:
        md = "Before\n```python\ncode = True\n```\nAfter"
        text = await ContentExtractors.extract(md, DocumentFormat.MARKDOWN)
        assert "code = True" not in text
        assert "Before" in text
        assert "After" in text

    @pytest.mark.asyncio
    async def test_strips_inline_code(self) -> None:
        text = await ContentExtractors.extract("Use `foo()` here", DocumentFormat.MARKDOWN)
        assert "`" not in text

    @pytest.mark.asyncio
    async def test_strips_images(self) -> None:
        text = await ContentExtractors.extract("![alt](image.png)", DocumentFormat.MARKDOWN)
        assert "image.png" not in text
        assert "alt" in text

    @pytest.mark.asyncio
    async def test_strips_list_markers(self) -> None:
        md = "- item 1\n- item 2\n1. numbered"
        text = await ContentExtractors.extract(md, DocumentFormat.MARKDOWN)
        assert "item 1" in text
        assert "numbered" in text


class TestSourceCodeExtraction:
    @pytest.mark.asyncio
    async def test_extracts_comments(self) -> None:
        code = "# This is a comment\nx = 1"
        text = await ContentExtractors.extract(code, DocumentFormat.SOURCE_CODE)
        assert "This is a comment" in text

    @pytest.mark.asyncio
    async def test_extracts_docstrings(self) -> None:
        code = '"""Module docstring."""\ndef foo(): pass'
        text = await ContentExtractors.extract(code, DocumentFormat.SOURCE_CODE)
        assert "Module docstring" in text

    @pytest.mark.asyncio
    async def test_extracts_function_defs(self) -> None:
        code = "def my_function():\n    pass\n\nclass MyClass:\n    pass"
        text = await ContentExtractors.extract(code, DocumentFormat.SOURCE_CODE)
        assert "my_function" in text
        assert "MyClass" in text

    @pytest.mark.asyncio
    async def test_extracts_js_comments(self) -> None:
        code = "// This is JS\nconst x = 1;"
        text = await ContentExtractors.extract(code, DocumentFormat.SOURCE_CODE)
        assert "This is JS" in text


class TestJsonExtraction:
    @pytest.mark.asyncio
    async def test_extracts_structure(self) -> None:
        json_str = '{"name": "test", "version": "1.0"}'
        text = await ContentExtractors.extract(json_str, DocumentFormat.JSON)
        assert "name" in text
        assert "version" in text

    @pytest.mark.asyncio
    async def test_handles_nested(self) -> None:
        json_str = '{"config": {"host": "localhost", "port": 8080}}'
        text = await ContentExtractors.extract(json_str, DocumentFormat.JSON)
        assert "config" in text
        assert "host" in text

    @pytest.mark.asyncio
    async def test_handles_arrays(self) -> None:
        json_str = '{"items": [1, 2, 3]}'
        text = await ContentExtractors.extract(json_str, DocumentFormat.JSON)
        assert "items" in text

    @pytest.mark.asyncio
    async def test_handles_invalid_json(self) -> None:
        text = await ContentExtractors.extract("not json {", DocumentFormat.JSON)
        assert text == "not json {"


class TestYamlExtraction:
    @pytest.mark.asyncio
    async def test_strips_comments(self) -> None:
        yaml_str = "# comment\nkey: value\n# another comment"
        text = await ContentExtractors.extract(yaml_str, DocumentFormat.YAML)
        assert "key: value" in text
        assert "# comment" not in text

    @pytest.mark.asyncio
    async def test_preserves_structure(self) -> None:
        yaml_str = "name: test\nversion: 1.0\n"
        text = await ContentExtractors.extract(yaml_str, DocumentFormat.YAML)
        assert "name: test" in text
        assert "version: 1.0" in text


class TestPdfExtraction:
    @pytest.mark.asyncio
    async def test_strips_pdf_markers(self) -> None:
        text = await ContentExtractors.extract("%PDF-Some content%%EOF", DocumentFormat.PDF)
        assert "%PDF-" not in text
        assert "%%EOF" not in text
        assert "Some content" in text


class TestTextExtraction:
    @pytest.mark.asyncio
    async def test_passthrough(self) -> None:
        text = await ContentExtractors.extract("Plain text content", DocumentFormat.TEXT)
        assert text == "Plain text content"

    @pytest.mark.asyncio
    async def test_docx_passthrough(self) -> None:
        text = await ContentExtractors.extract("Doc content", DocumentFormat.DOCX)
        assert text == "Doc content"
