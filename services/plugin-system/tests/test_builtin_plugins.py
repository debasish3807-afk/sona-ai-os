"""Tests for built-in plugins."""

import pytest

from sona_plugins.domain.capability import PluginCapabilityType
from sona_plugins.infrastructure.builtin_plugins import (
    BUILTIN_MANIFESTS,
    BUILTIN_PLUGINS,
    EchoPlugin,
    FormatterPlugin,
    MetricsPlugin,
    TimerPlugin,
)


class TestEchoPlugin:
    """Tests for EchoPlugin."""

    @pytest.mark.asyncio
    async def test_activate(self) -> None:
        plugin = EchoPlugin()
        await plugin.activate()
        assert await plugin.health_check() is True

    @pytest.mark.asyncio
    async def test_deactivate(self) -> None:
        plugin = EchoPlugin()
        await plugin.activate()
        await plugin.deactivate()
        assert await plugin.health_check() is False

    @pytest.mark.asyncio
    async def test_execute_echoes(self) -> None:
        plugin = EchoPlugin()
        result = await plugin.execute("hello world")
        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_execute_empty(self) -> None:
        plugin = EchoPlugin()
        result = await plugin.execute("")
        assert result == ""

    @pytest.mark.asyncio
    async def test_invocation_count(self) -> None:
        plugin = EchoPlugin()
        await plugin.execute("a")
        await plugin.execute("b")
        assert plugin.invocations == 2

    @pytest.mark.asyncio
    async def test_get_capabilities(self) -> None:
        plugin = EchoPlugin()
        caps = await plugin.get_capabilities()
        assert "echo" in caps

    def test_manifest(self) -> None:
        assert EchoPlugin.MANIFEST.plugin_id == "builtin-echo"
        assert EchoPlugin.MANIFEST.version == "1.0.0"

    def test_capabilities_type(self) -> None:
        assert EchoPlugin.CAPABILITIES[0].capability_type == PluginCapabilityType.TOOL


class TestTimerPlugin:
    """Tests for TimerPlugin."""

    @pytest.mark.asyncio
    async def test_activate(self) -> None:
        plugin = TimerPlugin()
        await plugin.activate()
        assert await plugin.health_check() is True

    @pytest.mark.asyncio
    async def test_deactivate(self) -> None:
        plugin = TimerPlugin()
        await plugin.activate()
        await plugin.deactivate()
        assert await plugin.health_check() is False

    @pytest.mark.asyncio
    async def test_get_timestamp(self) -> None:
        plugin = TimerPlugin()
        ts = await plugin.get_timestamp()
        assert isinstance(ts, str)
        assert "T" in ts  # ISO format

    @pytest.mark.asyncio
    async def test_get_uptime_inactive(self) -> None:
        plugin = TimerPlugin()
        uptime = await plugin.get_uptime_seconds()
        assert uptime == 0.0

    @pytest.mark.asyncio
    async def test_get_uptime_active(self) -> None:
        plugin = TimerPlugin()
        await plugin.activate()
        uptime = await plugin.get_uptime_seconds()
        assert uptime >= 0.0

    @pytest.mark.asyncio
    async def test_get_capabilities(self) -> None:
        plugin = TimerPlugin()
        caps = await plugin.get_capabilities()
        assert "timer" in caps

    def test_manifest(self) -> None:
        assert TimerPlugin.MANIFEST.plugin_id == "builtin-timer"


class TestMetricsPlugin:
    """Tests for MetricsPlugin."""

    @pytest.mark.asyncio
    async def test_activate(self) -> None:
        plugin = MetricsPlugin()
        await plugin.activate()
        assert await plugin.health_check() is True

    @pytest.mark.asyncio
    async def test_record_and_get_metric(self) -> None:
        plugin = MetricsPlugin()
        await plugin.record_metric("requests", 42.0)
        result = await plugin.get_metric("requests")
        assert result == 42.0

    @pytest.mark.asyncio
    async def test_get_nonexistent_metric(self) -> None:
        plugin = MetricsPlugin()
        result = await plugin.get_metric("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_metrics(self) -> None:
        plugin = MetricsPlugin()
        await plugin.record_metric("a", 1.0)
        await plugin.record_metric("b", 2.0)
        all_m = await plugin.get_all_metrics()
        assert all_m == {"a": 1.0, "b": 2.0}

    @pytest.mark.asyncio
    async def test_reset_metrics(self) -> None:
        plugin = MetricsPlugin()
        await plugin.record_metric("a", 1.0)
        await plugin.reset_metrics()
        all_m = await plugin.get_all_metrics()
        assert all_m == {}

    @pytest.mark.asyncio
    async def test_get_capabilities(self) -> None:
        plugin = MetricsPlugin()
        caps = await plugin.get_capabilities()
        assert "metrics" in caps

    def test_manifest(self) -> None:
        assert MetricsPlugin.MANIFEST.plugin_id == "builtin-metrics"

    def test_capabilities_type(self) -> None:
        assert MetricsPlugin.CAPABILITIES[0].capability_type == PluginCapabilityType.MIDDLEWARE


class TestFormatterPlugin:
    """Tests for FormatterPlugin."""

    @pytest.mark.asyncio
    async def test_activate(self) -> None:
        plugin = FormatterPlugin()
        await plugin.activate()
        assert await plugin.health_check() is True

    @pytest.mark.asyncio
    async def test_to_uppercase(self) -> None:
        plugin = FormatterPlugin()
        result = await plugin.to_uppercase("hello world")
        assert result == "HELLO WORLD"

    @pytest.mark.asyncio
    async def test_to_lowercase(self) -> None:
        plugin = FormatterPlugin()
        result = await plugin.to_lowercase("HELLO WORLD")
        assert result == "hello world"

    @pytest.mark.asyncio
    async def test_to_title_case(self) -> None:
        plugin = FormatterPlugin()
        result = await plugin.to_title_case("hello world")
        assert result == "Hello World"

    @pytest.mark.asyncio
    async def test_reverse(self) -> None:
        plugin = FormatterPlugin()
        result = await plugin.reverse("hello")
        assert result == "olleh"

    @pytest.mark.asyncio
    async def test_word_count(self) -> None:
        plugin = FormatterPlugin()
        result = await plugin.word_count("hello world foo")
        assert result == 3

    @pytest.mark.asyncio
    async def test_word_count_empty(self) -> None:
        plugin = FormatterPlugin()
        result = await plugin.word_count("")
        assert result == 0

    @pytest.mark.asyncio
    async def test_get_capabilities(self) -> None:
        plugin = FormatterPlugin()
        caps = await plugin.get_capabilities()
        assert "format" in caps

    def test_manifest(self) -> None:
        assert FormatterPlugin.MANIFEST.plugin_id == "builtin-formatter"


class TestBuiltinRegistries:
    """Tests for built-in plugin registries."""

    def test_builtin_plugins_list(self) -> None:
        assert len(BUILTIN_PLUGINS) == 4

    def test_builtin_manifests_list(self) -> None:
        assert len(BUILTIN_MANIFESTS) == 4

    def test_all_manifests_have_unique_ids(self) -> None:
        ids = [m.plugin_id for m in BUILTIN_MANIFESTS]
        assert len(set(ids)) == len(ids)

    def test_all_manifests_are_valid(self) -> None:
        for manifest in BUILTIN_MANIFESTS:
            assert manifest.plugin_id
            assert manifest.name
            assert manifest.version
            assert manifest.entry_point
