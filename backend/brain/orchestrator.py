"""Brain Orchestrator — the central AI execution engine.

Connects all subsystems into a single coherent pipeline:
    Request → Memory Retrieval → Agent Routing → Context Assembly
    → Model Selection → Provider Execution → Memory Storage → Response

This is the beating heart of Sona AI OS.
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator

from brain.agent_router import detect_agent, get_agent_system_prompt
from brain.memory_bridge import (
    build_context_messages,
    retrieve_conversation_history,
    save_message_to_memory,
)
from brain.schemas import (
    BrainRequest,
    BrainResponse,
    BrainStreamChunk,
    TokenUsageSchema,
)
from config.logging import get_logger
from providers.base import BaseProvider
from providers.config import OllamaConfig
from providers.ollama_provider import OllamaProvider
from providers.types import (
    ChatMessage,
    ChatRequest,
    MessageRole,
    ModelInfo,
    StreamEvent,
)

logger = get_logger(__name__)


class BrainOrchestrator:
    """The AI Brain — orchestrates the complete execution pipeline.

    Manages provider lifecycle, routes requests through the full
    pipeline (memory → agent → provider → memory), and handles
    errors gracefully.
    """

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    @property
    def available_providers(self) -> dict[str, BaseProvider]:
        return self._providers

    async def initialize(self) -> None:
        """Initialize the Brain and all providers."""
        if self._initialized:
            return

        # Initialize Ollama provider (primary/local)
        ollama = OllamaProvider(OllamaConfig())
        await ollama.initialize()
        self._providers["ollama"] = ollama

        self._initialized = True
        logger.info(
            "Brain orchestrator initialized",
            providers=list(self._providers.keys()),
        )

    async def shutdown(self) -> None:
        """Shutdown the Brain and all providers."""
        for name, provider in self._providers.items():
            try:
                await provider.shutdown()
                logger.info("Provider shut down", provider=name)
            except Exception as exc:
                logger.warning("Provider shutdown error", provider=name, error=str(exc))
        self._providers.clear()
        self._initialized = False

    def _select_provider(self, requested_provider: str | None = None) -> BaseProvider:
        """Select the best available provider.

        Args:
            requested_provider: Explicit provider request (optional).

        Returns:
            The selected provider instance.

        Raises:
            RuntimeError: If no providers are available.
        """
        if not self._providers:
            raise RuntimeError("No AI providers available. Is the Brain initialized?")

        if requested_provider and requested_provider in self._providers:
            return self._providers[requested_provider]

        # Default: return first available (Ollama)
        return next(iter(self._providers.values()))

    def _select_model(self, provider: BaseProvider, requested_model: str | None) -> str:
        """Select model for the request.

        Args:
            provider: The provider to use.
            requested_model: Explicit model request (optional).

        Returns:
            Model identifier string.
        """
        if requested_model:
            return requested_model
        return provider.config.default_model

    async def process(self, request: BrainRequest) -> BrainResponse:
        """Process a chat request through the full AI pipeline.

        Pipeline:
            1. Retrieve conversation history (memory)
            2. Detect agent type (routing)
            3. Build context window (context assembly)
            4. Select provider + model
            5. Execute LLM request
            6. Save response to memory
            7. Return response

        Args:
            request: The brain request to process.

        Returns:
            BrainResponse with generated content.
        """
        start = time.perf_counter()

        # Step 1: Memory — retrieve conversation history
        history = retrieve_conversation_history(request.session_id)

        # Step 2: Agent routing — detect intent
        agent = detect_agent(request.messages)
        agent_prompt = get_agent_system_prompt(agent)

        # Step 3: Context assembly
        system_prompt = request.system_prompt or agent_prompt
        context_messages = build_context_messages(
            request_messages=request.messages,
            history=history,
            system_prompt=system_prompt,
        )

        # Step 4: Provider + model selection
        provider = self._select_provider(request.provider)
        model = self._select_model(provider, request.model)

        # Step 5: Build provider request and execute
        chat_messages = [
            ChatMessage(
                role=MessageRole(msg.role),
                content=msg.content,
                name=msg.name,
            )
            for msg in context_messages
        ]

        chat_request = ChatRequest(
            messages=chat_messages,
            model=model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        try:
            response = await provider.chat(chat_request)
        except ConnectionError as exc:
            raise RuntimeError(f"Provider unavailable: {exc}") from exc

        latency_ms = (time.perf_counter() - start) * 1000

        # Step 6: Save to memory
        if request.session_id:
            # Save user message
            last_user = next((m for m in reversed(request.messages) if m.role == "user"), None)
            if last_user:
                save_message_to_memory(
                    session_id=request.session_id,
                    role="user",
                    content=last_user.content,
                )
            # Save assistant response
            save_message_to_memory(
                session_id=request.session_id,
                role="assistant",
                content=response.content,
                model=model,
                token_count=response.token_usage.completion_tokens,
            )

        # Step 7: Build and return response
        return BrainResponse(
            content=response.content,
            model=response.model,
            provider=response.provider,
            agent=agent,
            finish_reason=response.finish_reason.value,
            token_usage=TokenUsageSchema(
                prompt_tokens=response.token_usage.prompt_tokens,
                completion_tokens=response.token_usage.completion_tokens,
                total_tokens=response.token_usage.total_tokens,
            ),
            latency_ms=latency_ms,
            response_id=response.response_id,
            session_id=request.session_id,
        )

    async def process_stream(self, request: BrainRequest) -> AsyncIterator[BrainStreamChunk]:
        """Process a streaming chat request through the AI pipeline.

        Same pipeline as process() but yields chunks via SSE.

        Args:
            request: The brain request to process.

        Yields:
            BrainStreamChunk instances.
        """
        # Step 1-4: Same setup as non-streaming
        history = retrieve_conversation_history(request.session_id)
        agent = detect_agent(request.messages)
        agent_prompt = get_agent_system_prompt(agent)
        system_prompt = request.system_prompt or agent_prompt

        context_messages = build_context_messages(
            request_messages=request.messages,
            history=history,
            system_prompt=system_prompt,
        )

        provider = self._select_provider(request.provider)
        model = self._select_model(provider, request.model)

        chat_messages = [
            ChatMessage(
                role=MessageRole(msg.role),
                content=msg.content,
                name=msg.name,
            )
            for msg in context_messages
        ]

        chat_request = ChatRequest(
            messages=chat_messages,
            model=model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True,
        )

        # Step 5: Stream from provider
        full_content: list[str] = []
        final_usage: TokenUsageSchema | None = None

        try:
            async for chunk in provider.stream(chat_request):
                if chunk.event == StreamEvent.START:
                    yield BrainStreamChunk(event="start", model=model)
                elif chunk.event == StreamEvent.DELTA:
                    full_content.append(chunk.content)
                    yield BrainStreamChunk(event="delta", content=chunk.content, model=model)
                elif chunk.event == StreamEvent.DONE:
                    prompt_tokens = chunk.metadata.get("prompt_eval_count", 0)
                    eval_count = chunk.metadata.get("eval_count", 0)
                    final_usage = TokenUsageSchema(
                        prompt_tokens=prompt_tokens,
                        completion_tokens=eval_count,
                        total_tokens=prompt_tokens + eval_count,
                    )
                    yield BrainStreamChunk(
                        event="done",
                        model=model,
                        finish_reason="stop",
                        token_usage=final_usage,
                    )
                elif chunk.event == StreamEvent.ERROR:
                    yield BrainStreamChunk(event="error", content=chunk.content, model=model)
                    return
        except Exception as exc:
            yield BrainStreamChunk(event="error", content=str(exc), model=model)
            return

        # Step 6: Save to memory after stream completes
        if request.session_id and full_content:
            last_user = next((m for m in reversed(request.messages) if m.role == "user"), None)
            if last_user:
                save_message_to_memory(
                    session_id=request.session_id,
                    role="user",
                    content=last_user.content,
                )
            save_message_to_memory(
                session_id=request.session_id,
                role="assistant",
                content="".join(full_content),
                model=model,
            )

    async def list_models(self) -> list[ModelInfo]:
        """List all available models across all providers."""
        all_models: list[ModelInfo] = []
        for provider in self._providers.values():
            try:
                models = await provider.list_models()
                all_models.extend(models)
            except Exception as exc:
                logger.warning(
                    "Failed to list models from provider",
                    provider=provider.provider_id.value,
                    error=str(exc),
                )
        return all_models

    async def get_provider_health(self) -> dict[str, bool]:
        """Check health of all providers."""
        health: dict[str, bool] = {}
        for name, provider in self._providers.items():
            try:
                health[name] = await provider.health()
            except Exception:
                health[name] = False
        return health


# Global singleton (initialized at app startup)
_brain: BrainOrchestrator | None = None


def get_brain() -> BrainOrchestrator:
    """Get the global Brain orchestrator instance."""
    global _brain
    if _brain is None:
        _brain = BrainOrchestrator()
    return _brain


async def initialize_brain() -> BrainOrchestrator:
    """Initialize the global Brain orchestrator."""
    brain = get_brain()
    await brain.initialize()
    return brain


async def shutdown_brain() -> None:
    """Shutdown the global Brain orchestrator."""
    global _brain
    if _brain:
        await _brain.shutdown()
        _brain = None
