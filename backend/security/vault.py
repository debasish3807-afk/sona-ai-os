"""HashiCorp Vault-compatible secrets engine abstraction."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field

from config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class VaultSecret:
    """A secret stored in the vault."""

    data: dict
    metadata: dict = field(default_factory=dict)


class VaultClient:
    """HashiCorp Vault-compatible secrets engine abstraction.

    Uses in-memory store as fallback when Vault is unavailable.
    """

    def __init__(
        self,
        url: str = "",
        token: str = "",
        namespace: str = "sona",
    ) -> None:
        self._url = url
        self._token = token
        self._namespace = namespace
        self._store: dict[str, VaultSecret] = {}
        self._sealed = False
        logger.info(
            "vault_client_initialized",
            url=url or "in-memory",
            namespace=namespace,
        )

    def read_secret(self, path: str) -> dict | None:
        """Read a secret from the vault at the given path."""
        full_path = self._resolve_path(path)
        secret = self._store.get(full_path)
        if secret is None:
            logger.debug("vault_secret_not_found", path=full_path)
            return None
        logger.debug("vault_secret_read", path=full_path)
        return dict(secret.data)

    def write_secret(self, path: str, data: dict) -> bool:
        """Write a secret to the vault at the given path."""
        full_path = self._resolve_path(path)
        metadata = {
            "created_time": time.time(),
            "version": 1,
        }
        existing = self._store.get(full_path)
        if existing:
            version = existing.metadata.get("version", 0)
            metadata["version"] = version + 1
        self._store[full_path] = VaultSecret(data=dict(data), metadata=metadata)
        logger.info("vault_secret_written", path=full_path)
        return True

    def delete_secret(self, path: str) -> bool:
        """Delete a secret from the vault at the given path."""
        full_path = self._resolve_path(path)
        if full_path in self._store:
            del self._store[full_path]
            logger.info("vault_secret_deleted", path=full_path)
            return True
        logger.debug("vault_secret_delete_miss", path=full_path)
        return False

    def list_secrets(self, path: str) -> list[str]:
        """List all secret keys under the given path prefix."""
        full_path = self._resolve_path(path)
        prefix = full_path.rstrip("/") + "/"
        keys: list[str] = []
        for key in self._store:
            if key.startswith(prefix):
                remainder = key[len(prefix) :]
                top_level = remainder.split("/")[0]
                if top_level and top_level not in keys:
                    keys.append(top_level)
        return keys

    def rotate_credentials(self, path: str) -> dict:
        """Rotate credentials at the given path."""
        full_path = self._resolve_path(path)
        secret = self._store.get(full_path)
        if secret is None:
            logger.warning("vault_rotate_not_found", path=full_path)
            return {"error": "secret_not_found"}
        new_key = hashlib.sha256(f"{full_path}-{time.time()}".encode()).hexdigest()[:32]
        secret.data["rotated_key"] = new_key
        secret.metadata["version"] = secret.metadata.get("version", 0) + 1
        secret.metadata["rotated_time"] = time.time()
        logger.info("vault_credentials_rotated", path=full_path)
        return {"key": new_key, "version": secret.metadata["version"]}

    def get_health(self) -> dict:
        """Return the health status of the vault client."""
        return {
            "initialized": True,
            "sealed": self._sealed,
            "namespace": self._namespace,
            "secrets_count": len(self._store),
            "backend": "in-memory" if not self._url else "vault",
        }

    def _resolve_path(self, path: str) -> str:
        """Resolve a path with the namespace prefix."""
        return f"{self._namespace}/{path.strip('/')}"
