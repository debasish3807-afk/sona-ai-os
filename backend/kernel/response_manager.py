"""Response pipeline management.

Manages the processing, validation, transformation, and delivery
of AI model responses back to the caller.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class ResponseStatus(str, Enum):
    """Status of a response in the pipeline."""

    PENDING = "pending"
    STREAMING = "streaming"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FILTERED = "filtered"
    FAILED = "failed"


class ResponseFormat(str, Enum):
    """Output format of the response."""

    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    CODE = "code"
    STRUCTURED = "structured"


@dataclass
class TokenUsage:
    """Token usage statistics for a response.

    Attributes:
        prompt_tokens: Tokens in the input prompt.
        completion_tokens: Tokens in the generated response.
        total_tokens: Total tokens consumed.
        estimated_cost: Estimated cost in USD.
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0


@dataclass
class ResponseChunk:
    """A single chunk in a streaming response.

    Attributes:
        chunk_id: Unique chunk identifier.
        content: The chunk content.
        index: Chunk sequence index.
        is_final: Whether this is the last chunk.
        metadata: Additional chunk metadata.
    """

    content: str
    chunk_id: str = field(default_factory=lambda: str(uuid4()))
    index: int = 0
    is_final: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelResponse:
    """Complete response from an AI model.

    Attributes:
        response_id: Unique response identifier.
        content: The full response content.
        model: Model identifier that generated this response.
        provider: Provider that served the model.
        status: Current response status.
        format: Detected or specified output format.
        token_usage: Token consumption statistics.
        latency_ms: Response generation latency in milliseconds.
        finish_reason: Why the model stopped generating.
        created_at: Response creation timestamp.
        metadata: Additional response metadata.
    """

    content: str
    model: str
    provider: str
    response_id: str = field(default_factory=lambda: str(uuid4()))
    status: ResponseStatus = ResponseStatus.COMPLETED
    format: ResponseFormat = ResponseFormat.TEXT
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    latency_ms: float = 0.0
    finish_reason: str = "stop"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessedResponse:
    """Response after pipeline processing.

    Attributes:
        response: The original model response.
        processed_content: Content after pipeline transformations.
        filters_applied: List of filters that modified the response.
        safety_passed: Whether the response passed safety checks.
        quality_score: Optional quality assessment score (0-1).
        metadata: Additional processing metadata.
    """

    response: ModelResponse
    processed_content: str
    filters_applied: list[str] = field(default_factory=list)
    safety_passed: bool = True
    quality_score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ResponseFilter(ABC):
    """Abstract interface for response processing filters.

    Filters are applied sequentially to transform, validate,
    or block model responses in the pipeline.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of this filter."""
        ...

    @property
    @abstractmethod
    def priority(self) -> int:
        """Execution priority (lower executes first)."""
        ...

    @abstractmethod
    async def process(self, response: ModelResponse) -> ModelResponse:
        """Process a model response through this filter.

        Args:
            response: The response to process.

        Returns:
            Processed ModelResponse (may be modified).

        Raises:
            ValueError: If the response should be blocked.
        """
        ...

    @abstractmethod
    async def should_apply(self, response: ModelResponse) -> bool:
        """Determine if this filter should be applied.

        Args:
            response: The response to check.

        Returns:
            True if the filter should process this response.
        """
        ...


class ResponseManager(ABC):
    """Abstract interface for response pipeline management.

    Manages the processing chain that model responses pass through
    before being delivered to the caller.
    """

    @abstractmethod
    async def process(self, response: ModelResponse) -> ProcessedResponse:
        """Process a model response through the full pipeline.

        Applies all registered filters in priority order.

        Args:
            response: Raw model response to process.

        Returns:
            ProcessedResponse after all filters have been applied.
        """
        ...

    @abstractmethod
    async def process_stream(
        self,
        chunks: AsyncIterator[ResponseChunk],
        model: str,
        provider: str,
    ) -> AsyncIterator[ResponseChunk]:
        """Process a streaming response through the pipeline.

        Applies streaming-compatible filters to each chunk.

        Args:
            chunks: Async iterator of response chunks.
            model: Model identifier.
            provider: Provider identifier.

        Yields:
            Processed response chunks.
        """
        ...

    @abstractmethod
    async def register_filter(self, filter: ResponseFilter) -> None:
        """Register a response processing filter.

        Args:
            filter: The filter to register.

        Raises:
            ValueError: If a filter with the same name exists.
        """
        ...

    @abstractmethod
    async def unregister_filter(self, filter_name: str) -> bool:
        """Remove a registered filter.

        Args:
            filter_name: Name of the filter to remove.

        Returns:
            True if the filter was found and removed.
        """
        ...

    @abstractmethod
    def list_filters(self) -> list[str]:
        """List names of all registered filters in execution order.

        Returns:
            Ordered list of filter names.
        """
        ...
