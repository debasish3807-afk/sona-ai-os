"""MCP (Model Context Protocol) tool security.

Provides tool allowlist/denylist management, permission validation for
tool execution, session isolation, and resource limit enforcement.
"""

from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger()


@dataclass
class MCPSecurityConfig:
    """Configuration for MCP security."""

    max_calls_per_session: int = 100
    max_output_size_bytes: int = 1_000_000  # 1MB
    session_timeout_seconds: int = 3600
    default_mode: str = "allowlist"  # "allowlist" or "denylist"


@dataclass
class ToolExecution:
    """Record of a tool execution."""

    tool_name: str
    user_id: str
    session_id: str
    timestamp: float
    allowed: bool
    reason: str = ""


@dataclass
class SessionState:
    """State for an MCP session."""

    session_id: str
    user_id: str
    call_count: int = 0
    total_output_bytes: int = 0
    is_active: bool = True
    tools_used: list[str] = field(default_factory=list)


class MCPSecurity:
    """MCP tool security manager."""

    def __init__(self, config: MCPSecurityConfig | None = None) -> None:
        self._config = config or MCPSecurityConfig()
        self._allowlist: set[str] = set()
        self._denylist: set[str] = set()
        self._tool_permissions: dict[str, list[str]] = {}  # tool -> required roles
        self._sessions: dict[str, SessionState] = {}
        self._execution_log: list[ToolExecution] = []

    def add_to_allowlist(self, tool_name: str) -> None:
        """Add a tool to the allowlist."""
        self._allowlist.add(tool_name)

    def remove_from_allowlist(self, tool_name: str) -> None:
        """Remove a tool from the allowlist."""
        self._allowlist.discard(tool_name)

    def add_to_denylist(self, tool_name: str) -> None:
        """Add a tool to the denylist."""
        self._denylist.add(tool_name)

    def remove_from_denylist(self, tool_name: str) -> None:
        """Remove a tool from the denylist."""
        self._denylist.discard(tool_name)

    def set_tool_permissions(self, tool_name: str, required_roles: list[str]) -> None:
        """Set required roles for a tool."""
        self._tool_permissions[tool_name] = required_roles

    async def validate_tool_access(
        self,
        tool_name: str,
        user_id: str,
        session_id: str,
        user_roles: list[str] | None = None,
    ) -> tuple[bool, str]:
        """Validate if a tool execution is allowed.

        Returns:
            Tuple of (allowed, reason).
        """
        # Check denylist first
        if tool_name in self._denylist:
            self._log_execution(tool_name, user_id, session_id, False, "tool_denied")
            return (False, f"Tool '{tool_name}' is denied")

        # Check allowlist (if in allowlist mode)
        if self._config.default_mode == "allowlist" and self._allowlist:
            if tool_name not in self._allowlist:
                self._log_execution(tool_name, user_id, session_id, False, "not_in_allowlist")
                return (False, f"Tool '{tool_name}' is not in allowlist")

        # Check role permissions
        if tool_name in self._tool_permissions and user_roles is not None:
            required = self._tool_permissions[tool_name]
            if not any(role in required for role in user_roles):
                self._log_execution(
                    tool_name, user_id, session_id, False, "insufficient_permissions"
                )
                return (False, f"Insufficient permissions for tool '{tool_name}'")

        # Check session limits
        session = self._get_or_create_session(session_id, user_id)
        if not session.is_active:
            self._log_execution(tool_name, user_id, session_id, False, "session_inactive")
            return (False, "Session is no longer active")

        if session.call_count >= self._config.max_calls_per_session:
            self._log_execution(tool_name, user_id, session_id, False, "call_limit_exceeded")
            return (False, "Session call limit exceeded")

        # Allow and record
        session.call_count += 1
        session.tools_used.append(tool_name)
        self._log_execution(tool_name, user_id, session_id, True, "allowed")
        return (True, "allowed")

    async def check_output_size(self, session_id: str, output_size: int) -> tuple[bool, str]:
        """Check if output size is within limits.

        Returns:
            Tuple of (allowed, reason).
        """
        session = self._sessions.get(session_id)
        if session is None:
            return (False, "Session not found")

        new_total = session.total_output_bytes + output_size
        if new_total > self._config.max_output_size_bytes:
            return (False, "Output size limit exceeded")

        session.total_output_bytes = new_total
        return (True, "within_limits")

    async def end_session(self, session_id: str) -> bool:
        """End an MCP session."""
        session = self._sessions.get(session_id)
        if session is None:
            return False
        session.is_active = False
        return True

    async def get_session_state(self, session_id: str) -> SessionState | None:
        """Get the state of a session."""
        return self._sessions.get(session_id)

    @property
    def execution_log(self) -> list[ToolExecution]:
        """Access the tool execution log."""
        return self._execution_log

    def _get_or_create_session(self, session_id: str, user_id: str) -> SessionState:
        """Get or create a session state."""
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(
                session_id=session_id,
                user_id=user_id,
            )
        return self._sessions[session_id]

    def _log_execution(
        self,
        tool_name: str,
        user_id: str,
        session_id: str,
        allowed: bool,
        reason: str,
    ) -> None:
        """Log a tool execution attempt."""
        import time

        self._execution_log.append(
            ToolExecution(
                tool_name=tool_name,
                user_id=user_id,
                session_id=session_id,
                timestamp=time.time(),
                allowed=allowed,
                reason=reason,
            )
        )
