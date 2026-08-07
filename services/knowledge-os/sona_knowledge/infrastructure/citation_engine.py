"""Citation engine for Knowledge OS.

Generates source citations from retrieved chunks for attribution
and context formatting for LLM augmentation.
"""

import structlog

from sona_knowledge.domain.citations import Citation
from sona_knowledge.infrastructure.hybrid_search import HybridResult

logger = structlog.get_logger()


class CitationEngine:
    """Generates citations from retrieved chunks.

    Creates Citation objects with scores, document metadata,
    and formats citation context for LLM augmentation.
    """

    def __init__(self, excerpt_length: int = 200) -> None:
        """Initialize the citation engine.

        Args:
            excerpt_length: Maximum length of content excerpts in citations.
        """
        self._excerpt_length = excerpt_length

    def generate_citations(self, results: list[HybridResult]) -> list[Citation]:
        """Generate citations from search results.

        Args:
            results: Ranked search results to create citations from.

        Returns:
            List of Citation objects with source attribution.
        """
        citations: list[Citation] = []

        for result in results:
            metadata = result.metadata
            citation = Citation(
                chunk_id=result.id,
                document_id=str(metadata.get("document_id", "")),
                document_title=str(metadata.get("title", "Unknown")),
                content_excerpt=self._create_excerpt(result.content),
                relevance_score=result.combined_score,
                source_url=str(metadata.get("source_url", "")),
                page_number=metadata.get("page_number"),  # type: ignore[arg-type]
                section=str(metadata.get("section", "")),
            )
            citations.append(citation)

        logger.debug("citations_generated", count=len(citations))
        return citations

    def format_context(self, results: list[HybridResult]) -> str:
        """Format retrieved chunks into augmented context for LLM.

        Args:
            results: Ranked search results to include in context.

        Returns:
            Formatted context string with source attribution.
        """
        if not results:
            return ""

        sections: list[str] = []

        for i, result in enumerate(results, 1):
            title = str(result.metadata.get("title", "Source"))
            section = f"[Source {i}: {title}]\n{result.content}"
            sections.append(section)

        context = "\n\n---\n\n".join(sections)

        logger.debug("context_formatted", sources_count=len(results))
        return context

    def _create_excerpt(self, content: str) -> str:
        """Create a truncated excerpt from content.

        Args:
            content: Full content text.

        Returns:
            Truncated excerpt with ellipsis if needed.
        """
        if len(content) <= self._excerpt_length:
            return content
        return content[: self._excerpt_length].rsplit(" ", 1)[0] + "..."
