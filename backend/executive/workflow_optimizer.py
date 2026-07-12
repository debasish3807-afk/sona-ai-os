"""Executive Intelligence layer — workflow optimization."""

from __future__ import annotations

from config.logging import get_logger
from executive.schemas import ExecutionPlan
from executive.task_graph import TaskGraph

logger = get_logger(__name__)


class WorkflowOptimizer:
    """Optimizes execution plans for improved performance."""

    def optimize(self, plan: ExecutionPlan, metric: str = "balanced") -> ExecutionPlan:
        """Optimize an execution plan based on the target metric.

        Metrics: 'speed', 'cost', 'balanced'.
        """
        if metric == "speed":
            plan.execution_mode = "parallel"
        elif metric == "cost":
            plan.execution_mode = "sequential"
            # Remove redundant tasks
            seen: set[str] = set()
            unique_tasks: list[str] = []
            for task in plan.tasks:
                if task not in seen:
                    seen.add(task)
                    unique_tasks.append(task)
            plan.tasks = unique_tasks
        else:
            # balanced: use parallel if >3 tasks, else sequential
            if len(plan.tasks) > 3:
                plan.execution_mode = "parallel"
            else:
                plan.execution_mode = "sequential"

        # Reduce estimated duration based on optimization
        if plan.execution_mode == "parallel" and len(plan.tasks) > 1:
            plan.estimated_duration_ms = plan.estimated_duration_ms / len(plan.tasks)

        logger.info(
            "workflow_optimized",
            plan_id=plan.plan_id,
            metric=metric,
            mode=plan.execution_mode,
        )
        return plan

    def optimize_order(self, tasks: list[str], graph: TaskGraph) -> list[str]:
        """Optimize task execution order using topological ordering."""
        topo_order = graph.get_execution_order()
        # Intersect with requested tasks preserving topo order
        task_set = set(tasks)
        ordered = [t for t in topo_order if t in task_set]
        # Add any tasks not in the graph at the end
        remaining = [t for t in tasks if t not in set(ordered)]
        return ordered + remaining

    def optimize_parallelism(self, graph: TaskGraph) -> list[list[str]]:
        """Identify groups of tasks that can execute in parallel."""
        order = graph.get_execution_order()
        if not order:
            return []

        # Group by depth level in the graph
        levels: dict[str, int] = {}
        for task_id in order:
            node = graph._nodes.get(task_id)
            if node is None:
                continue
            if not node.dependencies:
                levels[task_id] = 0
            else:
                max_dep_level = max(levels.get(dep, 0) for dep in node.dependencies)
                levels[task_id] = max_dep_level + 1

        groups: dict[int, list[str]] = {}
        for task_id, level in levels.items():
            if level not in groups:
                groups[level] = []
            groups[level].append(task_id)

        return [groups[lvl] for lvl in sorted(groups.keys())]

    def estimate_savings(self, original: ExecutionPlan, optimized: ExecutionPlan) -> dict:
        """Estimate performance savings from optimization."""
        time_saved = original.estimated_duration_ms - optimized.estimated_duration_ms
        cost_saved = len(original.tasks) * 0.002 - len(optimized.tasks) * 0.002
        original_duration = max(original.estimated_duration_ms, 1.0)
        efficiency_gain = time_saved / original_duration

        return {
            "time_saved_ms": max(time_saved, 0.0),
            "cost_saved": max(cost_saved, 0.0),
            "efficiency_gain": max(efficiency_gain, 0.0),
        }
