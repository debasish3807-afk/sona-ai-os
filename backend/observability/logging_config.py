"""Production structured logging configuration."""

from __future__ import annotations

import logging
import sys
from typing import Any

from config.logging import get_logger

logger = get_logger(__name__)


class StructuredLogger:
    """Production structured logging configuration."""

    def __init__(self) -> None:
        self._level: str = "INFO"
        self._format: str = "json"
        self._loggers: dict[str, Any] = {}

    def configure(self, level: str = "INFO", format: str = "json") -> None:
        """Configure logging level and format.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            format: Output format (json or text).
        """
        self._level = level.upper()
        self._format = format

        log_level = getattr(logging, self._level, logging.INFO)
        root = logging.getLogger()
        root.setLevel(log_level)

        if not root.handlers:
            handler = logging.StreamHandler(sys.stdout)
            root.addHandler(handler)

        logger.info("logging_configured", level=self._level, format=self._format)

    def get_logger(self, name: str) -> Any:
        """Get a named logger instance.

        Args:
            name: Logger name, typically __name__.

        Returns:
            A configured logger instance.
        """
        if name not in self._loggers:
            self._loggers[name] = get_logger(name)
        return self._loggers[name]
