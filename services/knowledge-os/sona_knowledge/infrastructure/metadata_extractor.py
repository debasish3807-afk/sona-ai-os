"""Metadata extraction for Knowledge OS.

Extracts structural and semantic metadata from documents including
title, word count, language detection, sections, and keywords.
"""

import re
from collections import Counter
from typing import Any

import structlog

logger = structlog.get_logger()

# Common English stop words for keyword extraction
_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "shall",
        "can",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "not",
        "no",
        "so",
        "if",
        "then",
        "than",
        "when",
        "where",
        "what",
        "which",
        "who",
        "whom",
        "how",
        "all",
        "each",
        "every",
        "both",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "only",
        "own",
        "same",
        "also",
        "just",
        "because",
        "as",
        "until",
        "while",
        "about",
        "between",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "up",
        "down",
        "out",
        "off",
        "over",
        "under",
        "again",
        "further",
        "once",
        "here",
        "there",
    }
)


class MetadataExtractor:
    """Extracts metadata from document content.

    Provides:
    - Title extraction (from content or filename)
    - Word count and sentence count
    - Language detection (simple heuristic)
    - Section headings
    - Tags/keywords (top N words by frequency)
    """

    def __init__(self, max_keywords: int = 10) -> None:
        """Initialize the metadata extractor.

        Args:
            max_keywords: Maximum number of keywords to extract.
        """
        self._max_keywords = max_keywords

    def extract(self, content: str, filename: str = "") -> dict[str, Any]:
        """Extract all metadata from document content.

        Args:
            content: The document text content.
            filename: Optional filename for title fallback.

        Returns:
            Dictionary of extracted metadata fields.
        """
        metadata: dict[str, Any] = {
            "title": self._extract_title(content, filename),
            "word_count": self._word_count(content),
            "sentence_count": self._sentence_count(content),
            "language": self._detect_language(content),
            "headings": self._extract_headings(content),
            "keywords": self._extract_keywords(content),
            "char_count": len(content),
        }

        logger.debug(
            "metadata_extracted",
            title=metadata["title"],
            word_count=metadata["word_count"],
        )
        return metadata

    def _extract_title(self, content: str, filename: str = "") -> str:
        """Extract title from content or filename.

        Looks for markdown headings, then falls back to first line
        or filename.
        """
        # Try markdown H1
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        # Try HTML title
        match = re.search(r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        # Fallback to first non-empty line
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped and len(stripped) > 3:
                return stripped[:100]
        # Fallback to filename
        if filename:
            return filename.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        return "Untitled"

    def _word_count(self, content: str) -> int:
        """Count words in content."""
        return len(content.split())

    def _sentence_count(self, content: str) -> int:
        """Count sentences using punctuation-based heuristic."""
        sentences = re.split(r"[.!?]+", content)
        return len([s for s in sentences if s.strip()])

    def _detect_language(self, content: str) -> str:
        """Detect language using simple heuristic.

        Checks for common English words as a basic detection method.
        Returns ISO 639-1 code.
        """
        words = [w.lower() for w in re.findall(r"\w+", content[:1000])]
        if not words:
            return "unknown"

        english_indicators = {"the", "is", "are", "was", "and", "or", "to", "in", "of", "a"}
        english_count = sum(1 for w in words if w in english_indicators)
        ratio = english_count / len(words)

        if ratio > 0.05:
            return "en"
        return "unknown"

    def _extract_headings(self, content: str) -> list[str]:
        """Extract section headings from content."""
        headings: list[str] = []
        # Markdown headings
        for match in re.finditer(r"^#{1,6}\s+(.+)$", content, re.MULTILINE):
            headings.append(match.group(1).strip())
        # HTML headings
        for match in re.finditer(r"<h[1-6][^>]*>(.*?)</h[1-6]>", content, re.IGNORECASE):
            text = re.sub(r"<[^>]+>", "", match.group(1)).strip()
            if text:
                headings.append(text)
        return headings

    def _extract_keywords(self, content: str) -> list[str]:
        """Extract top keywords by frequency, excluding stop words."""
        words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", content)]
        filtered = [w for w in words if w not in _STOP_WORDS]
        counts = Counter(filtered)
        return [word for word, _ in counts.most_common(self._max_keywords)]
