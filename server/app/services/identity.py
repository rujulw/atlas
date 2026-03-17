"""Identity crypto service contracts and scaffolding types."""

from __future__ import annotations

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
