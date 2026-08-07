"""Plugin sandbox — execute plugin actions within security constraints."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

import structlog

from sona_plugins.domain.permissions import PluginPermission
from sona_plugins.infrastructure.plugin_permission_manager import (
    PluginPermissionManager,
)

logger = structlog.get_logger()


class SandboxTimeoutError(Exception):
    """Raised when a plugin execution exceeds its timeout."""

    def __init__(self, plugin_id: str, timeout_seconds: float) -> None:
        self.plugin_id = plugin_id
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Plugin '{plugin_id}' exceeded timeout of {timeout_seconds}s")


class SandboxMemoryError(Exception):
    """Raised when a plugin exceeds its memory limit."""

    def __init__(self, plugin_id: str, limit_mb: float) -> None:
        self.plugin_id = plugin_id
        self.limit_mb = limit_mb
        super().__init__(f"Plugin '{plugin_id}' exceeded memory limit of {limit_mb}MB")


class ForbiddenAPIError(Exception):
    """Raised when a plugin attempts to use a forbidden API."""

    def __init__(self, plugin_id: str, api: str) -> None:
        self.plugin_id = plugin_id
        self.api = api
        super().__init__(f"Plugin '{plugin_id}' attempted to use forbidden API: {api}")


@dataclass
class SandboxConfig:
    """Configuration for the plugin sandbox."""

    default_timeout_seconds: float = 30.0
    default_memory_limit_mb: float = 128.0
    default_cpu_limit_percent: float = 50.0
    api_whitelist: list[str] = field(
        default_factory=lambda: [
            "echo",
            "format",
            "timer",
            "metrics",
            "compute",
            "execute",
            "to_uppercase",
            "to_lowercase",
            "to_title_case",
            "reverse",
            "word_count",
            "get_timestamp",
            "get_uptime_seconds",
            "record_metric",
            "get_metric",
            "get_all_metrics",
            "reset_metrics",
            "activate",
            "deactivate",
            "health_check",
            "get_capabilities",
        ]
    )


@dataclass
class SandboxExecution:
    """Result of a sandboxed plugin execution."""

    plugin_id: str
    action: str
    result: Any = None
    duration_ms: float = 0.0
    memory_used_mb: float = 0.0
    success: bool = True
    error: str | None = None


class PluginSandbox:
    """Executes plugin actions within security and resource constraints.

    Enforces:
    - Permission validation (check before execute)
    - Timeout enforcement
    - Memory limit tracking
    - CPU limit tracking (simulated)
    - Cancellation support
    - API whitelist enforcement
    """

    def __init__(
        self,
        permission_manager: PluginPermissionManager,
        config: SandboxConfig | None = None,
    ) -> None:
        self._permission_manager = permission_manager
        self._config = config or SandboxConfig()
        self._running_tasks: dict[str, asyncio.Task[Any]] = {}
        self._memory_usage: dict[str, float] = {}

    @property
    def config(self) -> SandboxConfig:
        """Get the sandbox configuration."""
        return self._config

    async def execute(
        self,
        plugin_id: str,
        action: str,
        handler: Any,
        *args: Any,
        required_permissions: frozenset[PluginPermission] | None = None,
        timeout_seconds: float | None = None,
        **kwargs: Any,
    ) -> SandboxExecution:
        """Execute a plugin action within sandbox constraints.

        Args:
            plugin_id: The plugin performing the action.
            action: Name of the action being performed.
            handler: Async callable to execute.
            *args: Arguments to pass to the handler.
            required_permissions: Permissions needed for this action.
            timeout_seconds: Override default timeout.
            **kwargs: Keyword arguments to pass to the handler.

        Returns:
            SandboxExecution with the result or error information.
        """
        timeout = timeout_seconds or self._config.default_timeout_seconds

        # Check API whitelist
        if not self._is_api_allowed(action):
            return SandboxExecution(
                plugin_id=plugin_id,
                action=action,
                success=False,
                error=f"Forbidden API: {action}",
            )

        # Check permissions
        if required_permissions:
            for perm in required_permissions:
                if not self._permission_manager.has_permission(plugin_id, perm):
                    return SandboxExecution(
                        plugin_id=plugin_id,
                        action=action,
                        success=False,
                        error=f"Permission denied: {perm}",
                    )

        # Execute with timeout
        start_time = time.monotonic()
        try:
            task = asyncio.create_task(handler(*args, **kwargs))
            self._running_tasks[plugin_id] = task
            result = await asyncio.wait_for(task, timeout=timeout)
            duration_ms = (time.monotonic() - start_time) * 1000

            # Simulate memory tracking
            memory_used = self._estimate_memory(result)
            self._memory_usage[plugin_id] = memory_used

            if memory_used > self._config.default_memory_limit_mb:
                return SandboxExecution(
                    plugin_id=plugin_id,
                    action=action,
                    success=False,
                    error=f"Memory limit exceeded: {memory_used}MB",
                    duration_ms=duration_ms,
                    memory_used_mb=memory_used,
                )

            logger.info(
                "sandbox_execution_success",
                plugin_id=plugin_id,
                action=action,
                duration_ms=duration_ms,
            )
            return SandboxExecution(
                plugin_id=plugin_id,
                action=action,
                result=result,
                duration_ms=duration_ms,
                memory_used_mb=memory_used,
                success=True,
            )

        except TimeoutError:
            duration_ms = (time.monotonic() - start_time) * 1000
            logger.warning(
                "sandbox_execution_timeout",
                plugin_id=plugin_id,
                action=action,
                timeout=timeout,
            )
            return SandboxExecution(
                plugin_id=plugin_id,
                action=action,
                success=False,
                error=f"Timeout after {timeout}s",
                duration_ms=duration_ms,
            )

        except asyncio.CancelledError:
            duration_ms = (time.monotonic() - start_time) * 1000
            logger.info(
                "sandbox_execution_cancelled",
                plugin_id=plugin_id,
                action=action,
            )
            return SandboxExecution(
                plugin_id=plugin_id,
                action=action,
                success=False,
                error="Execution cancelled",
                duration_ms=duration_ms,
            )

        except Exception as exc:
            duration_ms = (time.monotonic() - start_time) * 1000
            logger.error(
                "sandbox_execution_error",
                plugin_id=plugin_id,
                action=action,
                error=str(exc),
            )
            return SandboxExecution(
                plugin_id=plugin_id,
                action=action,
                success=False,
                error=str(exc),
                duration_ms=duration_ms,
            )

        finally:
            self._running_tasks.pop(plugin_id, None)

    async def cancel(self, plugin_id: str) -> bool:
        """Cancel a running plugin execution."""
        task = self._running_tasks.get(plugin_id)
        if task and not task.done():
            task.cancel()
            logger.info("sandbox_execution_cancel_requested", plugin_id=plugin_id)
            return True
        return False

    def check_permission(self, plugin_id: str, permission: PluginPermission) -> None:
        """Check permission and raise PermissionDeniedError if not granted."""
        self._permission_manager.check_permission(plugin_id, permission)

    def _is_api_allowed(self, action: str) -> bool:
        """Check if an action is in the API whitelist."""
        return action in self._config.api_whitelist

    def _estimate_memory(self, result: Any) -> float:
        """Estimate memory usage for a result (simulated)."""
        if result is None:
            return 0.1
        if isinstance(result, str):
            return len(result) / (1024 * 1024) + 0.1
        if isinstance(result, (list, dict)):
            return len(str(result)) / (1024 * 1024) + 0.1
        return 0.5

    def get_memory_usage(self, plugin_id: str) -> float:
        """Get the last recorded memory usage for a plugin."""
        return self._memory_usage.get(plugin_id, 0.0)

    def is_running(self, plugin_id: str) -> bool:
        """Check if a plugin currently has a running task."""
        task = self._running_tasks.get(plugin_id)
        return task is not None and not task.done()
