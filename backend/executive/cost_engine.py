"""Executive Intelligence layer — cost estimation and budget management."""

from __future__ import annotations

from config.logging import get_logger
from executive.schemas import ExecutionPlan

logger = get_logger(__name__)


class CostEngine:
    """Estimates costs for execution plans and performs budget checks."""

    TOKEN_COST_PER_TASK: float = 0.002
    COMPUTE_COST_PER_MS: float = 0.000001
    API_COST_PER_CALL: float = 0.005

    def estimate_cost(self, plan: ExecutionPlan, capabilities: list[str]) -> dict:
        """Estimate total cost breakdown for a plan."""
        task_count = len(plan.tasks)
        token_cost = task_count * self.TOKEN_COST_PER_TASK
        compute_cost = plan.estimated_duration_ms * self.COMPUTE_COST_PER_MS
        api_cost = len(capabilities) * self.API_COST_PER_CALL
        total = token_cost + compute_cost + api_cost

        breakdown: dict[str, float] = {}
        for task in plan.tasks:
            breakdown[task] = self.TOKEN_COST_PER_TASK + self.API_COST_PER_CALL * 0.5

        return {
            "total_estimated": total,
            "token_cost": token_cost,
            "compute_cost": compute_cost,
            "api_cost": api_cost,
            "breakdown": breakdown,
        }

    def compare_costs(self, plans: list[ExecutionPlan]) -> list[dict]:
        """Compare costs across multiple plans and rank them."""
        results: list[dict] = []
        for plan in plans:
            cost = self.estimate_cost(plan, plan.tasks)
            results.append(
                {
                    "plan_id": plan.plan_id,
                    "cost": cost["total_estimated"],
                    "rank": 0,
                }
            )
        results.sort(key=lambda x: x["cost"])
        for idx, item in enumerate(results):
            item["rank"] = idx + 1
        return results

    def budget_check(self, plan: ExecutionPlan, budget: float) -> tuple[bool, float]:
        """Check if a plan fits within a budget.

        Returns (within_budget, remaining_budget).
        """
        cost = self.estimate_cost(plan, plan.tasks)
        total = cost["total_estimated"]
        remaining = budget - total
        within = total <= budget
        if not within:
            logger.warning(
                "budget_exceeded",
                plan_id=plan.plan_id,
                cost=total,
                budget=budget,
            )
        return within, remaining
