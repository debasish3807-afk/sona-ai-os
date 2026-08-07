"""Dependency injection for the API Gateway.

Provides FastAPI dependencies including the pipeline singleton
and API key validation.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.pipeline.orchestrator import PipelineOrchestrator


@lru_cache(maxsize=1)
def _create_pipeline() -> PipelineOrchestrator:
    """Create the pipeline singleton with all wired dependencies.

    Uses the DI factories from each service to create real instances
    of THALAMUS, Brain OS, and Memory OS, then wires them into the
    pipeline orchestrator.

    Returns:
        A fully-configured PipelineOrchestrator.
    """
    from sona_brain.infrastructure.di import create_brain_runtime
    from sona_memory.infrastructure.di import create_memory_manager
    from sona_thalamus.infrastructure.di import create_thalamus_router

    thalamus = create_thalamus_router()
    brain = create_brain_runtime()
    memory = create_memory_manager()

    # AI Kernel is wired internally by Brain OS's StepExecutor
    return PipelineOrchestrator(
        thalamus=thalamus,
        brain=brain,
        memory=memory,
        kernel=None,
    )


def get_pipeline() -> PipelineOrchestrator:
    """FastAPI dependency that provides the pipeline orchestrator.

    Returns:
        The singleton PipelineOrchestrator instance.
    """
    return _create_pipeline()


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
