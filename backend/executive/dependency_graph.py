"""Executive Intelligence layer — dependency graph for goal and task ordering."""

from __future__ import annotations

from collections import deque


class ExecutiveDependencyGraph:
    """Generic dependency graph for ordering goals, tasks, or resources."""

    def __init__(self) -> None:
        self._adjacency: dict[str, list[str]] = {}
        self._reverse: dict[str, list[str]] = {}

    def add_node(self, node_id: str) -> None:
        """Add a node to the graph."""
        if node_id not in self._adjacency:
            self._adjacency[node_id] = []
        if node_id not in self._reverse:
            self._reverse[node_id] = []

    def add_edge(self, from_id: str, to_id: str) -> None:
        """Add a directed edge from from_id to to_id."""
        self.add_node(from_id)
        self.add_node(to_id)
        if to_id not in self._adjacency[from_id]:
            self._adjacency[from_id].append(to_id)
        if from_id not in self._reverse[to_id]:
            self._reverse[to_id].append(from_id)

    def get_dependencies(self, node_id: str) -> list[str]:
        """Get all nodes that node_id depends on (incoming edges)."""
        return list(self._reverse.get(node_id, []))

    def get_dependents(self, node_id: str) -> list[str]:
        """Get all nodes that depend on node_id (outgoing edges)."""
        return list(self._adjacency.get(node_id, []))

    def topological_sort(self) -> list[str]:
        """Return a topological ordering of all nodes."""
        in_degree: dict[str, int] = dict.fromkeys(self._adjacency, 0)
        for node in self._adjacency:
            for neighbor in self._adjacency[node]:
                in_degree[neighbor] = in_degree.get(neighbor, 0) + 1

        queue: deque[str] = deque(node for node, deg in in_degree.items() if deg == 0)
        order: list[str] = []
        while queue:
            current = queue.popleft()
            order.append(current)
            for neighbor in self._adjacency.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        return order

    def has_cycle(self) -> bool:
        """Check if the graph contains a cycle."""
        order = self.topological_sort()
        return len(order) != len(self._adjacency)

    def get_parallel_groups(self) -> list[list[str]]:
        """Return groups of nodes that can execute concurrently (by level)."""
        in_degree: dict[str, int] = dict.fromkeys(self._adjacency, 0)
        for node in self._adjacency:
            for neighbor in self._adjacency[node]:
                in_degree[neighbor] = in_degree.get(neighbor, 0) + 1

        current_level: list[str] = [node for node, deg in in_degree.items() if deg == 0]
        groups: list[list[str]] = []

        while current_level:
            groups.append(list(current_level))
            next_level: list[str] = []
            for node in current_level:
                for neighbor in self._adjacency.get(node, []):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        next_level.append(neighbor)
            current_level = next_level

        return groups

    def to_dict(self) -> dict:
        """Serialize the dependency graph."""
        return {
            "nodes": list(self._adjacency.keys()),
            "edges": {node: targets for node, targets in self._adjacency.items() if targets},
            "total_nodes": len(self._adjacency),
        }
