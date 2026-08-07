"""Security primitives for the MCP Integration service.

Defines tool access policies and user permission structures for controlling
which users can invoke which tools under what conditions.
"""

from dataclasses import dataclass, field
from enum import StrEnum


class SecurityAction(StrEnum):
    """Action to take when a security policy matches."""

    ALLOW = "allow"
    DENY = "deny"


@dataclass(frozen=True)
class ToolPolicy:
    """A policy rule that matches tool names and specifies an action.

    Attributes:
        tool_pattern: Glob pattern matching tool names (e.g., 'read_*', '*').
        action: Whether to allow or deny matching tools.
        reason: Human-readable explanation of the policy.
    """

    tool_pattern: str
    action: SecurityAction
    reason: str = ""


@dataclass
class UserPermissions:
    """Tracks permissions and constraints for a specific user.

    Attributes:
        user_id: Unique identifier for the user.
        allowed_permissions: Set of permission strings the user holds.
        denied_tools: Set of tool names explicitly denied to this user.
        max_calls_per_minute: Rate limit for tool invocations.
    """

    user_id: str
    allowed_permissions: set[str] = field(default_factory=lambda: {"read"})
    denied_tools: set[str] = field(default_factory=set)
    max_calls_per_minute: int = 60
