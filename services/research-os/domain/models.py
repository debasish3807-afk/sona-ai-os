"""Domain models for the Research OS service.

Defines the data structures used by the Research OS for web search, content
extraction, summarization, and multi-source research synthesis.
"""

from dataclasses import dataclass
from enum import StrEnum


class ResearchType(StrEnum):
    """Available research operation types.

    Determines the kind of research operation to perform, affecting
    the depth, breadth, and methodology of information gathering.
    """

    WEB_SEARCH = "web_search"
    DEEP_RESEARCH = "deep_research"
    FACT_CHECK = "fact_check"
    SUMMARIZATION = "summarization"


@dataclass(frozen=True)
class ResearchQuery:
    """A request for research on a given topic.

    Attributes:
        query: The research question or topic to investigate.
        research_type: The type of research operation to perform.
        max_sources: Maximum number of sources to consult.
        language: Language code for results (ISO 639-1).
        context: Optional additional context to refine the research.
    """

    query: str
    research_type: ResearchType
    max_sources: int = 10
    language: str = "en"
    context: dict | None = None


@dataclass(frozen=True)
class SearchResult:
    """A single search result from a web search operation.

    Attributes:
        title: The title of the search result/page.
        url: The URL of the search result.
        snippet: A brief excerpt or description of the content.
        relevance_score: Score indicating relevance to the query (0.0 to 1.0).
        source_domain: The domain name of the source.
    """

    title: str
    url: str
    snippet: str
    relevance_score: float
    source_domain: str


@dataclass(frozen=True)
class ResearchReport:
    """A synthesized research report combining multiple sources.

    Attributes:
        query: The original research query.
        summary: A comprehensive summary synthesized from all sources.
        sources: List of search results that contributed to the report.
        confidence: Confidence score for the report's accuracy (0.0 to 1.0).
        key_findings: List of key findings extracted from the research.
    """

    query: str
    summary: str
    sources: list[SearchResult]
    confidence: float
    key_findings: list[str]
