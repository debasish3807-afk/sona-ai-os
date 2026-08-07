"""Tests for security metrics."""

from sona_security.infrastructure.metrics import SecurityMetrics


class TestSecurityMetrics:
    def setup_method(self) -> None:
        self.metrics = SecurityMetrics()

    def test_default_counters_initialized(self) -> None:
        all_metrics = self.metrics.get_all()
        assert "auth_success_total" in all_metrics
        assert "auth_failure_total" in all_metrics
        assert "token_validation_total" in all_metrics
        assert "permission_granted_total" in all_metrics
        assert "permission_denied_total" in all_metrics
        assert "safety_check_total" in all_metrics
        assert "rate_limit_hit_total" in all_metrics

    def test_all_start_at_zero(self) -> None:
        for value in self.metrics.get_all().values():
            assert value == 0

    def test_increment(self) -> None:
        self.metrics.increment("auth_success_total")
        assert self.metrics.get("auth_success_total") == 1

    def test_increment_by_amount(self) -> None:
        self.metrics.increment("auth_success_total", 5)
        assert self.metrics.get("auth_success_total") == 5

    def test_increment_creates_new_counter(self) -> None:
        self.metrics.increment("custom_metric")
        assert self.metrics.get("custom_metric") == 1

    def test_get_nonexistent_returns_zero(self) -> None:
        assert self.metrics.get("nonexistent") == 0

    def test_reset_single(self) -> None:
        self.metrics.increment("auth_success_total", 10)
        self.metrics.reset("auth_success_total")
        assert self.metrics.get("auth_success_total") == 0

    def test_reset_all(self) -> None:
        self.metrics.increment("auth_success_total", 5)
        self.metrics.increment("auth_failure_total", 3)
        self.metrics.reset_all()
        assert self.metrics.get("auth_success_total") == 0
        assert self.metrics.get("auth_failure_total") == 0

    def test_record_auth_success(self) -> None:
        self.metrics.record_auth_success()
        assert self.metrics.get("auth_success_total") == 1

    def test_record_auth_failure(self) -> None:
        self.metrics.record_auth_failure()
        assert self.metrics.get("auth_failure_total") == 1

    def test_record_token_validation_success(self) -> None:
        self.metrics.record_token_validation(success=True)
        assert self.metrics.get("token_validation_total") == 1
        assert self.metrics.get("token_validation_failure_total") == 0

    def test_record_token_validation_failure(self) -> None:
        self.metrics.record_token_validation(success=False)
        assert self.metrics.get("token_validation_total") == 1
        assert self.metrics.get("token_validation_failure_total") == 1

    def test_record_permission_check_granted(self) -> None:
        self.metrics.record_permission_check(granted=True)
        assert self.metrics.get("permission_granted_total") == 1

    def test_record_permission_check_denied(self) -> None:
        self.metrics.record_permission_check(granted=False)
        assert self.metrics.get("permission_denied_total") == 1

    def test_record_safety_check_safe(self) -> None:
        self.metrics.record_safety_check(blocked=False)
        assert self.metrics.get("safety_check_total") == 1
        assert self.metrics.get("safety_check_blocked_total") == 0

    def test_record_safety_check_blocked(self) -> None:
        self.metrics.record_safety_check(blocked=True)
        assert self.metrics.get("safety_check_total") == 1
        assert self.metrics.get("safety_check_blocked_total") == 1

    def test_record_rate_limit_hit(self) -> None:
        self.metrics.record_rate_limit_hit()
        assert self.metrics.get("rate_limit_hit_total") == 1

    def test_snapshot(self) -> None:
        self.metrics.increment("auth_success_total", 3)
        snapshot = self.metrics.snapshot()
        assert "metrics" in snapshot
        assert "counter_count" in snapshot
        assert snapshot["metrics"]["auth_success_total"] == 3
