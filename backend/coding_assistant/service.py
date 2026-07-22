"""Coding Assistant Service — unified interface for coding operations."""

from __future__ import annotations

from typing import Any

from coding_assistant.analyzer import CodeAnalyzer, IndexResult
from coding_assistant.generator import CodeGenerator, GenerationResult, TestGenerationResult
from coding_assistant.reviewer import CodeReviewer, ReviewResult


class CodingAssistantService:
    """Unified service for all coding assistant capabilities."""

    def __init__(self, workspace_root: str | None = None) -> None:
        self._analyzer = CodeAnalyzer(workspace_root)
        self._reviewer = CodeReviewer()
        self._generator = CodeGenerator()

    async def index_workspace(self, path: str | None = None) -> IndexResult:
        """Index the workspace or a specific path."""
        return self._analyzer.index_directory(path)

    async def index_file(self, file_path: str) -> IndexResult:
        """Index a single file."""
        return self._analyzer.index_file(file_path)

    async def search_code(self, query: str, kind: str | None = None) -> list[dict[str, Any]]:
        """Search indexed code symbols."""
        symbols = self._analyzer.search_symbol(query, kind)
        return [
            {
                "name": s.name,
                "kind": s.kind,
                "file": s.file_path,
                "line": s.line,
                "column": s.column,
                "docstring": s.docstring[:200] if s.docstring else "",
                "parent": s.parent,
            }
            for s in symbols
        ]

    async def review_code(self, source: str, file_path: str = "unknown") -> ReviewResult:
        """Review source code for issues."""
        return self._reviewer.review(source, file_path)

    async def generate_tests(self, source: str, language: str = "python") -> TestGenerationResult:
        """Generate test code from source."""
        return self._generator.generate_tests(source, language)

    async def generate_documentation(
        self, source: str, language: str = "python"
    ) -> GenerationResult:
        """Generate documentation from source."""
        return self._generator.generate_documentation(source, language)

    async def refactor_code(self, source: str, language: str = "python") -> GenerationResult:
        """Apply refactoring to source code."""
        return self._generator.refactor_code(source, language)

    async def get_analyzer(self) -> CodeAnalyzer:
        """Get the code analyzer instance."""
        return self._analyzer

    async def get_stats(self) -> dict[str, Any]:
        """Get coding assistant statistics."""
        return self._analyzer.get_stats()
