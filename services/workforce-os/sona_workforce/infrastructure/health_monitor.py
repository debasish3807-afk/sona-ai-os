"""Health Monitor - periodic health checks and error tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

from sona_workforce.domain.agent import AgentState
from sona_workforce.infrastructure.agent_registry import AgentRegistry
from sona_workforce.infrastructure.agents.base_agent import BaseAgent

logger = structlog.get_logger()


@dataclass
class AgentHealthStatus:
    """Health status for a single agent."""

    agent_id: str
    healthy: bool
    error_count: int = 0
    last_check_passed: bool = True
    consecutive_failures: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class HealthMonitor:
    """Monitors health of all agents in the workforce.

    Performs periodic health checks, marks unhealthy agents as unavailable,
    tracks error rates, and detects auto-recovery.
    """

    def __init__(
        self,
        registry: AgentRegistry,
        agents: dict[str, BaseAgent],
        max_consecutive_failures: int = 3,
    ) -> None:
        self._registry = registry
        self._agents = agents
        self._max_consecutive_failures = max_consecutive_failures
        self._status: dict[str, AgentHealthStatus] = {}
        self._check_count = 0

    async def check_agent(self, agent_id: str) -> AgentHealthStatus:
        """Perform a health check on a single agent."""
        agent = self._agents.get(agent_id)
        if agent is None:
            status = AgentHealthStatus(
                agent_id=agent_id,
                healthy=False,
                error_count=1,
                last_check_passed=False,
                consecutive_failures=1,
            )
            self._status[agent_id] = status
            return status

        self._check_count += 1
        is_healthy = await agent.health_check()

        if agent_id not in self._status:
            self._status[agent_id] = AgentHealthStatus(
                agent_id=agent_id,
                healthy=is_healthy,
            )

        current = self._status[agent_id]
        current.last_check_passed = is_healthy

        if is_healthy:
            # Recovery detection
            if not current.healthy:
                await logger.ainfo("agent_recovered", agent_id=agent_id)
            current.healthy = True
            current.consecutive_failures = 0
        else:
            current.error_count += 1
            current.consecutive_failures += 1
            current.healthy = False

            if current.consecutive_failures >= self._max_consecutive_failures:
                # Mark agent as unavailable
                self._registry.update_state(agent_id, AgentState.ERROR)
                await logger.awarning(
                    "agent_marked_unhealthy",
                    agent_id=agent_id,
                    consecutive_failures=current.consecutive_failures,
                )

        return current

    async def check_all(self) -> dict[str, AgentHealthStatus]:
        """Check health of all registered agents."""
        results: dict[str, AgentHealthStatus] = {}
        for agent_id in self._agents:
            results[agent_id] = await self.check_agent(agent_id)
        return results

    def get_healthy_agents(self) -> list[str]:
        """Return IDs of all currently healthy agents."""
        return [agent_id for agent_id, status in self._status.items() if status.healthy]

    def get_unhealthy_agents(self) -> list[str]:
        """Return IDs of all currently unhealthy agents."""
        return [agent_id for agent_id, status in self._status.items() if not status.healthy]

    def get_status(self, agent_id: str) -> AgentHealthStatus | None:
        """Get health status for a specific agent."""
        return self._status.get(agent_id)

    def get_stats(self) -> dict[str, Any]:
        """Get health monitor statistics."""
        total = len(self._status)
        healthy = len(self.get_healthy_agents())
        return {
            "total_agents": total,
            "healthy_agents": healthy,
            "unhealthy_agents": total - healthy,
            "total_checks": self._check_count,
        }
