"""Agent execution context.

Provides contextual information to agents during task execution
including session data, task parameters, available tools, and
shared state.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class AgentTool:
    """A tool available to an agent during execution.

    Attributes:
        tool_id: Unique tool identifier.
        name: Human-readable tool name.
        description: What the tool does.
        parameters: Tool parameter schema.
        required_capability: Capability needed to use this tool.
    """

    tool_id: str
    name: str
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    required_capability: Optional[str] = None



@dataclass
class ExecutionContext:
    """Context provided to an agent during task execution.

    Contains all information the agent needs to process a task
    including session details, available tools, shared state,
    and configuration.

    Attributes:
        context_id: Unique context identifier.
        session_id: Associated user session.
        task_id: The task being executed.
        agent_id: The executing agent.
        input_data: Task input payload.
        tools: Available tools for this execution.
        shared_state: State shared between agents in a workflow.
        parent_context_id: Parent context (for delegated tasks).
        max_tokens: Token budget for this execution.
        timeout_seconds: Maximum execution time.
        created_at: Context creation timestamp.
        metadata: Additional context metadata.
    """

    session_id: str
    task_id: str
    agent_id: str
    input_data: Dict[str, Any]
    context_id: str = field(default_factory=lambda: str(uuid4()))
    tools: List[AgentTool] = field(default_factory=list)
    shared_state: Dict[str, Any] = field(default_factory=dict)
    parent_context_id: Optional[str] = None
    max_tokens: int = 4096
    timeout_seconds: float = 120.0
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_delegated(self) -> bool:
        """Check if this is a delegated (child) execution."""
        return self.parent_context_id is not None


@dataclass
class ExecutionResult:
    """Result of an agent's task execution.

    Attributes:
        result_id: Unique result identifier.
        context_id: The execution context that produced this.
        agent_id: The agent that executed.
        success: Whether execution succeeded.
        output: Result output data.
        error: Error details if failed.
        token_usage: Tokens consumed.
        execution_ms: Execution time in milliseconds.
        tool_calls: Tools that were invoked.
        created_at: Result creation timestamp.
        metadata: Additional result metadata.
    """

    context_id: str
    agent_id: str
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    result_id: str = field(default_factory=lambda: str(uuid4()))
    error: Optional[Dict[str, Any]] = None
    token_usage: int = 0
    execution_ms: float = 0.0
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: Dict[str, Any] = field(default_factory=dict)
