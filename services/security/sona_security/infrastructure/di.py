"""Dependency injection factory for the security runtime.

Creates and wires all security components together.
"""

from sona_security.infrastructure.ai_safety import AISafetyService
from sona_security.infrastructure.api_key_service import APIKeyService
from sona_security.infrastructure.audit_logger import AuditLogger
from sona_security.infrastructure.auth_service import AuthService
from sona_security.infrastructure.cors_config import CORSManager
from sona_security.infrastructure.jwt_service import JWTConfig, JWTService
from sona_security.infrastructure.mcp_security import MCPSecurity
from sona_security.infrastructure.metrics import SecurityMetrics
from sona_security.infrastructure.password_service import PasswordService
from sona_security.infrastructure.permission_engine import PermissionEngine
from sona_security.infrastructure.prompt_guard import PromptGuard
from sona_security.infrastructure.rate_limiter import RateLimiter
from sona_security.infrastructure.rbac_engine import RBACEngine
from sona_security.infrastructure.secret_manager import SecretManager
from sona_security.infrastructure.security_headers import SecurityHeaders
from sona_security.infrastructure.security_runtime import SecurityRuntime
from sona_security.infrastructure.user_store import UserStore


def create_security_runtime(
    jwt_secret: str = "dev-secret-change-in-production",
) -> SecurityRuntime:
    """Create a fully-wired SecurityRuntime instance.

    Args:
        jwt_secret: The secret key for JWT token signing.

    Returns:
        A configured SecurityRuntime instance.
    """
    # Core services
    jwt_config = JWTConfig(secret=jwt_secret)
    jwt_service = JWTService(config=jwt_config)
    password_service = PasswordService()
    user_store = UserStore(password_service=password_service)

    # Authentication & Authorization
    auth_service = AuthService(jwt_service=jwt_service, user_store=user_store)
    rbac_engine = RBACEngine()
    permission_engine = PermissionEngine()

    # API Keys & Rate Limiting
    api_key_service = APIKeyService()
    rate_limiter = RateLimiter()

    # AI Safety
    ai_safety = AISafetyService()
    prompt_guard = PromptGuard(ai_safety=ai_safety)
    mcp_security = MCPSecurity()

    # Support services
    audit_logger = AuditLogger()
    secret_manager = SecretManager()
    security_headers = SecurityHeaders()
    cors_manager = CORSManager()
    metrics = SecurityMetrics()

    return SecurityRuntime(
        jwt_service=jwt_service,
        password_service=password_service,
        user_store=user_store,
        auth_service=auth_service,
        rbac_engine=rbac_engine,
        permission_engine=permission_engine,
        api_key_service=api_key_service,
        rate_limiter=rate_limiter,
        ai_safety=ai_safety,
        prompt_guard=prompt_guard,
        mcp_security=mcp_security,
        audit_logger=audit_logger,
        secret_manager=secret_manager,
        security_headers=security_headers,
        cors_manager=cors_manager,
        metrics=metrics,
    )
