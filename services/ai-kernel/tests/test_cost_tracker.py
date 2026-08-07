"""Unit tests for the cost tracker module.

Tests verify recording, session/user/provider cost queries, and breakdown.
"""

import pytest

from sona_ai_kernel.infrastructure.cost_tracker import CostRecord, CostTracker


class TestCostRecord:
    """Tests for the CostRecord dataclass."""

    def test_frozen(self) -> None:
        """CostRecord is immutable."""
        record = CostRecord(
            provider="openai",
            model="gpt-4o",
            tokens_input=100,
            tokens_output=50,
            cost_input=0.0005,
            cost_output=0.00075,
            total_cost=0.00125,
        )
        with pytest.raises(AttributeError):
            record.total_cost = 0.0  # type: ignore[misc]


class TestCostTracker:
    """Tests for the CostTracker."""

    def test_record_creates_entry(self) -> None:
        """record() creates a CostRecord and adds it to the tracker."""
        tracker = CostTracker()
        record = tracker.record(
            provider="openai",
            model="gpt-4o",
            tokens_input=1000,
            tokens_output=500,
            cost_per_input=0.000005,
            cost_per_output=0.000015,
        )

        assert record.provider == "openai"
        assert record.model == "gpt-4o"
        assert record.tokens_input == 1000
        assert record.tokens_output == 500
        assert record.cost_input == pytest.approx(0.005)
        assert record.cost_output == pytest.approx(0.0075)
        assert record.total_cost == pytest.approx(0.0125)

    def test_get_total_cost(self) -> None:
        """get_total_cost returns sum of all recorded costs."""
        tracker = CostTracker()
        tracker.record("openai", "gpt-4o", 100, 50, 0.01, 0.02)
        tracker.record("anthropic", "claude", 200, 100, 0.01, 0.02)

        # First: 100*0.01 + 50*0.02 = 1.0 + 1.0 = 2.0
        # Second: 200*0.01 + 100*0.02 = 2.0 + 2.0 = 4.0
        assert tracker.get_total_cost() == pytest.approx(6.0)

    def test_get_total_cost_empty(self) -> None:
        """get_total_cost returns 0 when no records exist."""
        tracker = CostTracker()
        assert tracker.get_total_cost() == 0.0

    def test_get_session_cost(self) -> None:
        """get_session_cost returns cost for a specific session."""
        tracker = CostTracker()
        tracker.record("openai", "gpt-4o", 100, 50, 0.001, 0.002, session_id="s1")
        tracker.record("openai", "gpt-4o", 200, 100, 0.001, 0.002, session_id="s2")
        tracker.record("openai", "gpt-4o", 300, 150, 0.001, 0.002, session_id="s1")

        # s1: (100*0.001 + 50*0.002) + (300*0.001 + 150*0.002)
        #   = (0.1 + 0.1) + (0.3 + 0.3) = 0.2 + 0.6 = 0.8
        assert tracker.get_session_cost("s1") == pytest.approx(0.8)

    def test_get_user_cost(self) -> None:
        """get_user_cost returns cost for a specific user."""
        tracker = CostTracker()
        tracker.record("openai", "gpt-4o", 100, 50, 0.001, 0.002, user_id="user1")
        tracker.record("openai", "gpt-4o", 100, 50, 0.001, 0.002, user_id="user2")

        # user1: 100*0.001 + 50*0.002 = 0.1 + 0.1 = 0.2
        assert tracker.get_user_cost("user1") == pytest.approx(0.2)

    def test_get_provider_cost(self) -> None:
        """get_provider_cost returns cost for a specific provider."""
        tracker = CostTracker()
        tracker.record("openai", "gpt-4o", 100, 50, 0.01, 0.02)
        tracker.record("anthropic", "claude", 100, 50, 0.01, 0.02)
        tracker.record("openai", "gpt-3.5", 100, 50, 0.001, 0.002)

        # openai: (100*0.01+50*0.02) + (100*0.001+50*0.002) = 2.0 + 0.2 = 2.2
        assert tracker.get_provider_cost("openai") == pytest.approx(2.2)

    def test_get_cost_breakdown(self) -> None:
        """get_cost_breakdown returns per-provider cost dictionary."""
        tracker = CostTracker()
        tracker.record("openai", "gpt-4o", 100, 50, 0.01, 0.02)
        tracker.record("anthropic", "claude", 100, 50, 0.01, 0.02)

        breakdown = tracker.get_cost_breakdown()
        assert "openai" in breakdown
        assert "anthropic" in breakdown
        assert breakdown["openai"] == pytest.approx(2.0)
        assert breakdown["anthropic"] == pytest.approx(2.0)

    def test_cost_breakdown_empty(self) -> None:
        """get_cost_breakdown returns empty dict when no records."""
        tracker = CostTracker()
        assert tracker.get_cost_breakdown() == {}

    def test_session_and_user_ids_stored(self) -> None:
        """session_id and user_id are properly stored in records."""
        tracker = CostTracker()
        record = tracker.record(
            "openai",
            "gpt-4o",
            10,
            5,
            0.001,
            0.002,
            session_id="sess123",
            user_id="user456",
        )
        assert record.session_id == "sess123"
        assert record.user_id == "user456"
