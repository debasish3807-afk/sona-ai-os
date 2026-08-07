"""Execution graph for dependency management and ordering.

Builds a directed acyclic graph (DAG) from execution steps, validates
no cycles exist, identifies parallel execution groups, and computes
the critical path latency.
"""

from dataclasses import dataclass, field

import structlog

from sona_thalamus.domain.execution_plan import ExecutionStep

logger = structlog.get_logger(__name__)


class CyclicDependencyError(Exception):
    """Raised when a cycle is detected in the execution graph."""


@dataclass
class ExecutionGraph:
    """DAG of execution steps with dependency tracking.

    Provides topological ordering, parallel group identification,
    and critical path estimation for execution planning.
    """

    _steps: dict[str, ExecutionStep] = field(default_factory=dict)
    _adjacency: dict[str, list[str]] = field(default_factory=dict)

    def add_step(self, step: ExecutionStep) -> None:
        """Add a step to the execution graph.

        Args:
            step: The execution step to add.
        """
        self._steps[step.step_id] = step
        if step.step_id not in self._adjacency:
            self._adjacency[step.step_id] = []

        # Add edges for dependencies
        for dep_id in step.depends_on:
            if dep_id not in self._adjacency:
                self._adjacency[dep_id] = []
            self._adjacency[dep_id].append(step.step_id)

    def topological_sort(self) -> list[ExecutionStep]:
        """Return steps in topologically sorted order.

        Returns:
            List of ExecutionSteps in valid execution order.

        Raises:
            CyclicDependencyError: If a cycle is detected.
        """
        # Calculate in-degree for each node
        in_degree: dict[str, int] = dict.fromkeys(self._steps, 0)
        for step in self._steps.values():
            for dep_id in step.depends_on:
                if dep_id in self._steps:
                    in_degree[step.step_id] = in_degree.get(step.step_id, 0) + 1

        # Find all nodes with no dependencies (in-degree = 0)
        # Use priority for tie-breaking
        queue: list[str] = sorted(
            [sid for sid, deg in in_degree.items() if deg == 0],
            key=lambda sid: self._steps[sid].priority,
        )

        result: list[ExecutionStep] = []
        visited_count = 0

        while queue:
            current = queue.pop(0)
            result.append(self._steps[current])
            visited_count += 1

            # Process neighbors
            for neighbor in self._adjacency.get(current, []):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
                        queue.sort(key=lambda sid: self._steps[sid].priority)

        if visited_count != len(self._steps):
            raise CyclicDependencyError(
                f"Cycle detected: processed {visited_count} of {len(self._steps)} steps"
            )

        return result

    def get_parallel_groups(self) -> list[list[ExecutionStep]]:
        """Identify groups of steps that can execute in parallel.

        Steps with no mutual dependencies and whose prerequisites
        are all satisfied at the same level form a parallel group.

        Returns:
            List of parallel groups, where each group is a list of steps.
        """
        if not self._steps:
            return []

        # Calculate levels using BFS
        in_degree: dict[str, int] = dict.fromkeys(self._steps, 0)
        for step in self._steps.values():
            for dep_id in step.depends_on:
                if dep_id in self._steps:
                    in_degree[step.step_id] = in_degree.get(step.step_id, 0) + 1

        # Group by level
        current_level = [sid for sid, deg in in_degree.items() if deg == 0]
        groups: list[list[ExecutionStep]] = []

        while current_level:
            group = [self._steps[sid] for sid in current_level]
            groups.append(group)

            next_level: list[str] = []
            for sid in current_level:
                for neighbor in self._adjacency.get(sid, []):
                    if neighbor in in_degree:
                        in_degree[neighbor] -= 1
                        if in_degree[neighbor] == 0:
                            next_level.append(neighbor)

            current_level = next_level

        return groups

    def estimate_critical_path_latency(self) -> float:
        """Estimate the critical path latency through the graph.

        The critical path is the longest path considering step timeouts,
        representing the minimum possible total execution time.

        Returns:
            Estimated critical path latency in seconds.
        """
        if not self._steps:
            return 0.0

        # Calculate longest path to each node
        longest_path: dict[str, float] = dict.fromkeys(self._steps, 0.0)

        try:
            sorted_steps = self.topological_sort()
        except CyclicDependencyError:
            # If cycle detected, return sum of all timeouts as upper bound
            return sum(s.timeout_seconds for s in self._steps.values())

        for step in sorted_steps:
            step_time = step.timeout_seconds
            # Add max of dependency paths
            if step.depends_on:
                max_dep_path = max(
                    longest_path.get(dep_id, 0.0)
                    for dep_id in step.depends_on
                    if dep_id in self._steps
                )
                longest_path[step.step_id] = max_dep_path + step_time
            else:
                longest_path[step.step_id] = step_time

        return max(longest_path.values()) if longest_path else 0.0

    def validate(self) -> bool:
        """Validate the graph has no cycles.

        Returns:
            True if the graph is a valid DAG.
        """
        try:
            self.topological_sort()
            return True
        except CyclicDependencyError:
            return False

    @property
    def step_count(self) -> int:
        """Return the number of steps in the graph."""
        return len(self._steps)
