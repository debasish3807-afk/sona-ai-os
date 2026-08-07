"""Tests for the plugin sandbox."""

import asyncio

import pytest

from sona_plugins.domain.permissions import PluginPermission
from sona_plugins.infrastructure.plugin_permission_manager import PluginPermissionManager
from sona_plugins.infrastructure.plugin_sandbox import (
    PluginSandbox,
    SandboxConfig,
)


@pytest.fixture
def permission_manager() -> PluginPermissionManager:
    pm = PluginPermissionManager()
    pm.register("test-plugin", frozenset({PluginPermission.NETWORK_HTTP}))
    pm.grant("test-plugin", PluginPermission.NETWORK_HTTP)
    return pm


@pytest.fixture
def sandbox(permission_manager: PluginPermissionManager) -> PluginSandbox:
    config = SandboxConfig(
        default_timeout_seconds=5.0,
        default_memory_limit_mb=128.0,
        api_whitelist=["echo", "format", "timer", "metrics", "compute", "execute"],
    )
    return PluginSandbox(permission_manager, config)


class TestSandboxExecution:
    """Tests for basic sandbox execution."""

    @pytest.mark.asyncio
    async def test_execute_simple_action(self, sandbox: PluginSandbox) -> None:
        async def handler() -> str:
            return "hello"

        result = await sandbox.execute("test-plugin", "echo", handler)
        assert result.success is True
        assert result.result == "hello"

    @pytest.mark.asyncio
    async def test_execute_with_args(self, sandbox: PluginSandbox) -> None:
        async def handler(text: str) -> str:
            return text.upper()

        result = await sandbox.execute("test-plugin", "echo", handler, "hi")
        assert result.success is True
        assert result.result == "HI"

    @pytest.mark.asyncio
    async def test_execute_records_duration(self, sandbox: PluginSandbox) -> None:
        async def handler() -> str:
            return "done"

        result = await sandbox.execute("test-plugin", "echo", handler)
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_execute_handler_error(self, sandbox: PluginSandbox) -> None:
        async def handler() -> str:
            raise ValueError("boom")

        result = await sandbox.execute("test-plugin", "echo", handler)
        assert result.success is False
        assert "boom" in (result.error or "")


class TestSandboxTimeout:
    """Tests for timeout enforcement."""

    @pytest.mark.asyncio
    async def test_timeout_exceeded(self, sandbox: PluginSandbox) -> None:
        async def slow_handler() -> str:
            await asyncio.sleep(10)
            return "done"

        result = await sandbox.execute("test-plugin", "echo", slow_handler, timeout_seconds=0.1)
        assert result.success is False
        assert "Timeout" in (result.error or "")

    @pytest.mark.asyncio
    async def test_within_timeout(self, sandbox: PluginSandbox) -> None:
        async def fast_handler() -> str:
            await asyncio.sleep(0.01)
            return "fast"

        result = await sandbox.execute("test-plugin", "echo", fast_handler, timeout_seconds=5.0)
        assert result.success is True
        assert result.result == "fast"


class TestSandboxPermissions:
    """Tests for permission checking."""

    @pytest.mark.asyncio
    async def test_permission_granted_executes(self, sandbox: PluginSandbox) -> None:
        async def handler() -> str:
            return "ok"

        result = await sandbox.execute(
            "test-plugin",
            "echo",
            handler,
            required_permissions=frozenset({PluginPermission.NETWORK_HTTP}),
        )
        assert result.success is True

    @pytest.mark.asyncio
    async def test_permission_denied(self, sandbox: PluginSandbox) -> None:
        async def handler() -> str:
            return "ok"

        result = await sandbox.execute(
            "test-plugin",
            "echo",
            handler,
            required_permissions=frozenset({PluginPermission.DATABASE_WRITE}),
        )
        assert result.success is False
        assert "Permission denied" in (result.error or "")

    @pytest.mark.asyncio
    async def test_multiple_permissions_all_required(self, sandbox: PluginSandbox) -> None:
        async def handler() -> str:
            return "ok"

        result = await sandbox.execute(
            "test-plugin",
            "echo",
            handler,
            required_permissions=frozenset(
                {
                    PluginPermission.NETWORK_HTTP,
                    PluginPermission.DATABASE_READ,
                }
            ),
        )
        assert result.success is False


class TestSandboxAPIWhitelist:
    """Tests for API whitelist enforcement."""

    @pytest.mark.asyncio
    async def test_allowed_api(self, sandbox: PluginSandbox) -> None:
        async def handler() -> str:
            return "ok"

        result = await sandbox.execute("test-plugin", "echo", handler)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_forbidden_api(self, sandbox: PluginSandbox) -> None:
        async def handler() -> str:
            return "ok"

        result = await sandbox.execute("test-plugin", "forbidden_action", handler)
        assert result.success is False
        assert "Forbidden API" in (result.error or "")


class TestSandboxCancellation:
    """Tests for execution cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_running_task(self, sandbox: PluginSandbox) -> None:
        async def slow_handler() -> str:
            await asyncio.sleep(100)
            return "done"

        # Start execution in background
        task = asyncio.create_task(
            sandbox.execute("test-plugin", "echo", slow_handler, timeout_seconds=100)
        )
        await asyncio.sleep(0.05)

        # Cancel
        cancelled = await sandbox.cancel("test-plugin")
        assert cancelled is True

        result = await task
        assert result.success is False

    @pytest.mark.asyncio
    async def test_cancel_nonexistent(self, sandbox: PluginSandbox) -> None:
        result = await sandbox.cancel("nonexistent")
        assert result is False


class TestSandboxMemory:
    """Tests for memory tracking."""

    @pytest.mark.asyncio
    async def test_memory_tracked(self, sandbox: PluginSandbox) -> None:
        async def handler() -> str:
            return "result"

        await sandbox.execute("test-plugin", "echo", handler)
        mem = sandbox.get_memory_usage("test-plugin")
        assert mem >= 0

    @pytest.mark.asyncio
    async def test_is_running_false_after_complete(self, sandbox: PluginSandbox) -> None:
        async def handler() -> str:
            return "done"

        await sandbox.execute("test-plugin", "echo", handler)
        assert sandbox.is_running("test-plugin") is False
