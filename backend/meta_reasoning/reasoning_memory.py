"""Meta Reasoning & Self Reflection Engine — reasoning experience memory."""

from __future__ import annotations

import time
from typing import Any

from config.logging import get_logger
from meta_reasoning.schemas import ReasoningResult, ReasoningVerdict

logger = get_logger(__name__)


class ReasoningMemory:
    """Stores and retrieves past reasoning experiences for learning."""

    def __init__(self) -> None:
        self._experiences: list[dict[str, Any]] = []

    def store(self, result: ReasoningResult, plan_id: str) -> None:
        """Store a reasoning result for future reference.

        Args:
            result: The reasoning result to store.
            plan_id: Identifier of the plan that was reasoned about.
        """
        experience: dict[str, Any] = {
            "plan_id": plan_id,
            "result_id": result.result_id,
            "verdict": result.verdict.value,
            "confidence": result.confidence,
            "quality_score": result.quality_score,
            "risk": result.risk,
            "critique_count": len(result.critique),
            "simulation_passed": result.simulation_passed,
            "iterations": result.iterations,
            "stored_at": time.time(),
        }
        self._experiences.append(experience)
        logger.info("reasoning_experience_stored", plan_id=plan_id)

    def get_similar(self, plan: dict, limit: int = 5) -> list[dict[str, Any]]:
        """Retrieve similar past reasoning experiences.

        Args:
            plan: The current plan to find similar experiences for.
            limit: Maximum number of results to return.

        Returns:
            List of similar experience dictionaries.
        """
        # Simple similarity: match on task count and execution mode
        task_count = len(plan.get("tasks", []))
        exec_mode = plan.get("execution_mode", "sequential")

        scored: list[tuple[float, dict[str, Any]]] = []
        for exp in self._experiences:
            score = 0.5
            if exp.get("verdict") == ReasoningVerdict.APPROVED.value:
                score += 0.2
            if exp.get("simulation_passed"):
                score += 0.1
            scored.append((score, exp))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [exp for _, exp in scored[:limit]]

    def get_success_rate(self) -> float:
        """Get the success rate of past reasoning sessions.

        Returns:
            Ratio of approved verdicts to total, or 0.0 if no history.
        """
        if not self._experiences:
            return 0.0
        approved = sum(
            1 for e in self._experiences if e["verdict"] == ReasoningVerdict.APPROVED.value
        )
        return approved / len(self._experiences)

    def get_common_failures(self) -> list[str]:
        """Identify common failure patterns from history.

        Returns:
            List of common failure descriptions.
        """
        failures: list[str] = []
        rejected = [
            e for e in self._experiences if e["verdict"] == ReasoningVerdict.REJECTED.value
        ]
        if not rejected:
            return failures

        high_risk = sum(1 for e in rejected if e.get("risk", 0) > 0.5)
        if high_risk > 0:
            failures.append(f"High risk plans rejected: {high_risk}")

        low_quality = sum(1 for e in rejected if e.get("quality_score", 0) < 0.5)
        if low_quality > 0:
            failures.append(f"Low quality plans rejected: {low_quality}")

        sim_failed = sum(1 for e in rejected if not e.get("simulation_passed", True))
        if sim_failed > 0:
            failures.append(f"Simulation failures: {sim_failed}")

        return failures

    def get_successful_strategies(self) -> list[str]:
        """Identify strategies that have worked well historically.

        Returns:
            List of successful strategy descriptions.
        """
        strategies: list[str] = []
        approved = [
            e for e in self._experiences if e["verdict"] == ReasoningVerdict.APPROVED.value
        ]
        if not approved:
            return strategies

        high_conf = sum(1 for e in approved if e.get("confidence", 0) > 0.8)
        if high_conf > 0:
            strategies.append(f"High confidence approvals: {high_conf}")

        low_iter = sum(1 for e in approved if e.get("iterations", 3) == 1)
        if low_iter > 0:
            strategies.append(f"First-pass approvals (no refinement needed): {low_iter}")

        return strategies

    def stats(self) -> dict[str, Any]:
        """Get summary statistics of reasoning memory.

        Returns:
            Dictionary with memory statistics.
        """
        total = len(self._experiences)
        if total == 0:
            return {"total": 0, "success_rate": 0.0, "avg_confidence": 0.0, "avg_quality": 0.0}

        return {
            "total": total,
            "success_rate": self.get_success_rate(),
            "avg_confidence": sum(e["confidence"] for e in self._experiences) / total,
            "avg_quality": sum(e["quality_score"] for e in self._experiences) / total,
            "avg_iterations": sum(e["iterations"] for e in self._experiences) / total,
        }
