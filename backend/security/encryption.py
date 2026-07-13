"""Encryption utilities for data at rest and in transit."""

from __future__ import annotations

import base64
import hashlib
import time
from dataclasses import dataclass, field

from config.logging import get_logger

logger = get_logger(__name__)


class EncryptionAtRest:
    """Encrypts data at rest using AES-like XOR cipher with key derivation."""

    def __init__(self, master_key: str = "") -> None:
        self._master_key = master_key or "sona-default-master-key"
        self._derived_key = self._derive_key(self._master_key)
        logger.info("encryption_at_rest_initialized")

    def encrypt_field(self, plaintext: str) -> str:
        """Encrypt a plaintext string, returning base64-encoded ciphertext."""
        if not plaintext:
            return ""
        key_bytes = self._derived_key
        data_bytes = plaintext.encode("utf-8")
        encrypted = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data_bytes))
        return base64.b64encode(encrypted).decode("utf-8")

    def decrypt_field(self, ciphertext: str) -> str:
        """Decrypt a base64-encoded ciphertext back to plaintext."""
        if not ciphertext:
            return ""
        key_bytes = self._derived_key
        encrypted = base64.b64decode(ciphertext)
        decrypted = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(encrypted))
        return decrypted.decode("utf-8")

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

    def _derive_key(self, master: str) -> bytes:
        """Derive an encryption key from the master key."""
        return hashlib.sha256(master.encode("utf-8")).digest()


@dataclass
class TransitKey:
    """Metadata about a transit encryption key."""

    name: str
    version: int = 1
    created_at: float = field(default_factory=time.time)


class TransitEncryption:
    """Simulates transit/transport encryption for data in motion."""

    def __init__(self, key_name: str = "default") -> None:
        self._key = TransitKey(name=key_name)
        self._key_material = self._generate_key_material(key_name, 1)
        logger.info("transit_encryption_initialized", key_name=key_name)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext for transit."""
        if not plaintext:
            return ""
        data_bytes = plaintext.encode("utf-8")
        encrypted = bytes(
            b ^ self._key_material[i % len(self._key_material)] for i, b in enumerate(data_bytes)
        )
        versioned = f"v{self._key.version}:"
        return versioned + base64.b64encode(encrypted).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt transit-encrypted ciphertext."""
        if not ciphertext:
            return ""
        if ":" in ciphertext:
            _, payload = ciphertext.split(":", 1)
        else:
            payload = ciphertext
        encrypted = base64.b64decode(payload)
        decrypted = bytes(
            b ^ self._key_material[i % len(self._key_material)] for i, b in enumerate(encrypted)
        )
        return decrypted.decode("utf-8")

    def rotate_key(self) -> str:
        """Rotate the encryption key, returning the new key identifier."""
        self._key.version += 1
        self._key_material = self._generate_key_material(self._key.name, self._key.version)
        key_id = f"{self._key.name}-v{self._key.version}"
        logger.info("transit_key_rotated", key_id=key_id)
        return key_id

    def get_key_info(self) -> dict:
        """Return metadata about the current transit key."""
        return {
            "name": self._key.name,
            "version": self._key.version,
            "created_at": self._key.created_at,
            "algorithm": "xor-sha256",
        }

    @staticmethod
    def _generate_key_material(name: str, version: int) -> bytes:
        """Generate key material from name and version."""
        seed = f"{name}:{version}".encode()
        return hashlib.sha256(seed).digest()
