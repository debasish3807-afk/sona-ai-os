"""Security Runtime orchestrator.

Combines all security components into a unified high-level API
for the gateway and other services.
"""

from typing import Any

import structlog

from sona_security.domain.models import AuthToken, Permission
from sona_security.infrastructure.ai_safety import AISafetyService
from sona_security.infrastructure.api_key_service import APIKeyService
from sona_security.infrastructure.audit_logger import AuditLogger
from sona_security.infrastructure.auth_service import AuthService
from sona_security.infrastructure.cors_config import CORSManager
from sona_security.infrastructure.jwt_service import JWTService
from sona_security.infrastructure.mcp_security import MCPSecurity
from sona_security.infrastructure.metrics import SecurityMetrics
from sona_security.infrastructure.password_service import PasswordService
from sona_security.infrastructure.permission_engine import PermissionEngine
from sona_security.infrastructure.prompt_guard import PromptGuard
from sona_security.infrastructure.rate_limiter import RateLimiter
from sona_security.infrastructure.rbac_engine import RBACEngine
from sona_security.infrastructure.secret_manager import SecretManager
from sona_security.infrastructure.security_headers import SecurityHeaders
from sona_security.infrastructure.user_store import UserStore

logger = structlog.get_logger()


class SecurityRuntime:
    """Unified security runtime combining all security components."""

    def __init__(
        self,
        jwt_service: JWTService,
        password_service: PasswordService,
        user_store: UserStore,
        auth_service: AuthService,
        rbac_engine: RBACEngine,
        permission_engine: PermissionEngine,
        api_key_service: APIKeyService,
        rate_limiter: RateLimiter,
        ai_safety: AISafetyService,
        prompt_guard: PromptGuard,
        mcp_security: MCPSecurity,
        audit_logger: AuditLogger,
        secret_manager: SecretManager,
        security_headers: SecurityHeaders,
        cors_manager: CORSManager,
        metrics: SecurityMetrics,
    ) -> None:
        self.jwt = jwt_service
        self.passwords = password_service
        self.users = user_store
        self.auth = auth_service
        self.rbac = rbac_engine
        self.permissions = permission_engine
        self.api_keys = api_key_service
        self.rate_limiter = rate_limiter
        self.ai_safety = ai_safety
        self.prompt_guard = prompt_guard
        self.mcp = mcp_security
        self.audit = audit_logger
        self.secrets = secret_manager
        self.headers = security_headers
        self.cors = cors_manager
        self.metrics = metrics

    async def authenticate_request(
        self,
        credentials: dict[str, Any],
        ip_address: str = "unknown",
    ) -> AuthToken:
        """Authenticate a request and record metrics.

        Raises:
            ValueError: If authentication fails.
        """
        credentials["ip_address"] = ip_address

        try:
            token = await self.auth.authenticate(credentials)
            self.metrics.record_auth_success()
            await self.audit.log(
                event_type="auth_success",
                user_id=token.user_id,
                ip_address=ip_address,
            )
            return token
        except ValueError:
            self.metrics.record_auth_failure()
            await self.audit.log(
                event_type="auth_failure",
                user_id=credentials.get("username", ""),
                ip_address=ip_address,
                details={"reason": "invalid_credentials"},
            )
            raise

    async def validate_request_token(self, token: str) -> AuthToken | None:
        """Validate a request token and record metrics."""
        result = await self.auth.validate_token(token)
        self.metrics.record_token_validation(success=result is not None)
        return result

    async def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        """Check if a user has permission for a resource/action."""
        permission = Permission(resource=resource, action=action)
        allowed = await self.rbac.check_permission(user_id, permission)
        self.metrics.record_permission_check(granted=allowed)

        if not allowed:
            await self.audit.log(
                event_type="permission_denied",
                user_id=user_id,
                resource=resource,
                action=action,
            )

        return allowed

    async def check_rate_limit(
        self, user_id: str, endpoint: str = "default"
    ) -> tuple[bool, dict[str, Any]]:
        """Check rate limit for a request.

        Returns:
            Tuple of (allowed, headers_dict).
        """
        result = await self.rate_limiter.check_rate_limit(user_id, endpoint)
        if not result.allowed:
            self.metrics.record_rate_limit_hit()
            await self.audit.log(
                event_type="rate_limit_hit",
                user_id=user_id,
                resource=endpoint,
            )

        headers = {
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Reset": str(int(result.reset_at)),
        }
        return (result.allowed, headers)

    async def check_ai_safety(self, content: str, user_id: str = "") -> tuple[bool, str | None]:
        """Check content for AI safety violations."""
        result = await self.prompt_guard.process_input(content, user_id=user_id)
        self.metrics.record_safety_check(blocked=not result.allowed)
        if not result.allowed:
            return (False, result.reason)
        return (True, None)

    async def validate_api_key(self, key: str) -> tuple[bool, str]:
        """Validate an API key and return (valid, user_id)."""
        metadata = await self.api_keys.validate_key(key)
        if metadata is None:
            return (False, "")
        return (True, metadata.user_id)

    async def get_response_headers(
        self, origin: str = "", request_id: str | None = None
    ) -> dict[str, str]:
        """Get all response headers (security + CORS)."""
        headers = self.headers.get_headers(request_id=request_id)
        if origin:
            cors_headers = self.cors.get_cors_headers(origin)
            headers.update(cors_headers)
        return headers

    async def startup(self) -> None:
        """Initialize the security runtime."""
        await self.secrets.load_secrets()
        valid, missing = await self.secrets.validate_required()
        if not valid:
            logger.warning("security_startup_missing_secrets", missing=missing)
        logger.info("security_runtime_started")

    async def health_check(self) -> dict[str, Any]:
        """Get health check status."""
        return {
            "status": "healthy",
            "metrics": self.metrics.snapshot(),
            "secrets_loaded": self.secrets.is_loaded,
        }
