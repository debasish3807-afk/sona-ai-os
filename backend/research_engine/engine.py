"""Deep Research Engine orchestration."""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path

from research_engine.models import ResearchReport, SourceKind
from research_engine.pipeline import (
    FactVerifier,
    ReportGenerator,
    ResearchCache,
    SourceCollector,
    SourceRanker,
)
from research_engine.planner import ResearchPlanner
from research_engine.providers import (
    ArxivProvider,
    BraveProvider,
    DuckDuckGoProvider,
    GitHubProvider,
    LocalFileProvider,
    SearchProvider,
    WikipediaProvider,
)


class DeepResearchEngine:
    """Multi-provider, local-first deep research engine."""

    def __init__(
        self,
        *,
        local_roots: list[Path] | None = None,
        cache: ResearchCache | None = None,
        providers: list[SearchProvider] | None = None,
    ) -> None:
        self.planner = ResearchPlanner()
        self.cache = cache or ResearchCache()
        self.collector = SourceCollector()
        self.ranker = SourceRanker()
        self.verifier = FactVerifier()
        self.reporter = ReportGenerator()
        self.providers = providers or [
            LocalFileProvider(local_roots),
            WikipediaProvider(),
            ArxivProvider(),
            GitHubProvider(),
            BraveProvider(),
            DuckDuckGoProvider(),
        ]

    async def research(
        self, query: str, *, offline: bool = False, use_cache: bool = True
    ) -> ResearchReport:
        plan = self.planner.create_plan(query, offline=offline)
        key = hashlib.sha256(f"{plan.original_query}|{offline}".encode()).hexdigest()
        if use_cache and plan.use_cache:
            cached = self.cache.get(key)
            if cached:
                return cached
        allowed = {kind for task in plan.tasks for kind in task.required_sources}
        docs = []
        searches = []
        for task in plan.tasks:
            for provider in self.providers:
                if self._provider_allowed(provider.kind, allowed):
                    searches.append(provider.search(task.question, limit=3))
                if len(searches) >= plan.max_searches:
                    break
            if len(searches) >= plan.max_searches:
                break
        for result in await asyncio.gather(*searches, return_exceptions=True):
            if isinstance(result, list):
                docs.extend(result)
        ranked = self.ranker.rank(self.collector.deduplicate(docs), plan.original_query)
        claims, contradictions, confidence = self.verifier.verify(ranked)
        report = self.reporter.generate(
            plan.original_query, ranked, claims, contradictions, confidence
        )
        if use_cache:
            self.cache.set(key, report)
        return report

    def _provider_allowed(self, provider_kind: SourceKind, allowed: set[SourceKind]) -> bool:
        if provider_kind is SourceKind.LOCAL_DOCUMENT:
            return bool(
                {
                    SourceKind.LOCAL_DOCUMENT,
                    SourceKind.MARKDOWN,
                    SourceKind.PDF,
                    SourceKind.LOCAL_KNOWLEDGE,
                    SourceKind.LOCAL_MEMORY,
                }
                & allowed
            )
        return provider_kind in allowed
