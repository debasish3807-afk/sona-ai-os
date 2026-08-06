"""Tests for gateway chat request/response models."""

import pytest
from pydantic import ValidationError

from app.models.chat import ChatMessage, ChatRequest, ChatResponse, ChatRole, TokenUsage


class TestChatRole:
    """Tests for the ChatRole enum."""

    def test_valid_roles(self):
        assert ChatRole.USER == "user"
        assert ChatRole.ASSISTANT == "assistant"
        assert ChatRole.SYSTEM == "system"

    def test_enum_count(self):
        assert len(ChatRole) == 3


class TestChatMessage:
    """Tests for ChatMessage validation."""

    def test_valid_message(self):
        msg = ChatMessage(role="user", content="Hello, Sona!")
        assert msg.role == ChatRole.USER
        assert msg.content == "Hello, Sona!"

    def test_role_case_insensitive(self):
        msg = ChatMessage(role="USER", content="test")
        assert msg.role == ChatRole.USER

    def test_invalid_role(self):
        with pytest.raises(ValidationError) as exc_info:
            ChatMessage(role="invalid", content="test")
        assert "role" in str(exc_info.value)

    def test_content_empty_string_rejected(self):
        with pytest.raises(ValidationError):
            ChatMessage(role="user", content="")

    def test_content_max_length(self):
        # Exactly at limit should work
        msg = ChatMessage(role="user", content="a" * 100000)
        assert len(msg.content) == 100000

    def test_content_exceeds_max_length(self):
        with pytest.raises(ValidationError):
            ChatMessage(role="user", content="a" * 100001)

    def test_all_roles_valid(self):
        for role in ["user", "assistant", "system"]:
            msg = ChatMessage(role=role, content="test")
            assert msg.role == role


class TestChatRequest:
    """Tests for ChatRequest validation."""

    def _make_messages(self, count: int = 1) -> list[dict]:
        return [{"role": "user", "content": f"Message {i}"} for i in range(count)]

    def test_minimal_valid_request(self):
        req = ChatRequest(messages=[ChatMessage(role="user", content="Hi")])
        assert len(req.messages) == 1
        assert req.model == "default"
        assert req.temperature == 0.7
        assert req.max_tokens == 4096
        assert req.stream is False

    def test_empty_messages_rejected(self):
        with pytest.raises(ValidationError):
            ChatRequest(messages=[])

    def test_temperature_lower_bound(self):
        req = ChatRequest(
            messages=[ChatMessage(role="user", content="test")],
            temperature=0.0,
        )
        assert req.temperature == 0.0

    def test_temperature_upper_bound(self):
        req = ChatRequest(
            messages=[ChatMessage(role="user", content="test")],
            temperature=2.0,
        )
        assert req.temperature == 2.0

    def test_temperature_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            ChatRequest(
                messages=[ChatMessage(role="user", content="test")],
                temperature=-0.1,
            )

    def test_temperature_above_two_rejected(self):
        with pytest.raises(ValidationError):
            ChatRequest(
                messages=[ChatMessage(role="user", content="test")],
                temperature=2.1,
            )

    def test_max_tokens_lower_bound(self):
        req = ChatRequest(
            messages=[ChatMessage(role="user", content="test")],
            max_tokens=1,
        )
        assert req.max_tokens == 1

    def test_max_tokens_upper_bound(self):
        req = ChatRequest(
            messages=[ChatMessage(role="user", content="test")],
            max_tokens=128000,
        )
        assert req.max_tokens == 128000

    def test_max_tokens_zero_rejected(self):
        with pytest.raises(ValidationError):
            ChatRequest(
                messages=[ChatMessage(role="user", content="test")],
                max_tokens=0,
            )

    def test_max_tokens_exceeds_limit(self):
        with pytest.raises(ValidationError):
            ChatRequest(
                messages=[ChatMessage(role="user", content="test")],
                max_tokens=128001,
            )

    def test_custom_model(self):
        req = ChatRequest(
            messages=[ChatMessage(role="user", content="test")],
            model="gpt-4o",
        )
        assert req.model == "gpt-4o"

    def test_stream_flag(self):
        req = ChatRequest(
            messages=[ChatMessage(role="user", content="test")],
            stream=True,
        )
        assert req.stream is True


class TestTokenUsage:
    """Tests for TokenUsage model."""

    def test_defaults(self):
        usage = TokenUsage()
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0

    def test_negative_tokens_rejected(self):
        with pytest.raises(ValidationError):
            TokenUsage(prompt_tokens=-1)


class TestChatResponse:
    """Tests for ChatResponse model."""

    def test_valid_response(self):
        resp = ChatResponse(
            messages=[ChatMessage(role="assistant", content="Hello!")],
            model="gpt-4o",
        )
        assert resp.id is not None
        assert resp.model == "gpt-4o"
        assert resp.finish_reason == "stop"
        assert resp.created_at is not None

    def test_response_with_usage(self):
        resp = ChatResponse(
            messages=[ChatMessage(role="assistant", content="Hello!")],
            model="gpt-4o",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )
        assert resp.usage.total_tokens == 15
