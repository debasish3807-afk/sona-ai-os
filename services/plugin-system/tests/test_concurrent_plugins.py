"""Tests for concurrent plugin execution."""

import asyncio

import pytest

from sona_plugins.domain.models import PluginManifest
from sona_plugins.infrastructure.di import create_plugin_runtime
from sona_plugins.infrastructure.plugin_runtime import PluginRuntime
from sona_plugins.infrastructure.plugin_sandbox import SandboxConfig


def _make_manifest(plugin_id: str) -> PluginManifest:
    return PluginManifest(
        plugin_id=plugin_id,
        name=f"Plugin {plugin_id}",
        version="1.0.0",
        author="Test",
        description="Test",
        entry_point="sona_plugins.infrastructure.builtin_plugins.EchoPlugin",
        permissions=[],
    )


@pytest.fixture
async def runtime() -> PluginRuntime:
    config = SandboxConfig(
        api_whitelist=["echo", "execute", "format", "timer", "metrics", "compute"],
    )
    rt = create_plugin_runtime(sandbox_config=config)
    for i in range(5):
        await rt.install(_make_manifest(f"plugin-{i}"))
        await rt.activate(f"plugin-{i}")
    return rt


class TestConcurrentExecution:
    """Tests for parallel plugin execution."""

    @pytest.mark.asyncio
    async def test_parallel_executions(self, runtime: PluginRuntime) -> None:
        tasks = [runtime.execute_plugin(f"plugin-{i}", "execute", f"msg-{i}") for i in range(5)]
        results = await asyncio.gather(*tasks)
        for i, result in enumerate(results):
            assert result.success is True
            assert result.result == f"msg-{i}"

    @pytest.mark.asyncio
    async def test_parallel_different_plugins(self, runtime: PluginRuntime) -> None:
        tasks = [
            runtime.execute_plugin("plugin-0", "execute", "a"),
            runtime.execute_plugin("plugin-1", "execute", "b"),
            runtime.execute_plugin("plugin-2", "execute", "c"),
        ]
        results = await asyncio.gather(*tasks)
        assert all(r.success for r in results)
        assert results[0].result == "a"
        assert results[1].result == "b"
        assert results[2].result == "c"

    @pytest.mark.asyncio
    async def test_same_plugin_sequential(self, runtime: PluginRuntime) -> None:
        for i in range(10):
            result = await runtime.execute_plugin("plugin-0", "execute", f"msg-{i}")
            assert result.success is True
            assert result.result == f"msg-{i}"

    @pytest.mark.asyncio
    async def test_parallel_install_and_activate(self) -> None:
        rt = create_plugin_runtime()
        manifests = [_make_manifest(f"p-{i}") for i in range(10)]
        install_tasks = [rt.install(m) for m in manifests]
        await asyncio.gather(*install_tasks)

        activate_tasks = [rt.activate(f"p-{i}") for i in range(10)]
        results = await asyncio.gather(*activate_tasks)
        assert all(results)

    @pytest.mark.asyncio
    async def test_metrics_during_concurrent_execution(self, runtime: PluginRuntime) -> None:
        tasks = [runtime.execute_plugin(f"plugin-{i}", "execute", "test") for i in range(5)]
        await asyncio.gather(*tasks)
        assert runtime.metrics.get_counter("plugin_execution_total") >= 5

    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, runtime: PluginRuntime) -> None:
        tasks = [runtime.check_health(f"plugin-{i}") for i in range(5)]
        results = await asyncio.gather(*tasks)
        assert all(results)

    @pytest.mark.asyncio
    async def test_mixed_operations(self, runtime: PluginRuntime) -> None:
        """Test mix of execute, health check, and list operations concurrently."""
        tasks = [
            runtime.execute_plugin("plugin-0", "execute", "a"),
            runtime.check_health("plugin-1"),
            runtime.list_plugins(),
            runtime.execute_plugin("plugin-2", "execute", "b"),
            runtime.check_health("plugin-3"),
        ]
        results = await asyncio.gather(*tasks)
        assert results[0].success is True  # execute
        assert results[1] is True  # health_check
        assert len(results[2]) == 5  # list_plugins
        assert results[3].success is True  # execute
        assert results[4] is True  # health_check
