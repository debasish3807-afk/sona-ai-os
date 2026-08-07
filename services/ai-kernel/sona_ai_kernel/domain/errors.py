"""AI Kernel domain errors using Result pattern.

Provides typed error codes and error containers for use with the
shared-kernel Result pattern throughout the AI Kernel service.
"""

from dataclasses import dataclass
from enum import StrEnum


class ErrorCode(StrEnum):
    """Error codes for AI Kernel operations."""

    PROVIDER_UNAVAILABLE = "provider_unavailable"
    MODEL_NOT_FOUND = "model_not_found"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    INVALID_REQUEST = "invalid_request"
    INTERNAL_ERROR = "internal_error"


@dataclass(frozen=True)
class KernelError:
    """Structured error for AI Kernel operations.

    Attributes:
        code: Typed error code indicating the category of failure.
        message: Human-readable error description.
        provider: The provider that caused the error, if applicable.
        retryable: Whether the operation can be safely retried.
    """

    code: ErrorCode
    message: str
    provider: str | None = None
    retryable: bool = False
