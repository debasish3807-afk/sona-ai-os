"""Unit tests for the model capabilities module.

Tests verify register, find by capability, cheapest, and fastest selection.
"""

from sona_ai_kernel.infrastructure.model_capabilities import (
    ModelCapability,
    ModelCapabilityRegistry,
    ModelProfile,
)


def _gpt4_profile() -> ModelProfile:
    return ModelProfile(
        model_id="gpt-4o",
        provider="openai",
        capabilities=frozenset(
            {ModelCapability.CHAT, ModelCapability.CODE, ModelCapability.VISION}
        ),
        context_window=128000,
        max_output_tokens=4096,
        cost_per_input_token=0.000005,
        cost_per_output_token=0.000015,
        avg_latency_ms=500.0,
    )


def _claude_profile() -> ModelProfile:
    return ModelProfile(
        model_id="claude-3-opus",
        provider="anthropic",
        capabilities=frozenset(
            {ModelCapability.CHAT, ModelCapability.CODE, ModelCapability.REASONING}
        ),
        context_window=200000,
        max_output_tokens=4096,
        cost_per_input_token=0.000015,
        cost_per_output_token=0.000075,
        avg_latency_ms=800.0,
    )


def _fast_model_profile() -> ModelProfile:
    return ModelProfile(
        model_id="llama-3-8b",
        provider="ollama",
        capabilities=frozenset({ModelCapability.CHAT, ModelCapability.FAST}),
        context_window=8192,
        max_output_tokens=2048,
        cost_per_input_token=0.0,
        cost_per_output_token=0.0,
        avg_latency_ms=50.0,
    )


class TestModelCapabilityRegistry:
    """Tests for the ModelCapabilityRegistry."""

    def test_register_and_get(self) -> None:
        """Registered model can be retrieved by ID."""
        registry = ModelCapabilityRegistry()
        profile = _gpt4_profile()
        registry.register(profile)

        result = registry.get("gpt-4o")
        assert result is not None
        assert result.model_id == "gpt-4o"
        assert result.provider == "openai"

    def test_get_returns_none_for_unknown(self) -> None:
        """get() returns None for unregistered model."""
        registry = ModelCapabilityRegistry()
        assert registry.get("nonexistent") is None

    def test_find_by_single_capability(self) -> None:
        """find_by_capability returns models with the specified capability."""
        registry = ModelCapabilityRegistry()
        registry.register(_gpt4_profile())
        registry.register(_claude_profile())
        registry.register(_fast_model_profile())

        results = registry.find_by_capability(ModelCapability.CODE)
        model_ids = [r.model_id for r in results]
        assert "gpt-4o" in model_ids
        assert "claude-3-opus" in model_ids
        assert "llama-3-8b" not in model_ids

    def test_find_by_multiple_capabilities(self) -> None:
        """find_by_capability requires ALL specified capabilities."""
        registry = ModelCapabilityRegistry()
        registry.register(_gpt4_profile())
        registry.register(_claude_profile())

        results = registry.find_by_capability(ModelCapability.CODE, ModelCapability.VISION)
        model_ids = [r.model_id for r in results]
        assert "gpt-4o" in model_ids
        assert "claude-3-opus" not in model_ids  # No VISION

    def test_find_cheapest(self) -> None:
        """find_cheapest returns model with lowest total cost per token."""
        registry = ModelCapabilityRegistry()
        registry.register(_gpt4_profile())
        registry.register(_claude_profile())
        registry.register(_fast_model_profile())

        cheapest = registry.find_cheapest(ModelCapability.CHAT)
        assert cheapest is not None
        assert cheapest.model_id == "llama-3-8b"  # cost is 0

    def test_find_cheapest_returns_none_no_match(self) -> None:
        """find_cheapest returns None when no model matches."""
        registry = ModelCapabilityRegistry()
        registry.register(_fast_model_profile())

        result = registry.find_cheapest(ModelCapability.VISION)
        assert result is None

    def test_find_fastest(self) -> None:
        """find_fastest returns model with lowest average latency."""
        registry = ModelCapabilityRegistry()
        registry.register(_gpt4_profile())
        registry.register(_claude_profile())
        registry.register(_fast_model_profile())

        fastest = registry.find_fastest(ModelCapability.CHAT)
        assert fastest is not None
        assert fastest.model_id == "llama-3-8b"

    def test_find_fastest_returns_none_no_match(self) -> None:
        """find_fastest returns None when no model matches."""
        registry = ModelCapabilityRegistry()
        result = registry.find_fastest(ModelCapability.EMBEDDING)
        assert result is None

    def test_list_all(self) -> None:
        """list_all returns all registered profiles."""
        registry = ModelCapabilityRegistry()
        registry.register(_gpt4_profile())
        registry.register(_claude_profile())

        all_models = registry.list_all()
        assert len(all_models) == 2

    def test_list_all_empty(self) -> None:
        """list_all returns empty list when no models registered."""
        registry = ModelCapabilityRegistry()
        assert registry.list_all() == []
