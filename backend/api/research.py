"""Deep research API endpoints."""

from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, Field

from research_engine.engine import DeepResearchEngine

router = APIRouter(prefix="/research", tags=["research"])


class DeepResearchRequest(BaseModel):
    """Request for a deep research run."""

    query: str = Field(min_length=1)
    offline: bool = False
    use_cache: bool = True
    local_roots: list[str] | None = None


@router.post("/deep")
async def deep_research(request: DeepResearchRequest) -> dict:
    """Run local-first deep research across local and free web providers."""
    roots = [Path(root) for root in request.local_roots] if request.local_roots else None
    report = await DeepResearchEngine(local_roots=roots).research(
        request.query, offline=request.offline, use_cache=request.use_cache
    )
    return {"ok": True, "report": report}
