"""Unit tests for Thalamus Router domain models.

Tests verify that all domain models, enums, and dataclasses are correctly
defined, instantiate properly, and enforce immutability.
"""

from dataclasses import FrozenInstanceError

import pytest

from sona_thalamus.domain.models import (
    IntentCategory,
    RequestPriority,
    RoutingDecision,
)


class TestRequestPriority:
    """Tests for the RequestPriority enum."""

    def test_all_priorities_defined(self) -> None:
        """Verify all expected priority levels are available."""
        assert RequestPriority.CRITICAL == "critical"
        assert RequestPriority.HIGH == "high"
        assert RequestPriority.NORMAL == "normal"
        assert RequestPriority.LOW == "low"
        assert RequestPriority.BACKGROUND == "background"

    def test_priority_count(self) -> None:
        """Verify exactly 5 priority levels exist."""
        assert len(RequestPriority) == 5

    def test_priority_is_str_enum(self) -> None:
        """Verify priorities are usable as strings."""
        assert str(RequestPriority.CRITICAL) == "critical"
        assert str(RequestPriority.NORMAL) == "normal"


class TestIntentCategory:
    """Tests for the IntentCategory enum."""

    def test_all_categories_defined(self) -> None:
        """Verify all expected intent categories are available."""
        assert IntentCategory.CHAT == "chat"
        assert IntentCategory.RESEARCH == "research"
        assert IntentCategory.CODE == "code"
        assert IntentCategory.AUTOMATION == "automation"
        assert IntentCategory.MEMORY == "memory"
        assert IntentCategory.SYSTEM == "system"

    def test_category_count(self) -> None:
        """Verify exactly 6 intent categories exist."""
        assert len(IntentCategory) == 6

    def test_category_is_str_enum(self) -> None:
        """Verify categories are usable as strings."""
        assert str(IntentCategory.CHAT) == "chat"
        assert str(IntentCategory.CODE) == "code"


class TestRoutingDecision:
    """Tests for the RoutingDecision frozen dataclass."""

    def test_creation_without_fallback(self) -> None:
        """Create a routing decision without fallback service."""
        decision = RoutingDecision(
            target_service="brain-os",
            intent=IntentCategory.CHAT,
            priority=RequestPriority.NORMAL,
            requires_agents=["chat"],
            estimated_latency_ms=200,
        )
        assert decision.target_service == "brain-os"
        assert decision.intent == IntentCategory.CHAT
        assert decision.priority == RequestPriority.NORMAL
        assert decision.requires_agents == ["chat"]
        assert decision.estimated_latency_ms == 200
        assert decision.fallback_service is None

    def test_creation_with_fallback(self) -> None:
        """Create a routing decision with fallback service."""
        decision = RoutingDecision(
            target_service="research-os",
            intent=IntentCategory.RESEARCH,
            priority=RequestPriority.HIGH,
            requires_agents=["research", "web"],
            estimated_latency_ms=500,
            fallback_service="brain-os",
        )
        assert decision.fallback_service == "brain-os"
        assert decision.requires_agents == ["research", "web"]

    def test_creation_no_agents_required(self) -> None:
        """Create a routing decision requiring no agents."""
        decision = RoutingDecision(
            target_service="memory-os",
            intent=IntentCategory.MEMORY,
            priority=RequestPriority.LOW,
            requires_agents=[],
            estimated_latency_ms=50,
        )
        assert decision.requires_agents == []

    def test_is_frozen(self) -> None:
        """Verify RoutingDecision is immutable."""
        decision = RoutingDecision(
            target_service="brain-os",
            intent=IntentCategory.CHAT,
            priority=RequestPriority.NORMAL,
            requires_agents=[],
            estimated_latency_ms=100,
        )
        with pytest.raises((TypeError, AttributeError, FrozenInstanceError)):
            decision.target_service = "other"  # type: ignore[misc]

    def test_critical_priority_routing(self) -> None:
        """Test routing with critical priority."""
        decision = RoutingDecision(
            target_service="security",
            intent=IntentCategory.SYSTEM,
            priority=RequestPriority.CRITICAL,
            requires_agents=["system"],
            estimated_latency_ms=20,
            fallback_service="brain-os",
        )
        assert decision.priority == RequestPriority.CRITICAL
        assert decision.intent == IntentCategory.SYSTEM
