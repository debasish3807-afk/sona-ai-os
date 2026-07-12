"""Capability Selector — intelligent selection of capabilities for goals."""

from __future__ import annotations

from typing import Any

from capabilities.registry import CapabilityRegistry
from capabilities.schemas import Capability
from config.logging import get_logger

logger = get_logger(__name__)


class CapabilitySelector:
    """Selects the best capability for a given goal and intent.

    Uses multi-factor scoring based on keyword matching,
    confidence, cost, latency, health status, and priority.
    """

    def select(
        self,
        goal: str,
        intent: str,
        registry: CapabilityRegistry,
        constraints: dict[str, Any] | None = None,
    ) -> str | None:
        """Select the single best capability for a goal.

        Args:
            goal: High-level goal description.
            intent: Specific intent or action.
            registry: The capability registry.
            constraints: Optional constraints (max_cost, max_latency, required_tags).

        Returns:
            The capability_id of the best match, or None.
        """
        candidates = registry.list_all()
        if not candidates:
            return None

        best_id: str | None = None
        best_score: float = -1.0

        for schema in candidates:
            if not schema.is_active:
                continue
            score = self._score(schema, goal, intent, constraints)
            if score > best_score:
                best_score = score
                best_id = schema.capability_id

        return best_id

    def select_multiple(
        self,
        goal: str,
        intent: str,
        registry: CapabilityRegistry,
        max_count: int = 5,
    ) -> list[str]:
        """Select multiple capabilities ranked by suitability.

        Args:
            goal: High-level goal description.
            intent: Specific intent or action.
            registry: The capability registry.
            max_count: Maximum number of capabilities to return.

        Returns:
            List of capability_ids sorted by score (best first).
        """
        candidates = registry.list_all()
        scored: list[tuple[float, str]] = []

        for schema in candidates:
            if not schema.is_active:
                continue
            score = self._score(schema, goal, intent, None)
            scored.append((score, schema.capability_id))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [cap_id for _, cap_id in scored[:max_count]]

    def _score(
        self,
        schema: Capability,
        goal: str,
        intent: str,
        constraints: dict[str, Any] | None,
    ) -> float:
        """Compute a relevance score for a capability.

        Scoring factors:
        - Keyword match in name/description/tags vs goal+intent
        - Confidence level
        - Cost (lower is better)
        - Latency (lower is better)
        - Health status
        - Priority (lower number = higher priority)
        """
        score: float = 0.0
        combined_query = f"{goal} {intent}".lower()

        # Keyword matching (0-40 points)
        keyword_hits = 0
        words = combined_query.split()
        searchable = f"{schema.name} {schema.description} {' '.join(schema.tags)}".lower()
        for word in words:
            if word in searchable:
                keyword_hits += 1
        if words:
            score += (keyword_hits / len(words)) * 40.0

        # Confidence (0-20 points)
        score += schema.confidence * 20.0

        # Cost penalty (0-10 points, lower cost = higher score)
        if schema.cost <= 0:
            score += 10.0
        else:
            score += max(0.0, 10.0 - schema.cost)

        # Latency penalty (0-10 points, lower latency = higher score)
        if schema.latency_ms <= 0:
            score += 10.0
        else:
            score += max(0.0, 10.0 - (schema.latency_ms / 1000.0))

        # Health bonus (0-10 points)
        if schema.health_status == "healthy":
            score += 10.0
        elif schema.health_status == "degraded":
            score += 5.0

        # Priority bonus (0-10 points, lower priority value = higher score)
        score += max(0.0, 10.0 - (schema.priority / 10.0))

        # Constraint filtering
        if constraints:
            max_cost = constraints.get("max_cost")
            if max_cost is not None and schema.cost > max_cost:
                return -1.0
            max_latency = constraints.get("max_latency")
            if max_latency is not None and schema.latency_ms > max_latency:
                return -1.0
            required_tags = constraints.get("required_tags")
            if required_tags and not any(t in schema.tags for t in required_tags):
                return -1.0

        return score
