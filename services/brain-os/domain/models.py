"""Domain models for the Brain OS service.

Defines the data structures used by the Brain OS orchestrator for request
processing, pipeline execution, and response generation.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BrainRequest:
    """Request to the Brain OS orchestrator for pipeline execution.

    Attributes:
        session_id: Unique identifier for the user session.
        user_id: Identifier of the requesting user.
        messages: List of message dicts with role/content for conversation context.
        stream: Whether to stream the response tokens.
        metadata: Optional additional metadata for the request.
    """

    session_id: str
    user_id: str
    messages: list[dict[str, str]]
    stream: bool = False
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class BrainResponse:
    """Response from the Brain OS orchestrator after pipeline execution.

    Attributes:
        content: The generated text content.
        session_id: Session identifier this response belongs to.
        model_used: Identifier of the model that produced the response.
        tokens: Dictionary of token usage (e.g., {"input": N, "output": M}).
        latency_ms: Total processing latency in milliseconds.
        agent_used: Optional identifier of the agent that assisted (if any).
        memory_updated: Whether memory was updated during this request.
    """

    content: str
    session_id: str
    model_used: str
    tokens: dict[str, int]
    latency_ms: float
    agent_used: str | None = None
    memory_updated: bool = False
