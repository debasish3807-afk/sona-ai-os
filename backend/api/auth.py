"""Authentication API endpoints.

Endpoints:
    POST /auth/register       — Create new user account
    POST /auth/login          — Authenticate and get tokens
    POST /auth/refresh        — Refresh access token
    POST /auth/logout         — Invalidate session (client-side)
    GET  /auth/me             — Get current user profile
    POST /auth/change-password — Change password
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth.middleware import get_current_user
from auth.tokens import create_access_token, create_refresh_token, decode_token
from auth.user_store import authenticate_user, change_password, create_user
from config.logging import get_logger
from models.user import User

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# --- Schemas ---


class RegisterRequest(BaseModel):
    """POST /auth/register request."""

    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(...)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """POST /auth/login request."""

    username: str = Field(...)
    password: str = Field(...)


class RefreshRequest(BaseModel):
    """POST /auth/refresh request."""

    refresh_token: str = Field(...)


class ChangePasswordRequest(BaseModel):
    """POST /auth/change-password request."""

    old_password: str = Field(...)
    new_password: str = Field(..., min_length=8, max_length=128)


class AuthResponse(BaseModel):
    """Authentication response with tokens."""

    success: bool = True
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    """User profile response."""

    success: bool = True
    user: dict


# --- Endpoints ---


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest) -> AuthResponse:
    """Create a new user account.

    Returns access and refresh tokens on successful registration.
    """
    user = create_user(
        username=request.username,
        email=request.email,
        password=request.password,
    )
    if user is None:
        raise HTTPException(status_code=409, detail="Username or email already exists")

    access_token = create_access_token(user.user_id, user.username, user.role.value)
    refresh_token = create_refresh_token(user.user_id)

    logger.info("User registered", username=user.username)

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user.to_public_dict(),
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest) -> AuthResponse:
    """Authenticate user and return tokens.

    Rate-limited: 5 failed attempts triggers 5-minute lockout.
    """
    user = authenticate_user(request.username, request.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(user.user_id, user.username, user.role.value)
    refresh_token = create_refresh_token(user.user_id)

    logger.info("User logged in", username=user.username)

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user.to_public_dict(),
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh(request: RefreshRequest) -> AuthResponse:
    """Refresh an access token using a valid refresh token.

    Implements token rotation — returns new access AND refresh tokens.
    """
    payload = decode_token(request.refresh_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    from auth.user_store import get_user_by_id

    user = get_user_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or deactivated")

    # Token rotation: issue new pair
    access_token = create_access_token(user.user_id, user.username, user.role.value)
    new_refresh_token = create_refresh_token(user.user_id)

    return AuthResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=user.to_public_dict(),
    )


@router.post("/logout")
async def logout(user: User = Depends(get_current_user)) -> dict:
    """Logout the current user.

    JWT is stateless — client must discard tokens.
    Server-side token revocation requires a blocklist (future).
    """
    logger.info("User logged out", username=user.username)
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    """Get the current authenticated user's profile."""
    return UserResponse(user=user.to_public_dict())


@router.post("/change-password")
async def change_password_endpoint(
    request: ChangePasswordRequest,
    user: User = Depends(get_current_user),
) -> dict:
    """Change the current user's password.

    Requires the old password for verification.
    """
    success = change_password(user.user_id, request.old_password, request.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid current password")

    logger.info("Password changed", username=user.username)
    return {"success": True, "message": "Password changed successfully"}
