"""Enterprise security: secrets, encryption, and monitoring."""

from __future__ import annotations

import base64
import hashlib
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime

from config.logging import get_logger

logger = get_logger(__name__)


class SecretManager:
    """Manages application secrets with rotation support."""

    def __init__(self) -> None:
        self._secrets: dict[str, str] = {}
        self._lock = threading.Lock()

    def get_secret(self, key: str) -> str | None:
        """Retrieve a secret by key."""
        with self._lock:
            return self._secrets.get(key)

    def set_secret(self, key: str, value: str) -> None:
        """Store a secret value."""
        with self._lock:
            self._secrets[key] = value
            logger.info("secret_set", key=key)

    def rotate_secret(self, key: str) -> str:
        """Rotate a secret, generating a new random value."""
        new_value = base64.urlsafe_b64encode(os.urandom(32)).decode()
        with self._lock:
            self._secrets[key] = new_value
            logger.info("secret_rotated", key=key)
        return new_value

    def list_secrets(self) -> list[str]:
        """List all secret keys (values are not exposed)."""
        with self._lock:
            return list(self._secrets.keys())


class EncryptionUtility:
    """Simple XOR-based encryption utility for non-critical data."""

    def __init__(self, key: str | None = None) -> None:
        if key is None:
            key = base64.urlsafe_b64encode(os.urandom(32)).decode()
        self._key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext and return base64 ciphertext."""
        data = plaintext.encode()
        encrypted = bytes(b ^ self._key[i % len(self._key)] for i, b in enumerate(data))
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt base64 ciphertext and return plaintext."""
        data = base64.urlsafe_b64decode(ciphertext)
        decrypted = bytes(b ^ self._key[i % len(self._key)] for i, b in enumerate(data))
        return decrypted.decode()


@dataclass
class _SecurityEvent:
    """Internal security event record."""

    event_type: str
    user_id: str
    ip: str
    details: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    severity: str = "medium"


class SecurityMonitor:
    """Monitors security events and detects anomalies."""

    def __init__(self) -> None:
        self._events: list[_SecurityEvent] = []
        self._user_actions: dict[str, list[float]] = {}
        self._lock = threading.Lock()
        self._anomaly_threshold = 100  # actions per minute

    def record_event(
        self,
        event_type: str,
        user_id: str = "",
        ip: str = "",
        details: dict | None = None,
    ) -> None:
        """Record a security event."""
        severity = "high" if "fail" in event_type.lower() else "medium"
        event = _SecurityEvent(
            event_type=event_type,
            user_id=user_id,
            ip=ip,
            details=details or {},
            severity=severity,
        )
        with self._lock:
            self._events.append(event)
        logger.info(
            "security_event",
            event_type=event_type,
            user_id=user_id,
            severity=severity,
        )

    def get_alerts(self, severity: str = "high", limit: int = 50) -> list[dict]:
        """Get security alerts filtered by severity."""
        with self._lock:
            filtered = [e for e in self._events if e.severity == severity]
            return [
                {
                    "event_type": e.event_type,
                    "user_id": e.user_id,
                    "ip": e.ip,
                    "details": e.details,
                    "timestamp": e.timestamp.isoformat(),
                    "severity": e.severity,
                }
                for e in filtered[-limit:]
            ]

    def detect_anomaly(self, user_id: str, action: str) -> bool:
        """Detect anomalous activity based on action rate."""
        now = time.time()
        with self._lock:
            key = f"{user_id}:{action}"
            if key not in self._user_actions:
                self._user_actions[key] = []
            timestamps = self._user_actions[key]
            cutoff = now - 60
            timestamps[:] = [t for t in timestamps if t > cutoff]
            timestamps.append(now)

            if len(timestamps) > self._anomaly_threshold:
                self.record_event(
                    "anomaly_detected",
                    user_id=user_id,
                    details={"action": action, "count": len(timestamps)},
                )
                return True
        return False

    def get_stats(self) -> dict:
        """Return security monitoring statistics."""
        with self._lock:
            return {
                "total_events": len(self._events),
                "high_severity": sum(1 for e in self._events if e.severity == "high"),
                "tracked_users": len({e.user_id for e in self._events if e.user_id}),
            }
