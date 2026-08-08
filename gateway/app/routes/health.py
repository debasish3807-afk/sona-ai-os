"""Health, readiness, and liveness endpoints.

Provides Kubernetes-style health probes for the Sona AI OS Gateway:
- /health: Basic liveness probe (process alive)
- /ready: Readiness probe (dependencies available)
- /health/detailed: Full dependency status
"""

from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from sona_shared.config.env import InfraConfig
from sona_shared.health.checks import (
    HealthManager,
    OllamaHealthCheck,
    QdrantHealthCheck,
    RedisHealthCheck,
)

logger = structlog.get_logger()

router = APIRouter()

# Lazily initialized health manager
_health_manager: HealthManager | None = None


def _get_health_manager() -> HealthManager:
    """Get or create the health manager with configured checks."""
    global _health_manager  # noqa: PLW0603
    if _health_manager is None:
        config = InfraConfig.from_env()
        _health_manager = HealthManager()
        _health_manager.register(RedisHealthCheck(config.redis_url))
        _health_manager.register(QdrantHealthCheck(config.qdrant_url))
        _health_manager.register(OllamaHealthCheck(config.ollama_url))
    return _health_manager


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Basic liveness probe - returns 200 if process is running."""
    return {"status": "healthy", "service": "sona-gateway"}


@router.get("/ready")
async def readiness_check() -> JSONResponse:
    """Readiness probe - returns 200 only if all dependencies are connected."""
    manager = _get_health_manager()
    await manager.check_all()
    readiness = manager.get_readiness()

    status_code = 200 if manager.is_ready else 503
    return JSONResponse(content=readiness, status_code=status_code)


@router.get("/health/detailed")
async def detailed_health() -> JSONResponse:
    """Detailed health with per-dependency status."""
    manager = _get_health_manager()
    results = await manager.check_all()

    checks_detail: dict[str, Any] = {}
    for name, result in results.items():
        checks_detail[name] = {
            "status": result.status.value,
            "latency_ms": round(result.latency_ms, 2),
            "message": result.message,
            "checked_at": result.checked_at.isoformat(),
        }

    overall_status = (
        "healthy" if manager.is_healthy else ("degraded" if manager.is_ready else "unhealthy")
    )

    response = {
        "service": "sona-gateway",
        "status": overall_status,
        "checks": checks_detail,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    status_code = 200 if manager.is_ready else 503
    return JSONResponse(content=response, status_code=status_code)
