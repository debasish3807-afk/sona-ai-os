"""Comprehensive tests for the Dynamic Capability Fabric."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio

import pytest

from capabilities.cache import CapabilityCache
from capabilities.composer import CapabilityComposer
from capabilities.dependency_graph import DependencyGraph
from capabilities.exceptions import (
    CapabilityConflictError,
    CapabilityNotFoundError,
)
from capabilities.health import HealthMonitor
from capabilities.loader import CapabilityLoader
from capabilities.manager import CapabilityManager
from capabilities.marketplace import Marketplace
from capabilities.optimizer import CapabilityOptimizer
from capabilities.permissions import PermissionValidator
from capabilities.registry import CapabilityRegistry
from capabilities.sandbox import CapabilitySandbox
from capabilities.schemas import Capability, CapabilityCategory, CapabilityState
from capabilities.selector import CapabilitySelector
from capabilities.telemetry import CapabilityTelemetry
from capabilities.versioning import VersionManager


def _make_capability(**kwargs) -> Capability:
    """Helper to create a test capability with defaults."""
    defaults = {
        "name": "test-cap",
        "version": "1.0.0",
        "description": "A test capability",
        "author": "tester",
        "category": CapabilityCategory.TOOL,
        "entrypoint": "test.module:run",
    }
    defaults.update(kwargs)
    return Capability(**defaults)


class TestSchemas:
    """Tests for capability schemas and enums."""

    def test_capability_creation(self) -> None:
        cap = _make_capability(name="my-tool")
        assert cap.name == "my-tool"
        assert cap.version == "1.0.0"
        assert cap.is_active is True
        assert cap.capability_id  # non-empty uuid

    def test_capability_to_dict(self) -> None:
        cap = _make_capability(name="dict-test", tags=["ai", "search"])
        d = cap.to_dict()
        assert d["name"] == "dict-test"
        assert d["tags"] == ["ai", "search"]
        assert d["category"] == "tool"
        assert "capability_id" in d

    def test_capability_category_values(self) -> None:
        assert CapabilityCategory.TOOL.value == "tool"
        assert CapabilityCategory.PROVIDER.value == "provider"
        assert CapabilityCategory.WORKFLOW.value == "workflow"

    def test_capability_state_values(self) -> None:
        assert CapabilityState.ACTIVE.value == "active"
        assert CapabilityState.SUSPENDED.value == "suspended"
        assert CapabilityState.REMOVED.value == "removed"


class TestRegistry:
    """Tests for the CapabilityRegistry."""

    def test_register_and_get(self) -> None:
        registry = CapabilityRegistry()
        cap = _make_capability()
        registry.register(cap)
        assert registry.get(cap.capability_id) is cap

    def test_register_duplicate_raises(self) -> None:
        registry = CapabilityRegistry()
        cap = _make_capability()
        registry.register(cap)
        with pytest.raises(CapabilityConflictError):
            registry.register(cap)

    def test_unregister(self) -> None:
        registry = CapabilityRegistry()
        cap = _make_capability()
        registry.register(cap)
        assert registry.unregister(cap.capability_id) is True
        assert registry.get(cap.capability_id) is None

    def test_unregister_missing(self) -> None:
        registry = CapabilityRegistry()
        assert registry.unregister("nonexistent") is False

    def test_filter_by_category(self) -> None:
        registry = CapabilityRegistry()
        cap1 = _make_capability(category=CapabilityCategory.TOOL)
        cap2 = _make_capability(category=CapabilityCategory.PROVIDER)
        registry.register(cap1)
        registry.register(cap2)
        results = registry.filter_by(category=CapabilityCategory.TOOL)
        assert len(results) == 1
        assert results[0].capability_id == cap1.capability_id

    def test_search(self) -> None:
        registry = CapabilityRegistry()
        cap = _make_capability(name="web-search", description="Searches the web")
        registry.register(cap)
        results = registry.search("web")
        assert len(results) == 1
        assert results[0].name == "web-search"

    def test_has_and_count(self) -> None:
        registry = CapabilityRegistry()
        cap = _make_capability()
        registry.register(cap)
        assert registry.has(cap.capability_id) is True
        assert registry.has("nope") is False
        assert registry.count == 1


class TestLoader:
    """Tests for the CapabilityLoader."""

    def test_validate_valid_schema(self) -> None:
        loader = CapabilityLoader()
        cap = _make_capability()
        assert loader._validate(cap) is True

    def test_validate_invalid_schema(self) -> None:
        loader = CapabilityLoader()
        cap = _make_capability(name="", entrypoint="")
        assert loader._validate(cap) is False

    def test_load_not_found(self) -> None:
        loader = CapabilityLoader()
        registry = CapabilityRegistry()
        with pytest.raises(CapabilityNotFoundError):
            asyncio.run(loader.load("nonexistent", registry))


class TestSelector:
    """Tests for the CapabilitySelector."""

    def test_select_returns_best(self) -> None:
        registry = CapabilityRegistry()
        cap1 = _make_capability(name="web-search", description="search the web", confidence=0.9)
        cap2 = _make_capability(name="file-read", description="read files", confidence=0.8)
        registry.register(cap1)
        registry.register(cap2)
        selector = CapabilitySelector()
        result = selector.select("search", "find info on web", registry)
        assert result == cap1.capability_id

    def test_select_empty_registry(self) -> None:
        registry = CapabilityRegistry()
        selector = CapabilitySelector()
        result = selector.select("anything", "any intent", registry)
        assert result is None

    def test_select_with_constraints(self) -> None:
        registry = CapabilityRegistry()
        cap = _make_capability(name="expensive", cost=100.0)
        registry.register(cap)
        selector = CapabilitySelector()
        result = selector.select("task", "do something", registry, constraints={"max_cost": 10.0})
        assert result is None

    def test_select_multiple(self) -> None:
        registry = CapabilityRegistry()
        for i in range(10):
            cap = _make_capability(name=f"cap-{i}", confidence=i / 10.0)
            registry.register(cap)
        selector = CapabilitySelector()
        results = selector.select_multiple("task", "do", registry, max_count=3)
        assert len(results) == 3

    def test_score_keyword_matching(self) -> None:
        selector = CapabilitySelector()
        cap = _make_capability(name="image-generator", tags=["ai", "image"])
        score = selector._score(cap, "generate image", "create picture", None)
        assert score > 0


class TestComposer:
    """Tests for the CapabilityComposer."""

    def test_compose_sequential(self) -> None:
        registry = CapabilityRegistry()
        cap1 = _make_capability(name="step1")
        cap2 = _make_capability(name="step2")
        registry.register(cap1)
        registry.register(cap2)
        composer = CapabilityComposer()
        result = composer.compose_sequential([cap1.capability_id, cap2.capability_id], registry)
        assert result.mode == "sequential"
        assert len(result.capabilities) == 2

    def test_compose_parallel(self) -> None:
        registry = CapabilityRegistry()
        cap1 = _make_capability(name="parallel1")
        cap2 = _make_capability(name="parallel2")
        registry.register(cap1)
        registry.register(cap2)
        composer = CapabilityComposer()
        result = composer.compose_parallel([cap1.capability_id, cap2.capability_id], registry)
        assert result.mode == "parallel"

    def test_compose_conditional(self) -> None:
        registry = CapabilityRegistry()
        cap = _make_capability(name="cond-cap")
        registry.register(cap)
        composer = CapabilityComposer()
        result = composer.compose_conditional([("x > 0", cap.capability_id)], registry)
        assert result.mode == "conditional"
        assert cap.capability_id in result.capabilities

    def test_compose_not_found(self) -> None:
        registry = CapabilityRegistry()
        composer = CapabilityComposer()
        with pytest.raises(CapabilityNotFoundError):
            composer.compose_sequential(["nonexistent"], registry)


class TestOptimizer:
    """Tests for the CapabilityOptimizer."""

    def test_optimize_order_by_latency(self) -> None:
        registry = CapabilityRegistry()
        cap1 = _make_capability(name="slow", latency_ms=500.0)
        cap2 = _make_capability(name="fast", latency_ms=10.0)
        registry.register(cap1)
        registry.register(cap2)
        optimizer = CapabilityOptimizer()
        order = optimizer.optimize_order(
            [cap1.capability_id, cap2.capability_id], registry, metric="latency"
        )
        assert order[0] == cap2.capability_id

    def test_estimate_cost(self) -> None:
        registry = CapabilityRegistry()
        cap1 = _make_capability(name="c1", cost=1.5)
        cap2 = _make_capability(name="c2", cost=2.5)
        registry.register(cap1)
        registry.register(cap2)
        optimizer = CapabilityOptimizer()
        total = optimizer.estimate_cost([cap1.capability_id, cap2.capability_id], registry)
        assert total == pytest.approx(4.0)

    def test_estimate_latency(self) -> None:
        registry = CapabilityRegistry()
        cap1 = _make_capability(name="l1", latency_ms=100.0)
        cap2 = _make_capability(name="l2", latency_ms=200.0)
        registry.register(cap1)
        registry.register(cap2)
        optimizer = CapabilityOptimizer()
        total = optimizer.estimate_latency([cap1.capability_id, cap2.capability_id], registry)
        assert total == pytest.approx(300.0)

    def test_suggest_alternatives(self) -> None:
        registry = CapabilityRegistry()
        cap1 = _make_capability(name="search-a", tags=["search"], category=CapabilityCategory.TOOL)
        cap2 = _make_capability(name="search-b", tags=["search"], category=CapabilityCategory.TOOL)
        registry.register(cap1)
        registry.register(cap2)
        optimizer = CapabilityOptimizer()
        alts = optimizer.suggest_alternatives(cap1.capability_id, registry)
        assert cap2.capability_id in alts


class TestDependencyGraph:
    """Tests for the DependencyGraph."""

    def test_add_node(self) -> None:
        graph = DependencyGraph()
        graph.add_node("a")
        assert "a" in graph.to_dict()["nodes"]

    def test_add_edge(self) -> None:
        graph = DependencyGraph()
        graph.add_edge("a", "b")
        assert "b" in graph.get_dependencies("a")

    def test_get_dependents(self) -> None:
        graph = DependencyGraph()
        graph.add_edge("a", "b")
        assert "a" in graph.get_dependents("b")

    def test_topological_sort(self) -> None:
        graph = DependencyGraph()
        graph.add_edge("a", "b")
        graph.add_edge("b", "c")
        result = graph.topological_sort()
        assert result.index("a") < result.index("b")

    def test_has_cycle_false(self) -> None:
        graph = DependencyGraph()
        graph.add_edge("a", "b")
        graph.add_edge("b", "c")
        assert graph.has_cycle() is False

    def test_has_cycle_true(self) -> None:
        graph = DependencyGraph()
        graph.add_edge("a", "b")
        graph.add_edge("b", "c")
        graph.add_edge("c", "a")
        assert graph.has_cycle() is True


class TestHealth:
    """Tests for the HealthMonitor."""

    def test_check_healthy(self) -> None:
        registry = CapabilityRegistry()
        cap = _make_capability(health_status="healthy")
        registry.register(cap)
        monitor = HealthMonitor()
        status = asyncio.run(monitor.check(cap.capability_id, registry))
        assert status.healthy is True

    def test_check_all(self) -> None:
        registry = CapabilityRegistry()
        cap1 = _make_capability(name="h1")
        cap2 = _make_capability(name="h2")
        registry.register(cap1)
        registry.register(cap2)
        monitor = HealthMonitor()
        results = asyncio.run(monitor.check_all(registry))
        assert len(results) == 2

    def test_history(self) -> None:
        registry = CapabilityRegistry()
        cap = _make_capability()
        registry.register(cap)
        monitor = HealthMonitor()
        asyncio.run(monitor.check(cap.capability_id, registry))
        asyncio.run(monitor.check(cap.capability_id, registry))
        history = monitor.get_history(cap.capability_id)
        assert len(history) == 2


class TestSandbox:
    """Tests for the CapabilitySandbox."""

    def test_validate_path_allowed(self) -> None:
        sandbox = CapabilitySandbox(workspace_root="/tmp/workspace")
        assert sandbox.validate_path("/tmp/workspace/data/file.txt") is True

    def test_validate_path_denied(self) -> None:
        sandbox = CapabilitySandbox(workspace_root="/tmp/workspace")
        assert sandbox.validate_path("/etc/passwd") is False

    def test_validate_network(self) -> None:
        sandbox = CapabilitySandbox(
            workspace_root="/tmp/workspace", allowed_hosts=["api.example.com"]
        )
        assert sandbox.validate_network("api.example.com") is True
        assert sandbox.validate_network("evil.com") is False

    def test_enforce_timeout(self) -> None:
        sandbox = CapabilitySandbox(workspace_root="/tmp/workspace", max_timeout=30)
        assert sandbox.enforce_timeout(10) == 10
        assert sandbox.enforce_timeout(100) == 30

    def test_enforce_memory(self) -> None:
        sandbox = CapabilitySandbox(workspace_root="/tmp/workspace", max_memory_mb=256)
        assert sandbox.enforce_memory(128) == 128
        assert sandbox.enforce_memory(1024) == 256


class TestPermissions:
    """Tests for the PermissionValidator."""

    def test_validate_known_permissions(self) -> None:
        validator = PermissionValidator()
        cap = _make_capability(permissions=["filesystem.read", "network.http"])
        assert validator.validate(cap, ["filesystem.read", "network.http"]) is True

    def test_validate_unknown_permission(self) -> None:
        validator = PermissionValidator()
        cap = _make_capability()
        assert validator.validate(cap, ["unknown.perm"]) is False

    def test_check_grant(self) -> None:
        registry = CapabilityRegistry()
        cap = _make_capability(permissions=["filesystem.read", "network.http"])
        registry.register(cap)
        validator = PermissionValidator()
        assert (
            validator.check_grant(cap.capability_id, ["filesystem.read", "network.http"], registry)
            is True
        )
        assert validator.check_grant(cap.capability_id, ["filesystem.read"], registry) is False


class TestCache:
    """Tests for the CapabilityCache."""

    def test_get_set(self) -> None:
        cache = CapabilityCache()
        cache.set("key1", {"result": "data"})
        assert cache.get("key1") == {"result": "data"}

    def test_get_missing(self) -> None:
        cache = CapabilityCache()
        assert cache.get("nonexistent") is None

    def test_invalidate(self) -> None:
        cache = CapabilityCache()
        cache.set("key1", "value1")
        cache.invalidate("key1")
        assert cache.get("key1") is None

    def test_stats(self) -> None:
        cache = CapabilityCache()
        cache.set("k1", "v1")
        cache.get("k1")  # hit
        cache.get("k2")  # miss
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1


class TestTelemetry:
    """Tests for the CapabilityTelemetry."""

    def test_record_execution(self) -> None:
        telemetry = CapabilityTelemetry()
        telemetry.record_execution(
            "cap1", success=True, duration_ms=50.0, tokens_used=100, cost=0.01
        )
        stats = telemetry.get_stats("cap1")
        assert stats["total_executions"] == 1
        assert stats["success_rate"] == 1.0

    def test_get_stats_empty(self) -> None:
        telemetry = CapabilityTelemetry()
        stats = telemetry.get_stats("nonexistent")
        assert stats["total_executions"] == 0

    def test_get_all_stats(self) -> None:
        telemetry = CapabilityTelemetry()
        telemetry.record_execution("cap1", True, 10.0)
        telemetry.record_execution("cap2", False, 20.0)
        all_stats = telemetry.get_all_stats()
        assert "cap1" in all_stats
        assert "cap2" in all_stats
        assert all_stats["cap2"]["success_rate"] == 0.0


class TestVersioning:
    """Tests for the VersionManager."""

    def test_parse(self) -> None:
        vm = VersionManager()
        assert vm.parse("1.2.3") == (1, 2, 3)
        assert vm.parse("0.10.5") == (0, 10, 5)

    def test_is_compatible(self) -> None:
        vm = VersionManager()
        assert vm.is_compatible("1.0.0", "1.5.2") is True
        assert vm.is_compatible("1.0.0", "2.0.0") is False
        assert vm.is_compatible("0.2.0", "0.2.5") is True
        assert vm.is_compatible("0.2.0", "0.3.0") is False

    def test_compare(self) -> None:
        vm = VersionManager()
        assert vm.compare("1.0.0", "1.0.1") == -1
        assert vm.compare("2.0.0", "1.9.9") == 1
        assert vm.compare("1.0.0", "1.0.0") == 0

    def test_latest(self) -> None:
        vm = VersionManager()
        versions = ["1.0.0", "2.1.0", "1.5.3", "2.0.9"]
        assert vm.latest(versions) == "2.1.0"


class TestMarketplace:
    """Tests for the Marketplace."""

    def test_search(self) -> None:
        mp = Marketplace()
        mp._catalog["cap1"] = {
            "name": "web-scraper",
            "description": "Scrapes web pages",
            "category": "tool",
            "version": "1.0.0",
            "author": "dev",
            "entrypoint": "scraper:run",
        }
        results = mp.search("web")
        assert len(results) == 1

    def test_install(self) -> None:
        mp = Marketplace()
        mp._catalog["cap-install"] = {
            "name": "installer",
            "description": "Test install",
            "category": "tool",
            "version": "1.0.0",
            "author": "dev",
            "entrypoint": "installer:run",
        }
        registry = CapabilityRegistry()
        result = mp.install("cap-install", registry)
        assert result is True
        assert registry.has("cap-install") is True

    def test_list_available(self) -> None:
        mp = Marketplace()
        mp._catalog["a"] = {"name": "a", "description": "aa", "category": "tool"}
        mp._catalog["b"] = {"name": "b", "description": "bb", "category": "tool"}
        available = mp.list_available()
        assert len(available) == 2


class TestManager:
    """Tests for the CapabilityManager."""

    def _make_manager(self) -> CapabilityManager:
        registry = CapabilityRegistry()
        loader = CapabilityLoader()
        health_monitor = HealthMonitor()
        selector = CapabilitySelector()
        return CapabilityManager(registry, loader, health_monitor, selector)

    def test_register_capability(self) -> None:
        manager = self._make_manager()
        cap = _make_capability(name="mgr-cap")
        cap_id = manager.register_capability(cap)
        assert cap_id == cap.capability_id
        assert manager._registry.has(cap_id)

    def test_suspend(self) -> None:
        manager = self._make_manager()
        cap = _make_capability(name="suspend-test")
        manager.register_capability(cap)
        result = asyncio.run(manager.suspend(cap.capability_id))
        assert result is True
        assert cap.is_active is False

    def test_resume(self) -> None:
        manager = self._make_manager()
        cap = _make_capability(name="resume-test")
        manager.register_capability(cap)
        asyncio.run(manager.suspend(cap.capability_id))
        result = asyncio.run(manager.resume(cap.capability_id))
        assert result is True
        assert cap.is_active is True

    def test_remove(self) -> None:
        manager = self._make_manager()
        cap = _make_capability(name="remove-test")
        manager.register_capability(cap)
        result = asyncio.run(manager.remove(cap.capability_id))
        assert result is True
        assert not manager._registry.has(cap.capability_id)

    def test_get_status(self) -> None:
        manager = self._make_manager()
        cap1 = _make_capability(name="status1")
        cap2 = _make_capability(name="status2")
        manager.register_capability(cap1)
        manager.register_capability(cap2)
        status = manager.get_status()
        assert status["total"] == 2
        assert status["active"] == 2
