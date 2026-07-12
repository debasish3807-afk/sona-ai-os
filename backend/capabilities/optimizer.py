"""Capability Optimizer — optimize execution order and estimate costs."""

from __future__ import annotations

from capabilities.registry import CapabilityRegistry
from config.logging import get_logger

logger = get_logger(__name__)


class CapabilityOptimizer:
    """Optimizes capability execution order and provides cost/latency estimates."""

    def optimize_order(
        self,
        capability_ids: list[str],
        registry: CapabilityRegistry,
        metric: str = "latency",
    ) -> list[str]:
        """Optimize execution order based on a metric.

        Args:
            capability_ids: List of capability IDs to order.
            registry: The capability registry.
            metric: Optimization metric ('latency', 'cost', 'priority').

        Returns:
            Reordered list of capability IDs.
        """
        scored: list[tuple[float, str]] = []
        for cap_id in capability_ids:
            schema = registry.get(cap_id)
            if schema is None:
                scored.append((float("inf"), cap_id))
                continue
            if metric == "latency":
                scored.append((schema.latency_ms, cap_id))
            elif metric == "cost":
                scored.append((schema.cost, cap_id))
            elif metric == "priority":
                scored.append((float(schema.priority), cap_id))
            else:
                scored.append((schema.latency_ms, cap_id))

        scored.sort(key=lambda x: x[0])
        return [cap_id for _, cap_id in scored]

    def estimate_cost(self, capability_ids: list[str], registry: CapabilityRegistry) -> float:
        """Estimate total cost for executing a set of capabilities.

        Args:
            capability_ids: List of capability IDs.
            registry: The capability registry.

        Returns:
            Total estimated cost.
        """
        total: float = 0.0
        for cap_id in capability_ids:
            schema = registry.get(cap_id)
            if schema is not None:
                total += schema.cost
        return total

    def estimate_latency(self, capability_ids: list[str], registry: CapabilityRegistry) -> float:
        """Estimate total latency for sequential execution.

        Args:
            capability_ids: List of capability IDs.
            registry: The capability registry.

        Returns:
            Total estimated latency in milliseconds.
        """
        total: float = 0.0
        for cap_id in capability_ids:
            schema = registry.get(cap_id)
            if schema is not None:
                total += schema.latency_ms
        return total

    def suggest_alternatives(self, capability_id: str, registry: CapabilityRegistry) -> list[str]:
        """Suggest alternative capabilities with similar function.

        Args:
            capability_id: The capability to find alternatives for.
            registry: The capability registry.

        Returns:
            List of alternative capability IDs.
        """
        schema = registry.get(capability_id)
        if schema is None:
            return []

        alternatives: list[str] = []
        for other in registry.list_all():
            if other.capability_id == capability_id:
                continue
            if other.category == schema.category:
                # Check tag overlap
                common_tags = set(other.tags) & set(schema.tags)
                if common_tags:
                    alternatives.append(other.capability_id)
        return alternatives
