"""Security module tests — rate limiting, API keys, sessions, audit, abuse."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRateLimiter:
    """Test sliding window rate limiter."""

    def test_allow_under_limit(self):
        from security.rate_limit import RateLimiter

        limiter = RateLimiter()
        allowed, headers = limiter.check("192.168.1.1", "chat")
        assert allowed is True
        assert "X-RateLimit-Limit" in headers

    def test_block_over_limit(self):
        from security.rate_limit import RateLimit, RateLimiter

        limiter = RateLimiter(
            limits={
                "test": RateLimit(requests=3, window_seconds=60),
                "default": RateLimit(requests=100),
            }
        )
        for _ in range(3):
            limiter.check("test-ip", "test")
        allowed, headers = limiter.check("test-ip", "test")
        assert allowed is False
        assert "Retry-After" in headers

    def test_different_categories_independent(self):
        from security.rate_limit import RateLimit, RateLimiter

        limiter = RateLimiter(
            limits={
                "a": RateLimit(requests=2),
                "b": RateLimit(requests=2),
                "default": RateLimit(requests=100),
            }
        )
        limiter.check("ip1", "a")
        limiter.check("ip1", "a")
        allowed_a, _ = limiter.check("ip1", "a")
        allowed_b, _ = limiter.check("ip1", "b")
        assert allowed_a is False
        assert allowed_b is True

    def test_different_ips_independent(self):
        from security.rate_limit import RateLimit, RateLimiter

        limiter = RateLimiter(
            limits={"x": RateLimit(requests=1), "default": RateLimit(requests=100)}
        )
        limiter.check("ip-a", "x")
        allowed_a, _ = limiter.check("ip-a", "x")
        allowed_b, _ = limiter.check("ip-b", "x")
        assert allowed_a is False
        assert allowed_b is True

    def test_remaining_count(self):
        from security.rate_limit import RateLimit, RateLimiter

        limiter = RateLimiter(
            limits={"r": RateLimit(requests=5), "default": RateLimit(requests=100)}
        )
        assert limiter.get_remaining("ip", "r") == 5
        limiter.check("ip", "r")
        assert limiter.get_remaining("ip", "r") == 4

    def test_reset(self):
        from security.rate_limit import RateLimit, RateLimiter

        limiter = RateLimiter(
            limits={"z": RateLimit(requests=2), "default": RateLimit(requests=100)}
        )
        limiter.check("ip", "z")
        limiter.check("ip", "z")
        limiter.reset("ip", "z")
        allowed, _ = limiter.check("ip", "z")
        assert allowed is True

    def test_cleanup(self):
        from security.rate_limit import RateLimiter

        limiter = RateLimiter()
        limiter.check("old-ip", "default")
        # Cleanup shouldn't crash
        cleaned = limiter.cleanup()
        assert cleaned >= 0

    def test_headers_format(self):
        from security.rate_limit import RateLimiter

        limiter = RateLimiter()
        _, headers = limiter.check("header-ip", "chat")
        assert headers["X-RateLimit-Limit"] == "60"


class TestAPIKeys:
    """Test API key management."""

    def test_create_key(self):
        from security.api_keys import APIKeyManager

        mgr = APIKeyManager()
        key, record = mgr.create_key("user-1", "test key")
        assert key.startswith("sona_sk_")
        assert len(key) > 20
        assert record.user_id == "user-1"
        assert record.is_active is True

    def test_validate_key(self):
        from security.api_keys import APIKeyManager

        mgr = APIKeyManager()
        key, _ = mgr.create_key("user-2", "validate")
        record = mgr.validate_key(key)
        assert record is not None
        assert record.user_id == "user-2"

    def test_validate_invalid_key(self):
        from security.api_keys import APIKeyManager

        mgr = APIKeyManager()
        assert mgr.validate_key("sona_sk_invalid") is None

    def test_revoke_key(self):
        from security.api_keys import APIKeyManager

        mgr = APIKeyManager()
        key, record = mgr.create_key("user-3", "revoke-me")
        assert mgr.revoke_key(record.key_id, "user-3") is True
        assert mgr.validate_key(key) is None

    def test_rotate_key(self):
        from security.api_keys import APIKeyManager

        mgr = APIKeyManager()
        old_key, old_record = mgr.create_key("user-4", "rotate")
        result = mgr.rotate_key(old_record.key_id, "user-4")
        assert result is not None
        new_key, new_record = result
        assert new_key != old_key
        assert mgr.validate_key(old_key) is None
        assert mgr.validate_key(new_key) is not None

    def test_list_keys(self):
        from security.api_keys import APIKeyManager

        mgr = APIKeyManager()
        mgr.create_key("user-5", "key-a")
        mgr.create_key("user-5", "key-b")
        keys = mgr.list_keys("user-5")
        assert len(keys) == 2

    def test_key_prefix_format(self):
        from security.api_keys import APIKeyManager

        mgr = APIKeyManager()
        key, record = mgr.create_key("user-6")
        assert record.key_prefix == key[:12]

    def test_sha256_storage(self):
        from security.api_keys import APIKeyManager

        mgr = APIKeyManager()
        key, record = mgr.create_key("user-7")
        assert key not in record.key_hash
        assert len(record.key_hash) == 64  # SHA-256 hex


class TestSessions:
    """Test session management."""

    def test_create_session(self):
        from security.sessions import SessionManager

        mgr = SessionManager()
        session = mgr.create_session("user-1", ip_address="10.0.0.1", user_agent="Mozilla/5.0")
        assert session.user_id == "user-1"
        assert session.is_active is True
        assert session.ip_address == "10.0.0.1"

    def test_get_session(self):
        from security.sessions import SessionManager

        mgr = SessionManager()
        session = mgr.create_session("user-2")
        found = mgr.get_session(session.session_id)
        assert found is not None
        assert found.user_id == "user-2"

    def test_revoke_session(self):
        from security.sessions import SessionManager

        mgr = SessionManager()
        session = mgr.create_session("user-3")
        assert mgr.revoke_session(session.session_id) is True
        assert mgr.get_session(session.session_id) is None

    def test_revoke_all_sessions(self):
        from security.sessions import SessionManager

        mgr = SessionManager()
        mgr.create_session("user-4")
        mgr.create_session("user-4")
        mgr.create_session("user-4")
        count = mgr.revoke_all_sessions("user-4")
        assert count == 3
        assert mgr.get_active_count("user-4") == 0

    def test_list_sessions(self):
        from security.sessions import SessionManager

        mgr = SessionManager()
        mgr.create_session("user-5", ip_address="1.1.1.1")
        mgr.create_session("user-5", ip_address="2.2.2.2")
        sessions = mgr.list_sessions("user-5")
        assert len(sessions) == 2

    def test_refresh_session(self):
        from security.sessions import SessionManager

        mgr = SessionManager()
        session = mgr.create_session("user-6")
        old_expires = session.expires_at
        time.sleep(0.01)
        mgr.refresh_session(session.session_id)
        assert session.expires_at >= old_expires

    def test_device_detection(self):
        from security.sessions import SessionManager

        mgr = SessionManager()
        s1 = mgr.create_session("u", user_agent="Mozilla/5.0 (iPhone; CPU)")
        s2 = mgr.create_session("u", user_agent="Mozilla/5.0 (Windows NT)")
        assert s1.device == "mobile"
        assert s2.device == "desktop"


class TestAuditLogger:
    """Test audit logging."""

    def test_log_event(self):
        from security.audit import AuditAction, AuditLogger

        logger = AuditLogger()
        logger.log_action(AuditAction.LOGIN, user_id="u1", username="admin", status="success")
        assert logger.total_events == 1

    def test_get_events_filtered(self):
        from security.audit import AuditAction, AuditLogger

        logger = AuditLogger()
        logger.log_action(AuditAction.LOGIN, user_id="u1")
        logger.log_action(AuditAction.LOGOUT, user_id="u2")
        logger.log_action(AuditAction.LOGIN, user_id="u1")
        events = logger.get_events(user_id="u1")
        assert len(events) == 2

    def test_get_events_by_action(self):
        from security.audit import AuditAction, AuditLogger

        logger = AuditLogger()
        logger.log_action(AuditAction.LOGIN_FAILED, ip_address="1.2.3.4")
        logger.log_action(AuditAction.LOGIN, ip_address="5.6.7.8")
        events = logger.get_events(action=AuditAction.LOGIN_FAILED)
        assert len(events) == 1

    def test_event_serialization(self):
        from security.audit import AuditAction, AuditEvent

        event = AuditEvent(action=AuditAction.PASSWORD_CHANGE, user_id="u1", status="success")
        data = event.to_dict()
        assert data["action"] == "password_change"
        assert data["status"] == "success"
        assert "timestamp" in data

    def test_max_entries_limit(self):
        from security.audit import AuditAction, AuditLogger

        logger = AuditLogger(max_entries=5)
        for i in range(10):
            logger.log_action(AuditAction.LOGIN, user_id=f"u{i}")
        assert logger.total_events == 5


class TestAbuseDetector:
    """Test abuse detection."""

    def test_not_blocked_initially(self):
        from security.abuse import AbuseDetector

        detector = AbuseDetector()
        assert detector.is_blocked("new-ip") is False

    def test_block_after_failed_logins(self):
        from security.abuse import AbuseDetector

        detector = AbuseDetector()
        for _ in range(10):
            detector.record_failed_login("bad-ip")
        assert detector.is_blocked("bad-ip") is True

    def test_block_after_permission_denials(self):
        from security.abuse import AbuseDetector

        detector = AbuseDetector()
        for _ in range(20):
            detector.record_permission_denial("bad-ip-2")
        assert detector.is_blocked("bad-ip-2") is True

    def test_block_after_rate_limit_hits(self):
        from security.abuse import AbuseDetector

        detector = AbuseDetector()
        for _ in range(50):
            detector.record_rate_limit_hit("bad-ip-3")
        assert detector.is_blocked("bad-ip-3") is True

    def test_unblock(self):
        from security.abuse import AbuseDetector

        detector = AbuseDetector()
        for _ in range(10):
            detector.record_failed_login("blocked-ip")
        assert detector.is_blocked("blocked-ip") is True
        detector.unblock("blocked-ip")
        assert detector.is_blocked("blocked-ip") is False

    def test_get_status(self):
        from security.abuse import AbuseDetector

        detector = AbuseDetector()
        detector.record_failed_login("status-ip")
        status = detector.get_status("status-ip")
        assert status["failed_logins"] == 1
        assert status["blocked"] is False


class TestMetrics:
    """Test security metrics."""

    def test_record_request(self):
        from security.metrics import SecurityMetrics

        m = SecurityMetrics()
        m.record_request()
        m.record_request()
        assert m.total_requests == 2

    def test_error_rate(self):
        from security.metrics import SecurityMetrics

        m = SecurityMetrics()
        m.record_request()
        m.record_request()
        m.record_error()
        assert m.error_rate == 0.5

    def test_latency_tracking(self):
        from security.metrics import SecurityMetrics

        m = SecurityMetrics()
        m.record_latency(10.0)
        m.record_latency(20.0)
        assert m.average_latency_ms == 15.0

    def test_to_dict(self):
        from security.metrics import SecurityMetrics

        m = SecurityMetrics()
        m.record_request()
        m.record_rate_limit()
        data = m.to_dict()
        assert data["total_requests"] == 1
        assert data["rate_limited_count"] == 1

    def test_reset(self):
        from security.metrics import SecurityMetrics

        m = SecurityMetrics()
        m.record_request()
        m.record_error()
        m.reset()
        assert m.total_requests == 0
        assert m.total_errors == 0


class TestSecurityHeaders:
    """Test security headers middleware."""

    def test_headers_defined(self):
        from security.headers import SECURITY_HEADERS

        assert "X-Frame-Options" in SECURITY_HEADERS
        assert SECURITY_HEADERS["X-Frame-Options"] == "DENY"
        assert "X-Content-Type-Options" in SECURITY_HEADERS
        assert "Strict-Transport-Security" in SECURITY_HEADERS
        assert "Content-Security-Policy" in SECURITY_HEADERS
        assert "Referrer-Policy" in SECURITY_HEADERS
        assert "Permissions-Policy" in SECURITY_HEADERS
