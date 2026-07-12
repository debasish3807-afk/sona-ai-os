"""Cognitive Kernel exceptions — failure classification and recovery."""

from __future__ import annotations

from enum import Enum
from typing import Any


class FailureCategory(str, Enum):
    """Classification of kernel failures for recovery strategy selection."""

    TRANSIENT = "transient"  # Retry likely to succeed
    PERMANENT = "permanent"  # Retry will not help
    RESOURCE = "resource"  # Budget/limit exceeded
    TIMEOUT = "timeout"  # Deadline exceeded
    CANCELLED = "cancelled"  # User or system cancellation
    DEPENDENCY = "dependency"  # Upstream engine failure
    CONFIGURATION = "configuration"  # Invalid setup
    SECURITY = "security"  # Permission or policy violation


class KernelError(Exception):
    """Base exception for all kernel errors."""

    def __init__(
        self,
        message: str,
        category: FailureCategory = FailureCategory.PERMANENT,
        engine: str = "",
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.category = category
        self.engine = engine
        self.retryable = retryable
        self.details = details or {}
        super().__init__(message)


class EngineError(KernelError):
    """Error from a specific engine during execution."""


class PipelineError(KernelError):
    """Error in the kernel pipeline orchestration."""


class RegistryError(KernelError):
    """Error in engine registration or lookup."""


class BudgetExceededError(KernelError):
    """Token or cost budget exceeded."""

    def __init__(self, message: str = "Budget exceeded", **kwargs: Any) -> None:
        super().__init__(message, category=FailureCategory.RESOURCE, **kwargs)


class TimeoutError(KernelError):
    """Execution deadline exceeded."""

    def __init__(self, message: str = "Execution timed out", **kwargs: Any) -> None:
        super().__init__(message, category=FailureCategory.TIMEOUT, **kwargs)


class CancellationError(KernelError):
    """Request was cancelled."""

    def __init__(self, message: str = "Request cancelled", **kwargs: Any) -> None:
        super().__init__(message, category=FailureCategory.CANCELLED, **kwargs)
