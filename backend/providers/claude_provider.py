"""Anthropic Claude provider — Claude Sonnet 4, Claude 3.5, Opus.

Claude uses a unique Messages API (not OpenAI-compatible), so this
provider has its own implementation while still conforming to BaseProvider.
Env var: ANTHROPIC_API_KEY
"""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from typing import Any

from config.logging import get_logger
from providers.base import BaseProvider
from providers.capabilities import (
    Capability,
    CapabilityDescriptor,
    CapabilityLevel,
    CapabilitySet,
)
from providers.config import ClaudeConfig, ProviderConfig
from providers.http_client import ProviderClient, load_api_key
from providers.types import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    FinishReason,
    ModelInfo,
    ProviderID,
    StreamChunk,
    StreamEvent,
    TokenUsage,
)

logger = get_logger(__name__)

# Claude static model catalog (no /models endpoint available)
CLAUDE_MODELS: list[ModelInfo] = [
    ModelInfo(
        model_id="claude-sonnet-4-20250514",
        name="Claude Sonnet 4",
        provider="claude",
        max_context_tokens=200000,
        max_output_tokens=8192,
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        cost_per_input_token=3.0 / 1_000_000,
        cost_per_output_token=15.0 / 1_000_000,
    ),
    ModelInfo(
        model_id="claude-3-5-sonnet-20241022",
        name="Claude 3.5 Sonnet",
        provider="claude",
        max_context_tokens=200000,
        max_output_tokens=8192,
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        cost_per_input_token=3.0 / 1_000_000,
        cost_per_output_token=15.0 / 1_000_000,
    ),
    ModelInfo(
        model_id="claude-3-5-haiku-20241022",
        name="Claude 3.5 Haiku",
        provider="claude",
        max_context_tokens=200000,
        max_output_tokens=8192,
        supports_streaming=True,
        supports_tools=True,
        cost_per_input_token=0.8 / 1_000_000,
        cost_per_output_token=4.0 / 1_000_000,
    ),
    ModelInfo(
        model_id="claude-3-opus-20240229",
        name="Claude 3 Opus",
        provider="claude",
        max_context_tokens=200000,
        max_output_tokens=4096,
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        cost_per_input_token=15.0 / 1_000_000,
        cost_per_output_token=75.0 / 1_000_000,
    ),
]


def _convert_messages_for_claude(
    messages: list[ChatMessage],
) -> tuple[str | None, list[dict[str, str]]]:
    """Convert messages to Claude format (separate system from messages)."""
    system_prompt: str | None = None
    converted: list[dict[str, str]] = []

    for msg in messages:
        if msg.role.value == "system":
            system_prompt = msg.content
        else:
            role = "user" if msg.role.value == "user" else "assistant"
            converted.append({"role": role, "content": msg.content})

    return system_prompt, converted


class ClaudeProvider(BaseProvider):
    """Anthropic Claude provider — full Messages API implementation.

    Capabilities: chat, streaming, vision, tool calling.
    Authentication: ANTHROPIC_API_KEY environment variable.
    """

    def __init__(self, config: ClaudeConfig | None = None) -> None:
        self._config = config or ClaudeConfig()
        self._initialized = False
        self._http: ProviderClient | None = None
        self._capabilities = CapabilitySet(
            provider_id=ProviderID.CLAUDE,
            capabilities=[
                CapabilityDescriptor(Capability.CHAT_COMPLETION, CapabilityLevel.EXPERT),
                CapabilityDescriptor(Capability.STREAMING, CapabilityLevel.EXPERT),
                CapabilityDescriptor(Capability.CODE_GENERATION, CapabilityLevel.EXPERT),
                CapabilityDescriptor(Capability.FUNCTION_CALLING, CapabilityLevel.ADVANCED),
            ],
        )

    @property
    def provider_id(self) -> ProviderID:
        return ProviderID.CLAUDE

    @property
    def display_name(self) -> str:
        return "Anthropic Claude"

    @property
    def config(self) -> ProviderConfig:
        return self._config

    @property
    def capabilities(self) -> CapabilitySet:
        return self._capabilities

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    async def initialize(self) -> None:
        """Load API key and create HTTP client with Claude-specific headers."""
        api_key = load_api_key(self._config.api_key_env_var)
        if not api_key:
            logger.info(
                "Claude API key not found, provider disabled",
                env_var=self._config.api_key_env_var,
            )
            self._initialized = False
            return

        # Claude uses x-api-key header instead of Bearer token
        self._http = ProviderClient(self._config, api_key=None)
        await self._http.initialize()
        # Override headers for Claude's auth scheme
        if self._http._client:
            self._http._client.headers.update(
                {
                    "x-api-key": api_key,
                    "anthropic-version": self._config.api_version or "2024-01-01",
                    "Content-Type": "application/json",
                }
            )
        self._initialized = True
        logger.info("Claude provider initialized")

    async def shutdown(self) -> None:
        if self._http:
            await self._http.close()
            self._http = None
        self._initialized = False

    def _get_http(self) -> ProviderClient:
        if self._http is None:
            raise RuntimeError("Claude provider not initialized")
        return self._http

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Execute chat via Claude Messages API."""
        http = self._get_http()
        model = request.model or self._config.default_model
        system_prompt, messages = _convert_messages_for_claude(request.messages)

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
        }
        if system_prompt:
            payload["system"] = system_prompt
        if request.stop:
            payload["stop_sequences"] = request.stop

        start = time.perf_counter()
        data = await http.post("/messages", payload)
        latency_ms = (time.perf_counter() - start) * 1000

        # Extract content from Claude's response format
        content_blocks = data.get("content", [])
        content = "".join(
            block.get("text", "") for block in content_blocks if block.get("type") == "text"
        )
        usage = data.get("usage", {})
        stop_reason = data.get("stop_reason", "end_turn")
        finish = FinishReason.STOP if stop_reason == "end_turn" else FinishReason.LENGTH

        return ChatResponse(
            content=content,
            model=data.get("model", model),
            provider=self.provider_id.value,
            response_id=data.get("id", ""),
            finish_reason=finish,
            token_usage=TokenUsage(
                prompt_tokens=usage.get("input_tokens", 0),
                completion_tokens=usage.get("output_tokens", 0),
                total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            ),
            latency_ms=latency_ms,
        )

    async def stream(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        """Stream chat via Claude Messages API with SSE."""
        http = self._get_http()
        model = request.model or self._config.default_model
        system_prompt, messages = _convert_messages_for_claude(request.messages)

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": True,
        }
        if system_prompt:
            payload["system"] = system_prompt

        yield StreamChunk(event=StreamEvent.START, model=model)

        try:
            resp = await http.post_stream("/messages", payload)
            try:
                async for line in resp.aiter_lines():
                    line = line.strip()
                    if not line or line.startswith("event:"):
                        continue
                    if line.startswith("data: "):
                        line = line[6:]
                    try:
                        event_data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    event_type = event_data.get("type", "")

                    if event_type == "content_block_delta":
                        delta = event_data.get("delta", {})
                        text = delta.get("text", "")
                        if text:
                            yield StreamChunk(event=StreamEvent.DELTA, content=text, model=model)

                    elif event_type == "message_delta":
                        usage = event_data.get("usage", {})
                        yield StreamChunk(
                            event=StreamEvent.DONE,
                            model=model,
                            finish_reason=FinishReason.STOP,
                            metadata={
                                "prompt_eval_count": usage.get("input_tokens", 0),
                                "eval_count": usage.get("output_tokens", 0),
                            },
                        )
            finally:
                await resp.aclose()
        except Exception as exc:
            yield StreamChunk(
                event=StreamEvent.ERROR,
                content=f"Claude stream error: {exc}",
                model=model,
            )

    async def embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Claude does not support embeddings."""
        raise NotImplementedError("Anthropic Claude does not provide an embeddings API")

    async def list_models(self) -> list[ModelInfo]:
        """Return static model catalog."""
        return CLAUDE_MODELS.copy()

    async def get_model(self, model_id: str) -> ModelInfo | None:
        for m in CLAUDE_MODELS:
            if m.model_id == model_id:
                return m
        return None

    def supports_tools(self) -> bool:
        return True

    def supports_vision(self) -> bool:
        return True

    def supports_function_calling(self) -> bool:
        return True

    def supports_streaming(self) -> bool:
        return True

    async def health(self) -> bool:
        """Health check by sending a minimal request."""
        if not self._http:
            return False
        try:
            # Claude has no /models endpoint; check by sending minimal message
            http = self._get_http()
            client = http._get_client()
            resp = await client.post(
                "/messages",
                json={
                    "model": self._config.default_model,
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "hi"}],
                },
                timeout=10.0,
            )
            return bool(resp.status_code < 500)
        except Exception:
            return False
