"""Tests for plugin hot-reload functionality."""

import pytest

from sona_plugins.domain.models import PluginManifest, PluginStatus
from sona_plugins.infrastructure.di import create_plugin_runtime
from sona_plugins.infrastructure.plugin_runtime import PluginRuntime


def _make_manifest(plugin_id: str = "test-plugin") -> PluginManifest:
    return PluginManifest(
        plugin_id=plugin_id,
        name="Test Plugin",
        version="1.0.0",
        author="Test",
        description="Test",
        entry_point="sona_plugins.infrastructure.builtin_plugins.EchoPlugin",
        permissions=[],
    )


@pytest.fixture
def runtime() -> PluginRuntime:
    return create_plugin_runtime()


class TestHotReload:
    """Tests for hot-reload without restart."""

    @pytest.mark.asyncio
    async def test_reload_active_plugin(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        await runtime.activate("test-plugin")
        result = await runtime.reload_plugin("test-plugin")
        assert result is True

    @pytest.mark.asyncio
    async def test_reload_preserves_active_status(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        await runtime.activate("test-plugin")
        await runtime.reload_plugin("test-plugin")
        plugin = await runtime.get_plugin("test-plugin")
        assert plugin is not None
        assert plugin.status == PluginStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_reload_nonexistent_returns_false(self, runtime: PluginRuntime) -> None:
        result = await runtime.reload_plugin("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_reload_inactive_plugin(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        result = await runtime.reload_plugin("test-plugin")
        assert result is True

    @pytest.mark.asyncio
    async def test_reload_plugin_still_functional(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        await runtime.activate("test-plugin")
        await runtime.reload_plugin("test-plugin")
        execution = await runtime.execute_plugin("test-plugin", "execute", "after-reload")
        assert execution.success is True
        assert execution.result == "after-reload"

    @pytest.mark.asyncio
    async def test_reload_multiple_times(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        await runtime.activate("test-plugin")
        for _ in range(3):
            result = await runtime.reload_plugin("test-plugin")
            assert result is True

    @pytest.mark.asyncio
    async def test_reload_preserves_other_plugins(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest("a"))
        await runtime.install(_make_manifest("b"))
        await runtime.activate("a")
        await runtime.activate("b")
        await runtime.reload_plugin("a")
        plugin_b = await runtime.get_plugin("b")
        assert plugin_b is not None
        assert plugin_b.status == PluginStatus.ACTIVE
