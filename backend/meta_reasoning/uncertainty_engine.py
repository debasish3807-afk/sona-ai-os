"""Meta Reasoning & Self Reflection Engine — uncertainty assessment."""

from __future__ import annotations

from typing import Any

from config.logging import get_logger
from meta_reasoning.schemas import EvidenceLabel

logger = get_logger(__name__)


class UncertaintyEngine:
    """Assesses uncertainty in plans and evidence."""

    def assess(
        self, plan: dict, evidence: dict[str, EvidenceLabel], context: dict
    ) -> dict[str, Any]:
        """Assess overall uncertainty of a plan.

        Args:
            plan: The execution plan.
            evidence: Evidence labels from verification.
            context: Environment context.

        Returns:
            Uncertainty assessment dictionary.
        """
        unknown_facts = self._detect_unknown_facts(plan, context)
        missing_context = self._detect_missing_context(plan, context)
        weak_evidence = self._detect_weak_evidence(evidence)
        ambiguous_goals = self._detect_ambiguous_goals(plan)

        assessment: dict[str, Any] = {
            "unknown_facts": unknown_facts,
            "missing_context": missing_context,
            "weak_evidence": weak_evidence,
            "ambiguous_goals": ambiguous_goals,
            "total_issues": (
                len(unknown_facts) + len(missing_context)
                + len(weak_evidence) + len(ambiguous_goals)
            ),
        }

        assessment["overall_uncertainty"] = self.overall_uncertainty(assessment)
        logger.info(
            "uncertainty_assessed", overall=assessment["overall_uncertainty"]
        )
        return assessment

    def _detect_unknown_facts(self, plan: dict, context: dict) -> list[str]:
        """Detect facts that are required but unknown."""
        unknowns: list[str] = []
        if not context.get("available_providers"):
            unknowns.append("No providers listed — availability unknown")
        if not context.get("available_capabilities"):
            unknowns.append("No capabilities listed — support unknown")
        if not plan.get("estimated_duration_ms"):
            unknowns.append("Execution duration is unknown")
        return unknowns

    def _detect_missing_context(self, plan: dict, context: dict) -> list[str]:
        """Detect context gaps that affect decision confidence."""
        missing: list[str] = []
        if "budget" not in context:
            missing.append("Budget constraint not specified")
        if "max_risk" not in context:
            missing.append("Risk threshold not specified")
        if not context.get("prior_results"):
            missing.append("No historical execution data available")
        return missing

    def _detect_weak_evidence(self, evidence: dict[str, EvidenceLabel]) -> list[str]:
        """Detect evidence claims with weak support."""
        weak: list[str] = []
        weak_labels = {EvidenceLabel.HYPOTHESIS, EvidenceLabel.ESTIMATED}
        for claim, label in evidence.items():
            if label in weak_labels:
                weak.append(f"Weak evidence for: {claim} (label={label.value})")
        return weak

    def _detect_ambiguous_goals(self, plan: dict) -> list[str]:
        """Detect ambiguous or underspecified goals."""
        ambiguous: list[str] = []
        goal_id = plan.get("goal_id", "")
        if not goal_id:
            ambiguous.append("Plan has no associated goal")
        tasks = plan.get("tasks", [])
        if len(tasks) == 1 and tasks[0] in ("", "unknown"):
            ambiguous.append("Single undefined task — goal may be ambiguous")
        return ambiguous

    @staticmethod
    def overall_uncertainty(assessment: dict) -> float:
        """Compute overall uncertainty score (0-1, higher = more uncertain).

        Args:
            assessment: Uncertainty assessment dictionary.

        Returns:
            Float between 0.0 (certain) and 1.0 (highly uncertain).
        """
        total_issues = assessment.get("total_issues", 0)
        # Each issue contributes to uncertainty, capped at 1.0
        base = 0.1
        per_issue = 0.1
        return min(base + (total_issues * per_issue), 1.0)
