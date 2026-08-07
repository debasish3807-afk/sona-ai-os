"""Tests for workspace scanner."""

import pytest

from sona_research.domain.workspace_models import DocumentFormat
from sona_research.infrastructure.workspace.scanner import (
    WorkspaceScanner,
    detect_format,
    extract_title,
)


class TestDetectFormat:
    def test_markdown(self) -> None:
        assert detect_format("readme.md") == DocumentFormat.MARKDOWN
        assert detect_format("docs/guide.markdown") == DocumentFormat.MARKDOWN

    def test_source_code(self) -> None:
        assert detect_format("main.py") == DocumentFormat.SOURCE_CODE
        assert detect_format("app.ts") == DocumentFormat.SOURCE_CODE
        assert detect_format("lib.rs") == DocumentFormat.SOURCE_CODE
        assert detect_format("Main.java") == DocumentFormat.SOURCE_CODE

    def test_json(self) -> None:
        assert detect_format("config.json") == DocumentFormat.JSON

    def test_yaml(self) -> None:
        assert detect_format("config.yaml") == DocumentFormat.YAML
        assert detect_format("config.yml") == DocumentFormat.YAML

    def test_pdf(self) -> None:
        assert detect_format("doc.pdf") == DocumentFormat.PDF

    def test_text(self) -> None:
        assert detect_format("notes.txt") == DocumentFormat.TEXT

    def test_unknown_defaults_to_text(self) -> None:
        assert detect_format("file.xyz") == DocumentFormat.TEXT
        assert detect_format("noext") == DocumentFormat.TEXT


class TestExtractTitle:
    def test_simple_filename(self) -> None:
        assert extract_title("readme.md") == "Readme"

    def test_path_with_dirs(self) -> None:
        assert extract_title("/docs/user_guide.md") == "User Guide"

    def test_dashes(self) -> None:
        assert extract_title("my-project.py") == "My Project"

    def test_no_extension(self) -> None:
        assert extract_title("Makefile") == "Makefile"

    def test_nested_path(self) -> None:
        assert extract_title("/a/b/c/my_module.py") == "My Module"


class TestWorkspaceScannerScan:
    @pytest.fixture
    def scanner(self) -> WorkspaceScanner:
        s = WorkspaceScanner()
        s.add_file("/docs/readme.md", "# Welcome", size_bytes=100)
        s.add_file("/docs/guide.md", "## Guide content")
        s.add_file("/src/main.py", "import os", size_bytes=50, last_modified="2024-01-01")
        s.add_file("/src/utils.py", "def helper(): pass")
        s.add_file("/config.json", '{"key": "value"}')
        return s

    @pytest.mark.asyncio
    async def test_scan_all(self, scanner: WorkspaceScanner) -> None:
        docs = await scanner.scan("/")
        assert len(docs) == 5

    @pytest.mark.asyncio
    async def test_scan_subdirectory(self, scanner: WorkspaceScanner) -> None:
        docs = await scanner.scan("/docs")
        assert len(docs) == 2
        assert all(d.path.startswith("/docs") for d in docs)

    @pytest.mark.asyncio
    async def test_scan_src(self, scanner: WorkspaceScanner) -> None:
        docs = await scanner.scan("/src")
        assert len(docs) == 2
        assert all(d.format == DocumentFormat.SOURCE_CODE for d in docs)

    @pytest.mark.asyncio
    async def test_scan_detects_format(self, scanner: WorkspaceScanner) -> None:
        docs = await scanner.scan("/")
        formats = {d.path: d.format for d in docs}
        assert formats["/docs/readme.md"] == DocumentFormat.MARKDOWN
        assert formats["/src/main.py"] == DocumentFormat.SOURCE_CODE
        assert formats["/config.json"] == DocumentFormat.JSON

    @pytest.mark.asyncio
    async def test_scan_includes_metadata(self, scanner: WorkspaceScanner) -> None:
        docs = await scanner.scan("/src/main.py")
        assert len(docs) == 1
        doc = docs[0]
        assert doc.size_bytes == 50
        assert doc.last_modified == "2024-01-01"

    @pytest.mark.asyncio
    async def test_scan_auto_calculates_size(self, scanner: WorkspaceScanner) -> None:
        docs = await scanner.scan("/docs/guide.md")
        assert len(docs) == 1
        assert docs[0].size_bytes == len(b"## Guide content")

    @pytest.mark.asyncio
    async def test_scan_empty_root(self) -> None:
        s = WorkspaceScanner()
        docs = await s.scan("/")
        assert docs == []


class TestWorkspaceScannerByFormat:
    @pytest.fixture
    def scanner(self) -> WorkspaceScanner:
        s = WorkspaceScanner()
        s.add_file("/a.md", "# A")
        s.add_file("/b.py", "# B")
        s.add_file("/c.json", "{}")
        s.add_file("/d.txt", "text")
        return s

    @pytest.mark.asyncio
    async def test_filter_single_format(self, scanner: WorkspaceScanner) -> None:
        docs = await scanner.scan_by_format("/", [DocumentFormat.MARKDOWN])
        assert len(docs) == 1
        assert docs[0].format == DocumentFormat.MARKDOWN

    @pytest.mark.asyncio
    async def test_filter_multiple_formats(self, scanner: WorkspaceScanner) -> None:
        docs = await scanner.scan_by_format("/", [DocumentFormat.MARKDOWN, DocumentFormat.JSON])
        assert len(docs) == 2

    @pytest.mark.asyncio
    async def test_filter_none_returns_all(self, scanner: WorkspaceScanner) -> None:
        docs = await scanner.scan_by_format("/", None)
        assert len(docs) == 4
