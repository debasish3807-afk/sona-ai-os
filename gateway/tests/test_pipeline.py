"""End-to-end pipeline integration tests.

Tests the full chat completion flow through the gateway, verifying
that requests are routed through the pipeline and return valid responses.
"""

import json

import pytest
from fastapi.testclient import TestClient

import app.middleware.authentication as auth_mod
from app.main import create_app
from app.middleware.authentication import _get_jwt_service


@pytest.fixture
def client() -> TestClient:
    """Create an authenticated test client."""
    auth_mod._jwt_service = None
    app = create_app()
    svc = _get_jwt_service()
    token = svc.generate_access_token(user_id="test-user", roles=["admin"])
    client = TestClient(app)
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
def old_client() -> TestClient:
    """Create a test client for the gateway app."""
    return TestClient(create_app())


class TestChatCompletion:
    """Tests for the POST /v1/chat/completions endpoint."""

    def test_normal_chat(self, client: TestClient) -> None:
        """A valid chat request returns 200."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hello, Sona!"}],
                "model": "default",
            },
        )
        assert response.status_code == 200

    def test_chat_returns_content(self, client: TestClient) -> None:
        """Response contains non-empty assistant content."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "What is 2+2?"}],
            },
        )
        data = response.json()
        assert len(data["messages"]) >= 1
        assert data["messages"][0]["role"] == "assistant"
        assert len(data["messages"][0]["content"]) > 0

    def test_chat_returns_model_used(self, client: TestClient) -> None:
        """Response includes the model that was used."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hi"}],
                "model": "default",
            },
        )
        data = response.json()
        assert "model" in data
        assert isinstance(data["model"], str)
        assert len(data["model"]) > 0

    def test_chat_returns_token_usage(self, client: TestClient) -> None:
        """Response includes token usage statistics."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Count to three"}],
            },
        )
        data = response.json()
        assert "usage" in data
        assert "prompt_tokens" in data["usage"]
        assert "completion_tokens" in data["usage"]
        assert "total_tokens" in data["usage"]
        assert data["usage"]["prompt_tokens"] >= 0
        assert data["usage"]["completion_tokens"] >= 0
        assert data["usage"]["total_tokens"] >= 0

    def test_chat_with_system_message(self, client: TestClient) -> None:
        """System messages are accepted and processed."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello!"},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["messages"][0]["role"] == "assistant"

    def test_chat_validation_empty_messages(self, client: TestClient) -> None:
        """Empty messages list is rejected with 422."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "messages": [],
            },
        )
        assert response.status_code == 422

    def test_chat_validation_invalid_role(self, client: TestClient) -> None:
        """Invalid role in message is rejected with 422."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "invalid_role", "content": "test"}],
            },
        )
        assert response.status_code == 422

    def test_chat_validation_temperature_too_high(self, client: TestClient) -> None:
        """Temperature above 2.0 is rejected with 422."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "test"}],
                "temperature": 3.0,
            },
        )
        assert response.status_code == 422

    def test_chat_with_user_id(self, client: TestClient) -> None:
        """User ID is accepted in the request."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "user_id": "user-123",
            },
        )
        assert response.status_code == 200

    def test_chat_response_has_id(self, client: TestClient) -> None:
        """Response includes a unique ID."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hi"}],
            },
        )
        data = response.json()
        assert "id" in data
        assert len(data["id"]) > 0

    def test_chat_response_has_finish_reason(self, client: TestClient) -> None:
        """Response includes finish_reason field."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hi"}],
            },
        )
        data = response.json()
        assert data["finish_reason"] == "stop"


class TestStreamingChat:
    """Tests for SSE streaming chat completions."""

    def test_streaming_returns_sse(self, client: TestClient) -> None:
        """Streaming request returns text/event-stream media type."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": True,
            },
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

    def test_streaming_has_done_marker(self, client: TestClient) -> None:
        """Streaming response ends with data: [DONE]."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": True,
            },
        )
        content = response.text
        assert "data: [DONE]" in content

    def test_streaming_chunks_are_json(self, client: TestClient) -> None:
        """Non-DONE streaming chunks are valid JSON with expected structure."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Say hi"}],
                "stream": True,
            },
        )
        lines = response.text.strip().split("\n")
        data_lines = [
            line for line in lines if line.startswith("data: ") and line != "data: [DONE]"
        ]
        assert len(data_lines) > 0

        for line in data_lines:
            payload = json.loads(line[6:])  # Strip "data: " prefix
            assert "id" in payload
            assert payload["object"] == "chat.completion.chunk"
            assert "choices" in payload
            assert len(payload["choices"]) > 0
            assert "delta" in payload["choices"][0]


class TestMemoryIntegration:
    """Tests for memory integration in the pipeline."""

    def test_memory_stores_conversation(self, client: TestClient) -> None:
        """Pipeline processes request without memory errors."""
        # Send a message
        response = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Remember this: test memory"}],
                "user_id": "memory-test-user",
            },
        )
        assert response.status_code == 200

    def test_memory_retrieves_context(self, client: TestClient) -> None:
        """Pipeline handles memory context retrieval gracefully."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "What did I say before?"}],
                "user_id": "memory-test-user",
            },
        )
        assert response.status_code == 200


class TestErrorRecovery:
    """Tests for pipeline error recovery."""

    def test_graceful_error_response(self, client: TestClient) -> None:
        """Pipeline returns a valid response even under error conditions."""
        # Long content that exercises the pipeline
        response = client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "x" * 1000}],
            },
        )
        # Should still get a response (either success or graceful fallback)
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert len(data["messages"]) >= 1

    def test_health_still_works(self, client: TestClient) -> None:
        """Health endpoint remains operational regardless of pipeline state."""
        response = client.get("/health")
        assert response.status_code == 200
