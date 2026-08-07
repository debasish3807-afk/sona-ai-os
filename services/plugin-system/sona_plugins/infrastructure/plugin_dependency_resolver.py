"""Plugin dependency resolver — resolve graphs, detect cycles, order installation."""

from __future__ import annotations

import structlog

logger = structlog.get_logger()


class CyclicDependencyError(Exception):
    """Raised when a cyclic dependency is detected."""

    def __init__(self, cycle: list[str]) -> None:
        self.cycle = cycle
        super().__init__(f"Cyclic dependency detected: {' -> '.join(cycle)}")


class MissingDependencyError(Exception):
    """Raised when a required dependency is not available."""

    def __init__(self, plugin_id: str, missing: list[str]) -> None:
        self.plugin_id = plugin_id
        self.missing = missing
        super().__init__(f"Plugin '{plugin_id}' has missing dependencies: {', '.join(missing)}")


class PluginDependencyResolver:
    """Resolves plugin dependency graphs and determines installation order.

    Detects:
    - Cyclic dependencies
    - Missing dependencies
    - Correct topological ordering for installation
    """

    def __init__(self) -> None:
        self._dependencies: dict[str, list[str]] = {}
        self._available: set[str] = set()

    def register(self, plugin_id: str, dependencies: list[str]) -> None:
        """Register a plugin with its dependencies."""
        self._dependencies[plugin_id] = list(dependencies)
        self._available.add(plugin_id)

    def unregister(self, plugin_id: str) -> None:
        """Remove a plugin from the resolver."""
        self._dependencies.pop(plugin_id, None)
        self._available.discard(plugin_id)

    def resolve_order(self, plugin_ids: list[str] | None = None) -> list[str]:
        """Resolve the installation order using topological sort.

        Args:
            plugin_ids: Specific plugins to resolve. If None, resolves all.

        Returns:
            List of plugin IDs in dependency-first order.

        Raises:
            CyclicDependencyError: If a cycle is detected.
            MissingDependencyError: If a dependency is not available.
        """
        targets = plugin_ids or list(self._dependencies.keys())

        # Check for missing dependencies
        for pid in targets:
            deps = self._dependencies.get(pid, [])
            missing = [d for d in deps if d not in self._available]
            if missing:
                raise MissingDependencyError(pid, missing)

        # Topological sort with cycle detection
        visited: set[str] = set()
        in_stack: set[str] = set()
        order: list[str] = []

        def _visit(node: str, path: list[str]) -> None:
            if node in in_stack:
                cycle_start = path.index(node)
                raise CyclicDependencyError(path[cycle_start:] + [node])
            if node in visited:
                return

            in_stack.add(node)
            path.append(node)

            for dep in self._dependencies.get(node, []):
                if dep in targets or dep in self._available:
                    _visit(dep, path)

            path.pop()
            in_stack.remove(node)
            visited.add(node)
            order.append(node)

        for pid in targets:
            if pid not in visited:
                _visit(pid, [])

        logger.info("dependency_order_resolved", order=order)
        return order

    def get_dependencies(self, plugin_id: str) -> list[str]:
        """Get direct dependencies for a plugin."""
        return list(self._dependencies.get(plugin_id, []))

    def get_dependents(self, plugin_id: str) -> list[str]:
        """Get plugins that depend on the given plugin."""
        return [pid for pid, deps in self._dependencies.items() if plugin_id in deps]

    def has_dependencies(self, plugin_id: str) -> bool:
        """Check if a plugin has any dependencies."""
        return len(self._dependencies.get(plugin_id, [])) > 0

    def detect_cycles(self) -> list[list[str]]:
        """Detect all cycles in the dependency graph.

        Returns:
            List of cycles found (each cycle is a list of plugin IDs).
        """
        cycles: list[list[str]] = []
        visited: set[str] = set()
        in_stack: set[str] = set()

        def _find_cycle(node: str, path: list[str]) -> None:
            if node in in_stack:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
            if node in visited:
                return

            in_stack.add(node)
            path.append(node)

            for dep in self._dependencies.get(node, []):
                _find_cycle(dep, path)

            path.pop()
            in_stack.remove(node)
            visited.add(node)

        for pid in self._dependencies:
            if pid not in visited:
                _find_cycle(pid, [])

        return cycles
