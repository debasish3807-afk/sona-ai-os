"""Meta Reasoning & Self Reflection Engine — plan simulation."""

from __future__ import annotations

from typing import Any

from config.logging import get_logger
from meta_reasoning.schemas import SimulationResult

logger = get_logger(__name__)


class SimulationEngine:
    """Simulates plan execution to predict outcomes without side effects."""

    def simulate(self, plan: dict, context: dict) -> SimulationResult:
        """Simulate plan execution and predict outcomes.

        Args:
            plan: The execution plan to simulate.
            context: Environment context.

        Returns:
            SimulationResult with predicted metrics.
        """
        latency = self._estimate_latency(plan)
        cost = self._estimate_cost(plan)
        tokens = self._estimate_tokens(plan)
        failure_prob = self._estimate_failure_probability(plan)
        resource_usage = self._estimate_resource_usage(plan)
        outcome = self._predict_outcome(plan)

        success = failure_prob < 0.5
        warnings: list[str] = []
        if failure_prob > 0.3:
            warnings.append("Elevated failure probability detected")
        if latency > 10000:
            warnings.append("Estimated latency exceeds 10 seconds")
        if cost > context.get("budget", float("inf")):
            warnings.append("Estimated cost exceeds budget")

        result = SimulationResult(
            success=success,
            estimated_latency_ms=latency,
            estimated_cost=cost,
            estimated_tokens=tokens,
            failure_probability=failure_prob,
            resource_usage=resource_usage,
            expected_outcome=outcome,
            warnings=warnings,
        )
        logger.info("simulation_complete", success=success, latency_ms=latency)
        return result

    def _estimate_latency(self, plan: dict) -> float:
        """Estimate total execution latency in milliseconds."""
        base_latency = plan.get("estimated_duration_ms", 500.0)
        tasks = plan.get("tasks", [])
        task_count = len(tasks)
        mode = plan.get("execution_mode", "sequential")

        if mode == "parallel":
            return float(base_latency + (task_count * 100.0))
        return float(base_latency + (task_count * 200.0))

    def _estimate_cost(self, plan: dict) -> float:
        """Estimate total execution cost."""
        cost_info = plan.get("cost", {})
        base_cost = cost_info.get("total_estimated", 0.01)
        tasks = plan.get("tasks", [])
        return float(base_cost + (len(tasks) * 0.005))

    def _estimate_tokens(self, plan: dict) -> int:
        """Estimate total token usage."""
        tasks = plan.get("tasks", [])
        base_tokens = 500
        per_task = 200
        return base_tokens + (len(tasks) * per_task)

    def _estimate_failure_probability(self, plan: dict) -> float:
        """Estimate probability of plan failure."""
        risk_info = plan.get("risk", {})
        base_risk = risk_info.get("overall_risk", 0.1)
        tasks = plan.get("tasks", [])
        task_factor = min(len(tasks) * 0.02, 0.3)
        mode = plan.get("execution_mode", "sequential")
        mode_factor = 0.05 if mode == "parallel" else 0.0
        return float(min(base_risk + task_factor + mode_factor, 1.0))

    def _estimate_resource_usage(self, plan: dict) -> dict[str, Any]:
        """Estimate resource usage during execution."""
        tasks = plan.get("tasks", [])
        mode = plan.get("execution_mode", "sequential")
        concurrency = len(tasks) if mode == "parallel" else 1
        return {
            "memory_mb": 128 + (concurrency * 64),
            "cpu_cores": max(1, concurrency),
            "network_calls": len(tasks) * 2,
            "concurrency": concurrency,
        }

    def _predict_outcome(self, plan: dict) -> str:
        """Predict the expected outcome of plan execution."""
        risk_info = plan.get("risk", {})
        risk = risk_info.get("overall_risk", 0.1)
        tasks = plan.get("tasks", [])
        if risk < 0.2 and len(tasks) <= 5:
            return "High probability of successful completion"
        if risk < 0.5:
            return "Moderate probability of success with possible partial failures"
        return "Elevated risk — may require intervention or fallback"

    def dry_run(self, plan: dict) -> dict[str, Any]:
        """Execute a dry run producing an execution trace without side effects.

        Args:
            plan: The execution plan to dry-run.

        Returns:
            Execution trace dictionary.
        """
        tasks = plan.get("tasks", [])
        trace_steps: list[dict[str, Any]] = []
        cumulative_ms = 0.0

        for i, task in enumerate(tasks):
            step_latency = 200.0
            cumulative_ms += step_latency
            trace_steps.append(
                {
                    "step": i + 1,
                    "task": task,
                    "status": "simulated_success",
                    "latency_ms": step_latency,
                    "cumulative_ms": cumulative_ms,
                }
            )

        return {
            "plan_id": plan.get("plan_id", "unknown"),
            "steps": trace_steps,
            "total_latency_ms": cumulative_ms,
            "total_steps": len(trace_steps),
            "dry_run": True,
        }
