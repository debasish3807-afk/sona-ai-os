"""Executive Intelligence layer — risk assessment engine."""

from __future__ import annotations

from config.logging import get_logger
from executive.schemas import ExecutionPlan, Goal

logger = get_logger(__name__)


class RiskEngine:
    """Assesses risk across multiple dimensions for execution plans."""

    def assess_risk(self, plan: ExecutionPlan, goal: Goal) -> dict:
        """Produce a comprehensive risk assessment."""
        execution_risk = self._execution_risk(plan)
        security_risk = self._security_risk(plan)
        failure_probability = self._failure_probability(plan)
        recovery_complexity = self._recovery_complexity(plan)

        task_count = len(plan.tasks)
        resource_risk = min(task_count / 20.0, 1.0)
        cost_risk = min(plan.estimated_duration_ms / 60000.0, 1.0)
        confidence_risk = 1.0 - min(goal.progress + 0.3, 1.0)

        overall = (
            execution_risk * 0.25
            + security_risk * 0.20
            + failure_probability * 0.20
            + recovery_complexity * 0.15
            + resource_risk * 0.10
            + cost_risk * 0.05
            + confidence_risk * 0.05
        )

        return {
            "overall_risk": min(overall, 1.0),
            "execution_risk": execution_risk,
            "security_risk": security_risk,
            "failure_probability": failure_probability,
            "recovery_complexity": recovery_complexity,
            "resource_risk": resource_risk,
            "cost_risk": cost_risk,
            "confidence_risk": confidence_risk,
        }

    def _execution_risk(self, plan: ExecutionPlan) -> float:
        """Assess risk from execution complexity."""
        task_count = len(plan.tasks)
        if task_count == 0:
            return 0.0
        base = min(task_count / 10.0, 0.8)
        mode_factor = {"parallel": 0.1, "conditional": 0.15}.get(plan.execution_mode, 0.0)
        return min(base + mode_factor, 1.0)

    def _security_risk(self, plan: ExecutionPlan) -> float:
        """Assess security-related risk."""
        sensitive_keywords = ["delete", "admin", "secret", "credential", "sudo"]
        hit_count = sum(1 for task in plan.tasks for kw in sensitive_keywords if kw in task.lower())
        return min(hit_count * 0.2, 1.0)

    def _failure_probability(self, plan: ExecutionPlan) -> float:
        """Estimate probability of plan failure."""
        task_count = len(plan.tasks)
        if task_count == 0:
            return 0.0
        per_task_failure = 0.05
        # 1 - (1 - p)^n compound probability
        return 1.0 - (1.0 - per_task_failure) ** task_count

    def _recovery_complexity(self, plan: ExecutionPlan) -> float:
        """Assess how complex recovery would be on failure."""
        if plan.rollback_path:
            return min(len(plan.rollback_path) / 20.0, 0.8)
        return min(len(plan.tasks) / 10.0, 1.0)

    def get_risk_factors(self, plan: ExecutionPlan) -> list[dict]:
        """Return individual risk factors with descriptions and severity."""
        factors: list[dict] = []
        task_count = len(plan.tasks)

        if task_count > 5:
            factors.append(
                {
                    "factor": "high_task_count",
                    "description": f"Plan has {task_count} tasks which increases complexity",
                    "severity": min(task_count / 10.0, 1.0),
                }
            )
        if plan.execution_mode == "parallel":
            factors.append(
                {
                    "factor": "parallel_execution",
                    "description": "Parallel execution increases coordination risk",
                    "severity": 0.3,
                }
            )
        if not plan.rollback_path:
            factors.append(
                {
                    "factor": "no_rollback",
                    "description": "No rollback path defined for recovery",
                    "severity": 0.5,
                }
            )
        if not plan.checkpoints:
            factors.append(
                {
                    "factor": "no_checkpoints",
                    "description": "No checkpoints for progress tracking",
                    "severity": 0.3,
                }
            )
        return factors
