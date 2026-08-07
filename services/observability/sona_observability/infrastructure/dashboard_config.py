"""Dashboard configuration templates for Grafana-compatible dashboards.

Generates JSON configurations for monitoring dashboards that visualize
the metrics collected by the observability runtime.
"""

from __future__ import annotations

from typing import Any


class DashboardConfig:
    """Generates Grafana-compatible dashboard JSON configurations.

    Provides pre-built dashboard templates for common monitoring scenarios.
    """

    @staticmethod
    def generate_overview_dashboard(service_name: str = "sona-ai-os") -> dict[str, Any]:
        """Generate an overview dashboard configuration.

        Args:
            service_name: The service name for the dashboard title.

        Returns:
            Grafana-compatible dashboard JSON configuration.
        """
        return {
            "dashboard": {
                "title": f"{service_name} Overview",
                "uid": f"{service_name}-overview",
                "timezone": "utc",
                "refresh": "30s",
                "panels": [
                    {
                        "title": "Request Rate",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "targets": [
                            {
                                "expr": "rate(http_requests_total[5m])",
                                "legendFormat": "{{method}} {{path}}",
                            }
                        ],
                    },
                    {
                        "title": "Request Duration (p95)",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, http_request_duration_ms)",
                                "legendFormat": "p95",
                            }
                        ],
                    },
                    {
                        "title": "Error Rate",
                        "type": "singlestat",
                        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 8},
                        "targets": [
                            {
                                "expr": 'rate(http_requests_total{status=~"5.."}[5m])',
                                "legendFormat": "errors/s",
                            }
                        ],
                    },
                    {
                        "title": "Active Requests",
                        "type": "gauge",
                        "gridPos": {"h": 4, "w": 6, "x": 6, "y": 8},
                        "targets": [
                            {
                                "expr": "http_requests_active",
                                "legendFormat": "active",
                            }
                        ],
                    },
                ],
            }
        }

    @staticmethod
    def generate_llm_dashboard() -> dict[str, Any]:
        """Generate an LLM monitoring dashboard configuration.

        Returns:
            Grafana-compatible dashboard JSON configuration for LLM metrics.
        """
        return {
            "dashboard": {
                "title": "LLM Operations",
                "uid": "llm-operations",
                "timezone": "utc",
                "refresh": "30s",
                "panels": [
                    {
                        "title": "LLM Request Rate",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "targets": [
                            {
                                "expr": "rate(llm_requests_total[5m])",
                                "legendFormat": "{{provider}} {{model}}",
                            }
                        ],
                    },
                    {
                        "title": "Token Usage",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "targets": [
                            {
                                "expr": "rate(llm_tokens_input_total[5m])",
                                "legendFormat": "input {{model}}",
                            },
                            {
                                "expr": "rate(llm_tokens_output_total[5m])",
                                "legendFormat": "output {{model}}",
                            },
                        ],
                    },
                    {
                        "title": "LLM Errors",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                        "targets": [
                            {
                                "expr": "rate(llm_errors_total[5m])",
                                "legendFormat": "{{provider}} {{error_type}}",
                            }
                        ],
                    },
                    {
                        "title": "LLM Latency (p95)",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, llm_request_duration_ms)",
                                "legendFormat": "p95 {{model}}",
                            }
                        ],
                    },
                ],
            }
        }

    @staticmethod
    def generate_memory_dashboard() -> dict[str, Any]:
        """Generate a memory operations monitoring dashboard.

        Returns:
            Grafana-compatible dashboard JSON configuration for memory metrics.
        """
        return {
            "dashboard": {
                "title": "Memory Operations",
                "uid": "memory-operations",
                "timezone": "utc",
                "refresh": "30s",
                "panels": [
                    {
                        "title": "Memory Retrieval Rate",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "targets": [
                            {
                                "expr": "rate(memory_retrieval_total[5m])",
                                "legendFormat": "{{memory_type}}",
                            }
                        ],
                    },
                    {
                        "title": "Hit/Miss Ratio",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "targets": [
                            {
                                "expr": "rate(memory_hit_total[5m])",
                                "legendFormat": "hits",
                            },
                            {
                                "expr": "rate(memory_miss_total[5m])",
                                "legendFormat": "misses",
                            },
                        ],
                    },
                ],
            }
        }
