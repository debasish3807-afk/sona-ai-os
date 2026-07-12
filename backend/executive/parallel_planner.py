"""Executive Intelligence layer — parallel execution planning."""

from __future__ import annotations

from executive.task_graph import TaskGraph


class ParallelPlanner:
    """Plans and validates parallel task execution."""

    def identify_parallel_tasks(self, graph: TaskGraph) -> list[list[str]]:
        """Identify groups of tasks that can run concurrently."""
        order = graph.get_execution_order()
        if not order:
            return []

        levels: dict[str, int] = {}
        for task_id in order:
            node = graph._nodes.get(task_id)
            if node is None:
                continue
            if not node.dependencies:
                levels[task_id] = 0
            else:
                dep_levels = [levels.get(d, 0) for d in node.dependencies if d in levels]
                levels[task_id] = (max(dep_levels) + 1) if dep_levels else 0

        groups: dict[int, list[str]] = {}
        for task_id, level in levels.items():
            if level not in groups:
                groups[level] = []
            groups[level].append(task_id)

        return [groups[lvl] for lvl in sorted(groups.keys())]

    def plan_parallel_execution(
        self, tasks: list[list[str]], max_concurrency: int = 4
    ) -> list[dict]:
        """Plan parallel execution respecting concurrency limits."""
        execution_plan: list[dict] = []
        for group in tasks:
            # Split large groups into batches
            batches: list[list[str]] = []
            for i in range(0, len(group), max_concurrency):
                batches.append(group[i : i + max_concurrency])

            for batch in batches:
                execution_plan.append(
                    {
                        "mode": "parallel",
                        "tasks": batch,
                        "concurrency": len(batch),
                    }
                )
        return execution_plan

    def estimate_parallel_duration(self, groups: list[list[str]], graph: TaskGraph) -> float:
        """Estimate total duration with parallel execution."""
        total_ms = 0.0
        for group in groups:
            # Duration of a parallel group is the max task duration
            max_duration = 0.0
            for task_id in group:
                node = graph._nodes.get(task_id)
                if node is not None:
                    duration = node.timeout_seconds * 1000.0
                    max_duration = max(max_duration, duration)
            total_ms += max_duration
        return total_ms

    def validate_parallel_safety(
        self, groups: list[list[str]], graph: TaskGraph
    ) -> tuple[bool, list[str]]:
        """Validate that parallel groups don't violate dependencies."""
        errors: list[str] = []
        for group in groups:
            group_set = set(group)
            for task_id in group:
                node = graph._nodes.get(task_id)
                if node is None:
                    continue
                for dep in node.dependencies:
                    if dep in group_set:
                        errors.append(f"Task {task_id} depends on {dep} in same parallel group")
        valid = len(errors) == 0
        return valid, errors
