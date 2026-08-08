"""Shared fixtures for gateway tests.

Provides authenticated test clients for protected endpoint testing.
"""

import pytest

from app.middleware.authentication import _get_jwt_service


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Generate valid JWT auth headers for testing."""
    import app.middleware.authentication as auth_mod

    auth_mod._jwt_service = None  # Reset singleton
    svc = _get_jwt_service()
    token = svc.generate_access_token(user_id="test-user", roles=["admin"])
    return {"Authorization": f"Bearer {token}"}
