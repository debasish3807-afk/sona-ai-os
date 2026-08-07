"""Content extractors for different document formats.

Extract text from various document formats for indexing.
"""

import json
import re

import structlog

from sona_research.domain.workspace_models import DocumentFormat

logger = structlog.get_logger()


class ContentExtractors:
    """Extract text content from different document formats."""

    @staticmethod
    async def extract(content: str, format: DocumentFormat) -> str:
        """Extract text from content based on its format.

        Args:
            content: Raw content string.
            format: The document format.

        Returns:
            Extracted plain text content.
        """
        match format:
            case DocumentFormat.MARKDOWN:
                return ContentExtractors._extract_markdown(content)
            case DocumentFormat.SOURCE_CODE:
                return ContentExtractors._extract_source_code(content)
            case DocumentFormat.JSON:
                return ContentExtractors._extract_json(content)
            case DocumentFormat.YAML:
                return ContentExtractors._extract_yaml(content)
            case DocumentFormat.PDF:
                return ContentExtractors._extract_pdf(content)
            case DocumentFormat.TEXT | DocumentFormat.DOCX:
                return content

    @staticmethod
    def _extract_markdown(content: str) -> str:
        """Extract plain text from Markdown by stripping formatting.

        Removes headers (#), bold/italic markers, links, code fences, etc.
        """
        text = content
        # Remove code blocks
        text = re.sub(r"```[\s\S]*?```", "", text)
        # Remove inline code
        text = re.sub(r"`[^`]+`", "", text)
        # Remove headers
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        # Remove bold/italic
        text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
        text = re.sub(r"_{1,3}([^_]+)_{1,3}", r"\1", text)
        # Remove links but keep text
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        # Remove images
        text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
        # Remove horizontal rules
        text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
        # Remove list markers
        text = re.sub(r"^[\s]*[-*+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^[\s]*\d+\.\s+", "", text, flags=re.MULTILINE)
        # Collapse whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def _extract_source_code(content: str) -> str:
        """Extract comments and structure from source code.

        Extracts single-line comments, multi-line comments, docstrings,
        and function/class definitions.
        """
        lines: list[str] = []
        # Extract docstrings and multi-line comments
        docstrings = re.findall(r'"""([\s\S]*?)"""', content)
        docstrings += re.findall(r"'''([\s\S]*?)'''", content)
        for ds in docstrings:
            lines.append(ds.strip())

        # Extract single-line comments
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("#"):
                lines.append(stripped[1:].strip())
            elif stripped.startswith("//"):
                lines.append(stripped[2:].strip())

        # Extract function and class definitions
        defs = re.findall(
            r"^(?:def|class|function|async def|export)\s+(\w+)", content, re.MULTILINE
        )
        for d in defs:
            lines.append(f"Definition: {d}")

        return "\n".join(lines).strip()

    @staticmethod
    def _extract_json(content: str) -> str:
        """Extract structure from JSON content."""
        try:
            data = json.loads(content)
            return ContentExtractors._stringify_json(data, max_depth=3)
        except json.JSONDecodeError:
            return content

    @staticmethod
    def _stringify_json(data: object, max_depth: int = 3, depth: int = 0) -> str:
        """Recursively stringify JSON data with depth limit."""
        if depth >= max_depth:
            return str(type(data).__name__)

        if isinstance(data, dict):
            parts = []
            for key, value in data.items():
                val_str = ContentExtractors._stringify_json(value, max_depth, depth + 1)
                parts.append(f"{key}: {val_str}")
            return "{ " + ", ".join(parts) + " }"
        if isinstance(data, list):
            if not data:
                return "[]"
            first = ContentExtractors._stringify_json(data[0], max_depth, depth + 1)
            return f"[{first}, ...({len(data)} items)]"
        return str(data)

    @staticmethod
    def _extract_yaml(content: str) -> str:
        """Extract structure from YAML content.

        Simple extraction that preserves keys and top-level structure.
        """
        lines: list[str] = []
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                lines.append(stripped)
        return "\n".join(lines)

    @staticmethod
    def _extract_pdf(content: str) -> str:
        """Simulated PDF text extraction.

        In a real implementation, this would use a PDF library.
        For simulation, strips any PDF markers and returns clean text.
        """
        # Remove simulated PDF markers
        text = content.replace("%PDF-", "").replace("%%EOF", "")
        return text.strip()
