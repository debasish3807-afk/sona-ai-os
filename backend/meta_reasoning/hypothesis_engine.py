"""Meta Reasoning & Self Reflection Engine — hypothesis generation and evaluation."""

from __future__ import annotations

import uuid
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class HypothesisEngine:
    """Generates and evaluates hypotheses about plan outcomes."""

    def generate_hypotheses(self, plan: dict, context: dict) -> list[dict[str, Any]]:
        """Generate hypotheses about the plan's expected behavior.

        Args:
            plan: The execution plan to hypothesize about.
            context: Environment context.

        Returns:
            List of hypothesis dictionaries.
        """
        hypotheses: list[dict[str, Any]] = []

        # Success hypothesis
        hypotheses.append(
            self._create_hypothesis(
                description="Plan will complete successfully within estimated time",
                assumptions=["All capabilities available", "No provider failures"],
            )
        )

        # Partial failure hypothesis
        tasks = plan.get("tasks", [])
        if len(tasks) > 2:
            hypotheses.append(
                self._create_hypothesis(
                    description="Some tasks may fail requiring retry",
                    assumptions=["Network latency variability", "Provider rate limits"],
                )
            )

        # Budget overrun hypothesis
        cost_info = plan.get("cost", {})
        if cost_info.get("total_estimated", 0) > 0:
            hypotheses.append(
                self._create_hypothesis(
                    description="Actual cost may exceed estimate by 20-50%",
                    assumptions=["Token usage varies with input", "Retry costs not included"],
                )
            )

        # Context-dependent hypothesis
        if context.get("available_providers"):
            hypotheses.append(
                self._create_hypothesis(
                    description="Provider selection may impact quality",
                    assumptions=["Different providers have different capabilities"],
                )
            )

        logger.info("hypotheses_generated", count=len(hypotheses))
        return hypotheses

    def evaluate_hypothesis(self, hypothesis: dict, evidence: list[dict]) -> float:
        """Evaluate a hypothesis against available evidence.

        Args:
            hypothesis: The hypothesis to evaluate.
            evidence: List of evidence items.

        Returns:
            Confidence score between 0 and 1.
        """
        if not evidence:
            return 0.3

        assumptions = hypothesis.get("assumptions", [])
        supported = 0
        for _assumption in assumptions:
            for item in evidence:
                if item.get("supports", False):
                    supported += 1
                    break

        if not assumptions:
            return 0.5

        confidence = supported / len(assumptions)
        return min(max(confidence, 0.0), 1.0)

    def _create_hypothesis(self, description: str, assumptions: list[str]) -> dict[str, Any]:
        """Create a structured hypothesis.

        Args:
            description: What the hypothesis predicts.
            assumptions: Underlying assumptions.

        Returns:
            Hypothesis dictionary.
        """
        return {
            "hypothesis_id": str(uuid.uuid4()),
            "description": description,
            "assumptions": assumptions,
            "confidence": 0.5,
            "status": "untested",
        }

    def rank_hypotheses(self, hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Rank hypotheses by confidence (descending).

        Args:
            hypotheses: List of hypothesis dictionaries.

        Returns:
            Sorted list with highest-confidence hypotheses first.
        """
        return sorted(hypotheses, key=lambda h: h.get("confidence", 0.0), reverse=True)
