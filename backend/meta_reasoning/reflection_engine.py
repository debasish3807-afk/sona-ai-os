"""Meta Reasoning & Self Reflection Engine — self-reflection analysis."""

from __future__ import annotations

from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class ReflectionEngine:
    """Performs self-reflection on plans to assess alignment and quality."""

    def reflect(self, plan: dict, goal: dict, context: dict) -> dict[str, Any]:
        """Run full reflection on a plan against a goal.

        Args:
            plan: The execution plan to reflect on.
            goal: The goal the plan is intended to achieve.
            context: Environment context with available resources.

        Returns:
            Reflection report with scores and observations.
        """
        goal_alignment = self._assess_goal_alignment(plan, goal)
        reasoning_quality = self._assess_reasoning_quality(plan)
        planning_quality = self._assess_planning_quality(plan)
        execution_readiness = self._assess_execution_readiness(plan)
        capability_usage = self._assess_capability_usage(plan)
        knowledge_usage = self._assess_knowledge_usage(plan, context)

        overall = (
            goal_alignment * 0.25
            + reasoning_quality * 0.20
            + planning_quality * 0.20
            + execution_readiness * 0.15
            + capability_usage * 0.10
            + knowledge_usage * 0.10
        )

        report: dict[str, Any] = {
            "goal_alignment": goal_alignment,
            "reasoning_quality": reasoning_quality,
            "planning_quality": planning_quality,
            "execution_readiness": execution_readiness,
            "capability_usage": capability_usage,
            "knowledge_usage": knowledge_usage,
            "overall": min(overall, 1.0),
            "observations": [],
        }

        if goal_alignment < 0.5:
            report["observations"].append("Plan poorly aligns with stated goal")
        if reasoning_quality < 0.5:
            report["observations"].append("Reasoning quality below threshold")
        if execution_readiness < 0.5:
            report["observations"].append("Plan not ready for execution")

        logger.info("reflection_complete", overall=overall)
        return report

    def _assess_goal_alignment(self, plan: dict, goal: dict) -> float:
        """Assess how well the plan aligns with the goal."""
        score = 0.5
        plan_goal_id = plan.get("goal_id", "")
        goal_id = goal.get("goal_id", "")
        if plan_goal_id and plan_goal_id == goal_id:
            score += 0.2
        tasks = plan.get("tasks", [])
        if len(tasks) >= 1:
            score += 0.1
        description = goal.get("description", "")
        if description and len(tasks) >= 2:
            score += 0.2
        return min(score, 1.0)

    def _assess_reasoning_quality(self, plan: dict) -> float:
        """Assess the quality of reasoning behind the plan."""
        score = 0.4
        if plan.get("execution_mode"):
            score += 0.2
        if plan.get("estimated_duration_ms", 0) > 0:
            score += 0.2
        if plan.get("risk"):
            score += 0.2
        return min(score, 1.0)

    def _assess_planning_quality(self, plan: dict) -> float:
        """Assess the thoroughness of planning."""
        score = 0.3
        tasks = plan.get("tasks", [])
        if len(tasks) >= 2:
            score += 0.3
        if plan.get("checkpoints"):
            score += 0.2
        if plan.get("rollback_path"):
            score += 0.2
        return min(score, 1.0)

    def _assess_execution_readiness(self, plan: dict) -> float:
        """Assess whether the plan is ready to execute."""
        score = 0.3
        if plan.get("tasks"):
            score += 0.3
        if plan.get("execution_mode"):
            score += 0.2
        if plan.get("capabilities"):
            score += 0.2
        return min(score, 1.0)

    def _assess_capability_usage(self, plan: dict) -> float:
        """Assess how effectively capabilities are utilized."""
        capabilities = plan.get("capabilities", [])
        if not capabilities:
            return 0.3
        if len(capabilities) >= 3:
            return 0.9
        if len(capabilities) >= 1:
            return 0.7
        return 0.5

    def _assess_knowledge_usage(self, plan: dict, context: dict) -> float:
        """Assess how well available knowledge is leveraged."""
        score = 0.5
        available_providers = context.get("available_providers", [])
        if available_providers:
            score += 0.2
        available_caps = context.get("available_capabilities", [])
        plan_caps = plan.get("capabilities", [])
        if plan_caps and available_caps:
            overlap = len(set(plan_caps) & set(available_caps))
            if overlap > 0:
                score += 0.3
        return min(score, 1.0)
