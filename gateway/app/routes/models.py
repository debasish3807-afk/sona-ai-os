"""Model listing endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ModelInfo(BaseModel):
    """Information about an available model."""

    id: str
    provider: str
    context_window: int
    capabilities: list[str] = []


@router.get("/models")
async def list_models() -> list[ModelInfo]:
    """List available models.

    Scaffolding endpoint - actual model registry will be populated
    from provider configurations.
    """
    return []
