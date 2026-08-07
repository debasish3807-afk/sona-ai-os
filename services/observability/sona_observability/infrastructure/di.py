"""Dependency injection factory for the observability runtime.

Provides a simple factory function to create a fully configured
ObservabilityRuntime instance with all components wired together.
"""

from __future__ import annotations

from sona_observability.infrastructure.observability_runtime import ObservabilityRuntime


def create_observability_runtime(
    service_name: str = "sona-ai-os",
    sample_rate: float = 1.0,
) -> ObservabilityRuntime:
    """Create a fully configured ObservabilityRuntime instance.

    Args:
        service_name: Name of the service for identification in metrics/traces/logs.
        sample_rate: Log sampling rate (0.0 to 1.0). Default is 1.0 (no sampling).

    Returns:
        A configured ObservabilityRuntime instance with all components wired.
    """
    return ObservabilityRuntime(
        service_name=service_name,
        sample_rate=sample_rate,
    )
