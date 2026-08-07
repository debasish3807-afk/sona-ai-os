"""API Key service for generating, validating, and managing API keys.

Provides API key lifecycle management with metadata tracking.
"""

import os
import time
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass
class APIKeyMetadata:
    """Metadata associated with an API key."""

    key_id: str
    user_id: str
    name: str
    scopes: list[str]
    created_at: float
    last_used: float | None = None
    is_active: bool = True
    prefix: str = ""


class APIKeyService:
    """API key management service."""

    def __init__(self) -> None:
        self._keys: dict[str, APIKeyMetadata] = {}  # key_hash -> metadata
        self._key_to_hash: dict[str, str] = {}  # raw_key -> key_hash (for lookup)
        self._user_keys: dict[str, list[str]] = {}  # user_id -> list of key_hashes

    async def generate_key(
        self,
        user_id: str,
        name: str = "default",
        scopes: list[str] | None = None,
    ) -> tuple[str, APIKeyMetadata]:
        """Generate a new API key for a user.

        Returns:
            Tuple of (raw_key, metadata).
        """
        raw_key = os.urandom(32).hex()
        key_id = os.urandom(8).hex()
        prefix = raw_key[:8]

        metadata = APIKeyMetadata(
            key_id=key_id,
            user_id=user_id,
            name=name,
            scopes=scopes or ["read"],
            created_at=time.time(),
            prefix=prefix,
        )

        self._keys[raw_key] = metadata
        self._key_to_hash[raw_key] = raw_key

        if user_id not in self._user_keys:
            self._user_keys[user_id] = []
        self._user_keys[user_id].append(raw_key)

        logger.info("api_key_generated", user_id=user_id, key_id=key_id, name=name)
        return raw_key, metadata

    async def validate_key(self, key: str) -> APIKeyMetadata | None:
        """Validate an API key and return its metadata.

        Returns:
            The key metadata if valid, None otherwise.
        """
        metadata = self._keys.get(key)
        if metadata is None:
            return None
        if not metadata.is_active:
            return None

        # Update last_used
        metadata.last_used = time.time()
        return metadata

    async def revoke_key(self, key: str) -> bool:
        """Revoke an API key.

        Returns:
            True if the key was found and revoked.
        """
        metadata = self._keys.get(key)
        if metadata is None:
            return False
        metadata.is_active = False
        logger.info("api_key_revoked", key_id=metadata.key_id, user_id=metadata.user_id)
        return True

    async def revoke_key_by_id(self, key_id: str) -> bool:
        """Revoke an API key by its key_id."""
        for _key, metadata in self._keys.items():
            if metadata.key_id == key_id:
                metadata.is_active = False
                logger.info("api_key_revoked", key_id=key_id, user_id=metadata.user_id)
                return True
        return False

    async def get_user_keys(self, user_id: str) -> list[APIKeyMetadata]:
        """Get all API key metadata for a user."""
        key_hashes = self._user_keys.get(user_id, [])
        result = []
        for key_hash in key_hashes:
            metadata = self._keys.get(key_hash)
            if metadata:
                result.append(metadata)
        return result

    async def check_scope(self, key: str, required_scope: str) -> bool:
        """Check if an API key has the required scope."""
        metadata = await self.validate_key(key)
        if metadata is None:
            return False
        # Wildcard scope
        if "*" in metadata.scopes:
            return True
        return required_scope in metadata.scopes
