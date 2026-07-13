"""Typed models for the deep research engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class ResearchDepth(str, Enum):
    """Research depth selected by the planner."""

    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class SourceKind(str, Enum):
    """Supported source categories."""

    LOCAL_MEMORY = "local_memory"
    LOCAL_KNOWLEDGE = "local_knowledge"
    LOCAL_DOCUMENT = "local_document"
    MARKDOWN = "markdown"
    PDF = "pdf"
    GITHUB = "github"
    BRAVE = "brave"
    DUCKDUCKGO = "duckduckgo"
    WIKIPEDIA = "wikipedia"
    ARXIV = "arxiv"
    OFFICIAL_DOCS = "official_docs"


@dataclass(frozen=True)
class ResearchTask:
    """A focused sub-question to investigate."""

    question: str
    required_sources: list[SourceKind]
    priority: int = 1


@dataclass(frozen=True)
class ResearchPlan:
    """Planner output for a research request."""

    original_query: str
    intent: str
    depth: ResearchDepth
    tasks: list[ResearchTask]
    max_searches: int
    use_cache: bool = True


@dataclass
class SourceDocument:
    """Normalized source content with metadata and ranking fields."""

    id: str
    title: str
    url: str | None
    source_kind: SourceKind
    text: str
    provider: str
    published_at: datetime | None = None
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0
    relevance_score: float = 0.0


@dataclass(frozen=True)
class VerifiedClaim:
    """A claim extracted from ranked sources."""

    claim: str
    source_ids: list[str]
    confidence: float
    contradicted_by: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResearchReport:
    """Final professional research report."""

    query: str
    executive_summary: str
    detailed_analysis: str
    advantages: list[str]
    disadvantages: list[str]
    tradeoffs: list[str]
    recommendations: list[str]
    references: list[SourceDocument]
    verified_claims: list[VerifiedClaim]
    confidence_score: float
    contradictions: list[str]
    cached: bool = False
