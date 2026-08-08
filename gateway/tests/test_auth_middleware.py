"""Tests for Gateway authentication middleware enforcement.

Verifies that:
- Public endpoints are accessible without authentication
- Protected endpoints require valid JWT Bearer token
- Invalid/expired/revoked tokens are rejected with 401
- Valid tokens allow request to proceed
"""

import time

import pytest
from starlette.testclient import TestClient

from app.main import create_app
from app.middleware.authentication import _get_jwt_service, _is_public_path


@pytest.fixture
def app():
    """Create a test app instance."""
    return create_app()


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def jwt_service():
    """Reset and get the JWT service."""
    import app.middleware.authentication as auth_mod

    auth_mod._jwt_service = None  # Reset singleton
    """Get the JWT service used by the middleware."""
    return _get_jwt_service()


@pytest.fixture
def valid_token(jwt_service):
    """Generate a valid JWT token."""
    return jwt_service.generate_access_token(user_id="test-user", roles=["user"])


@pytest.fixture
def expired_token():
    """Generate an expired JWT token."""
    from sona_security.infrastructure.jwt_service import JWTConfig, JWTService

    svc = JWTService(
        JWTConfig(secret="dev-secret-change-in-production", access_token_expiry_seconds=0)
    )
    token = svc.generate_access_token(user_id="test-user", roles=["user"])
    time.sleep(1)
    return token


class TestPublicEndpoints:
    """Public endpoints accessible without authentication."""

    def test_health_endpoint(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_ready_endpoint(self, client: TestClient) -> None:
        response = client.get("/ready")
        assert response.status_code != 401  # Not blocked by auth

    def test_health_detailed(self, client: TestClient) -> None:
        response = client.get("/health/detailed")
        assert response.status_code != 401  # Not blocked by auth

    def test_is_public_path_function(self) -> None:
        assert _is_public_path("/health") is True
        assert _is_public_path("/ready") is True
        assert _is_public_path("/docs") is True
        assert _is_public_path("/v1/chat/completions") is False
        assert _is_public_path("/v1/models") is False


class TestMissingAuth:
    """Protected endpoints reject requests without auth."""

    def test_missing_auth_header(self, client: TestClient) -> None:
        response = client.post("/v1/chat/completions", json={"messages": []})
        assert response.status_code == 401
        assert "Missing Authorization header" in response.json()["detail"]

    def test_models_requires_auth(self, client: TestClient) -> None:
        response = client.get("/v1/models")
        assert response.status_code == 401

    def test_providers_requires_auth(self, client: TestClient) -> None:
        response = client.get("/v1/providers")
        assert response.status_code == 401


class TestMalformedAuth:
    """Malformed authorization headers are rejected."""

    def test_no_bearer_prefix(self, client: TestClient) -> None:
        response = client.get("/v1/models", headers={"Authorization": "Token abc123"})
        assert response.status_code == 401
        assert "Invalid Authorization header format" in response.json()["detail"]

    def test_empty_bearer(self, client: TestClient) -> None:
        response = client.get("/v1/models", headers={"Authorization": "Bearer"})
        assert response.status_code == 401

    def test_basic_auth_not_accepted(self, client: TestClient) -> None:
        response = client.get("/v1/models", headers={"Authorization": "Basic dXNlcjpwYXNz"})
        assert response.status_code == 401


class TestInvalidTokens:
    """Invalid tokens are rejected with 401."""

    def test_invalid_jwt_string(self, client: TestClient) -> None:
        response = client.get("/v1/models", headers={"Authorization": "Bearer not-a-jwt"})
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

    def test_tampered_jwt(self, client: TestClient, valid_token: str) -> None:
        tampered = valid_token[:-5] + "XXXXX"
        response = client.get("/v1/models", headers={"Authorization": f"Bearer {tampered}"})
        assert response.status_code == 401

    def test_expired_jwt(self, client: TestClient, expired_token: str) -> None:
        response = client.get("/v1/models", headers={"Authorization": f"Bearer {expired_token}"})
        assert response.status_code == 401

    def test_revoked_jwt(self, client: TestClient, valid_token: str, jwt_service) -> None:
        jwt_service.revoke_token(valid_token)
        response = client.get("/v1/models", headers={"Authorization": f"Bearer {valid_token}"})
        assert response.status_code == 401

    def test_wrong_secret_jwt(self, client: TestClient) -> None:
        from sona_security.infrastructure.jwt_service import JWTConfig, JWTService

        other_svc = JWTService(JWTConfig(secret="wrong-secret"))
        token = other_svc.generate_access_token(user_id="hacker", roles=["admin"])
        response = client.get("/v1/models", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


class TestValidAuth:
    """Valid tokens allow access to protected endpoints."""

    def test_valid_token_models(self, client: TestClient, valid_token: str) -> None:
        response = client.get("/v1/models", headers={"Authorization": f"Bearer {valid_token}"})
        assert response.status_code != 401  # Not blocked by auth

    def test_valid_token_providers(self, client: TestClient, valid_token: str) -> None:
        response = client.get("/v1/providers", headers={"Authorization": f"Bearer {valid_token}"})
        assert response.status_code != 401  # Not blocked by auth
