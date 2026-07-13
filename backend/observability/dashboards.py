"""Grafana-compatible dashboard configuration generation."""

from __future__ import annotations

from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class DashboardConfig:
    """Generates Grafana-compatible dashboard JSON."""

    def __init__(self, title: str = "Sona AI OS") -> None:
        self._title = title
        self._dashboards: list[str] = [
            "overview",
            "ai-performance",
            "agent-coordination",
        ]

    def generate_overview_dashboard(self) -> dict[str, Any]:
        """Returns Grafana JSON for the system overview dashboard."""
        return {
            "title": f"{self._title} - Overview",
            "uid": "sona-overview",
            "version": 1,
            "time": {"from": "now-1h", "to": "now"},
            "panels": [
                self._panel("Request Rate", "rate(http_requests_total[5m])", 0, 0),
                self._panel("Error Rate", "rate(http_errors_total[5m])", 12, 0),
                self._panel(
                    "Latency P95", "histogram_quantile(0.95, rate(http_duration_bucket[5m]))", 0, 8
                ),
                self._panel("Active Connections", "active_connections", 12, 8),
            ],
            "templating": {"list": []},
            "refresh": "10s",
            "schemaVersion": 38,
        }

    def generate_ai_dashboard(self) -> dict[str, Any]:
        """Returns Grafana JSON for the AI performance dashboard."""
        return {
            "title": f"{self._title} - AI Performance",
            "uid": "sona-ai-perf",
            "version": 1,
            "time": {"from": "now-1h", "to": "now"},
            "panels": [
                self._panel("LLM Requests/s", "rate(llm_requests_total[5m])", 0, 0),
                self._panel("Token Usage", "sum(llm_tokens_total)", 12, 0),
                self._panel(
                    "Inference Latency",
                    "histogram_quantile(0.95, rate(llm_latency_bucket[5m]))",
                    0,
                    8,
                ),
                self._panel("Cache Hit Rate", "llm_cache_hits / llm_cache_total", 12, 8),
            ],
            "templating": {"list": []},
            "refresh": "10s",
            "schemaVersion": 38,
        }

    def generate_agent_dashboard(self) -> dict[str, Any]:
        """Returns Grafana JSON for the agent coordination dashboard."""
        return {
            "title": f"{self._title} - Agent Coordination",
            "uid": "sona-agents",
            "version": 1,
            "time": {"from": "now-1h", "to": "now"},
            "panels": [
                self._panel("Active Agents", "agent_active_count", 0, 0),
                self._panel("Task Throughput", "rate(agent_tasks_total[5m])", 12, 0),
                self._panel("Delegation Rate", "rate(agent_delegations_total[5m])", 0, 8),
                self._panel("Recovery Events", "rate(agent_recoveries_total[5m])", 12, 8),
            ],
            "templating": {"list": []},
            "refresh": "10s",
            "schemaVersion": 38,
        }

    def list_dashboards(self) -> list[str]:
        """List available dashboard names."""
        return list(self._dashboards)

    def _panel(self, title: str, expr: str, grid_x: int, grid_y: int) -> dict[str, Any]:
        """Create a Grafana panel definition."""
        return {
            "title": title,
            "type": "timeseries",
            "gridPos": {"h": 8, "w": 12, "x": grid_x, "y": grid_y},
            "targets": [
                {
                    "expr": expr,
                    "datasource": {"type": "prometheus", "uid": "prometheus"},
                }
            ],
        }
