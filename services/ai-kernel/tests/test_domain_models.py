"""Unit tests for AI Kernel domain models.

Tests verify that all domain models, enums, and dataclasses are correctly
defined, instantiate properly, and enforce immutability.
"""

from dataclasses import FrozenInstanceError

import pytest

from sona_ai_kernel.domain.models import (
    KernelRequest,
    KernelResponse,
    ModelConfig,
    ReasoningStrategy,
)


class TestReasoningStrategy:
    """Tests for the ReasoningStrategy enum."""

    def test_all_strategies_defined(self) -> None:
        """Verify all expected reasoning strategies are available."""
        assert ReasoningStrategy.DIRECT == "direct"
        assert ReasoningStrategy.CHAIN_OF_THOUGHT == "chain_of_thought"
        assert ReasoningStrategy.TREE_OF_THOUGHT == "tree_of_thought"
        assert ReasoningStrategy.REFLECTION == "reflection"

    def test_strategy_count(self) -> None:
        """Verify exactly 4 reasoning strategies exist."""
        assert len(ReasoningStrategy) == 4

    def test_strategy_is_str_enum(self) -> None:
        """Verify strategies are usable as strings."""
        assert str(ReasoningStrategy.DIRECT) == "direct"
        assert str(ReasoningStrategy.CHAIN_OF_THOUGHT) == "chain_of_thought"


class TestModelConfig:
    """Tests for the ModelConfig frozen dataclass."""

    def test_minimal_creation(self) -> None:
        """Create with only required fields."""
        config = ModelConfig(provider="openai", model_id="gpt-4o")
        assert config.provider == "openai"
        assert config.model_id == "gpt-4o"

    def test_default_values(self) -> None:
        """Verify default values are set correctly."""
        config = ModelConfig(provider="ollama", model_id="llama3")
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.top_p == 1.0

    def test_custom_values(self) -> None:
        """Create with custom values."""
        config = ModelConfig(
            provider="anthropic",
            model_id="claude-3",
            temperature=0.3,
            max_tokens=8192,
            top_p=0.9,
        )
        assert config.temperature == 0.3
        assert config.max_tokens == 8192
        assert config.top_p == 0.9

    def test_is_frozen(self) -> None:
        """Verify ModelConfig is immutable."""
        config = ModelConfig(provider="openai", model_id="gpt-4o")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            config.model_id = "gpt-3.5"  # type: ignore[misc]


class TestKernelRequest:
    """Tests for the KernelRequest frozen dataclass."""

    def test_minimal_creation(self) -> None:
        """Create with only required fields."""
        req = KernelRequest(
            session_id="sess-123",
            user_id="user-456",
            content="Hello world",
        )
        assert req.session_id == "sess-123"
        assert req.user_id == "user-456"
        assert req.content == "Hello world"

    def test_default_values(self) -> None:
        """Verify default values."""
        req = KernelRequest(
            session_id="s1",
            user_id="u1",
            content="test",
        )
        assert req.context is None
        assert req.model_override is None
        assert req.strategy == ReasoningStrategy.DIRECT

    def test_with_all_fields(self) -> None:
        """Create with all optional fields."""
        model = ModelConfig(provider="openai", model_id="gpt-4o")
        req = KernelRequest(
            session_id="s1",
            user_id="u1",
            content="complex query",
            context={"memory": "previous interactions"},
            model_override=model,
            strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
        )
        assert req.context == {"memory": "previous interactions"}
        assert req.model_override == model
        assert req.strategy == ReasoningStrategy.CHAIN_OF_THOUGHT

    def test_is_frozen(self) -> None:
        """Verify KernelRequest is immutable."""
        req = KernelRequest(session_id="s1", user_id="u1", content="test")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            req.content = "changed"  # type: ignore[misc]


class TestKernelResponse:
    """Tests for the KernelResponse frozen dataclass."""

    def test_creation_without_trace(self) -> None:
        """Create response without reasoning trace."""
        resp = KernelResponse(
            content="The answer is 42.",
            model_used="gpt-4o",
            tokens_input=10,
            tokens_output=5,
            latency_ms=250.0,
        )
        assert resp.content == "The answer is 42."
        assert resp.model_used == "gpt-4o"
        assert resp.tokens_input == 10
        assert resp.tokens_output == 5
        assert resp.latency_ms == 250.0
        assert resp.reasoning_trace is None

    def test_creation_with_trace(self) -> None:
        """Create response with reasoning trace."""
        trace = ["Step 1: Analyze", "Step 2: Synthesize", "Step 3: Conclude"]
        resp = KernelResponse(
            content="Final answer",
            model_used="claude-3",
            tokens_input=50,
            tokens_output=20,
            latency_ms=500.0,
            reasoning_trace=trace,
        )
        assert resp.reasoning_trace == trace
        assert len(resp.reasoning_trace) == 3

    def test_is_frozen(self) -> None:
        """Verify KernelResponse is immutable."""
        resp = KernelResponse(
            content="test",
            model_used="gpt-4o",
            tokens_input=1,
            tokens_output=1,
            latency_ms=10.0,
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            resp.content = "changed"  # type: ignore[misc]
