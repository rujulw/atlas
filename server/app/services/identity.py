"""Identity crypto service contracts and scaffolding types."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class IdentityCryptoSettings:
    """Application-layer identity crypto configuration."""

    encryption_key: str
    blind_index_key: str
    key_version: str = "v1"


@dataclass(frozen=True)
class EncryptedIdentityValue:
    """Ciphertext envelope for a protected identity field."""

    ciphertext: str
    key_version: str


class IdentityCipherService(Protocol):
    """Encrypt/decrypt sensitive identity values for database persistence."""

    def encrypt(self, value: str) -> EncryptedIdentityValue:
        """Encrypt a plaintext identity value."""

    def decrypt(self, value: EncryptedIdentityValue) -> str:
        """Decrypt an encrypted identity value."""


class BlindIndexService(Protocol):
    """Derive deterministic lookup values for protected identity fields."""

    def derive(self, value: str) -> str:
        """Generate a blind index from a normalized identity value."""


def normalize_email(value: str) -> str:
    """Normalize email-like login identifiers for deterministic lookup."""

    return value.strip().lower()


@dataclass(frozen=True)
class HMACSHA256BlindIndexService:
    """Generate deterministic blind indexes using HMAC-SHA256."""

    key: str

    def derive(self, value: str) -> str:
        digest = hmac.new(
            self.key.encode("utf-8"),
            value.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return digest
