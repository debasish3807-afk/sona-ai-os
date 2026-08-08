"""Tests for Gateway rate limiting middleware."""

import pytest
from starlette.testclient import TestClient

import app.middleware.authentication as auth_mod
from app.main import create_app
from app.middleware.authentication import _get_jwt_service


@pytest.fixture
def client():
    auth_mod._jwt_service = None
    app = create_app()
    svc = _get_jwt_service()
    token = svc.generate_access_token(user_id="test", roles=["user"])
    c = TestClient(app)
    c.headers["Authorization"] = f"Bearer {token}"
    return c


class TestRateLimiting:
    def test_allowed_request(self, client: TestClient) -> None:
        response = client.get("/v1/models")
        assert response.status_code == 200

    def test_burst_allowed(self, client: TestClient) -> None:
        for _ in range(5):
            response = client.get("/v1/models")
            assert response.status_code == 200

    def test_rate_limit_exceeded(self, client: TestClient) -> None:
        # Exhaust the burst (chat has burst_size=5)
        statuses = []
        for _ in range(10):
            response = client.post(
                "/v1/chat/completions",
                json={"messages": [{"role": "user", "content": "hi"}], "model": "default"},
            )
            statuses.append(response.status_code)

        assert 429 in statuses, f"Expected 429 in statuses: {statuses}"

    def test_retry_after_header(self, client: TestClient) -> None:
        # Exhaust burst
        for _ in range(10):
            resp = client.post(
                "/v1/chat/completions",
                json={"messages": [{"role": "user", "content": "hi"}], "model": "default"},
            )
            if resp.status_code == 429:
                assert "Retry-After" in resp.headers
                assert int(resp.headers["Retry-After"]) >= 1
                break

    def test_health_exempt(self, client: TestClient) -> None:
        # Health should never be rate limited
        for _ in range(50):
            response = client.get("/health")
            assert response.status_code == 200
