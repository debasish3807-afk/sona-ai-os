"""Provider management endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ProviderStatus(BaseModel):
    """Status of a configured LLM provider."""

    name: str
    available: bool
    models: list[str] = []


@router.get("/providers")
async def list_providers() -> list[ProviderStatus]:
    """List configured LLM providers and their status.

    Scaffolding endpoint - actual provider health checks
    will be implemented in the ai-kernel service.
    """
    return []
