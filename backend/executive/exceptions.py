"""Executive Intelligence layer — exception hierarchy."""

from __future__ import annotations


class ExecutiveError(Exception):
    """Base exception for executive layer errors."""

    def __init__(self, message: str, category: str = "general") -> None:
        self.category = category
        super().__init__(message)


class GoalError(ExecutiveError):
    """Error related to goal management."""

    def __init__(self, message: str) -> None:
        super().__init__(message, category="goal")


class PlanningError(ExecutiveError):
    """Error during strategic or execution planning."""

    def __init__(self, message: str) -> None:
        super().__init__(message, category="planning")


class DecisionError(ExecutiveError):
    """Error during decision-making process."""

    def __init__(self, message: str) -> None:
        super().__init__(message, category="decision")


class ApprovalError(ExecutiveError):
    """Error in the approval process."""

    def __init__(self, message: str) -> None:
        super().__init__(message, category="approval")


class BudgetError(ExecutiveError):
    """Error when budget constraints are violated."""

    def __init__(self, message: str) -> None:
        super().__init__(message, category="budget")
