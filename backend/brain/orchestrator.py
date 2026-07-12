"""Brain Orchestrator — the central AI execution engine.

Connects all subsystems into a single coherent pipeline:
    Request → Memory Retrieval → Agent Routing → Context Assembly
    → Model Selection → Provider Execution → Memory Storage → Response

Features:
    - Automatic provider discovery (detects configured API keys)
    - Failover: if primary provider fails, tries next available
    - Priority-based provider selection
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
from providers.types import (
    ChatMessage,
    ChatRequest,
    MessageRole,
    ModelInfo,
    StreamEvent,
)

logger = get_logger(__name__)


async def _discover_providers() -> dict[str, BaseProvider]:
    """Auto-discover available providers based on environment variables.

    Initializes each provider. Providers without API keys are skipped.
    Ollama is always attempted (no key required).

    Returns:
        Dictionary of initialized providers keyed by provider ID.
    """
    from providers.claude_provider import ClaudeProvider
    from providers.config import (
        ClaudeConfig,
        DeepSeekConfig,
        GeminiConfig,
        MistralConfig,
        OllamaConfig,
        OpenAIConfig,
        QwenConfig,
    )
    from providers.deepseek_provider import DeepSeekProvider
    from providers.gemini_provider import GeminiProvider
    from providers.mistral_provider import MistralProvider
    from providers.ollama_provider import OllamaProvider
    from providers.openai_provider import OpenAIProvider
    from providers.qwen_provider import QwenProvider

    # Provider registry ordered by priority (lower = preferred)
    provider_factories: list[tuple[str, type, type, int]] = [
        ("openai", OpenAIProvider, OpenAIConfig, 10),
        ("claude", ClaudeProvider, ClaudeConfig, 20),
        ("gemini", GeminiProvider, GeminiConfig, 30),
        ("deepseek", DeepSeekProvider, DeepSeekConfig, 40),
        ("mistral", MistralProvider, MistralConfig, 50),
        ("qwen", QwenProvider, QwenConfig, 60),
        ("ollama", OllamaProvider, OllamaConfig, 90),
    ]

    providers: dict[str, BaseProvider] = {}

    for name, factory_cls, config_cls, priority in provider_factories:
        try:
            provider = factory_cls(config_cls())
            await provider.initialize()
            if provider.is_initialized:
                providers[name] = provider
                logger.info("Provider discovered and initialized", provider=name, priority=priority)
            else:
                logger.debug("Provider not available (no API key?)", provider=name)
        except Exception as exc:
            logger.warning("Provider initialization failed", provider=name, error=str(exc))

    return providers


class BrainOrchestrator:
    """The AI Brain — orchestrates the complete execution pipeline.

    Features:
        - Automatic provider discovery on startup
        - Priority-based provider selection
        - Automatic failover on provider failure
        - Memory integration (retrieve/store)
        - Agent routing (intent detection)
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
        """Initialize the Brain with auto-discovered providers."""
        if self._initialized:
            return

        self._providers = await _discover_providers()

        if not self._providers:
            logger.warning("No AI providers available — Brain will wait for provider configuration")

        self._initialized = True
        logger.info(
            "Brain orchestrator initialized",
            providers=list(self._providers.keys()),
            count=len(self._providers),
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

        Priority: explicit request > first initialized provider (by priority).

        Raises:
            RuntimeError: If no providers are available.
        """
        if not self._providers:
            raise RuntimeError("No AI providers available. Configure at least one API key.")

        if requested_provider and requested_provider in self._providers:
            return self._providers[requested_provider]

        # Return first available (they're ordered by priority in discovery)
        return next(iter(self._providers.values()))

    def _get_failover_providers(self, exclude: str) -> list[BaseProvider]:
        """Get alternative providers for failover, excluding the failed one."""
        return [p for name, p in self._providers.items() if name != exclude]

    def _select_model(self, provider: BaseProvider, requested_model: str | None) -> str:
        """Select model for the request."""
        if requested_model:
            return requested_model
        return provider.config.default_model

    async def process(self, request: BrainRequest) -> BrainResponse:
        """Process a chat request through the full AI pipeline with failover.

        Pipeline:
            1. Retrieve conversation history (memory)
            2. Detect agent type (routing)
            3. Build context window (context assembly)
            4. Select provider + model
            5. Execute LLM request (with failover on failure)
            6. Save response to memory
            7. Return response
        """
        start = time.perf_counter()

        # Step 1: Memory
        history = retrieve_conversation_history(request.session_id)

        # Step 2: Agent routing
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

        # Step 5: Execute with failover
        chat_messages = [
            ChatMessage(role=MessageRole(msg.role), content=msg.content, name=msg.name)
            for msg in context_messages
        ]
        chat_request = ChatRequest(
            messages=chat_messages,
            model=model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        response = None
        used_provider = provider.provider_id.value

        try:
            response = await provider.chat(chat_request)
        except Exception as primary_exc:
            logger.warning(
                "Primary provider failed, attempting failover",
                provider=used_provider,
                error=str(primary_exc),
            )
            # Failover: try other providers
            for fallback in self._get_failover_providers(used_provider):
                try:
                    fallback_model = fallback.config.default_model
                    fallback_request = ChatRequest(
                        messages=chat_messages,
                        model=fallback_model,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens,
                    )
                    response = await fallback.chat(fallback_request)
                    used_provider = fallback.provider_id.value
                    model = fallback_model
                    logger.info("Failover successful", provider=used_provider)
                    break
                except Exception as fb_exc:
                    logger.warning(
                        "Failover provider also failed",
                        provider=fallback.provider_id.value,
                        error=str(fb_exc),
                    )

            if response is None:
                raise RuntimeError(
                    f"All providers failed. Primary error: {primary_exc}"
                ) from primary_exc

        latency_ms = (time.perf_counter() - start) * 1000

        # Step 6: Save to memory
        if request.session_id:
            last_user = next((m for m in reversed(request.messages) if m.role == "user"), None)
            if last_user:
                save_message_to_memory(
                    session_id=request.session_id, role="user", content=last_user.content
                )
            save_message_to_memory(
                session_id=request.session_id,
                role="assistant",
                content=response.content,
                model=model,
                token_count=response.token_usage.completion_tokens,
            )

        # Step 7: Build response
        return BrainResponse(
            content=response.content,
            model=response.model,
            provider=used_provider,
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
        """Process a streaming chat request with failover."""
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
            ChatMessage(role=MessageRole(msg.role), content=msg.content, name=msg.name)
            for msg in context_messages
        ]
        chat_request = ChatRequest(
            messages=chat_messages,
            model=model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True,
        )

        full_content: list[str] = []

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
                    yield BrainStreamChunk(
                        event="done",
                        model=model,
                        finish_reason="stop",
                        token_usage=TokenUsageSchema(
                            prompt_tokens=prompt_tokens,
                            completion_tokens=eval_count,
                            total_tokens=prompt_tokens + eval_count,
                        ),
                    )
                elif chunk.event == StreamEvent.ERROR:
                    yield BrainStreamChunk(event="error", content=chunk.content, model=model)
                    return
        except Exception as exc:
            yield BrainStreamChunk(event="error", content=str(exc), model=model)
            return

        # Save to memory
        if request.session_id and full_content:
            last_user = next((m for m in reversed(request.messages) if m.role == "user"), None)
            if last_user:
                save_message_to_memory(
                    session_id=request.session_id, role="user", content=last_user.content
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
                    "Failed to list models",
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


# Global singleton
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
