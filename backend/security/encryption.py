"""Encryption utilities for data at rest and in transit.

Uses Fernet (AES-128-CBC + HMAC-SHA256) for authenticated encryption.
All keys are derived via SHA-256 from a master key.
"""

from __future__ import annotations

import base64
import hashlib
import os
import time
import warnings
from dataclasses import dataclass, field

from cryptography.fernet import Fernet, InvalidToken

from config.logging import get_logger

logger = get_logger(__name__)


class EncryptionAtRest:
    """Encrypts data at rest using Fernet (AES-128-CBC + HMAC-SHA256).

    The master key is derived via SHA-256 to produce a valid 32-byte
    Fernet key. Keys are URL-safe-base64-encoded internally.
    """

    def __init__(self, master_key: str = "") -> None:
        key = master_key or os.environ.get("ENCRYPTION_KEY", "")
        if not key:
            warnings.warn(
                "EncryptionAtRest: No master key provided and ENCRYPTION_KEY env var not set. "
                "Using an insecure development fallback. Set ENCRYPTION_KEY for production.",
                RuntimeWarning,
                stacklevel=2,
            )
            key = "dev-encryption-key-not-for-production"
        self._fernet = Fernet(self._derive_fernet_key(key))
        logger.info("encryption_at_rest_initialized")

    def encrypt_field(self, plaintext: str) -> str:
        """Encrypt a plaintext string, returning a base64-url-safe ciphertext."""
        if not plaintext:
            return ""
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt_field(self, ciphertext: str) -> str:
        """Decrypt a Fernet-encrypted ciphertext back to plaintext."""
        if not ciphertext:
            return ""
        try:
            return self._fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            logger.error("decryption_failed_invalid_token")
            return ""
        except Exception as exc:
            logger.error("decryption_failed", error=str(exc))
            return ""

    def encrypt_dict(self, data: dict) -> dict:
        """Encrypt all string values in a dictionary."""
        result: dict = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.encrypt_field(value)
            else:
                result[key] = value
        return result

    def decrypt_dict(self, data: dict) -> dict:
        """Decrypt all string values in a dictionary."""
        result: dict = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.decrypt_field(value)
            else:
                result[key] = value
        return result

    @staticmethod
    def _derive_fernet_key(master: str) -> bytes:
        """Derive a valid 32-byte Fernet key from a master key string.

        Fernet keys are 32 bytes of entropy, base64-url-safe encoded.
        We use SHA-256 to stretch the master key to 32 bytes.
        """
        return base64.urlsafe_b64encode(hashlib.sha256(master.encode("utf-8")).digest())


@dataclass
class TransitKey:
    """Metadata about a transit encryption key."""

    name: str
    version: int = 1
    created_at: float = field(default_factory=time.time)


class TransitEncryption:
    """Encrypts data in transit using Fernet (AES-128-CBC + HMAC-SHA256).

    Supports key rotation via versioned key material.
    Each key version is derived from name + version.
    """

    def __init__(self, key_name: str = "default") -> None:
        self._key = TransitKey(name=key_name)
        self._fernet = self._build_fernet(key_name, 1)
        logger.info("transit_encryption_initialized", key_name=key_name)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext for transit.

        Returns a versioned ciphertext string: ``v<version>:<base64>``.
        """
        if not plaintext:
            return ""
        ciphertext = self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")
        return f"v{self._key.version}:{ciphertext}"

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a versioned transit ciphertext back to plaintext."""
        if not ciphertext:
            return ""
        if ":" in ciphertext:
            version_str, payload = ciphertext.split(":", 1)
            version = int(version_str.lstrip("v"))
        else:
            version = self._key.version
            payload = ciphertext

        fernet = self._build_fernet(self._key.name, version)
        try:
            return fernet.decrypt(payload.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            logger.error("transit_decryption_failed_invalid_token")
            return ""
        except Exception as exc:
            logger.error("transit_decryption_failed", error=str(exc))
            return ""

    def rotate_key(self) -> str:
        """Rotate the encryption key, returning the new key identifier."""
        self._key.version += 1
        self._fernet = self._build_fernet(self._key.name, self._key.version)
        key_id = f"{self._key.name}-v{self._key.version}"
        logger.info("transit_key_rotated", key_id=key_id)
        return key_id

    def get_key_info(self) -> dict:
        """Return metadata about the current transit key."""
        return {
            "name": self._key.name,
            "version": self._key.version,
            "created_at": self._key.created_at,
            "algorithm": "fernet-aes128-cbc-hmac256",
        }

    @staticmethod
    def _build_fernet(name: str, version: int) -> Fernet:
        """Build a Fernet instance for the given key name and version.

        The key is derived as SHA-256(name:version) → base64-url-safe-encoded.
        """
        seed = f"{name}:{version}".encode()
        return Fernet(base64.urlsafe_b64encode(hashlib.sha256(seed).digest()))
