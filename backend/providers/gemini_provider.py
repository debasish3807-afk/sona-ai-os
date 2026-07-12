"""Google Gemini provider — Gemini 2.0 Flash, 1.5 Pro, 1.5 Flash.

Gemini uses a unique API format. This provider handles the translation
between Sona's unified interface and Google's generateContent API.
Env var: GEMINI_API_KEY
"""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from config.logging import get_logger
from providers.base import BaseProvider
from providers.capabilities import (
    Capability,
    CapabilityDescriptor,
    CapabilityLevel,
    CapabilitySet,
)
from providers.config import GeminiConfig, ProviderConfig
from providers.http_client import load_api_key
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


GEMINI_MODELS: list[ModelInfo] = [
    ModelInfo(
        model_id="gemini-2.0-flash",
        name="Gemini 2.0 Flash",
        provider="gemini",
        max_context_tokens=1048576,
        max_output_tokens=8192,
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        cost_per_input_token=0.10 / 1_000_000,
        cost_per_output_token=0.40 / 1_000_000,
    ),
    ModelInfo(
        model_id="gemini-1.5-pro",
        name="Gemini 1.5 Pro",
        provider="gemini",
        max_context_tokens=2097152,
        max_output_tokens=8192,
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        cost_per_input_token=1.25 / 1_000_000,
        cost_per_output_token=5.00 / 1_000_000,
    ),
    ModelInfo(
        model_id="gemini-1.5-flash",
        name="Gemini 1.5 Flash",
        provider="gemini",
        max_context_tokens=1048576,
        max_output_tokens=8192,
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        cost_per_input_token=0.075 / 1_000_000,
        cost_per_output_token=0.30 / 1_000_000,
    ),
]


def _convert_messages_for_gemini(
    messages: list[ChatMessage],
) -> tuple[str | None, list[dict[str, Any]]]:
    """Convert messages to Gemini format."""
    system_instruction: str | None = None
    contents: list[dict[str, Any]] = []

    for msg in messages:
        if msg.role.value == "system":
            system_instruction = msg.content
        else:
            role = "user" if msg.role.value == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.content}]})

    return system_instruction, contents


class GeminiProvider(BaseProvider):
    """Google Gemini provider — full generateContent API implementation.

    Capabilities: chat, streaming, vision, tool calling.
    Authentication: GEMINI_API_KEY environment variable.
    """

    def __init__(self, config: GeminiConfig | None = None) -> None:
        self._config = config or GeminiConfig()
        self._initialized = False
        self._api_key: str | None = None
        self._client: httpx.AsyncClient | None = None
        self._capabilities = CapabilitySet(
            provider_id=ProviderID.GEMINI,
            capabilities=[
                CapabilityDescriptor(Capability.CHAT_COMPLETION, CapabilityLevel.EXPERT),
                CapabilityDescriptor(Capability.STREAMING, CapabilityLevel.EXPERT),
                CapabilityDescriptor(Capability.EMBEDDINGS, CapabilityLevel.ADVANCED),
                CapabilityDescriptor(Capability.CODE_GENERATION, CapabilityLevel.EXPERT),
                CapabilityDescriptor(Capability.FUNCTION_CALLING, CapabilityLevel.ADVANCED),
            ],
        )

    @property
    def provider_id(self) -> ProviderID:
        return ProviderID.GEMINI

    @property
    def display_name(self) -> str:
        return "Google Gemini"

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
        self._api_key = load_api_key(self._config.api_key_env_var)
        if not self._api_key:
            logger.info("Gemini API key not found, provider disabled")
            self._initialized = False
            return
        base = self._config.base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=base,
            timeout=httpx.Timeout(self._config.timeout_seconds, connect=10.0),
        )
        self._initialized = True
        logger.info("Gemini provider initialized")

    async def shutdown(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._initialized = False

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Gemini provider not initialized")
        return self._client

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Execute chat via Gemini generateContent."""
        client = self._get_client()
        model = request.model or self._config.default_model
        system_instruction, contents = _convert_messages_for_gemini(request.messages)

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
                "topP": request.top_p,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        if request.stop:
            payload["generationConfig"]["stopSequences"] = request.stop

        url = f"/models/{model}:generateContent?key={self._api_key}"
        start = time.perf_counter()
        resp = await client.post(url, json=payload)
        latency_ms = (time.perf_counter() - start) * 1000

        if resp.status_code >= 400:
            raise RuntimeError(f"Gemini error: {resp.status_code} {resp.text[:200]}")

        data = resp.json()
        candidates = data.get("candidates", [{}])
        content = ""
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            content = "".join(p.get("text", "") for p in parts)

        usage_meta = data.get("usageMetadata", {})
        prompt_tokens = usage_meta.get("promptTokenCount", 0)
        completion_tokens = usage_meta.get("candidatesTokenCount", 0)

        return ChatResponse(
            content=content,
            model=model,
            provider=self.provider_id.value,
            finish_reason=FinishReason.STOP,
            token_usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            latency_ms=latency_ms,
        )

    async def stream(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        """Stream chat via Gemini streamGenerateContent."""
        client = self._get_client()
        model = request.model or self._config.default_model
        system_instruction, contents = _convert_messages_for_gemini(request.messages)

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        url = f"/models/{model}:streamGenerateContent?alt=sse&key={self._api_key}"
        yield StreamChunk(event=StreamEvent.START, model=model)

        try:
            async with client.stream("POST", url, json=payload) as resp:
                if resp.status_code >= 400:
                    yield StreamChunk(
                        event=StreamEvent.ERROR,
                        content=f"Gemini error: {resp.status_code}",
                        model=model,
                    )
                    return
                async for line in resp.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    try:
                        chunk_data = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
                    candidates = chunk_data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        text = "".join(p.get("text", "") for p in parts)
                        if text:
                            yield StreamChunk(event=StreamEvent.DELTA, content=text, model=model)

            yield StreamChunk(event=StreamEvent.DONE, model=model, finish_reason=FinishReason.STOP)
        except Exception as exc:
            yield StreamChunk(
                event=StreamEvent.ERROR, content=f"Gemini stream error: {exc}", model=model
            )

    async def embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings via Gemini embedContent."""
        client = self._get_client()
        model = request.model or "text-embedding-004"
        all_embeddings: list[list[float]] = []
        total_tokens = 0

        for text in request.input:
            url = f"/models/{model}:embedContent?key={self._api_key}"
            payload = {"model": f"models/{model}", "content": {"parts": [{"text": text}]}}
            resp = await client.post(url, json=payload)
            if resp.status_code >= 400:
                raise RuntimeError(f"Gemini embeddings failed: {resp.status_code}")
            data = resp.json()
            embedding = data.get("embedding", {}).get("values", [])
            all_embeddings.append(embedding)
            total_tokens += len(text) // 4

        return EmbeddingResponse(
            embeddings=all_embeddings,
            model=model,
            provider=self.provider_id.value,
            token_usage=TokenUsage(prompt_tokens=total_tokens, total_tokens=total_tokens),
            dimensions=len(all_embeddings[0]) if all_embeddings else 0,
        )

    async def list_models(self) -> list[ModelInfo]:
        return GEMINI_MODELS.copy()

    async def get_model(self, model_id: str) -> ModelInfo | None:
        for m in GEMINI_MODELS:
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
        if not self._client or not self._api_key:
            return False
        try:
            url = f"/models?key={self._api_key}"
            resp = await self._client.get(url, timeout=10.0)
            return resp.status_code < 400
        except Exception:
            return False
