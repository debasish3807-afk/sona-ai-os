"""Server-Sent Events streaming for chat completions.

Implements OpenAI-compatible SSE streaming format for real-time
token delivery to clients.
"""

import json
import time
from collections.abc import AsyncIterator

import structlog
from fastapi.responses import StreamingResponse

logger = structlog.get_logger()


async def stream_chat_response(
    token_stream: AsyncIterator[str],
    request_id: str,
    model: str,
) -> StreamingResponse:
    """Create an SSE streaming response from a token stream.

    Args:
        token_stream: Async iterator yielding string tokens.
        request_id: Request ID for the response chunks.
        model: Model name for the response metadata.

    Returns:
        A FastAPI StreamingResponse with SSE media type.
    """
    return StreamingResponse(
        sse_generator(token_stream, request_id, model),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def sse_generator(
    token_stream: AsyncIterator[str],
    request_id: str,
    model: str,
) -> AsyncIterator[str]:
    """Generate SSE-formatted events from tokens.

    Produces OpenAI-compatible streaming format:
    data: {"id":"...","object":"chat.completion.chunk","choices":[{"delta":{"content":"token"},"index":0}]}

    Terminates with:
    data: [DONE]

    Args:
        token_stream: Async iterator yielding string tokens.
        request_id: Request ID for chunk identification.
        model: Model name for response metadata.

    Yields:
        SSE-formatted string events.
    """
    created = int(time.time())

    try:
        async for token in token_stream:
            chunk = {
                "id": request_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": token},
                        "finish_reason": None,
                    }
                ],
            }
            yield f"data: {json.dumps(chunk)}\n\n"

        # Send final chunk with finish_reason
        final_chunk = {
            "id": request_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop",
                }
            ],
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"

        # Send done marker
        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(
            "sse_stream_error",
            request_id=request_id,
            error=str(e),
        )
        # Send error and done
        error_chunk = {
            "id": request_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "error",
                }
            ],
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
        yield "data: [DONE]\n\n"
