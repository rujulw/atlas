"""File repository interfaces and SQLAlchemy implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.file import File


class FileRepository(Protocol):
    def create(
        self,
        owner_id: int,
        original_name: str,
        storage_key: str,
        size_bytes: int,
        checksum_sha256: str,
        mime_type: str | None = None,
    ) -> File:
        """Create and persist file metadata record."""

    def get_by_id_for_owner(self, file_id: int, owner_id: int) -> File | None:
        """Find active file metadata row by id and owner."""


@dataclass
class SQLAlchemyFileRepository:
    """File repository backed by a SQLAlchemy session."""

    db: Session

    def create(
        self,
        owner_id: int,
        original_name: str,
        storage_key: str,
        size_bytes: int,
        checksum_sha256: str,
        mime_type: str | None = None,
    ) -> File:
        file_record = File(
            owner_id=owner_id,
            original_name=original_name,
            storage_key=storage_key,
            size_bytes=size_bytes,
            checksum_sha256=checksum_sha256,
            mime_type=mime_type,
        )
        self.db.add(file_record)
        self.db.commit()
        self.db.refresh(file_record)
        return file_record

    def get_by_id_for_owner(self, file_id: int, owner_id: int) -> File | None:
        statement = select(File).where(
            File.id == file_id,
            File.owner_id == owner_id,
            File.is_deleted.is_(False),
        )
        return self.db.execute(statement).scalar_one_or_none()
