"""Source collection, ranking, verification, caching, and reporting."""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from research_engine.models import ResearchReport, SourceDocument, SourceKind, VerifiedClaim


class ResearchCache:
    """Small persistent JSON cache; Redis can be layered above this later."""

    def __init__(self, path: Path | None = None, ttl: timedelta = timedelta(hours=24)) -> None:
        self.path = path or Path.home() / ".cache" / "sona-ai-os" / "research-cache.json"
        self.ttl = ttl
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> ResearchReport | None:
        if not self.path.exists():
            return None
        try:
            payload = json.loads(self.path.read_text())
            item = payload.get(key)
            if (
                not item
                or datetime.fromisoformat(item["created_at"]) < datetime.now(UTC) - self.ttl
            ):
                return None
            report_data = item["report"]
            refs = []
            for source in report_data.get("references", []):
                source = dict(source)
                source["source_kind"] = SourceKind(source["source_kind"])
                if source.get("published_at"):
                    source["published_at"] = datetime.fromisoformat(source["published_at"])
                source["retrieved_at"] = datetime.fromisoformat(source["retrieved_at"])
                refs.append(SourceDocument(**source))
            report_data["references"] = refs
            report_data["verified_claims"] = [
                VerifiedClaim(**claim) for claim in report_data.get("verified_claims", [])
            ]
            report_data["cached"] = True
            return ResearchReport(**report_data)
        except (OSError, ValueError, TypeError, KeyError):
            return None

    def set(self, key: str, report: ResearchReport) -> None:
        try:
            payload = json.loads(self.path.read_text()) if self.path.exists() else {}
        except (OSError, ValueError):
            payload = {}
        serial = asdict(report)
        for source in serial["references"]:
            source["source_kind"] = source["source_kind"].value
            if source.get("published_at"):
                source["published_at"] = source["published_at"].isoformat()
            source["retrieved_at"] = source["retrieved_at"].isoformat()
        payload[key] = {"created_at": datetime.now(UTC).isoformat(), "report": serial}
        self.path.write_text(json.dumps(payload, indent=2, default=str))


class SourceCollector:
    """Deduplicate and normalize collected sources."""

    def deduplicate(self, docs: list[SourceDocument]) -> list[SourceDocument]:
        seen: set[str] = set()
        unique = []
        for doc in docs:
            key = (doc.url or re.sub(r"\W+", " ", doc.text[:500]).lower()).strip()
            if key in seen or not doc.text.strip():
                continue
            seen.add(key)
            unique.append(doc)
        return unique


class SourceRanker:
    """Rank source quality using transparent local heuristics."""

    base_scores = {
        SourceKind.OFFICIAL_DOCS: 1.0,
        SourceKind.ARXIV: 0.95,
        SourceKind.GITHUB: 0.88,
        SourceKind.PDF: 0.82,
        SourceKind.LOCAL_KNOWLEDGE: 0.8,
        SourceKind.LOCAL_MEMORY: 0.78,
        SourceKind.MARKDOWN: 0.76,
        SourceKind.WIKIPEDIA: 0.65,
        SourceKind.DUCKDUCKGO: 0.48,
        SourceKind.BRAVE: 0.48,
        SourceKind.LOCAL_DOCUMENT: 0.7,
    }
    official_domains = (".gov", ".edu", "ietf.org", "w3.org", "docs.", "developer.", "github.com")

    def rank(self, docs: list[SourceDocument], query: str) -> list[SourceDocument]:
        terms = {term.lower() for term in re.findall(r"[\w-]+", query) if len(term) > 2}
        for doc in docs:
            url = (doc.url or "").lower()
            quality = self.base_scores.get(doc.source_kind, 0.4)
            if any(domain in url for domain in self.official_domains):
                quality = max(quality, 0.9)
            term_hits = sum(
                1 for term in terms if term in doc.text.lower() or term in doc.title.lower()
            )
            doc.quality_score = round(quality, 3)
            doc.relevance_score = round(min(1.0, term_hits / max(len(terms), 1)), 3)
        return sorted(
            docs, key=lambda item: (item.quality_score, item.relevance_score), reverse=True
        )


class FactVerifier:
    """Cross-check repeated claims and flag simple contradictions."""

    contradiction_patterns = (
        (" is ", " is not "),
        (" can ", " cannot "),
        (" supports ", " does not support "),
    )

    def verify(self, docs: list[SourceDocument]) -> tuple[list[VerifiedClaim], list[str], float]:
        sentences: dict[str, list[str]] = {}
        for doc in docs:
            for sentence in re.split(r"(?<=[.!?])\s+", doc.text):
                cleaned = sentence.strip()
                if 40 <= len(cleaned) <= 240:
                    key = re.sub(r"\W+", " ", cleaned.lower())[:120]
                    sentences.setdefault(key, []).append(doc.id)
        claims = [
            VerifiedClaim(key, ids, min(0.95, 0.45 + 0.2 * len(set(ids))))
            for key, ids in sentences.items()
            if len(set(ids)) >= 1
        ][:12]
        contradictions = []
        lowered = [claim.claim for claim in claims]
        for left, right in self.contradiction_patterns:
            positives = [claim for claim in lowered if left in claim]
            negatives = [claim for claim in lowered if right in claim]
            if positives and negatives:
                contradictions.append(
                    f"Potential contradiction between '{positives[0]}' and '{negatives[0]}'."
                )
        confidence = (
            0.0 if not docs else sum(doc.quality_score for doc in docs[:5]) / min(len(docs), 5)
        )
        if contradictions:
            confidence *= 0.75
        return claims, contradictions, round(confidence, 3)


class ReportGenerator:
    """Generate citation-rich professional reports from verified sources."""

    def generate(
        self,
        query: str,
        docs: list[SourceDocument],
        claims: list[VerifiedClaim],
        contradictions: list[str],
        confidence: float,
    ) -> ResearchReport:
        citations = {doc.id: f"[{index}]" for index, doc in enumerate(docs, start=1)}
        top = docs[:8]
        summary_bits = [f"{doc.title} {citations[doc.id]}" for doc in top[:3]]
        executive = (
            "No reliable sources were available."
            if not top
            else f"Research on '{query}' found strongest evidence in "
            + ", ".join(summary_bits)
            + "."
        )
        detailed = "\n".join(f"- {doc.title}: {doc.text[:450]} {citations[doc.id]}" for doc in top)
        recs = [
            "Prefer higher-ranked official, research, and repository sources before community sources."
        ]
        if contradictions:
            recs.append("Treat contradicted claims as uncertain until manually reviewed.")
        return ResearchReport(
            query=query,
            executive_summary=executive,
            detailed_analysis=detailed,
            advantages=[
                "Local-first sources are searched before web providers.",
                "Unavailable providers degrade to empty results instead of failing the workflow.",
            ],
            disadvantages=[
                "Web coverage depends on free provider rate limits and network availability."
            ],
            tradeoffs=[
                "The engine minimizes cost by using heuristic ranking and local cache before LLM synthesis."
            ],
            recommendations=recs,
            references=top,
            verified_claims=claims,
            confidence_score=confidence,
            contradictions=contradictions,
        )
