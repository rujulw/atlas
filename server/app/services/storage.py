"""Storage service contracts for file upload/download flows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class StoredFileObject:
    """Immutable storage write result used by metadata persistence flows."""

    storage_key: str
    size_bytes: int
    checksum_sha256: str
    mime_type: str | None = None


class StorageKeyService(Protocol):
    """Generate deterministic, safe storage keys for owner-scoped files."""

    def generate_storage_key(self, owner_id: int, original_name: str) -> str:
        """Create a server-side storage key for a new file."""


class BlobStorageService(Protocol):
    """Read/write primitives for binary file objects under the storage root."""

    def write_bytes(
        self,
        storage_key: str,
        data: bytes,
        mime_type: str | None = None,
    ) -> StoredFileObject:
        """Persist bytes for a storage key and return integrity metadata."""

    def read_bytes(self, storage_key: str) -> bytes:
        """Read file bytes by storage key."""

    def delete(self, storage_key: str) -> None:
        """Delete file bytes by storage key."""

    def exists(self, storage_key: str) -> bool:
        """Check whether an object exists for the storage key."""
