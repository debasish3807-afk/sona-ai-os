"""API key management — generation, validation, and lifecycle.

Keys use the format: sona_sk_<32 hex chars>
Only SHA-256 hashes are stored — never plaintext keys.
"""

from __future__ import annotations

import hashlib
import os
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

API_KEY_LENGTH = int(os.environ.get("API_KEY_LENGTH", "32"))
API_KEY_PREFIX = "sona_sk_"


def _generate_key() -> str:
    """Generate a random API key with prefix."""
    random_part = secrets.token_hex(API_KEY_LENGTH)
    return f"{API_KEY_PREFIX}{random_part}"


def _hash_key(key: str) -> str:
    """SHA-256 hash of an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


@dataclass
class APIKeyRecord:
    """Stored API key record (hash only, never plaintext)."""

    key_id: str = field(default_factory=lambda: secrets.token_hex(8))
    key_hash: str = ""
    key_prefix: str = ""  # First 12 chars for identification
    user_id: str = ""
    name: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    expires_at: str | None = None
    last_used: str | None = None
    is_active: bool = True
    scopes: list[str] = field(default_factory=list)

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(UTC).isoformat() > self.expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "key_id": self.key_id,
            "key_prefix": self.key_prefix,
            "user_id": self.user_id,
            "name": self.name,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "last_used": self.last_used,
            "is_active": self.is_active,
            "scopes": self.scopes,
        }


class APIKeyManager:
    """Manages API key lifecycle: create, validate, rotate, revoke."""

    def __init__(self) -> None:
        self._keys: dict[str, APIKeyRecord] = {}  # key_hash → record
        self._id_index: dict[str, str] = {}  # key_id → key_hash

    def create_key(
        self,
        user_id: str,
        name: str = "default",
        expires_at: str | None = None,
        scopes: list[str] | None = None,
    ) -> tuple[str, APIKeyRecord]:
        """Create a new API key.

        Returns:
            Tuple of (plaintext_key, record). The plaintext key is
            shown ONCE and never stored.
        """
        plaintext = _generate_key()
        key_hash = _hash_key(plaintext)
        prefix = plaintext[:12]

        record = APIKeyRecord(
            key_hash=key_hash,
            key_prefix=prefix,
            user_id=user_id,
            name=name,
            expires_at=expires_at,
            scopes=scopes or [],
        )
        self._keys[key_hash] = record
        self._id_index[record.key_id] = key_hash
        return plaintext, record

    def validate_key(self, key: str) -> APIKeyRecord | None:
        """Validate an API key and return its record.

        Args:
            key: The plaintext API key to validate.

        Returns:
            APIKeyRecord if valid, None otherwise.
        """
        key_hash = _hash_key(key)
        record = self._keys.get(key_hash)
        if record is None:
            return None
        if not record.is_active:
            return None
        if record.is_expired:
            return None
        # Update last used
        record.last_used = datetime.now(UTC).isoformat()
        return record

    def rotate_key(self, key_id: str, user_id: str) -> tuple[str, APIKeyRecord] | None:
        """Rotate an API key — revoke old, create new.

        Args:
            key_id: The key to rotate.
            user_id: Owner verification.

        Returns:
            New (plaintext_key, record) or None if not found.
        """
        old_hash = self._id_index.get(key_id)
        if old_hash is None:
            return None
        old_record = self._keys.get(old_hash)
        if old_record is None or old_record.user_id != user_id:
            return None

        # Revoke old
        old_record.is_active = False

        # Create new with same properties
        return self.create_key(
            user_id=user_id,
            name=old_record.name,
            expires_at=old_record.expires_at,
            scopes=old_record.scopes,
        )

    def revoke_key(self, key_id: str, user_id: str) -> bool:
        """Revoke an API key.

        Args:
            key_id: The key to revoke.
            user_id: Owner verification.

        Returns:
            True if revoked successfully.
        """
        key_hash = self._id_index.get(key_id)
        if key_hash is None:
            return False
        record = self._keys.get(key_hash)
        if record is None or record.user_id != user_id:
            return False
        record.is_active = False
        return True

    def list_keys(self, user_id: str) -> list[dict[str, Any]]:
        """List all API keys for a user (without hashes)."""
        return [r.to_dict() for r in self._keys.values() if r.user_id == user_id and r.is_active]

    def get_key_count(self, user_id: str) -> int:
        """Count active keys for a user."""
        return sum(1 for r in self._keys.values() if r.user_id == user_id and r.is_active)
