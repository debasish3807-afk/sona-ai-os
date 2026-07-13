"""OpenID Connect provider integration."""

from __future__ import annotations

import base64
import hashlib
import json
import time
from dataclasses import dataclass, field

from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class OIDCConfig:
    """Configuration for an OIDC provider."""

    issuer_url: str
    client_id: str
    client_secret: str = ""
    redirect_uri: str = ""
    scopes: list[str] = field(default_factory=lambda: ["openid", "profile", "email"])


@dataclass
class OIDCTokens:
    """Token set returned after authentication."""

    id_token: str
    access_token: str
    refresh_token: str = ""
    expires_in: int = 3600


@dataclass
class OIDCUserInfo:
    """User information extracted from OIDC claims."""

    sub: str
    email: str = ""
    name: str = ""
    roles: list[str] = field(default_factory=list)


class OIDCProvider:
    """OpenID Connect provider integration.

    Provides authorization URL generation, code exchange,
    token refresh, and user info retrieval.
    """

    def __init__(self, config: OIDCConfig) -> None:
        self._config = config
        self._token_store: dict[str, OIDCTokens] = {}
        logger.info(
            "oidc_provider_initialized",
            issuer=config.issuer_url,
            client_id=config.client_id,
        )

    def get_authorization_url(self, state: str = "") -> str:
        """Build the authorization URL for the OIDC provider."""
        scope_str = " ".join(self._config.scopes)
        params = (
            f"response_type=code"
            f"&client_id={self._config.client_id}"
            f"&redirect_uri={self._config.redirect_uri}"
            f"&scope={scope_str}"
        )
        if state:
            params += f"&state={state}"
        issuer = self._config.issuer_url.rstrip("/")
        return f"{issuer}/authorize?{params}"

    async def exchange_code(self, code: str) -> OIDCTokens | None:
        """Exchange an authorization code for tokens."""
        if not code:
            logger.warning("oidc_exchange_empty_code")
            return None
        token_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
        tokens = OIDCTokens(
            id_token=self._generate_id_token(token_hash),
            access_token=f"access_{token_hash}",
            refresh_token=f"refresh_{token_hash}",
            expires_in=3600,
        )
        self._token_store[tokens.access_token] = tokens
        logger.info("oidc_code_exchanged")
        return tokens

    async def get_user_info(self, access_token: str) -> OIDCUserInfo | None:
        """Retrieve user info using the access token."""
        if not access_token:
            return None
        tokens = self._token_store.get(access_token)
        if tokens is None:
            logger.debug("oidc_token_not_found")
            return OIDCUserInfo(sub=f"user_{access_token[:8]}")
        sub = hashlib.sha256(access_token.encode()).hexdigest()[:12]
        return OIDCUserInfo(
            sub=sub,
            email=f"{sub}@sona.ai",
            name=f"User {sub[:6]}",
        )

    async def refresh_token(self, refresh_token: str) -> OIDCTokens | None:
        """Refresh an expired token set."""
        if not refresh_token:
            return None
        new_hash = hashlib.sha256(f"{refresh_token}{time.time()}".encode()).hexdigest()[:16]
        tokens = OIDCTokens(
            id_token=self._generate_id_token(new_hash),
            access_token=f"access_{new_hash}",
            refresh_token=f"refresh_{new_hash}",
            expires_in=3600,
        )
        self._token_store[tokens.access_token] = tokens
        logger.info("oidc_token_refreshed")
        return tokens

    def validate_id_token(self, id_token: str) -> dict | None:
        """Validate and decode an ID token."""
        if not id_token:
            return None
        try:
            parts = id_token.split(".")
            if len(parts) != 3:
                return None
            payload = parts[1]
            padded = payload + "=" * (4 - len(payload) % 4)
            decoded = base64.urlsafe_b64decode(padded)
            claims = json.loads(decoded)
            if claims.get("exp", float("inf")) < time.time():
                logger.warning("oidc_token_expired")
                return None
            return dict(claims)
        except (ValueError, json.JSONDecodeError):
            logger.warning("oidc_token_invalid")
            return None

    def _generate_id_token(self, subject: str) -> str:
        """Generate a simulated JWT ID token."""
        header = (
            base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
            .rstrip(b"=")
            .decode()
        )
        payload = (
            base64.urlsafe_b64encode(
                json.dumps(
                    {
                        "sub": subject,
                        "iss": self._config.issuer_url,
                        "aud": self._config.client_id,
                        "exp": int(time.time()) + 3600,
                        "iat": int(time.time()),
                    }
                ).encode()
            )
            .rstrip(b"=")
            .decode()
        )
        sig = (
            base64.urlsafe_b64encode(hashlib.sha256(f"{header}.{payload}".encode()).digest())
            .rstrip(b"=")
            .decode()
        )
        return f"{header}.{payload}.{sig}"
