"""Code Analyzer — repository indexing and code analysis."""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SymbolInfo:
    """Information about a code symbol (function, class, variable)."""

    name: str
    kind: str  # "function", "class", "method", "variable", "import"
    file_path: str
    line: int
    column: int
    docstring: str = ""
    source: str = ""
    parent: str = ""
    dependencies: list[str] = field(default_factory=list)


@dataclass
class DependencyInfo:
    """Information about a dependency between files."""

    source: str
    target: str
    kind: str  # "import", "inherit", "call"
    line: int


@dataclass
class IndexResult:
    """Result of indexing a repository or directory."""

    files: int = 0
    symbols: list[SymbolInfo] = field(default_factory=list)
    dependencies: list[DependencyInfo] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class CodeAnalyzer:
    """Analyzes Python code for symbols, dependencies, and structure.

    Supports:
        - AST-based symbol extraction (functions, classes, imports)
        - Dependency graph building
        - Docstring extraction
        - File-change detection for incremental reindexing
    """

    SUPPORTED_EXTENSIONS = {
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".rs",
        ".go",
        ".java",
        ".kt",
        ".swift",
        ".rb",
        ".php",
    }

    def __init__(self, workspace_root: str | None = None) -> None:
        self._root = Path(workspace_root or os.getcwd()).resolve()
        self._index: dict[str, IndexResult] = {}

    def index_directory(self, path: str | None = None) -> IndexResult:
        """Index a directory within the workspace."""
        target = self._root / (path or ".")
        if not target.exists():
            return IndexResult(errors=[f"Path does not exist: {target}"])

        result = IndexResult()
        for file_path in target.glob("**/*.py"):
            if file_path.is_file() and self._should_index(file_path):
                file_result = self._index_file(file_path)
                result.files += 1
                result.symbols.extend(file_result.symbols)
                result.dependencies.extend(file_result.dependencies)
                result.errors.extend(file_result.errors)
                self._index[str(file_path)] = file_result
        return result

    def index_file(self, file_path: str) -> IndexResult:
        """Index a single file."""
        path = Path(file_path).resolve()
        if not path.is_file():
            return IndexResult(errors=[f"File does not exist: {file_path}"])
        result = self._index_file(path)
        self._index[str(path)] = result
        return result

    def _should_index(self, path: Path) -> bool:
        """Check if a file should be (re)indexed."""
        ext = path.suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            return False
        skip_dirs = {".git", "node_modules", "__pycache__", ".tox", ".mypy_cache", ".ruff_cache"}
        for part in path.parts:
            if part in skip_dirs:
                return False
        return True

    def _index_file(self, path: Path) -> IndexResult:
        """Index a single Python file using AST."""
        result = IndexResult()
        str_path = str(path)
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str_path)
        except SyntaxError as e:
            result.errors.append(f"Syntax error in {str_path}: {e}")
            return result

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                docstring = ast.get_docstring(node) or ""
                end_line = node.end_lineno or node.lineno
                result.symbols.append(
                    SymbolInfo(
                        name=node.name,
                        kind="function",
                        file_path=str_path,
                        line=node.lineno,
                        column=node.col_offset,
                        docstring=docstring,
                        source=self._get_source_lines(source, node.lineno, end_line),
                    )
                )
            elif isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node) or ""
                methods = [
                    n.name
                    for n in ast.walk(node)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                end_line = node.end_lineno or node.lineno
                result.symbols.append(
                    SymbolInfo(
                        name=node.name,
                        kind="class",
                        file_path=str_path,
                        line=node.lineno,
                        column=node.col_offset,
                        docstring=docstring,
                        source=self._get_source_lines(source, node.lineno, end_line),
                        dependencies=methods,
                    )
                )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    result.symbols.append(
                        SymbolInfo(
                            name=alias.asname or alias.name,
                            kind="import",
                            file_path=str_path,
                            line=node.lineno,
                            column=node.col_offset,
                        )
                    )
                    result.dependencies.append(
                        DependencyInfo(
                            source=str_path,
                            target=alias.name,
                            kind="import",
                            line=node.lineno,
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    target = f"{module}.{alias.name}" if module else alias.name
                    result.symbols.append(
                        SymbolInfo(
                            name=alias.asname or alias.name,
                            kind="import",
                            file_path=str_path,
                            line=node.lineno,
                            column=node.col_offset,
                        )
                    )
                    result.dependencies.append(
                        DependencyInfo(
                            source=str_path,
                            target=target,
                            kind="import",
                            line=node.lineno,
                        )
                    )
        return result

    def search_symbol(self, query: str, kind: str | None = None) -> list[SymbolInfo]:
        """Search indexed symbols by name."""
        results = []
        for file_index in self._index.values():
            for sym in file_index.symbols:
                if query.lower() in sym.name.lower():
                    if kind is None or sym.kind == kind:
                        results.append(sym)
            # Also search indexed files that might not be cached
        return sorted(results, key=lambda s: s.name)

    def get_file_symbols(self, file_path: str) -> list[SymbolInfo]:
        """Get all symbols for a specific file."""
        rel_path = str(Path(file_path).resolve())
        for file_str, file_index in self._index.items():
            if str(Path(file_str).resolve()) == rel_path:
                return file_index.symbols
        return []

    def get_dependency_graph(self) -> dict[str, list[str]]:
        """Build a dependency graph from indexed dependencies."""
        graph: dict[str, list[str]] = {}
        for file_index in self._index.values():
            for dep in file_index.dependencies:
                if dep.source not in graph:
                    graph[dep.source] = []
                graph[dep.source].append(dep.target)
        return graph

    @staticmethod
    def _get_source_lines(source: str, start: int, end: int) -> str:
        """Extract source lines between start and end line numbers."""
        lines = source.split("\n")
        return "\n".join(lines[start - 1 : end])

    def get_stats(self) -> dict[str, Any]:
        """Get indexing statistics."""
        total_files = len(self._index)
        total_symbols = sum(len(fi.symbols) for fi in self._index.values())
        return {
            "indexed_files": total_files,
            "total_symbols": total_symbols,
            "total_dependencies": sum(len(fi.dependencies) for fi in self._index.values()),
            "total_errors": sum(len(fi.errors) for fi in self._index.values()),
        }
