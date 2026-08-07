"""AI Kernel runtime implementation.

Provides the concrete AIKernelPort implementation that ties together
all infrastructure components: provider registry, model routing,
retry logic, streaming, and token usage tracking.
"""

import time
import uuid
from collections.abc import AsyncIterator

import structlog

from sona_ai_kernel.application.ports import AIKernelPort
from sona_ai_kernel.domain.events import (
    InferenceCompletedEvent,
    InferenceFailedEvent,
    InferenceStartedEvent,
)
from sona_ai_kernel.domain.models import KernelRequest, KernelResponse, ModelConfig
from sona_ai_kernel.infrastructure.providers.base import CompletionRequest
from sona_ai_kernel.infrastructure.registry import ModelRegistry, ProviderRegistry
from sona_ai_kernel.infrastructure.retry import RetryConfig, with_retry
from sona_ai_kernel.infrastructure.streaming import StreamingEngine
from sona_ai_kernel.infrastructure.token_usage import TokenUsageManager, UsageRecord

logger = structlog.get_logger()


class AIKernelRuntime(AIKernelPort):
    """Concrete AI Kernel implementation connecting all subsystems.

    Orchestrates request processing by selecting models, building
    completion requests, invoking providers with retry logic, and
    tracking token usage across all operations.
    """

    def __init__(
        self,
        provider_registry: ProviderRegistry,
        model_registry: ModelRegistry,
        token_manager: TokenUsageManager,
        default_model: str = "llama3.2",
        default_provider: str = "ollama",
        retry_config: RetryConfig | None = None,
    ) -> None:
        """Initialize the AI Kernel runtime.

        Args:
            provider_registry: Registry of available LLM providers.
            model_registry: Registry mapping models to providers.
            token_manager: Token usage tracking manager.
            default_model: Default model ID when none specified.
            default_provider: Default provider name when model can't be resolved.
            retry_config: Configuration for retry behavior.
        """
        self._provider_registry = provider_registry
        self._model_registry = model_registry
        self._token_manager = token_manager
        self._default_model = default_model
        self._default_provider = default_provider
        self._retry_config = retry_config or RetryConfig(max_retries=2)
        self._streaming_engine = StreamingEngine()
        self._events: list[
            InferenceStartedEvent | InferenceCompletedEvent | InferenceFailedEvent
        ] = []

    @property
    def events(
        self,
    ) -> list[InferenceStartedEvent | InferenceCompletedEvent | InferenceFailedEvent]:
        """Return collected domain events."""
        return self._events

    def clear_events(self) -> None:
        """Clear collected domain events."""
        self._events.clear()

    async def process(self, request: KernelRequest) -> KernelResponse:
        """Process a single request through the kernel pipeline.

        Selects a model, builds a completion request, executes it with
        retry logic, records usage, and emits domain events.

        Args:
            request: The kernel request containing content, context, and config.

        Returns:
            A KernelResponse with generated content and usage metrics.

        Raises:
            RuntimeError: If the resolved provider is not available.
        """
        request_id = str(uuid.uuid4())
        model_config = await self.select_model(request)
        provider_name = model_config.provider
        model_id = model_config.model_id

        log = logger.bind(
            request_id=request_id,
            provider=provider_name,
            model=model_id,
            session_id=request.session_id,
        )

        # Emit started event
        started_event = InferenceStartedEvent(
            request_id=request_id,
            provider=provider_name,
            model_id=model_id,
        )
        self._events.append(started_event)

        provider = self._provider_registry.get(provider_name)
        if provider is None:
            error_msg = f"Provider '{provider_name}' not found in registry"
            failed_event = InferenceFailedEvent(
                request_id=request_id,
                provider=provider_name,
                model_id=model_id,
                error=error_msg,
            )
            self._events.append(failed_event)
            raise RuntimeError(error_msg)

        completion_request = self._build_completion_request(request, model_config)

        log.info("kernel_process_start")
        start = time.perf_counter()

        try:
            response = await with_retry(
                fn=lambda: provider.complete(completion_request),
                config=self._retry_config,
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            log.error("kernel_process_failed", error=str(exc), latency_ms=round(elapsed_ms, 2))
            failed_event = InferenceFailedEvent(
                request_id=request_id,
                provider=provider_name,
                model_id=model_id,
                error=str(exc),
            )
            self._events.append(failed_event)
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000

        # Record usage
        usage_record = UsageRecord(
            provider=provider_name,
            model=model_id,
            tokens_input=response.tokens_input,
            tokens_output=response.tokens_output,
            latency_ms=round(elapsed_ms, 2),
            session_id=request.session_id,
        )
        self._token_manager.record(usage_record)

        # Emit completed event
        completed_event = InferenceCompletedEvent(
            request_id=request_id,
            provider=provider_name,
            model_id=model_id,
            tokens_input=response.tokens_input,
            tokens_output=response.tokens_output,
            latency_ms=round(elapsed_ms, 2),
        )
        self._events.append(completed_event)

        log.info(
            "kernel_process_done",
            tokens_input=response.tokens_input,
            tokens_output=response.tokens_output,
            latency_ms=round(elapsed_ms, 2),
        )

        return KernelResponse(
            content=response.content,
            model_used=model_id,
            tokens_input=response.tokens_input,
            tokens_output=response.tokens_output,
            latency_ms=round(elapsed_ms, 2),
        )

    async def stream(self, request: KernelRequest) -> AsyncIterator[str]:
        """Stream response tokens for a request.

        Selects a model, builds a completion request, and streams
        the response through the streaming engine.

        Args:
            request: The kernel request containing content, context, and config.

        Yields:
            String tokens/chunks as they are generated by the model.

        Raises:
            RuntimeError: If the resolved provider is not available.
        """
        model_config = await self.select_model(request)
        provider_name = model_config.provider
        model_id = model_config.model_id

        provider = self._provider_registry.get(provider_name)
        if provider is None:
            raise RuntimeError(f"Provider '{provider_name}' not found in registry")

        completion_request = self._build_completion_request(request, model_config)

        log = logger.bind(provider=provider_name, model=model_id)
        log.info("kernel_stream_start")

        async for token in self._streaming_engine.stream_completion(provider, completion_request):
            yield token

    async def select_model(self, request: KernelRequest) -> ModelConfig:
        """Select the optimal model based on request characteristics.

        Uses model_override if specified, otherwise resolves the default
        model from the model registry.

        Args:
            request: The kernel request to analyze.

        Returns:
            A ModelConfig specifying the selected provider and model.
        """
        # Honor explicit override
        if request.model_override is not None:
            return request.model_override

        # Try to resolve from model registry
        provider_name = self._model_registry.resolve(self._default_model)
        if provider_name is not None:
            return ModelConfig(
                provider=provider_name,
                model_id=self._default_model,
            )

        # Fall back to default provider
        return ModelConfig(
            provider=self._default_provider,
            model_id=self._default_model,
        )

    def _build_completion_request(
        self, request: KernelRequest, model_config: ModelConfig
    ) -> CompletionRequest:
        """Build a CompletionRequest from a KernelRequest and ModelConfig.

        Args:
            request: The kernel request with user content.
            model_config: The selected model configuration.

        Returns:
            A CompletionRequest ready for provider execution.
        """
        messages: list[dict[str, str]] = []

        # Add system context if present
        if request.context and "system" in request.context:
            messages.append({"role": "system", "content": str(request.context["system"])})

        # Add user message
        messages.append({"role": "user", "content": request.content})

        return CompletionRequest(
            messages=messages,
            model=model_config.model_id,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens,
            top_p=model_config.top_p,
        )
