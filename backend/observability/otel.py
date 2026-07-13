"""OpenTelemetry-compatible trace and metric exporter."""

from __future__ import annotations

import time
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class OTelExporter:
    """OpenTelemetry-compatible trace and metric exporter."""

    def __init__(
        self,
        service_name: str = "sona-ai-os",
        endpoint: str = "",
    ) -> None:
        self._service_name = service_name
        self._endpoint = endpoint
        self._exported_traces: int = 0
        self._exported_metrics: int = 0
        self._last_export_time: float = 0.0
        self._errors: int = 0

    def export_traces(self, spans: list[dict[str, Any]]) -> bool:
        """Simulate exporting traces to an OTLP endpoint."""
        if not spans:
            return True

        try:
            self._exported_traces += len(spans)
            self._last_export_time = time.time()
            logger.debug(
                "traces_exported",
                count=len(spans),
                service=self._service_name,
            )
            return True
        except Exception:
            self._errors += 1
            logger.error("trace_export_failed", service=self._service_name)
            return False

    def export_metrics(self, metrics: dict[str, Any]) -> bool:
        """Simulate exporting metrics to an OTLP endpoint."""
        if not metrics:
            return True

        try:
            self._exported_metrics += len(metrics)
            self._last_export_time = time.time()
            logger.debug(
                "metrics_exported",
                count=len(metrics),
                service=self._service_name,
            )
            return True
        except Exception:
            self._errors += 1
            logger.error("metrics_export_failed", service=self._service_name)
            return False

    def get_resource_attributes(self) -> dict[str, Any]:
        """Get the OpenTelemetry resource attributes."""
        return {
            "service.name": self._service_name,
            "service.version": "1.0.0",
            "telemetry.sdk.name": "sona-otel",
            "telemetry.sdk.language": "python",
            "deployment.environment": "development",
        }

    def get_stats(self) -> dict[str, Any]:
        """Get exporter statistics."""
        return {
            "service_name": self._service_name,
            "endpoint": self._endpoint,
            "exported_traces": self._exported_traces,
            "exported_metrics": self._exported_metrics,
            "errors": self._errors,
            "last_export_time": self._last_export_time,
        }
