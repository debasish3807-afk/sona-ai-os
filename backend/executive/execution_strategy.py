"""Executive Intelligence layer — execution mode selection and resource estimation."""

from __future__ import annotations

from executive.task_graph import TaskNode


class ExecutionStrategy:
    """Selects execution mode and estimates resource requirements."""

    def select_mode(self, plan_size: int, dependencies: int, risk: float) -> str:
        """Select the best execution mode based on plan characteristics.

        Returns 'sequential', 'parallel', or 'mixed'.
        """
        if risk > 0.7:
            return "sequential"
        if dependencies == 0 and plan_size > 1:
            return "parallel"
        if plan_size > 5 and dependencies < plan_size * 0.5:
            return "mixed"
        if plan_size <= 2:
            return "sequential"
        return "mixed"

    def estimate_duration(self, tasks: list[TaskNode], mode: str) -> float:
        """Estimate total execution duration in milliseconds."""
        if not tasks:
            return 0.0
        timeouts = [t.timeout_seconds * 1000.0 for t in tasks]
        if mode == "parallel":
            return max(timeouts)
        if mode == "sequential":
            return sum(timeouts)
        # mixed: estimate as sqrt of sum * max (geometric mean approximation)
        total = sum(timeouts)
        longest = max(timeouts)
        return float((total * longest) ** 0.5)

    def calculate_resource_needs(self, tasks: list[TaskNode]) -> dict:
        """Calculate aggregate resource needs for a set of tasks."""
        total_timeout = sum(t.timeout_seconds for t in tasks)
        max_concurrency = min(len(tasks), 8)
        total_retries = sum(t.max_retries for t in tasks)

        return {
            "total_timeout_seconds": total_timeout,
            "max_concurrency": max_concurrency,
            "total_max_retries": total_retries,
            "task_count": len(tasks),
            "estimated_memory_mb": len(tasks) * 64,
        }
