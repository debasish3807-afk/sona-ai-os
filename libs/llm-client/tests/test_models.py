"""Unit tests for LLM Client data models.

Tests verify that the data models are correctly defined,
instantiate properly, and enforce immutability.
"""

from dataclasses import FrozenInstanceError

import pytest

from sona_llm.models import CompletionResult, LLMProviderConfig, Message, ProviderType


class TestProviderType:
    """Tests for the ProviderType enum."""

    def test_all_provider_types_defined(self) -> None:
        """Verify all expected provider types are available."""
        assert ProviderType.OLLAMA == "ollama"
        assert ProviderType.OPENAI == "openai"
        assert ProviderType.ANTHROPIC == "anthropic"
        assert ProviderType.GOOGLE == "google"

    def test_provider_type_string_values(self) -> None:
        """Verify provider types are StrEnum (usable as strings)."""
        assert str(ProviderType.OLLAMA) == "ollama"
        assert str(ProviderType.OPENAI) == "openai"
        assert str(ProviderType.ANTHROPIC) == "anthropic"
        assert str(ProviderType.GOOGLE) == "google"

    def test_provider_type_count(self) -> None:
        """Verify exactly 4 provider types are defined."""
        assert len(ProviderType) == 4


class TestLLMProviderConfig:
    """Tests for the LLMProviderConfig data model."""

    def test_minimal_config_creation(self) -> None:
        """Create a config with only required fields."""
        config = LLMProviderConfig(
            provider=ProviderType.OLLAMA,
            model_id="llama3.2",
        )
        assert config.provider == ProviderType.OLLAMA
        assert config.model_id == "llama3.2"
        assert config.api_key is None
        assert config.base_url is None

    def test_default_values(self) -> None:
        """Verify sensible default values."""
        config = LLMProviderConfig(
            provider=ProviderType.OPENAI,
            model_id="gpt-4o",
        )
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.timeout_seconds == 60

    def test_full_config_creation(self) -> None:
        """Create a config with all fields specified."""
        config = LLMProviderConfig(
            provider=ProviderType.ANTHROPIC,
            model_id="claude-3-5-sonnet",
            api_key="sk-ant-test",
            base_url="https://api.anthropic.com",
            max_tokens=8192,
            temperature=0.3,
            timeout_seconds=120,
        )
        assert config.api_key == "sk-ant-test"
        assert config.base_url == "https://api.anthropic.com"
        assert config.max_tokens == 8192
        assert config.temperature == 0.3
        assert config.timeout_seconds == 120

    def test_config_is_frozen(self) -> None:
        """Verify config is immutable (frozen dataclass)."""
        config = LLMProviderConfig(
            provider=ProviderType.OPENAI,
            model_id="gpt-4o",
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):  # FrozenInstanceError
            config.model_id = "gpt-3.5-turbo"  # type: ignore[misc]


class TestMessage:
    """Tests for the Message data model."""

    def test_message_creation(self) -> None:
        """Create a message with role and content."""
        msg = Message(role="user", content="Hello, how are you?")
        assert msg.role == "user"
        assert msg.content == "Hello, how are you?"

    def test_system_message(self) -> None:
        """Create a system message."""
        msg = Message(role="system", content="You are a helpful assistant.")
        assert msg.role == "system"

    def test_assistant_message(self) -> None:
        """Create an assistant message."""
        msg = Message(role="assistant", content="I'm doing great, thank you!")
        assert msg.role == "assistant"

    def test_message_is_frozen(self) -> None:
        """Verify message is immutable (frozen dataclass)."""
        msg = Message(role="user", content="test")
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):  # FrozenInstanceError
            msg.content = "changed"  # type: ignore[misc]


class TestCompletionResult:
    """Tests for the CompletionResult data model."""

    def test_completion_result_creation(self) -> None:
        """Create a completion result with all fields."""
        result = CompletionResult(
            content="The answer is 42.",
            model="gpt-4o",
            tokens_input=10,
            tokens_output=5,
            latency_ms=250.5,
        )
        assert result.content == "The answer is 42."
        assert result.model == "gpt-4o"
        assert result.tokens_input == 10
        assert result.tokens_output == 5
        assert result.latency_ms == 250.5

    def test_result_is_frozen(self) -> None:
        """Verify result is immutable (frozen dataclass)."""
        result = CompletionResult(
            content="test",
            model="gpt-4o",
            tokens_input=5,
            tokens_output=3,
            latency_ms=100.0,
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):  # FrozenInstanceError
            result.content = "changed"  # type: ignore[misc]

    def test_zero_latency_is_valid(self) -> None:
        """Verify that zero latency is an acceptable value."""
        result = CompletionResult(
            content="fast response",
            model="local-model",
            tokens_input=1,
            tokens_output=2,
            latency_ms=0.0,
        )
        assert result.latency_ms == 0.0
