"""Tests for security headers."""

from sona_security.infrastructure.security_headers import (
    SecurityHeaders,
    SecurityHeadersConfig,
)


class TestSecurityHeaders:
    def setup_method(self) -> None:
        self.headers = SecurityHeaders()

    def test_hsts_header(self) -> None:
        h = self.headers.get_headers()
        assert "Strict-Transport-Security" in h
        assert "max-age=31536000" in h["Strict-Transport-Security"]
        assert "includeSubDomains" in h["Strict-Transport-Security"]

    def test_hsts_preload(self) -> None:
        config = SecurityHeadersConfig(hsts_preload=True)
        headers = SecurityHeaders(config=config)
        h = headers.get_headers()
        assert "preload" in h["Strict-Transport-Security"]

    def test_x_frame_options(self) -> None:
        h = self.headers.get_headers()
        assert h["X-Frame-Options"] == "DENY"

    def test_x_content_type_options(self) -> None:
        h = self.headers.get_headers()
        assert h["X-Content-Type-Options"] == "nosniff"

    def test_x_xss_protection(self) -> None:
        h = self.headers.get_headers()
        assert h["X-XSS-Protection"] == "1; mode=block"

    def test_referrer_policy(self) -> None:
        h = self.headers.get_headers()
        assert h["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_csp_header(self) -> None:
        h = self.headers.get_headers()
        assert "Content-Security-Policy" in h
        csp = h["Content-Security-Policy"]
        assert "default-src" in csp
        assert "'self'" in csp

    def test_permissions_policy(self) -> None:
        h = self.headers.get_headers()
        assert "Permissions-Policy" in h
        assert "geolocation=()" in h["Permissions-Policy"]

    def test_request_id_auto_generated(self) -> None:
        h = self.headers.get_headers()
        assert "X-Request-ID" in h
        assert len(h["X-Request-ID"]) == 32  # 16 bytes hex

    def test_request_id_custom(self) -> None:
        h = self.headers.get_headers(request_id="my-request-123")
        assert h["X-Request-ID"] == "my-request-123"

    def test_request_id_disabled(self) -> None:
        config = SecurityHeadersConfig(add_request_id=False)
        headers = SecurityHeaders(config=config)
        h = headers.get_headers()
        assert "X-Request-ID" not in h

    def test_custom_frame_options(self) -> None:
        config = SecurityHeadersConfig(frame_options="SAMEORIGIN")
        headers = SecurityHeaders(config=config)
        h = headers.get_headers()
        assert h["X-Frame-Options"] == "SAMEORIGIN"

    def test_custom_csp(self) -> None:
        config = SecurityHeadersConfig(
            csp_directives={"default-src": "'none'", "script-src": "'self'"}
        )
        headers = SecurityHeaders(config=config)
        h = headers.get_headers()
        assert "default-src 'none'" in h["Content-Security-Policy"]
