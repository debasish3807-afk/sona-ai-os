"""Dependency Injection - Factory for Workforce OS components."""

from __future__ import annotations

from sona_workforce.domain.models import AgentType
from sona_workforce.infrastructure.agents.coding_agent import CodingAgent
from sona_workforce.infrastructure.agents.execution_agent import ExecutionAgent
from sona_workforce.infrastructure.agents.knowledge_agent import KnowledgeAgent
from sona_workforce.infrastructure.agents.manager_agent import ManagerAgent
from sona_workforce.infrastructure.agents.memory_agent import MemoryAgent
from sona_workforce.infrastructure.agents.planning_agent import PlanningAgent
from sona_workforce.infrastructure.agents.research_agent import ResearchAgent
from sona_workforce.infrastructure.agents.reviewer_agent import ReviewerAgent
from sona_workforce.infrastructure.agents.writing_agent import WritingAgent
from sona_workforce.infrastructure.workforce_manager import WorkforceManager


async def create_workforce_manager() -> WorkforceManager:
    """Create fully-wired Workforce OS with all built-in agents.

    Registers all 9 built-in agents automatically:
    - CodingAgent
    - ResearchAgent
    - PlanningAgent
    - WritingAgent
    - MemoryAgent
    - KnowledgeAgent
    - ExecutionAgent
    - ReviewerAgent
    - ManagerAgent
    """
    manager = WorkforceManager()

    # Register all built-in agents
    agents = [
        (AgentType.CODING, CodingAgent()),
        (AgentType.RESEARCH, ResearchAgent()),
        (AgentType.PLANNER, PlanningAgent()),
        (AgentType.COMMUNICATION, WritingAgent()),
        (AgentType.SYSTEM, MemoryAgent()),
        (AgentType.RESEARCH, KnowledgeAgent()),
        (AgentType.AUTOMATION, ExecutionAgent()),
        (AgentType.CODING, ReviewerAgent()),
        (AgentType.PLANNER, ManagerAgent()),
    ]

    for agent_type, agent in agents:
        await manager.register_agent(agent_type, agent)

    return manager
