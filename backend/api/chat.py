"""Chat API endpoints — the public interface to the AI Brain.

Endpoints:
    POST /chat         — Synchronous chat completion
    POST /chat/stream  — Server-Sent Events streaming chat
    GET  /models       — List available models
    GET  /providers    — List available providers
    GET  /health/providers — Provider health check
"""

from __future__ import annotations

import json
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from brain.orchestrator import get_brain
from brain.schemas import (
    ChatEndpointRequest,
    ChatEndpointResponse,
    ModelInfoSchema,
    ModelListResponse,
    ProviderHealthDetail,
    ProviderHealthResponse,
    ProviderInfoSchema,
    ProviderListResponse,
)
from config.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatEndpointResponse)
async def chat_completion(request: ChatEndpointRequest) -> ChatEndpointResponse:
    """Process a chat completion request.

    Executes the full AI Brain pipeline:
    1. Memory retrieval (conversation history)
    2. Agent routing (intent detection)
    3. Context assembly
    4. LLM execution via provider
    5. Memory storage
    6. Response generation

    Returns:
        ChatEndpointResponse with generated content and metadata.
    """
    brain = get_brain()
    if not brain.is_initialized:
        raise HTTPException(status_code=503, detail="AI Brain not initialized")

    from brain.schemas import BrainRequest

    brain_request = BrainRequest(
        messages=request.messages,
        model=request.model,
        provider=request.provider,
        session_id=request.session_id,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        system_prompt=request.system_prompt,
    )

    try:
        response = await brain.process(brain_request)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Chat completion failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Internal AI processing error") from exc

    return ChatEndpointResponse(
        response_id=response.response_id,
        content=response.content,
        model=response.model,
        provider=response.provider,
        agent=response.agent,
        finish_reason=response.finish_reason,
        token_usage=response.token_usage,
        latency_ms=response.latency_ms,
        session_id=response.session_id,
    )


@router.post("/chat/stream")
async def chat_completion_stream(request: ChatEndpointRequest) -> StreamingResponse:
    """Process a streaming chat completion request via SSE.

    Yields Server-Sent Events (SSE) with real-time token generation.
    Each event contains a JSON payload with content deltas.

    Returns:
        StreamingResponse with text/event-stream content type.
    """
    brain = get_brain()
    if not brain.is_initialized:
        raise HTTPException(status_code=503, detail="AI Brain not initialized")

    from brain.schemas import BrainRequest

    brain_request = BrainRequest(
        messages=request.messages,
        model=request.model,
        provider=request.provider,
        session_id=request.session_id,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        system_prompt=request.system_prompt,
    )

    async def event_generator():
        """Generate SSE events from the Brain stream."""
        try:
            async for chunk in brain.process_stream(brain_request):
                data = chunk.model_dump(exclude_none=True)
                yield f"data: {json.dumps(data)}\n\n"
        except Exception as exc:
            error_data = {"event": "error", "content": str(exc)}
            yield f"data: {json.dumps(error_data)}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/models", response_model=ModelListResponse)
async def list_models() -> ModelListResponse:
    """List all available models across all providers.

    Returns model metadata including capabilities and context window sizes.
    """
    brain = get_brain()
    if not brain.is_initialized:
        raise HTTPException(status_code=503, detail="AI Brain not initialized")

    try:
        models = await brain.list_models()
    except Exception as exc:
        logger.error("Failed to list models", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to retrieve model list") from exc

    model_schemas = [
        ModelInfoSchema(
            model_id=m.model_id,
            name=m.name,
            provider=m.provider,
            model_type=m.model_type.value,
            max_context_tokens=m.max_context_tokens,
            supports_streaming=m.supports_streaming,
            supports_tools=m.supports_tools,
            supports_vision=m.supports_vision,
        )
        for m in models
    ]

    return ModelListResponse(
        models=model_schemas,
        total=len(model_schemas),
    )


@router.get("/providers", response_model=ProviderListResponse)
async def list_providers() -> ProviderListResponse:
    """List all configured providers with their status."""
    brain = get_brain()
    if not brain.is_initialized:
        raise HTTPException(status_code=503, detail="AI Brain not initialized")

    health = await brain.get_provider_health()
    providers: list[ProviderInfoSchema] = []

    for name, provider in brain.available_providers.items():
        try:
            models = await provider.list_models()
            models_count = len(models)
        except Exception:
            models_count = 0

        providers.append(
            ProviderInfoSchema(
                provider_id=name,
                name=provider.display_name,
                enabled=provider.is_initialized,
                healthy=health.get(name, False),
                models_count=models_count,
            )
        )

    return ProviderListResponse(providers=providers)


@router.get("/health/providers", response_model=ProviderHealthResponse)
async def provider_health() -> ProviderHealthResponse:
    """Check health of all AI providers.

    Returns per-provider health status with latency measurements.
    """
    brain = get_brain()
    if not brain.is_initialized:
        return ProviderHealthResponse(providers=[])

    details: list[ProviderHealthDetail] = []
    for name, provider in brain.available_providers.items():
        start = time.perf_counter()
        error_msg: str | None = None
        try:
            healthy = await provider.health()
        except Exception as exc:
            healthy = False
            error_msg = str(exc)
        latency_ms = (time.perf_counter() - start) * 1000

        details.append(
            ProviderHealthDetail(
                provider_id=name,
                name=provider.display_name,
                healthy=healthy,
                latency_ms=round(latency_ms, 2),
                error=error_msg,
            )
        )

    return ProviderHealthResponse(providers=details)
