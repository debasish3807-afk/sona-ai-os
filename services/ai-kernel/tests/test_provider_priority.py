"""Unit tests for the provider priority module.

Tests verify ordering, weights, failover selection, and exclusion.
"""

import pytest

from sona_ai_kernel.infrastructure.provider_priority import (
    ProviderPriority,
    ProviderPriorityManager,
)


class TestProviderPriority:
    """Tests for the ProviderPriority dataclass."""

    def test_default_values(self) -> None:
        """Verify default priority values."""
        p = ProviderPriority(provider_name="openai")
        assert p.provider_name == "openai"
        assert p.priority == 0
        assert p.weight == 1.0
        assert p.is_fallback is False

    def test_frozen_dataclass(self) -> None:
        """Verify ProviderPriority is immutable."""
        p = ProviderPriority(provider_name="openai")
        with pytest.raises(AttributeError):
            p.priority = 5  # type: ignore[misc]


class TestProviderPriorityManager:
    """Tests for the ProviderPriorityManager."""

    def test_empty_manager_returns_empty_list(self) -> None:
        """Empty manager returns no providers."""
        manager = ProviderPriorityManager()
        assert manager.get_ordered() == []

    def test_single_provider(self) -> None:
        """Single provider is returned correctly."""
        manager = ProviderPriorityManager()
        manager.add(ProviderPriority(provider_name="openai"))
        assert manager.get_ordered() == ["openai"]

    def test_ordering_by_priority(self) -> None:
        """Providers ordered by priority (lower=higher)."""
        manager = ProviderPriorityManager()
        manager.add(ProviderPriority(provider_name="slow", priority=10))
        manager.add(ProviderPriority(provider_name="fast", priority=1))
        manager.add(ProviderPriority(provider_name="medium", priority=5))

        ordered = manager.get_ordered()
        assert ordered == ["fast", "medium", "slow"]

    def test_fallbacks_sorted_last(self) -> None:
        """Fallback providers are sorted after primary providers."""
        manager = ProviderPriorityManager()
        manager.add(ProviderPriority(provider_name="primary", priority=1))
        manager.add(ProviderPriority(provider_name="fallback", priority=0, is_fallback=True))

        ordered = manager.get_ordered()
        assert ordered == ["primary", "fallback"]

    def test_get_fallbacks(self) -> None:
        """get_fallbacks returns only fallback providers."""
        manager = ProviderPriorityManager()
        manager.add(ProviderPriority(provider_name="primary", priority=1))
        manager.add(ProviderPriority(provider_name="backup1", priority=1, is_fallback=True))
        manager.add(ProviderPriority(provider_name="backup2", priority=2, is_fallback=True))

        fallbacks = manager.get_fallbacks()
        assert "primary" not in fallbacks
        assert "backup1" in fallbacks
        assert "backup2" in fallbacks

    def test_get_ordered_with_exclusions(self) -> None:
        """get_ordered excludes specified providers."""
        manager = ProviderPriorityManager()
        manager.add(ProviderPriority(provider_name="a", priority=1))
        manager.add(ProviderPriority(provider_name="b", priority=2))
        manager.add(ProviderPriority(provider_name="c", priority=3))

        ordered = manager.get_ordered(exclude={"b"})
        assert ordered == ["a", "c"]

    def test_get_next_returns_first_non_failed(self) -> None:
        """get_next returns the first provider not in the failed set."""
        manager = ProviderPriorityManager()
        manager.add(ProviderPriority(provider_name="a", priority=1))
        manager.add(ProviderPriority(provider_name="b", priority=2))
        manager.add(ProviderPriority(provider_name="c", priority=3))

        result = manager.get_next(failed={"a"})
        assert result == "b"

    def test_get_next_returns_none_when_all_failed(self) -> None:
        """get_next returns None when all providers have failed."""
        manager = ProviderPriorityManager()
        manager.add(ProviderPriority(provider_name="a"))
        manager.add(ProviderPriority(provider_name="b"))

        result = manager.get_next(failed={"a", "b"})
        assert result is None

    def test_weight_ordering_same_priority(self) -> None:
        """Higher weight providers come first at same priority level."""
        manager = ProviderPriorityManager()
        manager.add(ProviderPriority(provider_name="light", priority=1, weight=0.5))
        manager.add(ProviderPriority(provider_name="heavy", priority=1, weight=2.0))

        ordered = manager.get_ordered()
        assert ordered[0] == "heavy"
