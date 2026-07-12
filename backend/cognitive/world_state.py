"""World State — the kernel's live awareness of system state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorldState:
    """Live representation of everything the kernel knows.

    Updated via events; queried by engines during processing.
    """

    # Goal
    current_goal: str = ""
    goal_state: str = ""

    # Project
    current_project: str = ""
    workspace: str = ""
    repository: str = ""
    branch: str = ""

    # Environment
    environment: str = "development"
    available_models: list[str] = field(default_factory=list)
    available_providers: list[str] = field(default_factory=list)
    available_capabilities: list[str] = field(default_factory=list)
    loaded_plugins: list[str] = field(default_factory=list)

    # Runtime
    running_tasks: int = 0
    system_health: str = "healthy"
    risk_level: str = "low"

    # Resources
    resources: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_goal": self.current_goal,
            "current_project": self.current_project,
            "workspace": self.workspace,
            "repository": self.repository,
            "branch": self.branch,
            "environment": self.environment,
            "available_models": self.available_models,
            "available_providers": self.available_providers,
            "available_capabilities": self.available_capabilities,
            "running_tasks": self.running_tasks,
            "system_health": self.system_health,
            "risk_level": self.risk_level,
        }
