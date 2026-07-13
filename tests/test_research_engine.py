import asyncio
from pathlib import Path

from research_engine.engine import DeepResearchEngine
from research_engine.models import SourceDocument, SourceKind
from research_engine.pipeline import FactVerifier, ResearchCache, SourceCollector, SourceRanker
from research_engine.planner import ResearchPlanner
from research_engine.providers import SearchProvider


class FailingProvider(SearchProvider):
    kind = SourceKind.WIKIPEDIA
    name = "failing"

    async def search(self, query: str, limit: int) -> list[SourceDocument]:
        raise RuntimeError("provider down")


class StaticProvider(SearchProvider):
    kind = SourceKind.OFFICIAL_DOCS
    name = "static"

    async def search(self, query: str, limit: int) -> list[SourceDocument]:
        return [
            SourceDocument(
                "s1",
                "Official Docs",
                "https://docs.example.test/x",
                self.kind,
                "This official documentation supports local first research with citations and source ranking.",
                self.name,
            )
        ]


def test_planner_selects_depth_and_sources() -> None:
    plan = ResearchPlanner().create_plan("Compare Ollama and Gemini for deep research architecture")
    assert plan.depth.value in {"standard", "deep"}
    assert plan.tasks
    assert SourceKind.GITHUB in plan.tasks[0].required_sources


def test_collection_ranking_verification() -> None:
    docs = [
        SourceDocument(
            "1",
            "Docs",
            "https://docs.python.org",
            SourceKind.OFFICIAL_DOCS,
            "Python official documentation explains supported APIs clearly enough for verification.",
            "x",
        ),
        SourceDocument("2", "Dup", "https://docs.python.org", SourceKind.BRAVE, "duplicate", "x"),
    ]
    unique = SourceCollector().deduplicate(docs)
    ranked = SourceRanker().rank(unique, "Python APIs")
    claims, contradictions, confidence = FactVerifier().verify(ranked)
    assert len(unique) == 1
    assert ranked[0].quality_score >= 0.9
    assert claims
    assert contradictions == []
    assert confidence > 0


def test_engine_provider_failover_and_report_cache(tmp_path: Path) -> None:
    cache = ResearchCache(tmp_path / "cache.json")
    engine = DeepResearchEngine(cache=cache, providers=[FailingProvider(), StaticProvider()])
    report = asyncio.run(engine.research("official local first research docs", use_cache=True))
    cached = asyncio.run(engine.research("official local first research docs", use_cache=True))
    assert report.references[0].title == "Official Docs"
    assert report.confidence_score > 0
    assert cached.cached is True
    assert "Official Docs" in cached.executive_summary
