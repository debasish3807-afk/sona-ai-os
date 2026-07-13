"""Strategy learning from agent successes and failures."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class StrategyRecord:
    """A record of a strategy outcome."""

    agent_id: str
    task: str
    outcome: str
    success: bool
    timestamp: float = field(default_factory=time.time)


class StrategyLearner:
    """Learns from agent successes and failures."""

    def __init__(self) -> None:
        self._records: list[StrategyRecord] = []

    def record(self, agent_id: str, task: str, outcome: str, success: bool) -> None:
        """Record a strategy outcome."""
        entry = StrategyRecord(
            agent_id=agent_id,
            task=task,
            outcome=outcome,
            success=success,
        )
        self._records.append(entry)
        logger.debug(
            "strategy_recorded",
            agent_id=agent_id,
            task=task[:50],
            success=success,
        )

    def get_best_strategy(self, task_type: str) -> dict[str, Any] | None:
        """Get the best known strategy for a task type."""
        matching = [r for r in self._records if task_type.lower() in r.task.lower() and r.success]
        if not matching:
            return None

        # Return the most recent successful strategy
        best = max(matching, key=lambda r: r.timestamp)
        return {
            "agent_id": best.agent_id,
            "task": best.task,
            "outcome": best.outcome,
            "timestamp": best.timestamp,
        }

    def get_success_rate(self, agent_id: str | None = None) -> float:
        """Get the success rate for an agent or overall."""
        if agent_id:
            records = [r for r in self._records if r.agent_id == agent_id]
        else:
            records = self._records

        if not records:
            return 0.0
        successes = sum(1 for r in records if r.success)
        return successes / len(records)

    def get_history(self, agent_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        """Get strategy history."""
        if agent_id:
            records = [r for r in self._records if r.agent_id == agent_id]
        else:
            records = list(self._records)

        records = sorted(records, key=lambda r: r.timestamp, reverse=True)[:limit]
        return [
            {
                "agent_id": r.agent_id,
                "task": r.task,
                "outcome": r.outcome,
                "success": r.success,
                "timestamp": r.timestamp,
            }
            for r in records
        ]

    def clear(self) -> None:
        """Clear all strategy records."""
        self._records.clear()
        logger.info("strategy_history_cleared")
