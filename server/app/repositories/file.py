"""File repository interfaces and SQLAlchemy implementation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.file import File

FileSortField = Literal["created_at", "updated_at", "original_name", "size_bytes"]
FileSortDirection = Literal["asc", "desc"]


@dataclass(frozen=True)
class FileQueryFilters:
    """Owner-scoped metadata filters for file browsing and search."""

    search: str | None = None
    mime_type: str | None = None
    size_bytes_min: int | None = None
    size_bytes_max: int | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None


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

    def list_for_owner(
        self,
        owner_id: int,
        *,
        filters: FileQueryFilters | None = None,
        limit: int = 50,
        offset: int = 0,
        sort_field: FileSortField = "created_at",
        sort_direction: FileSortDirection = "desc",
    ) -> list[File]:
        """List active owner-scoped file metadata rows for browsing and search."""

    def count_for_owner(
        self,
        owner_id: int,
        *,
        filters: FileQueryFilters | None = None,
    ) -> int:
        """Count active owner-scoped file metadata rows matching browse/search filters."""


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

    def list_for_owner(
        self,
        owner_id: int,
        *,
        filters: FileQueryFilters | None = None,
        limit: int = 50,
        offset: int = 0,
        sort_field: FileSortField = "created_at",
        sort_direction: FileSortDirection = "desc",
    ) -> list[File]:
        filters = filters or FileQueryFilters()
        statement = select(File)
        statement = self._apply_owner_scoped_filters(
            statement,
            owner_id=owner_id,
            filters=filters,
        )

        sort_column = self._resolve_sort_column(sort_field)
        if sort_direction == "asc":
            statement = statement.order_by(sort_column.asc(), File.id.asc())
        else:
            statement = statement.order_by(sort_column.desc(), File.id.desc())

        statement = statement.offset(max(offset, 0)).limit(max(limit, 1))
        return list(self.db.execute(statement).scalars())

    def count_for_owner(
        self,
        owner_id: int,
        *,
        filters: FileQueryFilters | None = None,
    ) -> int:
        filters = filters or FileQueryFilters()
        statement = select(func.count(File.id))
        statement = self._apply_owner_scoped_filters(
            statement,
            owner_id=owner_id,
            filters=filters,
        )
        return int(self.db.execute(statement).scalar_one())

    @staticmethod
    def _resolve_sort_column(sort_field: FileSortField):
        sort_columns = {
            "created_at": File.created_at,
            "updated_at": File.updated_at,
            "original_name": File.original_name,
            "size_bytes": File.size_bytes,
        }
        return sort_columns[sort_field]

    @staticmethod
    def _apply_owner_scoped_filters(statement, *, owner_id: int, filters: FileQueryFilters):
        statement = statement.where(
            File.owner_id == owner_id,
            File.is_deleted.is_(False),
        )

        if filters.search:
            normalized_search = filters.search.strip()
            if normalized_search:
                statement = statement.where(File.original_name.ilike(f"%{normalized_search}%"))

        if filters.mime_type:
            statement = statement.where(File.mime_type == filters.mime_type)

        if filters.size_bytes_min is not None:
            statement = statement.where(File.size_bytes >= filters.size_bytes_min)

        if filters.size_bytes_max is not None:
            statement = statement.where(File.size_bytes <= filters.size_bytes_max)

        if filters.created_after is not None:
            statement = statement.where(File.created_at >= filters.created_after)

        if filters.created_before is not None:
            statement = statement.where(File.created_at <= filters.created_before)

        return statement
