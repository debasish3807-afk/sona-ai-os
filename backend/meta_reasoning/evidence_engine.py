"""Meta Reasoning & Self Reflection Engine — evidence verification."""

from __future__ import annotations

from config.logging import get_logger
from meta_reasoning.schemas import EvidenceLabel

logger = get_logger(__name__)


class EvidenceEngine:
    """Verifies and labels evidence supporting a plan."""

    def verify(self, plan: dict, context: dict) -> dict[str, EvidenceLabel]:
        """Verify all evidence claims in a plan.

        Args:
            plan: The execution plan containing claims.
            context: Environment context for verification.

        Returns:
            Dictionary mapping claim keys to evidence labels.
        """
        labels: dict[str, EvidenceLabel] = {}

        for key, label in self._verify_memory_evidence(plan, context):
            labels[key] = label
        for key, label in self._verify_knowledge_evidence(plan, context):
            labels[key] = label
        for key, label in self._verify_reasoning_evidence(plan):
            labels[key] = label
        for key, label in self._verify_capability_evidence(plan):
            labels[key] = label

        logger.info("evidence_verification_complete", total_claims=len(labels))
        return labels

    def _verify_memory_evidence(self, plan: dict, context: dict) -> list[tuple[str, EvidenceLabel]]:
        """Verify claims based on memory/history."""
        results: list[tuple[str, EvidenceLabel]] = []
        plan_id = plan.get("plan_id", "unknown")

        # If context has prior execution data, we can verify
        prior_results = context.get("prior_results", [])
        if prior_results:
            results.append((f"{plan_id}:memory_backed", EvidenceLabel.VERIFIED))
        else:
            results.append((f"{plan_id}:memory_backed", EvidenceLabel.ESTIMATED))

        return results

    def _verify_knowledge_evidence(
        self, plan: dict, context: dict
    ) -> list[tuple[str, EvidenceLabel]]:
        """Verify claims based on knowledge base."""
        results: list[tuple[str, EvidenceLabel]] = []
        plan_id = plan.get("plan_id", "unknown")

        available_providers = context.get("available_providers", [])
        if available_providers:
            results.append((f"{plan_id}:provider_available", EvidenceLabel.VERIFIED))
        else:
            results.append((f"{plan_id}:provider_available", EvidenceLabel.HYPOTHESIS))

        available_caps = context.get("available_capabilities", [])
        plan_caps = plan.get("capabilities", [])
        if plan_caps and all(c in available_caps for c in plan_caps):
            results.append((f"{plan_id}:capabilities_available", EvidenceLabel.VERIFIED))
        elif plan_caps:
            results.append((f"{plan_id}:capabilities_available", EvidenceLabel.INFERRED))
        else:
            results.append((f"{plan_id}:capabilities_available", EvidenceLabel.HYPOTHESIS))

        return results

    def _verify_reasoning_evidence(self, plan: dict) -> list[tuple[str, EvidenceLabel]]:
        """Verify claims based on reasoning chain."""
        results: list[tuple[str, EvidenceLabel]] = []
        plan_id = plan.get("plan_id", "unknown")

        # Cost estimates are typically estimated, not verified
        cost_info = plan.get("cost", {})
        if cost_info.get("total_estimated", 0) > 0:
            results.append((f"{plan_id}:cost_estimate", EvidenceLabel.ESTIMATED))

        # Duration estimates are inferred from task count
        if plan.get("estimated_duration_ms", 0) > 0:
            results.append((f"{plan_id}:duration_estimate", EvidenceLabel.INFERRED))

        return results

    def _verify_capability_evidence(self, plan: dict) -> list[tuple[str, EvidenceLabel]]:
        """Verify claims about capability availability and fitness."""
        results: list[tuple[str, EvidenceLabel]] = []
        plan_id = plan.get("plan_id", "unknown")

        capabilities = plan.get("capabilities", [])
        if capabilities:
            results.append((f"{plan_id}:capability_fitness", EvidenceLabel.INFERRED))
        else:
            results.append((f"{plan_id}:capability_fitness", EvidenceLabel.HYPOTHESIS))

        return results

    @staticmethod
    def get_confidence_from_evidence(labels: dict[str, EvidenceLabel]) -> float:
        """Compute aggregate confidence from evidence labels.

        Args:
            labels: Dictionary of claim keys to evidence labels.

        Returns:
            Confidence score between 0 and 1.
        """
        if not labels:
            return 0.3

        weights = {
            EvidenceLabel.VERIFIED: 1.0,
            EvidenceLabel.INFERRED: 0.7,
            EvidenceLabel.ESTIMATED: 0.5,
            EvidenceLabel.HYPOTHESIS: 0.2,
        }

        total_weight = sum(weights.get(label, 0.3) for label in labels.values())
        return min(total_weight / len(labels), 1.0)
