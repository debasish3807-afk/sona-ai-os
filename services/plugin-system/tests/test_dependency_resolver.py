"""Tests for the plugin dependency resolver."""

import pytest

from sona_plugins.infrastructure.plugin_dependency_resolver import (
    CyclicDependencyError,
    MissingDependencyError,
    PluginDependencyResolver,
)


@pytest.fixture
def resolver() -> PluginDependencyResolver:
    return PluginDependencyResolver()


class TestDependencyResolverBasic:
    """Tests for basic dependency resolution."""

    def test_resolve_no_dependencies(self, resolver: PluginDependencyResolver) -> None:
        resolver.register("plugin-a", [])
        order = resolver.resolve_order()
        assert "plugin-a" in order

    def test_resolve_single_dependency(self, resolver: PluginDependencyResolver) -> None:
        resolver.register("plugin-a", [])
        resolver.register("plugin-b", ["plugin-a"])
        order = resolver.resolve_order()
        assert order.index("plugin-a") < order.index("plugin-b")

    def test_resolve_chain(self, resolver: PluginDependencyResolver) -> None:
        resolver.register("plugin-a", [])
        resolver.register("plugin-b", ["plugin-a"])
        resolver.register("plugin-c", ["plugin-b"])
        order = resolver.resolve_order()
        assert order.index("plugin-a") < order.index("plugin-b")
        assert order.index("plugin-b") < order.index("plugin-c")

    def test_resolve_diamond(self, resolver: PluginDependencyResolver) -> None:
        resolver.register("base", [])
        resolver.register("left", ["base"])
        resolver.register("right", ["base"])
        resolver.register("top", ["left", "right"])
        order = resolver.resolve_order()
        assert order.index("base") < order.index("left")
        assert order.index("base") < order.index("right")
        assert order.index("left") < order.index("top")
        assert order.index("right") < order.index("top")

    def test_resolve_specific_plugins(self, resolver: PluginDependencyResolver) -> None:
        resolver.register("a", [])
        resolver.register("b", ["a"])
        resolver.register("c", [])
        order = resolver.resolve_order(["b"])
        assert "a" in order
        assert "b" in order


class TestDependencyResolverCycles:
    """Tests for cycle detection."""

    def test_simple_cycle(self, resolver: PluginDependencyResolver) -> None:
        resolver.register("a", ["b"])
        resolver.register("b", ["a"])
        with pytest.raises(CyclicDependencyError):
            resolver.resolve_order()

    def test_three_node_cycle(self, resolver: PluginDependencyResolver) -> None:
        resolver.register("a", ["b"])
        resolver.register("b", ["c"])
        resolver.register("c", ["a"])
        with pytest.raises(CyclicDependencyError):
            resolver.resolve_order()

    def test_detect_cycles_returns_list(self, resolver: PluginDependencyResolver) -> None:
        resolver.register("a", ["b"])
        resolver.register("b", ["a"])
        cycles = resolver.detect_cycles()
        assert len(cycles) > 0

    def test_no_cycles(self, resolver: PluginDependencyResolver) -> None:
        resolver.register("a", [])
        resolver.register("b", ["a"])
        cycles = resolver.detect_cycles()
        assert cycles == []


class TestDependencyResolverMissing:
    """Tests for missing dependency detection."""

    def test_missing_dependency_raises(self, resolver: PluginDependencyResolver) -> None:
        resolver.register("plugin-a", ["nonexistent"])
        with pytest.raises(MissingDependencyError):
            resolver.resolve_order()

    def test_missing_dependency_error_fields(self, resolver: PluginDependencyResolver) -> None:
        resolver.register("plugin-a", ["missing-dep"])
        with pytest.raises(MissingDependencyError) as exc_info:
            resolver.resolve_order()
        assert exc_info.value.plugin_id == "plugin-a"
        assert "missing-dep" in exc_info.value.missing


class TestDependencyResolverHelpers:
    """Tests for helper methods."""

    def test_get_dependencies(self, resolver: PluginDependencyResolver) -> None:
        resolver.register("a", ["b", "c"])
        assert resolver.get_dependencies("a") == ["b", "c"]

    def test_get_dependencies_empty(self, resolver: PluginDependencyResolver) -> None:
        resolver.register("a", [])
        assert resolver.get_dependencies("a") == []

    def test_get_dependents(self, resolver: PluginDependencyResolver) -> None:
        resolver.register("a", [])
        resolver.register("b", ["a"])
        resolver.register("c", ["a"])
        dependents = resolver.get_dependents("a")
        assert "b" in dependents
        assert "c" in dependents

    def test_has_dependencies(self, resolver: PluginDependencyResolver) -> None:
        resolver.register("a", ["b"])
        resolver.register("b", [])
        assert resolver.has_dependencies("a") is True
        assert resolver.has_dependencies("b") is False

    def test_unregister(self, resolver: PluginDependencyResolver) -> None:
        resolver.register("a", [])
        resolver.unregister("a")
        assert resolver.get_dependencies("a") == []
