"""Prometheus-compatible metric registry."""

from __future__ import annotations

from config.logging import get_logger

logger = get_logger(__name__)

DEFAULT_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]


class Counter:
    """A monotonically increasing counter metric."""

    def __init__(self, name: str, help: str = "") -> None:
        self.name = name
        self.help = help
        self._value: float = 0.0
        self._labels: dict[str, float] = {}

    def inc(self, value: float = 1, labels: dict[str, str] | None = None) -> None:
        """Increment the counter."""
        if value < 0:
            raise ValueError("Counter can only increase")
        if labels:
            key = self._label_key(labels)
            self._labels[key] = self._labels.get(key, 0.0) + value
        else:
            self._value += value

    @property
    def value(self) -> float:
        """Get the current counter value."""
        return self._value

    def _label_key(self, labels: dict[str, str]) -> str:
        """Generate a key from labels."""
        parts = sorted(f'{k}="{v}"' for k, v in labels.items())
        return ",".join(parts)

    def export(self) -> str:
        """Export in Prometheus text format."""
        lines: list[str] = []
        if self.help:
            lines.append(f"# HELP {self.name} {self.help}")
        lines.append(f"# TYPE {self.name} counter")
        if self._labels:
            for label_key, val in self._labels.items():
                lines.append(f"{self.name}{{{label_key}}} {val}")
        else:
            lines.append(f"{self.name} {self._value}")
        return "\n".join(lines)


class Gauge:
    """A metric that can go up and down."""

    def __init__(self, name: str, help: str = "") -> None:
        self.name = name
        self.help = help
        self._value: float = 0.0
        self._labels: dict[str, float] = {}

    def set(self, value: float, labels: dict[str, str] | None = None) -> None:
        """Set the gauge to a specific value."""
        if labels:
            key = self._label_key(labels)
            self._labels[key] = value
        else:
            self._value = value

    def inc(self, value: float = 1) -> None:
        """Increment the gauge."""
        self._value += value

    def dec(self, value: float = 1) -> None:
        """Decrement the gauge."""
        self._value -= value

    @property
    def value(self) -> float:
        """Get the current gauge value."""
        return self._value

    def _label_key(self, labels: dict[str, str]) -> str:
        """Generate a key from labels."""
        parts = sorted(f'{k}="{v}"' for k, v in labels.items())
        return ",".join(parts)

    def export(self) -> str:
        """Export in Prometheus text format."""
        lines: list[str] = []
        if self.help:
            lines.append(f"# HELP {self.name} {self.help}")
        lines.append(f"# TYPE {self.name} gauge")
        if self._labels:
            for label_key, val in self._labels.items():
                lines.append(f"{self.name}{{{label_key}}} {val}")
        else:
            lines.append(f"{self.name} {self._value}")
        return "\n".join(lines)


class Histogram:
    """A metric that samples observations into buckets."""

    def __init__(
        self,
        name: str,
        help: str = "",
        buckets: list[float] | None = None,
    ) -> None:
        self.name = name
        self.help = help
        self._buckets = sorted(buckets or DEFAULT_BUCKETS)
        self._counts: dict[float, int] = dict.fromkeys(self._buckets, 0)
        self._count: int = 0
        self._sum: float = 0.0

    def observe(self, value: float, labels: dict[str, str] | None = None) -> None:
        """Record an observation."""
        self._count += 1
        self._sum += value
        for bucket in self._buckets:
            if value <= bucket:
                self._counts[bucket] += 1

    @property
    def count(self) -> int:
        """Get the total observation count."""
        return self._count

    @property
    def sum(self) -> float:
        """Get the sum of all observations."""
        return self._sum

    def export(self) -> str:
        """Export in Prometheus text format."""
        lines: list[str] = []
        if self.help:
            lines.append(f"# HELP {self.name} {self.help}")
        lines.append(f"# TYPE {self.name} histogram")
        for bucket, cnt in self._counts.items():
            lines.append(f'{self.name}_bucket{{le="{bucket}"}} {cnt}')
        lines.append(f'{self.name}_bucket{{le="+Inf"}} {self._count}')
        lines.append(f"{self.name}_sum {self._sum}")
        lines.append(f"{self.name}_count {self._count}")
        return "\n".join(lines)


class PrometheusRegistry:
    """Prometheus-compatible metric registry."""

    def __init__(self) -> None:
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}

    def counter(self, name: str, help: str = "") -> Counter:
        """Create or get a counter metric."""
        if name not in self._counters:
            self._counters[name] = Counter(name, help)
        return self._counters[name]

    def gauge(self, name: str, help: str = "") -> Gauge:
        """Create or get a gauge metric."""
        if name not in self._gauges:
            self._gauges[name] = Gauge(name, help)
        return self._gauges[name]

    def histogram(self, name: str, help: str = "", buckets: list[float] | None = None) -> Histogram:
        """Create or get a histogram metric."""
        if name not in self._histograms:
            self._histograms[name] = Histogram(name, help, buckets)
        return self._histograms[name]

    def export(self) -> str:
        """Full Prometheus text format output."""
        sections: list[str] = []
        for c in self._counters.values():
            sections.append(c.export())
        for g in self._gauges.values():
            sections.append(g.export())
        for h in self._histograms.values():
            sections.append(h.export())
        return "\n\n".join(sections)
