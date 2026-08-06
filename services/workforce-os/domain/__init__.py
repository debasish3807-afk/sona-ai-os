"""Workforce OS domain layer.

Contains domain models, enums, and value objects for the Workforce OS service.
"""

from domain.models import (
    AgentResult,
    AgentStatus,
    AgentTask,
    AgentType,
)

__all__ = [
    "AgentResult",
    "AgentStatus",
    "AgentTask",
    "AgentType",
]
