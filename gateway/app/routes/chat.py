"""Chat completion endpoints with full pipeline integration.

Replaces the placeholder endpoint with a real end-to-end pipeline
flowing through Memory OS, THALAMUS, Brain OS, and AI Kernel.
"""

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.deps import get_pipeline
from app.models.chat import ChatMessage, ChatRequest, ChatResponse, TokenUsage
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.streaming import sse_generator

router = APIRouter()


@router.post("/chat/completions", response_model=ChatResponse)
async def create_chat_completion(
    request: ChatRequest,
    pipeline: PipelineOrchestrator = Depends(get_pipeline),
) -> ChatResponse | StreamingResponse:
    """Create a chat completion flowing through the full AI pipeline.

    POST /v1/chat/completions

    The request flows through:
    1. Gateway receives ChatRequest
    2. Creates session/request/trace IDs
    3. Retrieves conversation memory (Memory OS)
    4. Routes through THALAMUS (intent + execution plan)
    5. Executes via Brain OS (orchestrates plan)
    6. Brain calls AI Kernel (LLM inference)
    7. Brain stores response in Memory OS
    8. Returns ChatResponse (or streams via SSE)
    """
    session_id = str(uuid.uuid4())
    user_id = request.user_id or "anonymous"
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    if request.stream:
        request_id = str(uuid.uuid4())
        token_stream = pipeline.execute_stream(
            messages=messages,
            user_id=user_id,
            session_id=session_id,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        return StreamingResponse(
            sse_generator(token_stream, request_id, request.model),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    result = await pipeline.execute(
        messages=messages,
        user_id=user_id,
        session_id=session_id,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    return ChatResponse(
        messages=[ChatMessage(role="assistant", content=result.content)],
        model=result.model_used,
        usage=TokenUsage(
            prompt_tokens=result.tokens_input,
            completion_tokens=result.tokens_output,
            total_tokens=result.tokens_input + result.tokens_output,
        ),
        finish_reason="stop",
    )
