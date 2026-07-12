"""Dependency Resolver — resolves capability dependencies and detects conflicts."""

from __future__ import annotations

from capabilities.exceptions import DependencyError
from capabilities.registry import CapabilityRegistry
from config.logging import get_logger

logger = get_logger(__name__)


class DependencyResolver:
    """Resolves capability dependency graphs and detects conflicts.

    Provides ordered dependency resolution and cycle detection
    for capability activation and composition.
    """

    def resolve(self, capability_id: str, registry: CapabilityRegistry) -> list[str]:
        """Resolve all dependencies for a capability in topological order.

        Args:
            capability_id: The capability whose dependencies to resolve.
            registry: The capability registry.

        Returns:
            Ordered list of dependency capability IDs (deepest first).

        Raises:
            DependencyError: If a circular dependency is detected.
        """
        visited: set[str] = set()
        stack: set[str] = set()
        order: list[str] = []

        self._resolve_recursive(capability_id, registry, visited, stack, order)
        return order

    def _resolve_recursive(
        self,
        capability_id: str,
        registry: CapabilityRegistry,
        visited: set[str],
        stack: set[str],
        order: list[str],
    ) -> None:
        if capability_id in stack:
            raise DependencyError(f"Circular dependency detected involving '{capability_id}'")
        if capability_id in visited:
            return

        stack.add(capability_id)
        schema = registry.get(capability_id)
        if schema is not None:
            for dep_id in schema.dependencies:
                self._resolve_recursive(dep_id, registry, visited, stack, order)

        stack.discard(capability_id)
        visited.add(capability_id)
        order.append(capability_id)

    def detect_conflicts(self, capability_id: str, registry: CapabilityRegistry) -> list[str]:
        """Detect conflicting capabilities based on category and name overlap.

        Returns:
            List of capability IDs that conflict with the given capability.
        """
        schema = registry.get(capability_id)
        if schema is None:
            return []

        conflicts: list[str] = []
        for other in registry.list_all():
            if other.capability_id == capability_id:
                continue
            if (
                other.category == schema.category
                and other.name == schema.name
                and other.capability_id != capability_id
            ):
                conflicts.append(other.capability_id)
        return conflicts

    def check_compatibility(
        self, cap_a_id: str, cap_b_id: str, registry: CapabilityRegistry
    ) -> bool:
        """Check if two capabilities are compatible (no circular deps between them).

        Returns:
            True if compatible, False if they create a cycle.
        """
        visited: set[str] = set()
        stack: set[str] = set()
        return not self._detect_cycles(cap_a_id, visited, stack, registry)

    def _detect_cycles(
        self,
        capability_id: str,
        visited: set[str],
        stack: set[str],
        registry: CapabilityRegistry,
    ) -> bool:
        """Detect if following dependencies from capability_id leads to a cycle.

        Returns:
            True if a cycle is detected, False otherwise.
        """
        if capability_id in stack:
            return True
        if capability_id in visited:
            return False

        stack.add(capability_id)
        schema = registry.get(capability_id)
        if schema is not None:
            for dep_id in schema.dependencies:
                if self._detect_cycles(dep_id, visited, stack, registry):
                    return True

        stack.discard(capability_id)
        visited.add(capability_id)
        return False
