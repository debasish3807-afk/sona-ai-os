"""Microkernel exceptions — failure types for the microkernel runtime."""

from __future__ import annotations


class MicrokernelError(Exception):
    """Base exception for all microkernel errors."""

    def __init__(self, message: str, component: str = "") -> None:
        self.component = component
        super().__init__(message)


class IPCError(MicrokernelError):
    """Error in inter-process communication."""


class SandboxError(MicrokernelError):
    """Error in sandbox management or enforcement."""


class SchedulerError(MicrokernelError):
    """Error in resource scheduling or allocation."""


class SecurityViolationError(MicrokernelError):
    """Security policy violation detected."""


class ProcessError(MicrokernelError):
    """Error in process supervision or lifecycle."""


class InterruptError(MicrokernelError):
    """Error in interrupt handling or delivery."""
