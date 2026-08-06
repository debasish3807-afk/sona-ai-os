"""Domain models for the AI Kernel service.

Defines the data structures used by the AI Kernel for request processing,
model selection, and response generation.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ReasoningStrategy(StrEnum):
    """Available reasoning strategies for the AI Kernel.

    Determines how the kernel approaches problem solving and chain-of-thought
    processing before generating a final response.
    """

    DIRECT = "direct"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHT = "tree_of_thought"
    REFLECTION = "reflection"


@dataclass(frozen=True)
class ModelConfig:
    """Configuration for an LLM model invocation.

    Attributes:
        provider: The LLM provider name (e.g., "ollama", "openai").
        model_id: Identifier of the specific model to use.
        temperature: Sampling temperature for generation (0.0 to 2.0).
        max_tokens: Maximum number of tokens to generate.
        top_p: Nucleus sampling parameter.
    """

    provider: str
    model_id: str
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0


@dataclass(frozen=True)
class KernelRequest:
    """Request to the AI Kernel for processing.

    Attributes:
        session_id: Unique identifier for the user session.
        user_id: Identifier of the requesting user.
        content: The input content/prompt to process.
        context: Optional additional context (e.g., memory, routing data).
        model_override: Optional model configuration override.
        strategy: Reasoning strategy to apply during processing.
    """

    session_id: str
    user_id: str
    content: str
    context: dict[str, Any] | None = None
    model_override: ModelConfig | None = None
    strategy: ReasoningStrategy = ReasoningStrategy.DIRECT


@dataclass(frozen=True)
class KernelResponse:
    """Response from the AI Kernel after processing.

    Attributes:
        content: The generated text content.
        model_used: Identifier of the model that produced the response.
        tokens_input: Number of input tokens consumed.
        tokens_output: Number of output tokens generated.
        latency_ms: Total processing latency in milliseconds.
        reasoning_trace: Optional list of reasoning steps (for CoT/ToT strategies).
    """

    content: str
    model_used: str
    tokens_input: int
    tokens_output: int
    latency_ms: float
    reasoning_trace: list[str] | None = None
