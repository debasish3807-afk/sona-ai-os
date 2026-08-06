"""Dependency injection for the API Gateway."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status


async def get_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
) -> str | None:
    """Extract API key from request headers."""
    return x_api_key


async def require_api_key(
    api_key: Annotated[str | None, Depends(get_api_key)],
) -> str:
    """Require a valid API key for protected endpoints."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )
    return api_key
