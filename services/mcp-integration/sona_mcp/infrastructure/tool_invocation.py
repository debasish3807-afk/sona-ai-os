"""Tool invocation engine for MCP Integration.

Executes tool calls with permission validation, input validation,
timeout handling, result capture, and metrics recording.
"""

import asyncio
import time
from typing import Any

import structlog

from sona_mcp.domain.events import ToolFailedEvent, ToolInvokedEvent
from sona_mcp.domain.models import MCPTool, ToolCallResult
from sona_mcp.domain.security import UserPermissions
from sona_mcp.infrastructure.metrics import MCPMetrics
from sona_mcp.infrastructure.security_manager import SecurityManager
from sona_mcp.infrastructure.tool_registry import ToolRegistry

logger = structlog.get_logger()


class ToolInvocationEngine:
    """Executes MCP tool calls with full validation and monitoring.

    Performs permission checks, input validation, timeout handling,
    and records metrics for each invocation.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        security_manager: SecurityManager,
        metrics: MCPMetrics,
        default_timeout: float = 30.0,
    ) -> None:
        """Initialize the tool invocation engine.

        Args:
            registry: The tool registry for looking up tools.
            security_manager: The security manager for permission checks.
            metrics: The metrics collector for recording stats.
            default_timeout: Default timeout for tool calls in seconds.
        """
        self._registry = registry
        self._security_manager = security_manager
        self._metrics = metrics
        self._default_timeout = default_timeout
        self._events: list[ToolInvokedEvent | ToolFailedEvent] = []
        self._tool_handlers: dict[str, Any] = {}

    @property
    def events(self) -> list[ToolInvokedEvent | ToolFailedEvent]:
        """Return collected domain events and clear the buffer."""
        events = list(self._events)
        self._events.clear()
        return events

    def register_handler(self, tool_name: str, handler: Any) -> None:
        """Register a callable handler for a tool.

        Args:
            tool_name: The tool name to associate with the handler.
            handler: An async callable that executes the tool logic.
        """
        self._tool_handlers[tool_name] = handler

    async def invoke(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        user_id: str,
        timeout: float | None = None,
    ) -> ToolCallResult:
        """Invoke a tool with full validation and monitoring.

        Performs: permission check → input validation → execution →
        result capture → metrics recording.

        Args:
            tool_name: Name of the tool to invoke.
            arguments: Arguments to pass to the tool.
            user_id: Identifier of the user making the call.
            timeout: Optional timeout override in seconds.

        Returns:
            A ToolCallResult with the output or error information.
        """
        start_time = time.monotonic()
        effective_timeout = timeout or self._default_timeout

        # Look up tool
        tool = await self._registry.get(tool_name)
        if tool is None:
            return self._fail(tool_name, f"Tool '{tool_name}' not found", start_time, user_id)

        # Permission check
        user_perms = self._security_manager.get_user_permissions(user_id)
        permission_error = self._check_permissions(tool, user_perms, user_id)
        if permission_error:
            return self._fail(tool_name, permission_error, start_time, user_id)

        # Rate limit check
        if not self._security_manager.check_rate_limit(user_id):
            return self._fail(tool_name, "Rate limit exceeded", start_time, user_id)

        # Input validation
        validation_error = self._validate_input(tool, arguments)
        if validation_error:
            return self._fail(tool_name, validation_error, start_time, user_id)

        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                self._execute_tool(tool_name, arguments),
                timeout=effective_timeout,
            )
            duration_ms = (time.monotonic() - start_time) * 1000

            self._metrics.record_invocation(tool_name, True, duration_ms)
            self._security_manager.record_call(user_id)
            self._events.append(
                ToolInvokedEvent(
                    tool_name=tool_name,
                    user_id=user_id,
                    success=True,
                    duration_ms=duration_ms,
                )
            )

            return ToolCallResult(
                tool_name=tool_name,
                output=result,
                success=True,
                duration_ms=duration_ms,
            )
        except TimeoutError:
            return self._fail(
                tool_name,
                f"Tool execution timed out after {effective_timeout}s",
                start_time,
                user_id,
            )
        except Exception as e:
            return self._fail(tool_name, f"Execution error: {e!s}", start_time, user_id)

    def _check_permissions(
        self, tool: MCPTool, user_perms: UserPermissions, user_id: str
    ) -> str | None:
        """Check if user has required permissions for the tool.

        Returns:
            Error message if denied, None if allowed.
        """
        # Check denied tools
        if tool.name in user_perms.denied_tools:
            return f"Tool '{tool.name}' is denied for user '{user_id}'"

        # Check policy
        if not self._security_manager.evaluate_tool_access(user_id, tool.name):
            return f"Tool '{tool.name}' is denied by policy for user '{user_id}'"

        # Check required permissions
        for perm in tool.permissions:
            if perm.value not in user_perms.allowed_permissions:
                return (
                    f"User '{user_id}' lacks required permission "
                    f"'{perm.value}' for tool '{tool.name}'"
                )

        return None

    def _validate_input(self, tool: MCPTool, arguments: dict[str, Any]) -> str | None:
        """Validate tool input against the tool's schema.

        Returns:
            Error message if invalid, None if valid.
        """
        schema = tool.input_schema
        if not schema:
            return None

        # Validate required fields
        required = schema.get("required", [])
        properties = schema.get("properties", {})

        for field_name in required:
            if field_name not in arguments:
                return f"Missing required field: '{field_name}'"

        # Validate types
        for field_name, value in arguments.items():
            if field_name in properties:
                expected_type = properties[field_name].get("type")
                if expected_type and not self._check_type(value, expected_type):
                    return (
                        f"Field '{field_name}' expected type "
                        f"'{expected_type}', got '{type(value).__name__}'"
                    )

        return None

    def _check_type(self, value: Any, expected: str) -> bool:
        """Check if a value matches the expected JSON Schema type."""
        type_map: dict[str, type | tuple[type, ...]] = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        expected_types = type_map.get(expected)
        if expected_types is None:
            return True  # Unknown type, allow
        return isinstance(value, expected_types)

    async def _execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Execute the tool's handler function.

        Args:
            tool_name: Name of the tool.
            arguments: Arguments to pass.

        Returns:
            The handler's return value.

        Raises:
            RuntimeError: If no handler is registered for the tool.
        """
        handler = self._tool_handlers.get(tool_name)
        if handler is None:
            raise RuntimeError(f"No handler registered for tool '{tool_name}'")
        return await handler(arguments)

    def _fail(
        self,
        tool_name: str,
        error: str,
        start_time: float,
        user_id: str,
    ) -> ToolCallResult:
        """Create a failed result and record metrics/events."""
        duration_ms = (time.monotonic() - start_time) * 1000
        self._metrics.record_invocation(tool_name, False, duration_ms)
        self._events.append(ToolFailedEvent(tool_name=tool_name, error=error))
        return ToolCallResult(
            tool_name=tool_name,
            output=None,
            success=False,
            error=error,
            duration_ms=duration_ms,
        )
