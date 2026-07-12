"""Request Context — tracks all state for a single kernel request."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass
class RequestContext:
    """Complete context for a single request flowing through the kernel.

    Tracks identity, state, budget, and accumulated results from each engine.
    """

    # Identity
    request_id: str = field(default_factory=lambda: str(uuid4()))
    session_id: str = ""
    user_id: str = ""
    goal_id: str = ""
    project_id: str = ""

    # Workspace
    workspace: str = ""
    repository: str = ""
    branch: str = ""
    environment: str = "development"

    # Pipeline state
    current_step: str = ""
    current_engine: str = ""
    completed_engines: list[str] = field(default_factory=list)

    # Quality metrics
    confidence: float = 1.0
    risk: float = 0.0
    cost: float = 0.0

    # Budget
    token_budget: int = 100000
    tokens_used: int = 0
    execution_deadline: float = 300.0  # seconds
    started_at: float = field(default_factory=time.time)

    # Results from engines
    engine_results: dict[str, Any] = field(default_factory=dict)

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.started_at

    @property
    def remaining_budget(self) -> int:
        return max(0, self.token_budget - self.tokens_used)

    @property
    def is_over_budget(self) -> bool:
        return self.tokens_used >= self.token_budget

    @property
    def is_over_deadline(self) -> bool:
        return self.elapsed_seconds >= self.execution_deadline

    def mark_engine_complete(self, engine_id: str, result: Any) -> None:
        """Record an engine's completion."""
        self.completed_engines.append(engine_id)
        self.engine_results[engine_id] = result
        self.current_engine = ""

    def add_tokens(self, count: int) -> None:
        """Record token consumption."""
        self.tokens_used += count

    def add_cost(self, amount: float) -> None:
        """Record cost accumulation."""
        self.cost += amount

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "goal_id": self.goal_id,
            "current_step": self.current_step,
            "current_engine": self.current_engine,
            "completed_engines": self.completed_engines,
            "confidence": self.confidence,
            "risk": self.risk,
            "cost": self.cost,
            "tokens_used": self.tokens_used,
            "token_budget": self.token_budget,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
            "environment": self.environment,
        }
