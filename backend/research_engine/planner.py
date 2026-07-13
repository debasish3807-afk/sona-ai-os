"""Intent-aware research planning without unnecessary searches."""

from __future__ import annotations

import re

from research_engine.models import ResearchDepth, ResearchPlan, ResearchTask, SourceKind


class ResearchPlanner:
    """Break complex questions into bounded, provider-aware research plans."""

    _split_re = re.compile(r"\b(?:and|vs\.?|versus|compare|trade[- ]?offs?|pros and cons)\b", re.I)

    def create_plan(self, query: str, *, offline: bool = False) -> ResearchPlan:
        """Create a concrete research plan for a user query."""
        cleaned = " ".join(query.strip().split())
        if not cleaned:
            raise ValueError("Research query cannot be empty")

        intent = self._detect_intent(cleaned)
        depth = self._estimate_depth(cleaned)
        source_policy = self._select_sources(cleaned, intent, offline=offline)
        questions = self._subquestions(cleaned, depth)
        tasks = [
            ResearchTask(question=question, required_sources=source_policy, priority=index + 1)
            for index, question in enumerate(questions)
        ]
        max_searches = min(
            len(tasks) * len(source_policy),
            {ResearchDepth.QUICK: 4, ResearchDepth.STANDARD: 10, ResearchDepth.DEEP: 18}[depth],
        )
        return ResearchPlan(cleaned, intent, depth, tasks, max_searches)

    def _detect_intent(self, query: str) -> str:
        lowered = query.lower()
        if any(word in lowered for word in ("recommend", "should i", "best", "choose")):
            return "recommendation"
        if any(word in lowered for word in ("compare", " vs ", "versus", "trade-off")):
            return "comparison"
        if any(word in lowered for word in ("latest", "current", "today", "recent")):
            return "current_research"
        if any(word in lowered for word in ("how", "implement", "build", "debug")):
            return "technical_how_to"
        return "explanatory"

    def _estimate_depth(self, query: str) -> ResearchDepth:
        words = query.split()
        lowered = query.lower()
        if len(words) > 28 or any(
            word in lowered for word in ("deep", "comprehensive", "architecture", "evidence")
        ):
            return ResearchDepth.DEEP
        if len(words) > 10 or any(word in lowered for word in ("compare", "why", "how", "risks")):
            return ResearchDepth.STANDARD
        return ResearchDepth.QUICK

    def _select_sources(self, query: str, intent: str, *, offline: bool) -> list[SourceKind]:
        lowered = query.lower()
        sources = [
            SourceKind.LOCAL_MEMORY,
            SourceKind.LOCAL_KNOWLEDGE,
            SourceKind.LOCAL_DOCUMENT,
            SourceKind.MARKDOWN,
            SourceKind.PDF,
        ]
        if offline:
            return sources
        if "github" in lowered or "architecture" in lowered or intent == "technical_how_to":
            sources.append(SourceKind.GITHUB)
        if any(word in lowered for word in ("paper", "research", "study", "arxiv")):
            sources.append(SourceKind.ARXIV)
        if any(word in lowered for word in ("who", "what is", "history", "overview")):
            sources.append(SourceKind.WIKIPEDIA)
        if (
            any(word in lowered for word in ("official", "docs", "api", "standard", "spec"))
            or intent == "technical_how_to"
        ):
            sources.append(SourceKind.OFFICIAL_DOCS)
        sources.extend([SourceKind.BRAVE, SourceKind.DUCKDUCKGO])
        return list(dict.fromkeys(sources))

    def _subquestions(self, query: str, depth: ResearchDepth) -> list[str]:
        parts = [part.strip(" ?.!") for part in self._split_re.split(query) if part.strip(" ?.!")]
        questions = parts[:4] if len(parts) > 1 else [query]
        if depth in {ResearchDepth.STANDARD, ResearchDepth.DEEP}:
            questions.extend(
                [
                    f"What evidence supports: {query}?",
                    f"What are limitations or contradictions for: {query}?",
                ]
            )
        if depth is ResearchDepth.DEEP:
            questions.append(f"What are practical recommendations and trade-offs for: {query}?")
        return list(dict.fromkeys(questions))
