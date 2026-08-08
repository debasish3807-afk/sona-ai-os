"""JWT token service using pure Python (base64 + hmac + json).

Implements token generation, validation, and decoding without external
JWT libraries. Uses HMAC-SHA256 for signing.
"""

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass
class JWTConfig:
    """Configuration for JWT token generation."""

    secret: str = "dev-secret-change-in-production"
    access_token_expiry_seconds: int = 900  # 15 minutes
    refresh_token_expiry_seconds: int = 604800  # 7 days
    issuer: str = "sona-security"
    algorithm: str = "HS256"


class JWTService:
    """Pure Python JWT service using HMAC-SHA256."""

    def __init__(self, config: JWTConfig | None = None) -> None:
        self._config = config or JWTConfig()
        self._revoked_tokens: set[str] = set()

    def _base64url_encode(self, data: bytes) -> str:
        """Encode bytes to base64url without padding."""
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    def _base64url_decode(self, data: str) -> bytes:
        """Decode base64url string with padding restoration."""
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        return base64.urlsafe_b64decode(data)

    def _sign(self, message: str) -> str:
        """Create HMAC-SHA256 signature."""
        signature = hmac.new(
            self._config.secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return self._base64url_encode(signature)

    def generate_access_token(
        self, user_id: str, roles: list[str], extra_claims: dict[str, object] | None = None
    ) -> str:
        """Generate an access token with the given claims."""
        now = int(time.time())
        header = {"alg": self._config.algorithm, "typ": "JWT"}
        payload: dict[str, object] = {
            "sub": user_id,
            "roles": roles,
            "iss": self._config.issuer,
            "iat": now,
            "exp": now + self._config.access_token_expiry_seconds,
            "type": "access",
        }
        if extra_claims:
            payload.update(extra_claims)

        header_encoded = self._base64url_encode(json.dumps(header, separators=(",", ":")).encode())
        payload_encoded = self._base64url_encode(
            json.dumps(payload, separators=(",", ":")).encode()
        )
        message = f"{header_encoded}.{payload_encoded}"
        signature = self._sign(message)
        return f"{message}.{signature}"

    def generate_refresh_token(self, user_id: str, roles: list[str]) -> str:
        """Generate a refresh token with longer expiry."""
        now = int(time.time())
        header = {"alg": self._config.algorithm, "typ": "JWT"}
        payload: dict[str, object] = {
            "sub": user_id,
            "roles": roles,
            "iss": self._config.issuer,
            "iat": now,
            "exp": now + self._config.refresh_token_expiry_seconds,
            "type": "refresh",
        }

        header_encoded = self._base64url_encode(json.dumps(header, separators=(",", ":")).encode())
        payload_encoded = self._base64url_encode(
            json.dumps(payload, separators=(",", ":")).encode()
        )
        message = f"{header_encoded}.{payload_encoded}"
        signature = self._sign(message)
        return f"{message}.{signature}"

    def validate_token(self, token: str) -> dict[str, object] | None:
        """Validate a token's signature and expiry. Returns claims or None."""
        if token in self._revoked_tokens:
            return None

        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None

            header_encoded, payload_encoded, signature = parts
            message = f"{header_encoded}.{payload_encoded}"
            expected_signature = self._sign(message)

            if not hmac.compare_digest(signature, expected_signature):
                return None

            payload_bytes = self._base64url_decode(payload_encoded)
            payload: dict[str, object] = json.loads(payload_bytes)

            exp = payload.get("exp")
            if isinstance(exp, int) and exp < int(time.time()):
                return None

            return payload
        except (ValueError, json.JSONDecodeError, KeyError):
            return None

    def decode_token(self, token: str) -> dict[str, object] | None:
        """Decode a token without signature validation (for inspection)."""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            payload_bytes = self._base64url_decode(parts[1])
            return json.loads(payload_bytes)  # type: ignore[no-any-return]
        except (ValueError, json.JSONDecodeError):
            return None

    def verify_token(self, token: str) -> dict[str, object] | None:
        """Verify token signature, expiration, and revocation status.

        Returns the payload if valid, None if invalid/expired/revoked.
        """
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            # Verify signature
            message = f"{parts[0]}.{parts[1]}"
            expected_sig = self._sign(message)
            if not hmac.compare_digest(parts[2], expected_sig):
                return None
            # Decode payload
            payload_bytes = self._base64url_decode(parts[1])
            payload = json.loads(payload_bytes)
            # Check expiration
            exp = payload.get("exp", 0)
            if int(time.time()) > exp:
                return None
            # Check revocation
            if self.is_revoked(token):
                return None
            return payload  # type: ignore[no-any-return]
        except (ValueError, json.JSONDecodeError, KeyError, TypeError):
            return None

    def revoke_token(self, token: str) -> None:
        """Add token to revocation set."""
        self._revoked_tokens.add(token)

    def is_revoked(self, token: str) -> bool:
        """Check if a token has been revoked."""
        return token in self._revoked_tokens
