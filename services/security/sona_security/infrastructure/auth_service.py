"""Authentication service implementing the AuthenticationPort.

Provides login, token validation, refresh, revocation, and logout.
"""

from datetime import UTC, datetime
from typing import Any

import structlog

from sona_security.application.ports import AuthenticationPort
from sona_security.domain.events import (
    AuthenticationFailedEvent,
    AuthenticationSucceededEvent,
    TokenRevokedEvent,
)
from sona_security.domain.models import AuthToken, Role
from sona_security.infrastructure.jwt_service import JWTService
from sona_security.infrastructure.user_store import UserStore

logger = structlog.get_logger()


class AuthService(AuthenticationPort):
    """Concrete authentication service implementing AuthenticationPort."""

    def __init__(self, jwt_service: JWTService, user_store: UserStore) -> None:
        self._jwt = jwt_service
        self._user_store = user_store
        self._events: list[object] = []

    @property
    def events(self) -> list[object]:
        """Access collected domain events."""
        return self._events

    def clear_events(self) -> None:
        """Clear collected domain events."""
        self._events.clear()

    async def authenticate(self, credentials: dict[str, Any]) -> AuthToken:
        """Authenticate a user with username/password credentials.

        Raises:
            ValueError: If credentials are invalid.
        """
        username = credentials.get("username", "")
        password = credentials.get("password", "")
        ip_address = credentials.get("ip_address", "unknown")

        if not username or not password:
            self._events.append(
                AuthenticationFailedEvent(
                    username=username,
                    reason="missing_credentials",
                    ip_address=ip_address,
                )
            )
            raise ValueError("Username and password are required")

        user = await self._user_store.authenticate(username, password)
        if user is None:
            self._events.append(
                AuthenticationFailedEvent(
                    username=username,
                    reason="invalid_credentials",
                    ip_address=ip_address,
                )
            )
            raise ValueError("Invalid credentials")

        roles_str = [r.value for r in user.roles]
        access_token = self._jwt.generate_access_token(user.user_id, roles_str)
        claims = self._jwt.decode_token(access_token)

        issued_at = datetime.now(UTC).isoformat()
        expires_at = ""
        if claims and "exp" in claims:
            exp_val = claims["exp"]
            if isinstance(exp_val, int):
                expires_at = datetime.fromtimestamp(exp_val, tz=UTC).isoformat()
        if claims and "iat" in claims:
            iat_val = claims["iat"]
            if isinstance(iat_val, int):
                issued_at = datetime.fromtimestamp(iat_val, tz=UTC).isoformat()

        self._events.append(
            AuthenticationSucceededEvent(
                user_id=user.user_id,
                method="password",
            )
        )

        logger.info("authentication_succeeded", user_id=user.user_id)
        return AuthToken(
            token=access_token,
            user_id=user.user_id,
            roles=user.roles,
            expires_at=expires_at,
            issued_at=issued_at,
        )

    async def validate_token(self, token: str) -> AuthToken | None:
        """Validate an existing token and return AuthToken if valid."""
        claims = self._jwt.validate_token(token)
        if claims is None:
            return None

        user_id = str(claims.get("sub", ""))
        roles_raw = claims.get("roles", [])
        roles: list[Role] = []
        if isinstance(roles_raw, list):
            for r in roles_raw:
                try:
                    roles.append(Role(str(r)))
                except ValueError:
                    pass

        exp_val = claims.get("exp")
        iat_val = claims.get("iat")
        expires_at = ""
        issued_at = ""
        if isinstance(exp_val, int):
            expires_at = datetime.fromtimestamp(exp_val, tz=UTC).isoformat()
        if isinstance(iat_val, int):
            issued_at = datetime.fromtimestamp(iat_val, tz=UTC).isoformat()

        return AuthToken(
            token=token,
            user_id=user_id,
            roles=roles,
            expires_at=expires_at,
            issued_at=issued_at,
        )

    async def refresh_token(self, refresh_token: str) -> AuthToken:
        """Refresh a token. Validates the refresh token and issues new access token.

        Raises:
            ValueError: If refresh token is invalid or not a refresh type.
        """
        claims = self._jwt.validate_token(refresh_token)
        if claims is None:
            raise ValueError("Invalid or expired refresh token")

        token_type = claims.get("type")
        if token_type != "refresh":
            raise ValueError("Token is not a refresh token")

        user_id = str(claims.get("sub", ""))
        roles_raw = claims.get("roles", [])
        roles_str: list[str] = []
        roles: list[Role] = []
        if isinstance(roles_raw, list):
            for r in roles_raw:
                roles_str.append(str(r))
                try:
                    roles.append(Role(str(r)))
                except ValueError:
                    pass

        new_access_token = self._jwt.generate_access_token(user_id, roles_str)
        new_claims = self._jwt.decode_token(new_access_token)

        expires_at = ""
        issued_at = ""
        if new_claims:
            exp_val = new_claims.get("exp")
            iat_val = new_claims.get("iat")
            if isinstance(exp_val, int):
                expires_at = datetime.fromtimestamp(exp_val, tz=UTC).isoformat()
            if isinstance(iat_val, int):
                issued_at = datetime.fromtimestamp(iat_val, tz=UTC).isoformat()

        return AuthToken(
            token=new_access_token,
            user_id=user_id,
            roles=roles,
            expires_at=expires_at,
            issued_at=issued_at,
        )

    async def revoke_token(self, token: str) -> bool:
        """Revoke a token by adding it to the revocation set."""
        self._jwt.revoke_token(token)
        claims = self._jwt.decode_token(token)
        user_id = ""
        if claims:
            user_id = str(claims.get("sub", ""))

        self._events.append(
            TokenRevokedEvent(
                user_id=user_id,
                token_id=token[:16] + "...",
            )
        )
        logger.info("token_revoked", user_id=user_id)
        return True

    async def logout(self, access_token: str, refresh_token: str | None = None) -> bool:
        """Revoke access and optionally refresh token."""
        await self.revoke_token(access_token)
        if refresh_token:
            await self.revoke_token(refresh_token)
        return True

    async def login(
        self, username: str, password: str, ip_address: str = "unknown"
    ) -> dict[str, str]:
        """Login convenience method returning both access and refresh tokens."""
        user = await self._user_store.authenticate(username, password)
        if user is None:
            self._events.append(
                AuthenticationFailedEvent(
                    username=username,
                    reason="invalid_credentials",
                    ip_address=ip_address,
                )
            )
            raise ValueError("Invalid credentials")

        roles_str = [r.value for r in user.roles]
        access_token = self._jwt.generate_access_token(user.user_id, roles_str)
        refresh_token = self._jwt.generate_refresh_token(user.user_id, roles_str)

        self._events.append(
            AuthenticationSucceededEvent(
                user_id=user.user_id,
                method="password",
            )
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_id": user.user_id,
        }
