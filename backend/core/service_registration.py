"""Service Registration — auto-registers all subsystems with the microkernel."""

from __future__ import annotations

import time
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)

# Service definitions for auto-registration
SERVICE_DEFINITIONS: list[dict[str, Any]] = [
    {
        "service_id": "executive",
        "name": "Executive Intelligence",
        "capabilities": ["goal_management", "strategic_planning", "decision_making"],
    },
    {
        "service_id": "meta_reasoning",
        "name": "Meta Reasoning Engine",
        "capabilities": ["plan_validation", "simulation", "quality_estimation"],
    },
    {
        "service_id": "runtime",
        "name": "Runtime Workflow Engine",
        "capabilities": ["workflow_execution", "task_scheduling", "checkpoint"],
    },
    {
        "service_id": "memory",
        "name": "Memory Manager",
        "capabilities": ["memory_store", "memory_search", "context_assembly"],
    },
    {
        "service_id": "capabilities",
        "name": "Capability Fabric",
        "capabilities": ["capability_registry", "capability_execution", "health_monitoring"],
    },
    {
        "service_id": "security",
        "name": "Security Layer",
        "capabilities": ["authentication", "rate_limiting", "audit_logging"],
    },
    {
        "service_id": "persistence",
        "name": "Persistence Manager",
        "capabilities": ["state_persistence", "checkpoint", "recovery"],
    },
    {
        "service_id": "telemetry",
        "name": "Telemetry Service",
        "capabilities": ["metrics", "tracing", "health_monitoring"],
    },
]


def register_all_services(container: Any) -> int:
    """Register all subsystems with the microkernel service registry.

    Args:
        container: The DI container with resolved instances.

    Returns:
        Number of services successfully registered.
    """
    from microkernel.schemas import ServiceInfo

    service_registry = container.resolve("service_registry")
    registered = 0

    for svc_def in SERVICE_DEFINITIONS:
        info = ServiceInfo(
            service_id=svc_def["service_id"],
            name=svc_def["name"],
            version="15.5.0",
            registered_at=time.time(),
            last_heartbeat=time.time(),
            capabilities=svc_def["capabilities"],
        )
        success = service_registry.register(info)
        if success:
            registered += 1
            logger.debug("service_registered", service_id=svc_def["service_id"])

    logger.info("services_registered", total=registered)
    return registered


def get_service_status(container: Any) -> dict[str, Any]:
    """Get registration status for all services."""
    service_registry = container.resolve("service_registry")
    all_services = service_registry.list_all()
    return {
        "total_registered": len(all_services),
        "services": [
            {
                "service_id": svc.service_id,
                "name": svc.name,
                "capabilities": svc.capabilities,
                "health": svc.health,
            }
            for svc in all_services
        ],
    }
