"""Executive Intelligence layer — confidence estimation for decisions and plans."""

from __future__ import annotations

from config.logging import get_logger
from executive.schemas import Decision, ExecutionPlan

logger = get_logger(__name__)


class ConfidenceEngine:
    """Estimates confidence levels across multiple dimensions."""

    def estimate_confidence(self, decision: Decision, plan: ExecutionPlan) -> dict:
        """Produce a comprehensive confidence report."""
        decision_conf = self._decision_confidence(decision)
        plan_conf = self._plan_confidence(plan)
        capability_conf = self._capability_confidence(plan)
        execution_conf = min(decision_conf, plan_conf)
        provider_conf = 0.85  # baseline provider confidence
        model_conf = 0.80  # baseline model confidence

        overall = (
            decision_conf * 0.25
            + plan_conf * 0.25
            + capability_conf * 0.20
            + execution_conf * 0.15
            + provider_conf * 0.10
            + model_conf * 0.05
        )

        return {
            "overall": min(overall, 1.0),
            "decision_confidence": decision_conf,
            "plan_confidence": plan_conf,
            "capability_confidence": capability_conf,
            "execution_confidence": execution_conf,
            "provider_confidence": provider_conf,
            "model_confidence": model_conf,
        }

    def _decision_confidence(self, decision: Decision) -> float:
        """Confidence derived from the decision quality."""
        base = decision.confidence
        # Boost if multiple alternatives were considered
        alt_bonus = min(len(decision.alternatives) * 0.05, 0.2)
        # Penalty for high risk
        risk_penalty = decision.risk * 0.2
        return max(0.0, min(base + alt_bonus - risk_penalty, 1.0))

    def _plan_confidence(self, plan: ExecutionPlan) -> float:
        """Confidence derived from plan completeness."""
        score = 0.5
        if plan.tasks:
            score += 0.2
        if plan.checkpoints:
            score += 0.1
        if plan.rollback_path:
            score += 0.1
        if plan.execution_mode in ("sequential", "parallel"):
            score += 0.1
        return min(score, 1.0)

    def _capability_confidence(self, plan: ExecutionPlan) -> float:
        """Confidence that required capabilities are available."""
        if not plan.tasks:
            return 0.5
        # Assume capabilities are available — in production, this would
        # check a capability registry
        return min(0.7 + len(plan.tasks) * 0.02, 0.95)

    def explain_confidence(self, confidence_report: dict) -> str:
        """Generate a human-readable confidence explanation."""
        overall = confidence_report.get("overall", 0.0)
        lines = [f"Overall Confidence: {overall:.1%}"]

        dimension_names = {
            "decision_confidence": "Decision Quality",
            "plan_confidence": "Plan Completeness",
            "capability_confidence": "Capability Availability",
            "execution_confidence": "Execution Readiness",
            "provider_confidence": "Provider Health",
            "model_confidence": "Model Reliability",
        }
        for key, label in dimension_names.items():
            value = confidence_report.get(key, 0.0)
            lines.append(f"  {label}: {value:.1%}")

        if overall >= 0.8:
            lines.append("Assessment: HIGH confidence — safe to proceed.")
        elif overall >= 0.5:
            lines.append("Assessment: MODERATE confidence — review recommended.")
        else:
            lines.append("Assessment: LOW confidence — human oversight required.")
        return "\n".join(lines)
