"""Executive Intelligence layer — task graph for execution planning."""

from __future__ import annotations

import uuid
from collections import deque
from dataclasses import dataclass, field


@dataclass
class TaskNode:
    """A single task node in the execution graph."""

    name: str
    capability_id: str
    params: dict = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    priority: int = 0
    timeout_seconds: float = 30.0
    max_retries: int = 3
    status: str = "pending"
    result: dict = field(default_factory=dict)
    duration_ms: float = 0.0
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class TaskGraph:
    """Directed acyclic graph of tasks for execution ordering."""

    def __init__(self) -> None:
        self._nodes: dict[str, TaskNode] = {}
        self._edges: dict[str, list[str]] = {}

    def add_task(self, node: TaskNode) -> str:
        """Add a task node to the graph. Returns the task_id."""
        self._nodes[node.task_id] = node
        if node.task_id not in self._edges:
            self._edges[node.task_id] = []
        return node.task_id

    def add_dependency(self, task_id: str, depends_on: str) -> None:
        """Mark task_id as depending on depends_on."""
        if depends_on not in self._edges:
            self._edges[depends_on] = []
        self._edges[depends_on].append(task_id)
        if task_id in self._nodes:
            node = self._nodes[task_id]
            if depends_on not in node.dependencies:
                node.dependencies.append(depends_on)

    def get_ready_tasks(self) -> list[TaskNode]:
        """Return tasks with no pending dependencies."""
        ready: list[TaskNode] = []
        for _task_id, node in self._nodes.items():
            if node.status != "pending":
                continue
            all_deps_completed = all(
                self._nodes[dep].status == "completed"
                for dep in node.dependencies
                if dep in self._nodes
            )
            if all_deps_completed:
                ready.append(node)
        return ready

    def mark_completed(self, task_id: str, result: dict) -> None:
        """Mark a task as completed with its result."""
        if task_id in self._nodes:
            self._nodes[task_id].status = "completed"
            self._nodes[task_id].result = result

    def mark_failed(self, task_id: str, error: str) -> None:
        """Mark a task as failed."""
        if task_id in self._nodes:
            self._nodes[task_id].status = "failed"
            self._nodes[task_id].result = {"error": error}

    def get_execution_order(self) -> list[str]:
        """Return topological sort of task IDs."""
        in_degree: dict[str, int] = dict.fromkeys(self._nodes, 0)
        for _source, targets in self._edges.items():
            for target in targets:
                if target in in_degree:
                    in_degree[target] += 1

        queue: deque[str] = deque(tid for tid, deg in in_degree.items() if deg == 0)
        order: list[str] = []
        while queue:
            current = queue.popleft()
            order.append(current)
            for neighbor in self._edges.get(current, []):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
        return order

    def has_cycle(self) -> bool:
        """Check if the graph contains a cycle."""
        order = self.get_execution_order()
        return len(order) != len(self._nodes)

    def get_critical_path(self) -> list[str]:
        """Return the longest path through the graph (critical path)."""
        if not self._nodes:
            return []
        order = self.get_execution_order()
        if not order:
            return []
        dist: dict[str, float] = dict.fromkeys(order, 0.0)
        parent: dict[str, str | None] = dict.fromkeys(order)

        for tid in order:
            node = self._nodes[tid]
            node_cost = node.timeout_seconds
            for neighbor in self._edges.get(tid, []):
                if neighbor in dist:
                    new_dist = dist[tid] + node_cost
                    if new_dist > dist[neighbor]:
                        dist[neighbor] = new_dist
                        parent[neighbor] = tid

        end_node = max(dist, key=lambda k: dist[k])
        path: list[str] = []
        current: str | None = end_node
        while current is not None:
            path.append(current)
            current = parent[current]
        path.reverse()
        return path

    def to_dict(self) -> dict:
        """Serialize the task graph."""
        return {
            "nodes": {
                tid: {
                    "task_id": n.task_id,
                    "name": n.name,
                    "capability_id": n.capability_id,
                    "status": n.status,
                    "priority": n.priority,
                    "dependencies": n.dependencies,
                }
                for tid, n in self._nodes.items()
            },
            "edges": self._edges,
            "total_tasks": len(self._nodes),
        }
