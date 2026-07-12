"""Shared type definitions for the provider system.

Contains enums, type aliases, and data structures used across
all provider implementations and management components.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class ProviderID(str, Enum):
    """Identifiers for supported AI providers."""

    OPENAI = "openai"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    CLAUDE = "claude"
    GROQ = "groq"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    MISTRAL = "mistral"


class ModelType(str, Enum):
    """Classification of model types."""

    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    IMAGE = "image"
    AUDIO = "audio"
    CODE = "code"
    MULTIMODAL = "multimodal"


class MessageRole(str, Enum):
    """Roles within a chat message sequence."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    FUNCTION = "function"


class FinishReason(str, Enum):
    """Reasons a model may stop generating."""

    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"


class StreamEvent(str, Enum):
    """Events emitted during streaming responses."""

    START = "start"
    DELTA = "delta"
    TOOL_CALL = "tool_call"
    DONE = "done"
    ERROR = "error"


@dataclass
class ChatMessage:
    """A single message in a chat conversation.

    Attributes:
        role: The message sender role.
        content: Text content of the message.
        name: Optional sender name.
        tool_calls: Optional tool call requests.
        tool_call_id: ID of the tool call this responds to.
        metadata: Additional message metadata.
    """

    role: MessageRole
    content: str
    name: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatRequest:
    """Request payload for chat completion.

    Attributes:
        messages: Conversation messages.
        model: Target model identifier.
        temperature: Sampling temperature (0-2).
        max_tokens: Maximum response tokens.
        top_p: Nucleus sampling parameter.
        frequency_penalty: Frequency penalty (-2 to 2).
        presence_penalty: Presence penalty (-2 to 2).
        stop: Stop sequences.
        stream: Whether to stream the response.
        tools: Available tool definitions.
        tool_choice: Tool selection strategy.
        response_format: Desired response format.
        seed: Optional seed for determinism.
        metadata: Additional request parameters.
    """

    messages: list[ChatMessage]
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: list[str] | None = None
    stream: bool = False
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | None = None
    response_format: dict[str, str] | None = None
    seed: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenUsage:
    """Token consumption statistics.

    Attributes:
        prompt_tokens: Tokens in the input.
        completion_tokens: Tokens in the output.
        total_tokens: Total tokens consumed.
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class ChatResponse:
    """Response from a chat completion request.

    Attributes:
        response_id: Unique response identifier.
        content: Generated text content.
        model: Model that generated the response.
        provider: Provider that served the request.
        finish_reason: Why generation stopped.
        token_usage: Token consumption statistics.
        tool_calls: Any tool calls requested by the model.
        latency_ms: Response latency in milliseconds.
        created_at: Response creation timestamp.
        metadata: Additional response metadata.
    """

    content: str
    model: str
    provider: str
    response_id: str = field(default_factory=lambda: str(uuid4()))
    finish_reason: FinishReason = FinishReason.STOP
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    tool_calls: list[dict[str, Any]] | None = None
    latency_ms: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StreamChunk:
    """A single chunk in a streaming response.

    Attributes:
        event: The stream event type.
        content: Text content delta.
        model: Model generating the stream.
        finish_reason: Set on the final chunk.
        tool_calls: Incremental tool call data.
        metadata: Additional chunk metadata.
    """

    event: StreamEvent
    content: str = ""
    model: str = ""
    finish_reason: FinishReason | None = None
    tool_calls: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingRequest:
    """Request payload for text embeddings.

    Attributes:
        input: Text(s) to embed.
        model: Target embedding model.
        encoding_format: Desired encoding format.
        dimensions: Optional target dimensions.
        metadata: Additional request parameters.
    """

    input: list[str]
    model: str
    encoding_format: str = "float"
    dimensions: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbeddingResponse:
    """Response from an embedding request.

    Attributes:
        embeddings: List of embedding vectors.
        model: Model that generated embeddings.
        provider: Provider that served the request.
        token_usage: Token consumption statistics.
        dimensions: Dimensions of each embedding.
        metadata: Additional response metadata.
    """

    embeddings: list[list[float]]
    model: str
    provider: str
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    dimensions: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelInfo:
    """Information about an available model.

    Attributes:
        model_id: Unique model identifier.
        name: Human-readable model name.
        provider: Provider offering this model.
        model_type: Type classification.
        max_context_tokens: Maximum context window.
        max_output_tokens: Maximum output length.
        supports_streaming: Whether streaming is supported.
        supports_tools: Whether tool calling is supported.
        supports_vision: Whether vision/image input is supported.
        supports_json_mode: Whether JSON output mode is supported.
        cost_per_input_token: Cost per input token (USD).
        cost_per_output_token: Cost per output token (USD).
        metadata: Additional model metadata.
    """

    model_id: str
    name: str
    provider: str
    model_type: ModelType = ModelType.CHAT
    max_context_tokens: int = 8192
    max_output_tokens: int = 4096
    supports_streaming: bool = True
    supports_tools: bool = False
    supports_vision: bool = False
    supports_json_mode: bool = False
    cost_per_input_token: float = 0.0
    cost_per_output_token: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
