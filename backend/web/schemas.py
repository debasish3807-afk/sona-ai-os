"""Data schemas for the web intelligence system."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class WebResult:
    """A web search result."""

    title: str
    url: str
    snippet: str
    score: float = 0.0
    cached_at: float | None = None


@dataclass
class WebPage:
    """A fetched web page."""

    url: str
    title: str
    content: str
    status_code: int = 200
    fetched_at: float = field(default_factory=time.time)
