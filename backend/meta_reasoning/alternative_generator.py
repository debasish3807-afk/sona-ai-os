"""Meta Reasoning & Self Reflection Engine — alternative plan generation."""

from __future__ import annotations

from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class AlternativeGenerator:
    """Generates alternative execution plans optimized for different dimensions."""

    def generate(self, plan: dict, critiques: list[str], context: dict) -> list[dict[str, Any]]:
        """Generate alternative plans based on critiques and context.

        Args:
            plan: The original execution plan.
            critiques: Critiques identifying weaknesses.
            context: Environment context with available resources.

        Returns:
            List of alternative plan dictionaries.
        """
        alternatives: list[dict[str, Any]] = []
        alternatives.append(self._generate_fastest(plan))
        alternatives.append(self._generate_cheapest(plan))
        alternatives.append(self._generate_safest(plan))
        alternatives.append(self._generate_highest_quality(plan))
        alternatives.append(self._generate_balanced(plan))
        logger.info("alternatives_generated", count=len(alternatives))
        return alternatives

    def _generate_fastest(self, plan: dict) -> dict[str, Any]:
        """Generate the fastest possible plan variant."""
        alt = dict(plan)
        alt["strategy"] = "fastest"
        alt["execution_mode"] = "parallel"
        duration = plan.get("estimated_duration_ms", 1000)
        alt["estimated_duration_ms"] = duration * 0.5
        alt["trade_offs"] = ["Higher resource usage", "Increased failure risk"]
        alt["score"] = 0.7
        return alt

    def _generate_cheapest(self, plan: dict) -> dict[str, Any]:
        """Generate the lowest-cost plan variant."""
        alt = dict(plan)
        alt["strategy"] = "cheapest"
        alt["execution_mode"] = "sequential"
        cost_info = plan.get("cost", {})
        original_cost = cost_info.get("total_estimated", 0.05)
        alt["cost"] = {"total_estimated": original_cost * 0.4}
        alt["trade_offs"] = ["Slower execution", "Potentially lower quality"]
        alt["score"] = 0.6
        return alt

    def _generate_safest(self, plan: dict) -> dict[str, Any]:
        """Generate the safest plan variant with maximum error handling."""
        alt = dict(plan)
        alt["strategy"] = "safest"
        alt["execution_mode"] = "sequential"
        alt["risk"] = {"overall_risk": 0.05}
        alt["checkpoints"] = [f"checkpoint_{i}" for i in range(3)]
        alt["rollback_path"] = ["rollback_all"]
        alt["trade_offs"] = ["Slower execution", "Higher overhead"]
        alt["score"] = 0.75
        return alt

    def _generate_highest_quality(self, plan: dict) -> dict[str, Any]:
        """Generate the highest-quality plan variant."""
        alt = dict(plan)
        alt["strategy"] = "highest_quality"
        alt["execution_mode"] = "sequential"
        alt["verification_steps"] = ["verify_each_task", "integration_test"]
        cost_info = plan.get("cost", {})
        original_cost = cost_info.get("total_estimated", 0.05)
        alt["cost"] = {"total_estimated": original_cost * 1.5}
        alt["trade_offs"] = ["Higher cost", "Longer execution time"]
        alt["score"] = 0.8
        return alt

    def _generate_balanced(self, plan: dict) -> dict[str, Any]:
        """Generate a balanced plan optimizing across all dimensions."""
        alt = dict(plan)
        alt["strategy"] = "balanced"
        alt["execution_mode"] = "hybrid"
        alt["risk"] = {"overall_risk": 0.2}
        alt["checkpoints"] = ["mid_checkpoint"]
        alt["trade_offs"] = ["No single dimension is maximized"]
        alt["score"] = 0.85
        return alt

    def rank(self, alternatives: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Rank alternatives by composite score (descending).

        Args:
            alternatives: List of alternative plans.

        Returns:
            Sorted list with highest-scoring alternatives first.
        """
        return sorted(alternatives, key=lambda a: a.get("score", 0.0), reverse=True)
