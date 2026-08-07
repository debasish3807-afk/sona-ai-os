"""Tests for the metadata extractor."""

import pytest

from sona_knowledge.infrastructure.metadata_extractor import MetadataExtractor


@pytest.fixture
def extractor() -> MetadataExtractor:
    return MetadataExtractor(max_keywords=10)


class TestMetadataExtractor:
    """Tests for MetadataExtractor."""

    def test_extract_returns_dict(self, extractor: MetadataExtractor) -> None:
        result = extractor.extract("Some content here.")
        assert isinstance(result, dict)

    def test_extracts_word_count(self, extractor: MetadataExtractor) -> None:
        result = extractor.extract("one two three four five")
        assert result["word_count"] == 5

    def test_extracts_char_count(self, extractor: MetadataExtractor) -> None:
        content = "Hello World"
        result = extractor.extract(content)
        assert result["char_count"] == len(content)

    def test_extracts_sentence_count(self, extractor: MetadataExtractor) -> None:
        content = "First sentence. Second sentence. Third sentence."
        result = extractor.extract(content)
        assert result["sentence_count"] == 3

    def test_extracts_title_from_markdown_h1(self, extractor: MetadataExtractor) -> None:
        content = "# My Document\n\nContent here."
        result = extractor.extract(content)
        assert result["title"] == "My Document"

    def test_extracts_title_from_html(self, extractor: MetadataExtractor) -> None:
        content = "<title>Page Title</title><body>Content</body>"
        result = extractor.extract(content)
        assert result["title"] == "Page Title"

    def test_title_fallback_to_first_line(self, extractor: MetadataExtractor) -> None:
        content = "First line of content\nSecond line"
        result = extractor.extract(content)
        assert result["title"] == "First line of content"

    def test_title_fallback_to_filename(self, extractor: MetadataExtractor) -> None:
        content = "ab"  # Too short for first-line title
        result = extractor.extract(content, filename="readme.md")
        assert result["title"] == "readme"

    def test_detects_english_language(self, extractor: MetadataExtractor) -> None:
        content = "The quick brown fox jumps over the lazy dog. It is a nice day."
        result = extractor.extract(content)
        assert result["language"] == "en"

    def test_unknown_language_for_short_text(self, extractor: MetadataExtractor) -> None:
        content = ""
        result = extractor.extract(content)
        assert result["language"] == "unknown"

    def test_extracts_markdown_headings(self, extractor: MetadataExtractor) -> None:
        content = "# Title\n## Section 1\n### Subsection\n## Section 2"
        result = extractor.extract(content)
        assert "Title" in result["headings"]
        assert "Section 1" in result["headings"]
        assert len(result["headings"]) == 4

    def test_extracts_keywords(self, extractor: MetadataExtractor) -> None:
        content = "Python Python Python programming programming language"
        result = extractor.extract(content)
        assert "python" in result["keywords"]
        assert "programming" in result["keywords"]

    def test_keywords_exclude_stop_words(self, extractor: MetadataExtractor) -> None:
        content = "the and or but is are was were have has been being"
        result = extractor.extract(content)
        # Stop words should not be in keywords
        for kw in result["keywords"]:
            assert kw not in ("the", "and", "or", "but", "is")

    def test_keywords_max_count(self, extractor: MetadataExtractor) -> None:
        content = " ".join([f"word{i}" * 3 for i in range(20)])
        result = extractor.extract(content)
        assert len(result["keywords"]) <= 10

    def test_custom_max_keywords(self) -> None:
        extractor = MetadataExtractor(max_keywords=5)
        content = " ".join([f"word{i}" * 3 for i in range(20)])
        result = extractor.extract(content)
        assert len(result["keywords"]) <= 5

    def test_empty_content(self, extractor: MetadataExtractor) -> None:
        result = extractor.extract("")
        assert result["word_count"] == 0
        assert result["char_count"] == 0
