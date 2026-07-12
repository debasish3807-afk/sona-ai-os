"""Tool Executor — runs tools with permission checks and resource management.

Handles:
    - Permission validation before execution
    - Timeout enforcement
    - Output truncation
    - Error handling and logging
    - Execution metrics
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from config.logging import get_logger
from tools.base import ToolResult
from tools.permissions import ToolPermissions
from tools.registry import ToolRegistry

logger = get_logger(__name__)


class ToolExecutionError(Exception):
    """Raised when tool execution fails."""

    def __init__(self, message: str, tool_name: str = "") -> None:
        self.tool_name = tool_name
        super().__init__(message)


class ToolExecutor:
    """Executes tools with permission checks, timeouts, and logging.

    The executor is the single entry point for running any tool.
    It validates permissions, enforces timeouts, truncates output,
    and logs all executions.
    """

    def __init__(self, registry: ToolRegistry, permissions: ToolPermissions) -> None:
        self._registry = registry
        self._permissions = permissions
        self._execution_count: int = 0

    @property
    def registry(self) -> ToolRegistry:
        return self._registry

    @property
    def permissions(self) -> ToolPermissions:
        return self._permissions

    @property
    def execution_count(self) -> int:
        return self._execution_count

    async def run(self, tool_name: str, **params: Any) -> ToolResult:
        """Execute a tool by name with the given parameters.

        Args:
            tool_name: The registered name of the tool.
            **params: Tool-specific parameters.

        Returns:
            ToolResult with output or error.
        """
        tool = self._registry.get(tool_name)
        if tool is None:
            return ToolResult(
                success=False,
                error=f"Tool not found: {tool_name}",
                tool_name=tool_name,
            )

        # Permission check: dangerous tools in safe mode
        if tool.is_dangerous and self._permissions.safe_mode:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' requires confirmation (dangerous operation in safe mode)",
                tool_name=tool_name,
            )

        # Execute with timeout
        timeout = self._permissions.max_timeout_seconds
        start = time.perf_counter()

        try:
            result = await asyncio.wait_for(
                tool.execute(**params),
                timeout=timeout,
            )
        except TimeoutError:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.warning("Tool execution timed out", tool=tool_name, timeout=timeout)
            return ToolResult(
                success=False,
                error=f"Execution timed out after {timeout}s",
                tool_name=tool_name,
                duration_ms=duration_ms,
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error("Tool execution failed", tool=tool_name, error=str(exc))
            return ToolResult(
                success=False,
                error=str(exc),
                tool_name=tool_name,
                duration_ms=duration_ms,
            )

        # Post-processing
        duration_ms = (time.perf_counter() - start) * 1000
        result.duration_ms = duration_ms
        result.tool_name = tool_name

        # Truncate output if needed
        if result.output:
            result.output = self._permissions.truncate_output(result.output)

        self._execution_count += 1
        logger.info(
            "Tool executed",
            tool=tool_name,
            success=result.success,
            duration_ms=round(duration_ms, 2),
        )
        return result

    def list_tools(self) -> list[dict[str, Any]]:
        """List all available tools as schema."""
        return self._registry.to_schema()
