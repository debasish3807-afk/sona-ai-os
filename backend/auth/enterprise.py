"""Enterprise authentication with JWT tokens and RBAC."""

from __future__ import annotations

import hashlib
import hmac
import json
import threading
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from dataclasses import dataclass
from enum import StrEnum

from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class JWTConfig:
    """JWT configuration settings."""

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


@dataclass
class TokenPair:
    """Access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 0


class RBACRole(StrEnum):
    """Role-based access control roles."""

    ADMIN = "admin"
    OPERATOR = "operator"
    USER = "user"
    SERVICE = "service"
    READONLY = "readonly"


class RBACPermission(StrEnum):
    """RBAC permission types."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"
    MANAGE_USERS = "manage_users"
    MANAGE_AGENTS = "manage_agents"
    MANAGE_WORKFLOWS = "manage_workflows"


# Role -> Permissions mapping
ROLE_PERMISSIONS: dict[RBACRole, set[RBACPermission]] = {
    RBACRole.ADMIN: set(RBACPermission),
    RBACRole.OPERATOR: {
        RBACPermission.READ,
        RBACPermission.WRITE,
        RBACPermission.EXECUTE,
        RBACPermission.MANAGE_AGENTS,
        RBACPermission.MANAGE_WORKFLOWS,
    },
    RBACRole.USER: {
        RBACPermission.READ,
        RBACPermission.WRITE,
        RBACPermission.EXECUTE,
    },
    RBACRole.SERVICE: {
        RBACPermission.READ,
        RBACPermission.EXECUTE,
    },
    RBACRole.READONLY: {RBACPermission.READ},
}


class EnterpriseAuth:
    """Enterprise authentication with JWT and RBAC."""

    def __init__(self, config: JWTConfig) -> None:
        self._config = config
        self._user_roles: dict[str, list[RBACRole]] = {}
        self._lock = threading.Lock()

    def create_token_pair(
        self,
        user_id: str,
        roles: list[RBACRole],
        scopes: list[str] | None = None,
    ) -> TokenPair:
        """Create an access/refresh token pair."""
        now = int(time.time())
        access_exp = now + (self._config.access_token_expire_minutes * 60)
        refresh_exp = now + (self._config.refresh_token_expire_days * 86400)

        access_payload = {
            "sub": user_id,
            "roles": [r.value for r in roles],
            "scopes": scopes or [],
            "exp": access_exp,
            "type": "access",
        }
        refresh_payload = {
            "sub": user_id,
            "exp": refresh_exp,
            "type": "refresh",
        }

        access_token = self._encode(access_payload)
        refresh_token = self._encode(refresh_payload)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self._config.access_token_expire_minutes * 60,
        )

    def verify_access_token(self, token: str) -> dict | None:
        """Verify an access token. Returns payload or None."""
        payload = self._decode(token)
        if payload and payload.get("type") == "access":
            return payload
        return None

    def verify_refresh_token(self, token: str) -> dict | None:
        """Verify a refresh token. Returns payload or None."""
        payload = self._decode(token)
        if payload and payload.get("type") == "refresh":
            return payload
        return None

    def refresh_tokens(self, refresh_token: str) -> TokenPair | None:
        """Generate new tokens from a valid refresh token."""
        payload = self.verify_refresh_token(refresh_token)
        if not payload:
            return None
        user_id = payload["sub"]
        roles = self.get_user_roles(user_id)
        return self.create_token_pair(user_id, roles)

    def assign_role(self, user_id: str, role: RBACRole) -> None:
        """Assign a role to a user."""
        with self._lock:
            if user_id not in self._user_roles:
                self._user_roles[user_id] = []
            if role not in self._user_roles[user_id]:
                self._user_roles[user_id].append(role)
                logger.info("role_assigned", user_id=user_id, role=role.value)

    def check_permission(self, user_id: str, permission: RBACPermission) -> bool:
        """Check if a user has a specific permission."""
        roles = self.get_user_roles(user_id)
        for role in roles:
            if permission in ROLE_PERMISSIONS.get(role, set()):
                return True
        return False

    def get_user_roles(self, user_id: str) -> list[RBACRole]:
        """Get all roles for a user."""
        with self._lock:
            return list(self._user_roles.get(user_id, []))

    def _encode(self, payload: dict) -> str:
        """Encode a JWT-like token."""
        header = urlsafe_b64encode(json.dumps({"alg": self._config.algorithm}).encode()).decode()
        body = urlsafe_b64encode(json.dumps(payload).encode()).decode()
        signature = hmac.new(
            self._config.secret_key.encode(),
            f"{header}.{body}".encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"{header}.{body}.{signature}"

    def _decode(self, token: str) -> dict | None:
        """Decode and verify a JWT-like token."""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            header, body, signature = parts
            expected = hmac.new(
                self._config.secret_key.encode(),
                f"{header}.{body}".encode(),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(signature, expected):
                return None
            payload = json.loads(urlsafe_b64decode(body + "=="))
            if payload.get("exp", 0) < time.time():
                return None
            return dict(payload)
        except Exception:
            return None
