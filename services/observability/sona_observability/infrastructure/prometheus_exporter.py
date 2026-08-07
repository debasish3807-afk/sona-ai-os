"""Prometheus text format exporter.

Exports all metrics from the MetricsRegistry in valid Prometheus
exposition format, parseable by real Prometheus scrapers.
"""

from __future__ import annotations

from sona_observability.infrastructure.metrics_registry import MetricsRegistry


class PrometheusExporter:
    """Exports metrics in Prometheus text exposition format.

    Generates output conforming to the Prometheus text-based exposition
    format specification, including HELP and TYPE annotations.
    """

    def __init__(self, registry: MetricsRegistry) -> None:
        self._registry = registry

    def export(self) -> str:
        """Export all metrics in Prometheus text format.

        Returns:
            A string in Prometheus exposition format.
        """
        return self._registry.export_prometheus()

    def content_type(self) -> str:
        """Return the content type for Prometheus exposition format."""
        return "text/plain; version=0.0.4; charset=utf-8"
