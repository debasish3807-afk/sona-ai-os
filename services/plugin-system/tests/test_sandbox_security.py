"""Tests for sandbox security — permission enforcement, forbidden APIs."""

import pytest

from sona_plugins.domain.models import PluginManifest
from sona_plugins.domain.permissions import PluginPermission
from sona_plugins.infrastructure.di import create_plugin_runtime
from sona_plugins.infrastructure.plugin_permission_manager import (
    PermissionDeniedError,
    PluginPermissionManager,
)
from sona_plugins.infrastructure.plugin_runtime import PluginRuntime
from sona_plugins.infrastructure.plugin_sandbox import (
    PluginSandbox,
    SandboxConfig,
)


def _make_manifest(plugin_id: str = "test-plugin") -> PluginManifest:
    return PluginManifest(
        plugin_id=plugin_id,
        name="Test Plugin",
        version="1.0.0",
        author="Test",
        description="Test",
        entry_point="sona_plugins.infrastructure.builtin_plugins.EchoPlugin",
        permissions=["network.http"],
    )


@pytest.fixture
def runtime() -> PluginRuntime:
    config = SandboxConfig(
        api_whitelist=["echo", "format", "timer", "metrics", "compute", "execute"],
    )
    return create_plugin_runtime(sandbox_config=config)


class TestSandboxPermissionEnforcement:
    """Tests for permission enforcement in the sandbox."""

    @pytest.mark.asyncio
    async def test_execute_with_granted_permission(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        await runtime.activate("test-plugin")
        runtime.grant_permission("test-plugin", PluginPermission.NETWORK_HTTP)

        execution = await runtime.execute_plugin(
            "test-plugin",
            "execute",
            "test",
            required_permissions=frozenset({PluginPermission.NETWORK_HTTP}),
        )
        assert execution.success is True

    @pytest.mark.asyncio
    async def test_execute_without_permission_denied(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        await runtime.activate("test-plugin")

        execution = await runtime.execute_plugin(
            "test-plugin",
            "execute",
            "test",
            required_permissions=frozenset({PluginPermission.DATABASE_WRITE}),
        )
        assert execution.success is False
        assert "Permission denied" in (execution.error or "")

    @pytest.mark.asyncio
    async def test_permission_check_raises(self) -> None:
        pm = PluginPermissionManager()
        pm.register("p1", frozenset())
        sandbox = PluginSandbox(pm)
        with pytest.raises(PermissionDeniedError):
            sandbox.check_permission("p1", PluginPermission.FILESYSTEM_WRITE)

    @pytest.mark.asyncio
    async def test_multiple_permissions_all_must_be_granted(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        await runtime.activate("test-plugin")
        runtime.grant_permission("test-plugin", PluginPermission.NETWORK_HTTP)
        # Only granted NETWORK_HTTP, but also requires DATABASE_READ

        execution = await runtime.execute_plugin(
            "test-plugin",
            "execute",
            "test",
            required_permissions=frozenset(
                {
                    PluginPermission.NETWORK_HTTP,
                    PluginPermission.DATABASE_READ,
                }
            ),
        )
        assert execution.success is False

    @pytest.mark.asyncio
    async def test_no_permissions_required_always_succeeds(self, runtime: PluginRuntime) -> None:
        await runtime.install(_make_manifest())
        await runtime.activate("test-plugin")

        execution = await runtime.execute_plugin("test-plugin", "execute", "test")
        assert execution.success is True


class TestSandboxForbiddenAPI:
    """Tests for API whitelist enforcement."""

    @pytest.mark.asyncio
    async def test_forbidden_api_blocked(self) -> None:
        pm = PluginPermissionManager()
        config = SandboxConfig(api_whitelist=["allowed_only"])
        sandbox = PluginSandbox(pm, config)

        async def handler() -> str:
            return "ok"

        result = await sandbox.execute("p1", "forbidden_action", handler)
        assert result.success is False
        assert "Forbidden API" in (result.error or "")

    @pytest.mark.asyncio
    async def test_allowed_api_passes(self) -> None:
        pm = PluginPermissionManager()
        config = SandboxConfig(api_whitelist=["my_action"])
        sandbox = PluginSandbox(pm, config)

        async def handler() -> str:
            return "ok"

        result = await sandbox.execute("p1", "my_action", handler)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_empty_whitelist_blocks_all(self) -> None:
        pm = PluginPermissionManager()
        config = SandboxConfig(api_whitelist=[])
        sandbox = PluginSandbox(pm, config)

        async def handler() -> str:
            return "ok"

        result = await sandbox.execute("p1", "any_action", handler)
        assert result.success is False


class TestSandboxResourceLimits:
    """Tests for resource limit enforcement."""

    @pytest.mark.asyncio
    async def test_timeout_enforced(self) -> None:
        import asyncio

        pm = PluginPermissionManager()
        config = SandboxConfig(
            default_timeout_seconds=0.1,
            api_whitelist=["slow"],
        )
        sandbox = PluginSandbox(pm, config)

        async def slow_handler() -> str:
            await asyncio.sleep(10)
            return "done"

        result = await sandbox.execute("p1", "slow", slow_handler)
        assert result.success is False
        assert "Timeout" in (result.error or "")

    @pytest.mark.asyncio
    async def test_memory_limit_enforced(self) -> None:
        pm = PluginPermissionManager()
        config = SandboxConfig(
            default_memory_limit_mb=0.001,  # Very low limit
            api_whitelist=["big_data"],
        )
        sandbox = PluginSandbox(pm, config)

        async def handler() -> str:
            return "x" * 10000  # Large result

        result = await sandbox.execute("p1", "big_data", handler)
        assert result.success is False
        assert "Memory limit" in (result.error or "")
