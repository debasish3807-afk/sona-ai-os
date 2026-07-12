"""Custom exceptions for the Runtime & Autonomous Workflow Engine."""

from __future__ import annotations


class RuntimeEngineError(Exception):
    """Base exception for runtime engine errors."""

    def __init__(self, message: str, component: str = "runtime") -> None:
        self.message = message
        self.component = component
        super().__init__(f"[{component}] {message}")


class WorkflowError(RuntimeEngineError):
    """Error in workflow creation or execution."""

    def __init__(self, message: str) -> None:
        super().__init__(message, component="workflow")


class SchedulerError(RuntimeEngineError):
    """Error in workflow scheduling."""

    def __init__(self, message: str) -> None:
        super().__init__(message, component="scheduler")


class WorkerError(RuntimeEngineError):
    """Error in worker pool management."""

    def __init__(self, message: str) -> None:
        super().__init__(message, component="worker")


class CheckpointError(RuntimeEngineError):
    """Error in checkpoint creation or loading."""

    def __init__(self, message: str) -> None:
        super().__init__(message, component="checkpoint")


class RollbackError(RuntimeEngineError):
    """Error during workflow rollback."""

    def __init__(self, message: str) -> None:
        super().__init__(message, component="rollback")


class RecoveryError(RuntimeEngineError):
    """Error during workflow recovery."""

    def __init__(self, message: str) -> None:
        super().__init__(message, component="recovery")
