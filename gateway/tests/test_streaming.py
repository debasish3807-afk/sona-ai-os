"""Tests for SSE streaming functionality."""

import json

import pytest

from app.pipeline.streaming import sse_generator


class TestSSEGenerator:
    """Tests for the SSE stream generator."""

    @pytest.mark.asyncio
    async def test_generates_data_lines(self) -> None:
        """SSE generator produces data: lines for each token."""

        async def token_source() -> None:
            yield "Hello"
            yield " world"

        chunks: list[str] = []
        async for chunk in sse_generator(token_source(), "req-1", "test-model"):
            chunks.append(chunk)

        # At least: 2 content chunks + 1 final chunk + 1 DONE
        assert len(chunks) >= 4

    @pytest.mark.asyncio
    async def test_done_marker_at_end(self) -> None:
        """SSE stream ends with data: [DONE]."""

        async def token_source() -> None:
            yield "token"

        chunks: list[str] = []
        async for chunk in sse_generator(token_source(), "req-1", "test-model"):
            chunks.append(chunk)

        assert chunks[-1] == "data: [DONE]\n\n"

    @pytest.mark.asyncio
    async def test_content_chunks_are_valid_json(self) -> None:
        """Each content chunk is valid JSON with OpenAI-compatible structure."""

        async def token_source() -> None:
            yield "Hi"

        chunks: list[str] = []
        async for chunk in sse_generator(token_source(), "req-123", "llama3.2"):
            chunks.append(chunk)

        # First chunk should be the content token
        payload = json.loads(chunks[0][6:].strip())  # Strip "data: " and newlines
        assert payload["id"] == "req-123"
        assert payload["object"] == "chat.completion.chunk"
        assert payload["model"] == "llama3.2"
        assert payload["choices"][0]["delta"]["content"] == "Hi"
        assert payload["choices"][0]["index"] == 0

    @pytest.mark.asyncio
    async def test_final_chunk_has_stop_reason(self) -> None:
        """The chunk before [DONE] has finish_reason='stop'."""

        async def token_source() -> None:
            yield "done"

        chunks: list[str] = []
        async for chunk in sse_generator(token_source(), "req-1", "model"):
            chunks.append(chunk)

        # Second-to-last chunk (before [DONE]) should have finish_reason
        final_data = chunks[-2]
        payload = json.loads(final_data[6:].strip())
        assert payload["choices"][0]["finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_empty_stream(self) -> None:
        """An empty token stream still produces final chunk and DONE."""

        async def token_source() -> None:
            return
            yield  # noqa: RET503 — make it an async generator

        chunks: list[str] = []
        async for chunk in sse_generator(token_source(), "req-1", "model"):
            chunks.append(chunk)

        # Should have at least: final stop chunk + DONE
        assert len(chunks) >= 2
        assert chunks[-1] == "data: [DONE]\n\n"

    @pytest.mark.asyncio
    async def test_multiple_tokens(self) -> None:
        """Multiple tokens produce multiple data lines."""

        async def token_source() -> None:
            for word in ["The", " quick", " fox"]:
                yield word

        chunks: list[str] = []
        async for chunk in sse_generator(token_source(), "req-1", "model"):
            chunks.append(chunk)

        # 3 content chunks + 1 stop chunk + 1 DONE = 5
        assert len(chunks) == 5
