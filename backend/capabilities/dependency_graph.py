"""Dependency Graph — directed graph of capability dependencies."""

from __future__ import annotations

from collections import deque
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class DependencyGraph:
    """Directed graph for tracking capability dependencies.

    Supports topological sorting, cycle detection, and
    querying dependents/dependencies for any node.
    """

    def __init__(self) -> None:
        self._nodes: set[str] = set()
        self._edges: dict[str, set[str]] = {}
        self._reverse_edges: dict[str, set[str]] = {}

    def add_node(self, capability_id: str) -> None:
        """Add a capability node to the graph."""
        self._nodes.add(capability_id)
        if capability_id not in self._edges:
            self._edges[capability_id] = set()
        if capability_id not in self._reverse_edges:
            self._reverse_edges[capability_id] = set()

    def add_edge(self, from_id: str, to_id: str) -> None:
        """Add a directed dependency edge (from_id depends on to_id)."""
        self.add_node(from_id)
        self.add_node(to_id)
        self._edges[from_id].add(to_id)
        self._reverse_edges[to_id].add(from_id)

    def get_dependents(self, capability_id: str) -> list[str]:
        """Get all capabilities that depend on the given capability.

        Returns:
            List of capability IDs that depend on capability_id.
        """
        return list(self._reverse_edges.get(capability_id, set()))

    def get_dependencies(self, capability_id: str) -> list[str]:
        """Get all capabilities that the given capability depends on.

        Returns:
            List of dependency capability IDs.
        """
        return list(self._edges.get(capability_id, set()))

    def topological_sort(self) -> list[str]:
        """Perform topological sort on the dependency graph.

        Returns:
            Topologically sorted list of capability IDs.

        Raises:
            ValueError: If the graph contains a cycle.
        """
        if self.has_cycle():
            raise ValueError("Cannot topologically sort a graph with cycles")

        in_degree: dict[str, int] = dict.fromkeys(self._nodes, 0)
        for node in self._nodes:
            for dep in self._edges.get(node, set()):
                in_degree[dep] = in_degree.get(dep, 0) + 1

        queue: deque[str] = deque()
        for node, degree in in_degree.items():
            if degree == 0:
                queue.append(node)

        result: list[str] = []
        while queue:
            node = queue.popleft()
            result.append(node)
            for dep in self._edges.get(node, set()):
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

        return result

    def has_cycle(self) -> bool:
        """Detect if the graph contains any cycles.

        Returns:
            True if a cycle exists, False otherwise.
        """
        visited: set[str] = set()
        stack: set[str] = set()

        for node in self._nodes:
            if node not in visited:
                if self._dfs_cycle(node, visited, stack):
                    return True
        return False

    def _dfs_cycle(self, node: str, visited: set[str], stack: set[str]) -> bool:
        visited.add(node)
        stack.add(node)

        for neighbor in self._edges.get(node, set()):
            if neighbor not in visited:
                if self._dfs_cycle(neighbor, visited, stack):
                    return True
            elif neighbor in stack:
                return True

        stack.discard(node)
        return False

    def to_dict(self) -> dict[str, Any]:
        """Serialize graph to dictionary."""
        return {
            "nodes": sorted(self._nodes),
            "edges": {k: sorted(v) for k, v in self._edges.items() if v},
        }
