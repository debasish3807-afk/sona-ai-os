"""JWT authentication middleware and dependencies.

Provides FastAPI dependency functions for:
    - Extracting and validating JWT from Authorization header
    - Resolving the current user
    - Checking role-based permissions
"""

from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.permissions import Permission, has_permission
from auth.tokens import decode_token
from auth.user_store import get_user_by_id
from models.user import User, UserRole

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> User:
    """FastAPI dependency — extract and validate the authenticated user.

    Reads the Bearer token from the Authorization header,
    decodes the JWT, and returns the corresponding User.

    Raises:
        HTTPException 401: If token is missing, invalid, or expired.
        HTTPException 403: If user account is deactivated.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    return user


def require_permission(permission: Permission):
    """FastAPI dependency factory — check a specific permission.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_permission(Permission.ADMIN))])

    Args:
        permission: The required permission.

    Returns:
        A dependency function that raises 403 if permission is denied.
    """

    async def _check(user: User = Depends(get_current_user)) -> User:
        if not has_permission(user.role, permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission.value} required",
            )
        return user

    return _check


def require_role(role: UserRole):
    """FastAPI dependency factory — require a minimum role.

    Args:
        role: The required role.

    Returns:
        A dependency function that raises 403 if role is insufficient.
    """
    role_hierarchy = {UserRole.USER: 0, UserRole.DEVELOPER: 1, UserRole.ADMIN: 2}

    async def _check(user: User = Depends(get_current_user)) -> User:
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(role, 0)
        if user_level < required_level:
            raise HTTPException(
                status_code=403,
                detail=f"Role {role.value} or higher required",
            )
        return user

    return _check
