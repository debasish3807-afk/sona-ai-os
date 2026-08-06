"""Unit tests for Brain OS domain models.

Tests verify that all domain models and dataclasses are correctly
defined, instantiate properly, and enforce immutability.
"""

from dataclasses import FrozenInstanceError

import pytest
from domain.models import (
    BrainRequest,
    BrainResponse,
)


class TestBrainRequest:
    """Tests for the BrainRequest frozen dataclass."""

    def test_minimal_creation(self) -> None:
        """Create with only required fields."""
        req = BrainRequest(
            session_id="sess-123",
            user_id="user-456",
            messages=[{"role": "user", "content": "Hello"}],
        )
        assert req.session_id == "sess-123"
        assert req.user_id == "user-456"
        assert req.messages == [{"role": "user", "content": "Hello"}]

    def test_default_values(self) -> None:
        """Verify default values are set correctly."""
        req = BrainRequest(
            session_id="s1",
            user_id="u1",
            messages=[{"role": "user", "content": "test"}],
        )
        assert req.stream is False
        assert req.metadata is None

    def test_with_all_fields(self) -> None:
        """Create with all optional fields."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is Python?"},
        ]
        metadata = {"source": "web", "priority": "high"}
        req = BrainRequest(
            session_id="sess-abc",
            user_id="user-xyz",
            messages=messages,
            stream=True,
            metadata=metadata,
        )
        assert req.stream is True
        assert req.metadata == metadata
        assert len(req.messages) == 2

    def test_is_frozen(self) -> None:
        """Verify BrainRequest is immutable."""
        req = BrainRequest(
            session_id="s1",
            user_id="u1",
            messages=[{"role": "user", "content": "test"}],
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            req.session_id = "changed"  # type: ignore[misc]

    def test_multiple_messages(self) -> None:
        """Verify BrainRequest handles multi-turn conversation."""
        messages = [
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "How are you?"},
        ]
        req = BrainRequest(
            session_id="s1",
            user_id="u1",
            messages=messages,
        )
        assert len(req.messages) == 4
        assert req.messages[0]["role"] == "system"
        assert req.messages[-1]["role"] == "user"


class TestBrainResponse:
    """Tests for the BrainResponse frozen dataclass."""

    def test_minimal_creation(self) -> None:
        """Create response with required fields only."""
        resp = BrainResponse(
            content="The answer is 42.",
            session_id="sess-123",
            model_used="gpt-4o",
            tokens={"input": 10, "output": 5},
            latency_ms=250.0,
        )
        assert resp.content == "The answer is 42."
        assert resp.session_id == "sess-123"
        assert resp.model_used == "gpt-4o"
        assert resp.tokens == {"input": 10, "output": 5}
        assert resp.latency_ms == 250.0

    def test_default_values(self) -> None:
        """Verify default values are set correctly."""
        resp = BrainResponse(
            content="response",
            session_id="s1",
            model_used="llama3",
            tokens={"input": 5, "output": 3},
            latency_ms=100.0,
        )
        assert resp.agent_used is None
        assert resp.memory_updated is False

    def test_with_all_fields(self) -> None:
        """Create response with all optional fields."""
        resp = BrainResponse(
            content="Research complete.",
            session_id="sess-abc",
            model_used="claude-3",
            tokens={"input": 50, "output": 200},
            latency_ms=1500.0,
            agent_used="research",
            memory_updated=True,
        )
        assert resp.agent_used == "research"
        assert resp.memory_updated is True

    def test_is_frozen(self) -> None:
        """Verify BrainResponse is immutable."""
        resp = BrainResponse(
            content="test",
            session_id="s1",
            model_used="gpt-4o",
            tokens={"input": 1, "output": 1},
            latency_ms=10.0,
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            resp.content = "changed"  # type: ignore[misc]

    def test_tokens_dict_structure(self) -> None:
        """Verify tokens dict can hold various usage data."""
        tokens = {"input": 100, "output": 50, "total": 150}
        resp = BrainResponse(
            content="response",
            session_id="s1",
            model_used="gpt-4o",
            tokens=tokens,
            latency_ms=200.0,
        )
        assert resp.tokens["input"] == 100
        assert resp.tokens["output"] == 50
        assert resp.tokens["total"] == 150
