"""Storage service contracts for file upload/download flows."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4
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


@dataclass(frozen=True)
class UUIDStorageKeyService:
    """Generate storage keys namespaced by owner and UTC date."""

    def generate_storage_key(self, owner_id: int, original_name: str) -> str:
        safe_name = Path(original_name).name or "file"
        suffix = Path(safe_name).suffix.lower()
        day_prefix = datetime.now(tz=UTC).strftime("%Y/%m/%d")
        return f"{owner_id}/{day_prefix}/{uuid4().hex}{suffix}"


@dataclass(frozen=True)
class LocalBlobStorageService:
    """Filesystem-backed blob storage constrained to a root directory."""

    root_path: Path

    def __post_init__(self) -> None:
        self.root_path.mkdir(parents=True, exist_ok=True)

    def _resolve_storage_path(self, storage_key: str) -> Path:
        candidate = (self.root_path / storage_key).resolve()
        root = self.root_path.resolve()
        if not str(candidate).startswith(str(root) + "/") and candidate != root:
            raise ValueError("Invalid storage key path.")
        return candidate

    def write_bytes(
        self,
        storage_key: str,
        data: bytes,
        mime_type: str | None = None,
    ) -> StoredFileObject:
        path = self._resolve_storage_path(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

        checksum_sha256 = hashlib.sha256(data).hexdigest()
        return StoredFileObject(
            storage_key=storage_key,
            size_bytes=len(data),
            checksum_sha256=checksum_sha256,
            mime_type=mime_type,
        )

    def read_bytes(self, storage_key: str) -> bytes:
        path = self._resolve_storage_path(storage_key)
        return path.read_bytes()

    def delete(self, storage_key: str) -> None:
        path = self._resolve_storage_path(storage_key)
        if path.exists():
            path.unlink()

    def exists(self, storage_key: str) -> bool:
        path = self._resolve_storage_path(storage_key)
        return path.exists()
