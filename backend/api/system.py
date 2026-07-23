"""System API — production-grade health, info, and version endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from config.logging import get_logger
from production.config_loader import ConfigLoader
from production.health import HealthService
from production.system_info import SystemInfoService

logger = get_logger(__name__)

router = APIRouter(prefix="/system", tags=["system"])

_health = HealthService()
_sysinfo = SystemInfoService()
_config = ConfigLoader()


@router.get("/health")
async def system_health():
    """Get system health status with component-level breakdown."""
    result = _health.check()
    return {
        "healthy": result.healthy,
        "status": result.status,
        "uptime_seconds": result.uptime_seconds,
        "components": result.components,
        "details": result.details,
        "timestamp": result.timestamp,
    }


@router.get("/info")
async def system_info():
    """Get detailed system information (OS, Python, process)."""
    info = _sysinfo.get_info()
    return {"system": info}


@router.get("/version")
async def system_version():
    """Get application version information."""
    return _sysinfo.get_version_info()


@router.post("/config/validate")
async def validate_config():
    """Validate configuration at runtime."""
    result = _config.load()
    return {
        "success": result.success,
        "errors": result.errors,
        "warnings": result.warnings,
    }


@router.get("/health/register")
async def register_component(name: str, dependencies: str = ""):
    """Register a health-checked component."""
    deps = [d.strip() for d in dependencies.split(",") if d.strip()]
    _health.register(name, deps)
    return {"registered": name, "dependencies": deps}
