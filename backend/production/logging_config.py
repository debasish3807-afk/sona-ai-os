"""Structured logging configuration — JSON format with file rotation."""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
from datetime import UTC, datetime
from typing import Any

LOG_DIR = os.environ.get("SONA_LOG_DIR", "logs")
LOG_LEVEL = os.environ.get("SONA_LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.environ.get("SONA_LOG_FORMAT", "json")
MAX_BYTES = 10 * 1024 * 1024
BACKUP_COUNT = 5


class _JSONFormatter(logging.Formatter):
    """Formats log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[0]:
            data["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_data"):
            data["extra"] = record.extra_data
        return json.dumps(data)


class LoggingConfig:
    """Configures structured logging with file rotation and console output."""

    @staticmethod
    def configure(log_dir: str = LOG_DIR, level: str = LOG_LEVEL) -> None:
        os.makedirs(log_dir, exist_ok=True)

        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level, logging.INFO))
        root_logger.handlers.clear()

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, "sona.log"),
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
        )
        file_handler.setLevel(logging.DEBUG)

        formatter = _JSONFormatter()
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

        root_logger.info(
            "logging_configured", extra={"log_dir": log_dir, "level": level, "format": "json"}
        )
