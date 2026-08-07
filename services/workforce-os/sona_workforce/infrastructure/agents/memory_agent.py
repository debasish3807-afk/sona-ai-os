"""Memory Agent - specialized in memory management and context persistence."""

from __future__ import annotations

from sona_workforce.domain.agent import AgentCapability, AgentRole
from sona_workforce.domain.models import AgentResult, AgentTask, AgentType
from sona_workforce.infrastructure.agents.base_agent import BaseAgent


class MemoryAgent(BaseAgent):
    """Agent specialized in memory management, context storage, and retrieval."""

    def __init__(self, agent_id: str = "memory-agent-001") -> None:
        super().__init__(
            agent_id=agent_id,
            name="Memory Agent",
            agent_type=AgentType.SYSTEM,
            role=AgentRole.WORKER,
            capabilities=[
                AgentCapability.MEMORY_MANAGEMENT,
                AgentCapability.DATA_ANALYSIS,
            ],
            max_concurrent_tasks=6,
            priority=3,
        )
        self._memory_store: dict[str, str] = {}

    async def _execute(self, task: AgentTask) -> AgentResult:
        """Execute memory task with simulated logic."""
        instruction = task.instruction
        context = task.context or {}

        output_parts = [
            f"Agent [Memory Agent] processed: {instruction}",
        ]

        if "store" in instruction.lower() or "save" in instruction.lower():
            key = context.get("key", "default")
            value = context.get("value", instruction)
            self._memory_store[key] = value
            output_parts.append(f"Memory stored with key: {key}")
            output_parts.append(f"Total memories: {len(self._memory_store)}")
        elif "retrieve" in instruction.lower() or "recall" in instruction.lower():
            key = context.get("key", "default")
            value = self._memory_store.get(key, "No memory found")
            output_parts.append(f"Retrieved memory for key: {key}")
            output_parts.append(f"Value: {value}")
        elif "clear" in instruction.lower():
            self._memory_store.clear()
            output_parts.append("Memory store cleared.")
        else:
            output_parts.append("Memory operation completed.")
            output_parts.append(f"Current memory entries: {len(self._memory_store)}")

        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType.SYSTEM,
            output="\n".join(output_parts),
            status="success",
            tokens_used=150,
        )
