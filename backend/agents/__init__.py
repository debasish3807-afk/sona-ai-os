"""Multi-Agent Coordination & Autonomous Execution Fabric.

Provides production-ready multi-agent orchestration with:
- Agent lifecycle management and state machines
- Dynamic agent creation and discovery
- Multi-mode coordination (parallel, sequential, consensus)
- Task routing, delegation, and execution
- Security, permissions, and policy enforcement
- Metrics, telemetry, and monitoring
- Recovery and checkpointing
"""

from __future__ import annotations

from agents.agent_coordinator import AgentCoordinator
from agents.agent_executor import AgentExecutor
from agents.agent_factory import AgentFactory
from agents.agent_manager import AgentManager
from agents.agent_registry import AgentRegistry

__all__ = [
    "AgentCoordinator",
    "AgentExecutor",
    "AgentFactory",
    "AgentManager",
    "AgentRegistry",
]
