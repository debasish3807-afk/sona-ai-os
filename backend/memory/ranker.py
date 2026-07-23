"""Memory Ranker — multi-factor memory scoring and ranking."""

from __future__ import annotations

import time
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class MemoryRanker:
    """Ranks memory entries by combining multiple relevance signals.

    Scoring factors:
        - Importance: explicit importance score (0.0-1.0)
        - Recency: how recently accessed (decays over time)
        - Frequency: how often accessed
        - Relevance: semantic match to query (external)
    """

    def __init__(
        self,
        importance_weight: float = 0.4,
        recency_weight: float = 0.3,
        frequency_weight: float = 0.2,
        relevance_weight: float = 0.1,
    ) -> None:
        self._weights = {
            "importance": importance_weight,
            "recency": recency_weight,
            "frequency": frequency_weight,
            "relevance": relevance_weight,
        }

    def score(self, entry: Any, query_relevance: float = 0.0) -> float:
        importance = getattr(entry, "importance_score", getattr(entry, "importance", 0.5))
        if isinstance(importance, (int, float)):
            imp_score = float(importance)
        else:
            imp_score = 0.5

        accessed = getattr(entry, "accessed_at", getattr(entry, "created_at", time.time()))
        if isinstance(accessed, (int, float)):
            hours_ago = (time.time() - accessed) / 3600
        else:
            hours_ago = 24
        recency = max(0.0, 1.0 - hours_ago / 720)  # Decay over 30 days

        access_count = getattr(entry, "access_count", 0)
        freq = min(1.0, access_count / 100)

        return (
            self._weights["importance"] * imp_score
            + self._weights["recency"] * recency
            + self._weights["frequency"] * freq
            + self._weights["relevance"] * query_relevance
        )

    def rank(self, entries: list[Any], query: str = "", top_k: int = 10) -> list[tuple[Any, float]]:
        relevance = 0.5 if query else 0.0
        scored = [(e, self.score(e, relevance)) for e in entries]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
