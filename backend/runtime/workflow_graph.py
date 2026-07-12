"""Directed Acyclic Graph (DAG) representation for workflow task dependencies."""

from __future__ import annotations

from collections import deque
from typing import Any

from config.logging import get_logger
from runtime.schemas import TaskState, WorkflowTask

logger = get_logger(__name__)


class WorkflowGraph:
    """DAG-based workflow graph supporting dependency resolution and execution ordering."""

    def __init__(self) -> None:
        self._tasks: dict[str, WorkflowTask] = {}
        self._edges: dict[str, list[str]] = {}

    def add_task(self, task: WorkflowTask) -> str:
        """Add a task to the graph and return its ID."""
        self._tasks[task.task_id] = task
        if task.task_id not in self._edges:
            self._edges[task.task_id] = []
        for dep in task.dependencies:
            if dep not in self._edges:
                self._edges[dep] = []
        logger.debug("task_added", task_id=task.task_id, name=task.name)
        return task.task_id

    def add_dependency(self, task_id: str, depends_on: str) -> None:
        """Add a dependency edge: task_id depends on depends_on."""
        if task_id in self._tasks:
            if depends_on not in self._tasks[task_id].dependencies:
                self._tasks[task_id].dependencies.append(depends_on)
        if depends_on not in self._edges:
            self._edges[depends_on] = []

    def get_ready_tasks(self) -> list[WorkflowTask]:
        """Return tasks whose dependencies are all completed."""
        ready: list[WorkflowTask] = []
        for _task_id, task in self._tasks.items():
            if task.state != TaskState.PENDING:
                continue
            all_deps_done = all(
                self._tasks[dep].state == TaskState.COMPLETED
                for dep in task.dependencies
                if dep in self._tasks
            )
            if all_deps_done:
                ready.append(task)
        return ready

    def get_execution_layers(self) -> list[list[str]]:
        """Return parallelizable groups (layers) for execution."""
        in_degree: dict[str, int] = dict.fromkeys(self._tasks, 0)
        for task in self._tasks.values():
            for dep in task.dependencies:
                if dep in self._tasks:
                    in_degree[task.task_id] = in_degree.get(task.task_id, 0) + 1

        layers: list[list[str]] = []
        remaining = dict(in_degree)

        while remaining:
            layer = [tid for tid, deg in remaining.items() if deg == 0]
            if not layer:
                break
            layers.append(layer)
            for tid in layer:
                del remaining[tid]
                for other_id, task in self._tasks.items():
                    if other_id in remaining and tid in task.dependencies:
                        remaining[other_id] -= 1

        return layers

    def topological_sort(self) -> list[str]:
        """Return task IDs in topological order."""
        in_degree: dict[str, int] = dict.fromkeys(self._tasks, 0)
        for task in self._tasks.values():
            for dep in task.dependencies:
                if dep in self._tasks:
                    in_degree[task.task_id] = in_degree.get(task.task_id, 0) + 1

        queue: deque[str] = deque(tid for tid, deg in in_degree.items() if deg == 0)
        result: list[str] = []

        while queue:
            tid = queue.popleft()
            result.append(tid)
            for other_id, task in self._tasks.items():
                if tid in task.dependencies:
                    in_degree[other_id] -= 1
                    if in_degree[other_id] == 0:
                        queue.append(other_id)

        return result

    def has_cycle(self) -> bool:
        """Check if the graph contains a cycle."""
        sorted_nodes = self.topological_sort()
        return len(sorted_nodes) != len(self._tasks)

    def get_critical_path(self) -> list[str]:
        """Compute the longest path through the DAG (critical path)."""
        topo_order = self.topological_sort()
        if not topo_order:
            return []

        dist: dict[str, float] = dict.fromkeys(self._tasks, 0.0)
        predecessor: dict[str, str] = {}

        for tid in topo_order:
            task = self._tasks[tid]
            for other_id, other_task in self._tasks.items():
                if tid in other_task.dependencies:
                    new_dist = dist[tid] + task.timeout_seconds
                    if new_dist > dist[other_id]:
                        dist[other_id] = new_dist
                        predecessor[other_id] = tid

        if not dist:
            return []

        end_node = max(dist, key=lambda k: dist[k])
        path: list[str] = []
        current: str | None = end_node
        while current is not None:
            path.append(current)
            current = predecessor.get(current)
        path.reverse()
        return path

    def mark_completed(self, task_id: str, result: dict[str, Any]) -> None:
        """Mark a task as completed with its result."""
        if task_id in self._tasks:
            self._tasks[task_id].state = TaskState.COMPLETED
            self._tasks[task_id].result = result

    def mark_failed(self, task_id: str, error: str) -> None:
        """Mark a task as failed with an error message."""
        if task_id in self._tasks:
            self._tasks[task_id].state = TaskState.FAILED
            self._tasks[task_id].result = {"error": error}

    def get_progress(self) -> float:
        """Return completion progress as a float between 0 and 1."""
        if not self._tasks:
            return 1.0
        completed = sum(1 for t in self._tasks.values() if t.state == TaskState.COMPLETED)
        return completed / len(self._tasks)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the graph to a dictionary."""
        return {
            "tasks": {tid: t.to_dict() for tid, t in self._tasks.items()},
            "edges": self._edges,
            "progress": self.get_progress(),
            "layers": self.get_execution_layers(),
        }
