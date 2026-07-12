"""Engine Registry — dynamic registration and lookup of cognitive engines.

Supports register, unregister, replace, health check, version tracking,
priority ordering, and dependency resolution. No hardcoded engine refs.
"""

from __future__ import annotations

from cognitive.engine_protocol import CognitiveEngine, EngineInfo
from cognitive.exceptions import RegistryError
from config.logging import get_logger

logger = get_logger(__name__)


class EngineRegistry:
    """Dynamic registry for cognitive engines.

    Engines register by ID. The kernel looks them up at runtime
    to build the processing pipeline. Supports hot-swap and health.
    """

    def __init__(self) -> None:
        self._engines: dict[str, CognitiveEngine] = {}

    @property
    def engine_count(self) -> int:
        return len(self._engines)

    def register(self, engine: CognitiveEngine) -> None:
        """Register an engine in the registry.

        Args:
            engine: The engine instance to register.

        Raises:
            RegistryError: If engine ID conflicts without replace.
        """
        engine_id = engine.info.engine_id
        if engine_id in self._engines:
            raise RegistryError(
                f"Engine already registered: {engine_id}. Use replace() instead.",
                engine=engine_id,
            )
        self._engines[engine_id] = engine
        logger.info("Engine registered", engine_id=engine_id, version=engine.info.version)

    def unregister(self, engine_id: str) -> bool:
        """Remove an engine from the registry.

        Returns:
            True if engine was found and removed.
        """
        if engine_id in self._engines:
            del self._engines[engine_id]
            logger.info("Engine unregistered", engine_id=engine_id)
            return True
        return False

    def replace(self, engine: CognitiveEngine) -> CognitiveEngine | None:
        """Replace an existing engine with a new version.

        Returns:
            The previous engine instance, or None if new registration.
        """
        engine_id = engine.info.engine_id
        previous = self._engines.get(engine_id)
        self._engines[engine_id] = engine
        logger.info(
            "Engine replaced",
            engine_id=engine_id,
            old_version=previous.info.version if previous else "none",
            new_version=engine.info.version,
        )
        return previous

    def get(self, engine_id: str) -> CognitiveEngine | None:
        """Get an engine by ID."""
        return self._engines.get(engine_id)

    def get_required(self, engine_id: str) -> CognitiveEngine:
        """Get an engine by ID, raising if not found."""
        engine = self._engines.get(engine_id)
        if engine is None:
            raise RegistryError(f"Engine not found: {engine_id}", engine=engine_id)
        return engine

    def list_engines(self) -> list[EngineInfo]:
        """List all registered engines with their info."""
        return [e.info for e in self._engines.values()]

    def list_by_priority(self) -> list[CognitiveEngine]:
        """List engines sorted by priority (lower = higher priority)."""
        return sorted(self._engines.values(), key=lambda e: e.info.priority)

    async def health_check_all(self) -> dict[str, bool]:
        """Run health checks on all registered engines."""
        results: dict[str, bool] = {}
        for engine_id, engine in self._engines.items():
            try:
                results[engine_id] = await engine.health()
            except Exception:
                results[engine_id] = False
        return results

    def get_dependencies(self, engine_id: str) -> list[str]:
        """Get dependency list for an engine."""
        engine = self._engines.get(engine_id)
        if engine is None:
            return []
        return engine.info.dependencies

    def resolve_order(self, engine_ids: list[str]) -> list[str]:
        """Resolve execution order respecting dependencies.

        Simple topological sort for the given engine IDs.
        """
        resolved: list[str] = []
        visited: set[str] = set()

        def visit(eid: str) -> None:
            if eid in visited:
                return
            visited.add(eid)
            for dep in self.get_dependencies(eid):
                if dep in engine_ids:
                    visit(dep)
            resolved.append(eid)

        for eid in engine_ids:
            visit(eid)
        return resolved

    def has_engine(self, engine_id: str) -> bool:
        """Check if an engine is registered."""
        return engine_id in self._engines
