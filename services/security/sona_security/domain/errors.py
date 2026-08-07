"""Security error types for the Security Layer service.

Defines structured error codes and error objects for security operations.
"""

from dataclasses import dataclass
from enum import StrEnum


class SecurityErrorCode(StrEnum):
    """Enumeration of all security error codes."""

    INVALID_CREDENTIALS = "invalid_credentials"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_REVOKED = "token_revoked"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMITED = "rate_limited"
    UNSAFE_CONTENT = "unsafe_content"
    PROMPT_INJECTION = "prompt_injection"


@dataclass(frozen=True)
class SecurityError:
    """A structured security error with code, message, and optional user context."""

    code: SecurityErrorCode
    message: str
    user_id: str = ""
