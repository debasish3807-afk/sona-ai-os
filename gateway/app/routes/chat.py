"""Chat completion endpoints."""

from fastapi import APIRouter

from app.models.chat import ChatRequest, ChatResponse, ChatMessage, TokenUsage

router = APIRouter()


@router.post("/chat/completions", response_model=ChatResponse)
async def create_chat_completion(request: ChatRequest) -> ChatResponse:
    """Create a chat completion.

    This is a scaffolding endpoint. The actual LLM routing logic
    will be implemented by the brain-os and thalamus-router services.
    """
    # Placeholder response - actual routing implemented in brain-os
    return ChatResponse(
        messages=[
            ChatMessage(
                role="assistant",
                content="Gateway placeholder response. Route to brain-os for actual processing.",
            )
        ],
        model=request.model,
        usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
        finish_reason="stop",
    )
