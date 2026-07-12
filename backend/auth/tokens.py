"""JWT token creation and verification.

Uses python-jose for JWT encoding/decoding with HS256.
Tokens include user ID, role, and expiration.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

# Configuration from environment (with secure defaults)
JWT_SECRET = os.environ.get("JWT_SECRET", "sona-dev-secret-change-in-production")  # noqa: S105
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def create_access_token(
    user_id: str,
    username: str,
    role: str,
    expires_minutes: int | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        user_id: The user's unique ID.
        username: The user's username.
        role: The user's role.
        expires_minutes: Custom expiration (uses default if None).

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(UTC) + timedelta(minutes=expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": user_id,
        "username": username,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)  # type: ignore[no-any-return]


def create_refresh_token(user_id: str, expires_days: int | None = None) -> str:
    """Create a JWT refresh token.

    Args:
        user_id: The user's unique ID.
        expires_days: Custom expiration (uses default if None).

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(UTC) + timedelta(days=expires_days or REFRESH_TOKEN_EXPIRE_DAYS)
    payload: dict[str, Any] = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)  # type: ignore[no-any-return]


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT token.

    Args:
        token: The encoded JWT string.

    Returns:
        Token payload dict, or None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload  # type: ignore[no-any-return]
    except JWTError:
        return None
