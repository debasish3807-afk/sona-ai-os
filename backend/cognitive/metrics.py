"""Kernel metrics — latency, tokens, cost, success/failure rates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class KernelMetrics:
    """Observability metrics for the Cognitive Kernel."""

    total_requests: int = 0
    completed_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    _latencies: list[float] = field(default_factory=list)
    engine_times: dict[str, list[float]] = field(default_factory=dict)

    def record_request(self, success: bool, latency_ms: float, tokens: int, cost: float) -> None:
        self.total_requests += 1
        if success:
            self.completed_requests += 1
        else:
            self.failed_requests += 1
        self._latencies.append(latency_ms)
        if len(self._latencies) > 1000:
            self._latencies = self._latencies[-1000:]
        self.total_tokens += tokens
        self.total_cost += cost

    def record_engine_time(self, engine_id: str, ms: float) -> None:
        if engine_id not in self.engine_times:
            self.engine_times[engine_id] = []
        self.engine_times[engine_id].append(ms)
        if len(self.engine_times[engine_id]) > 200:
            self.engine_times[engine_id] = self.engine_times[engine_id][-200:]

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.completed_requests / self.total_requests

    @property
    def avg_latency_ms(self) -> float:
        if not self._latencies:
            return 0.0
        return sum(self._latencies) / len(self._latencies)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "completed_requests": self.completed_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(self.success_rate, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 6),
            "engine_avg_ms": {
                k: round(sum(v) / len(v), 2) if v else 0 for k, v in self.engine_times.items()
            },
        }
