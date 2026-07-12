"""Meta Reasoning & Self Reflection Engine — exception hierarchy."""

from __future__ import annotations


class MetaReasoningError(Exception):
    """Base exception for meta-reasoning errors."""

    def __init__(self, message: str, stage: str = "general") -> None:
        self.stage = stage
        super().__init__(message)


class ReflectionError(MetaReasoningError):
    """Error during the reflection stage."""

    def __init__(self, message: str) -> None:
        super().__init__(message, stage="reflection")


class ValidationError(MetaReasoningError):
    """Error during plan validation."""

    def __init__(self, message: str) -> None:
        super().__init__(message, stage="validation")


class SimulationError(MetaReasoningError):
    """Error during plan simulation."""

    def __init__(self, message: str) -> None:
        super().__init__(message, stage="simulation")


class DeadlockError(MetaReasoningError):
    """Error when reasoning enters a deadlock cycle."""

    def __init__(self, message: str) -> None:
        super().__init__(message, stage="deadlock")
