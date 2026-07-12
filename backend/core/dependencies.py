"""FastAPI dependency injection providers."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request

from config.config import AppConfig
from config.settings import Settings, get_settings


@lru_cache(maxsize=1)
def get_app_config() -> AppConfig:
    """Get the application configuration singleton.

    Returns:
        Immutable AppConfig instance.
    """
    return AppConfig.from_settings()


def get_request_id(request: Request) -> str:
    """Extract or generate request ID from headers.

    Args:
        request: Incoming HTTP request.

    Returns:
        Request ID string.
    """
    return request.headers.get("X-Request-ID", "")


# Type aliases for dependency injection
SettingsDep = Annotated[Settings, Depends(get_settings)]
AppConfigDep = Annotated[AppConfig, Depends(get_app_config)]
RequestIdDep = Annotated[str, Depends(get_request_id)]
