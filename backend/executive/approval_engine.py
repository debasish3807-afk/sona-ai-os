"""Executive Intelligence layer — approval gate engine."""

from __future__ import annotations

import time

from config.logging import get_logger
from executive.schemas import ApprovalStatus, ExecutionPlan

logger = get_logger(__name__)


class ApprovalEngine:
    """Evaluates plans and determines approval status."""

    DEFAULT_BUDGET: float = 1.0

    def __init__(self) -> None:
        self._history: list[dict] = []

    def evaluate(
        self,
        plan: ExecutionPlan,
        risk: dict,
        cost: dict,
        confidence: dict,
    ) -> ApprovalStatus:
        """Evaluate a plan and determine approval status."""
        overall_risk = risk.get("overall_risk", 0.5)
        total_cost = cost.get("total_estimated", 0.0)
        overall_confidence = confidence.get("overall", 0.5)

        if self._should_block(risk):
            status = ApprovalStatus.BLOCKED
        elif self._should_auto_approve(risk, cost, confidence):
            status = ApprovalStatus.AUTO_APPROVED
        elif self._requires_human_approval(risk, cost):
            status = ApprovalStatus.PENDING_APPROVAL
        else:
            status = ApprovalStatus.PENDING_APPROVAL

        self._history.append(
            {
                "plan_id": plan.plan_id,
                "status": status.value,
                "risk": overall_risk,
                "cost": total_cost,
                "confidence": overall_confidence,
                "timestamp": time.time(),
            }
        )

        plan.approval_status = status
        logger.info(
            "approval_evaluated",
            plan_id=plan.plan_id,
            status=status.value,
            risk=overall_risk,
        )
        return status

    def _should_auto_approve(self, risk: dict, cost: dict, confidence: dict) -> bool:
        """Auto-approve if risk < 0.3 AND cost < budget AND confidence > 0.7."""
        overall_risk = risk.get("overall_risk", 1.0)
        total_cost = cost.get("total_estimated", float("inf"))
        overall_confidence = confidence.get("overall", 0.0)
        return bool(
            overall_risk < 0.3 and total_cost < self.DEFAULT_BUDGET and overall_confidence > 0.7
        )

    def _requires_human_approval(self, risk: dict, cost: dict) -> bool:
        """Require human approval if risk > 0.6 OR cost > budget * 0.8."""
        overall_risk = risk.get("overall_risk", 0.0)
        total_cost = cost.get("total_estimated", 0.0)
        return bool(overall_risk > 0.6 or total_cost > self.DEFAULT_BUDGET * 0.8)

    def _should_block(self, risk: dict) -> bool:
        """Block if risk > 0.9."""
        overall_risk = risk.get("overall_risk", 0.0)
        return bool(overall_risk > 0.9)

    def explain_decision(
        self,
        status: ApprovalStatus,
        risk: dict,
        cost: dict,
        confidence: dict,
    ) -> str:
        """Generate human-readable explanation of approval decision."""
        overall_risk = risk.get("overall_risk", 0.0)
        total_cost = cost.get("total_estimated", 0.0)
        overall_confidence = confidence.get("overall", 0.0)

        lines = [
            f"Approval Status: {status.value}",
            f"Risk Level: {overall_risk:.1%}",
            f"Estimated Cost: ${total_cost:.4f}",
            f"Confidence: {overall_confidence:.1%}",
        ]
        if status == ApprovalStatus.AUTO_APPROVED:
            lines.append("Reason: Low risk, within budget, high confidence.")
        elif status == ApprovalStatus.BLOCKED:
            lines.append("Reason: Risk exceeds safety threshold (>90%).")
        elif status == ApprovalStatus.PENDING_APPROVAL:
            lines.append("Reason: Requires human review due to risk or cost levels.")
        return "\n".join(lines)

    def get_approval_history(self) -> list[dict]:
        """Return the history of approval decisions."""
        return list(self._history)
