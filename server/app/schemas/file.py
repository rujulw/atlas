"""File storage request and response schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

FileSortField = Literal["created_at", "updated_at", "original_name", "size_bytes"]
FileSortDirection = Literal["asc", "desc"]


class FileMetadataResponse(BaseModel):
    id: int
    owner_id: int
    original_name: str
    storage_key: str
    mime_type: str | None = None
    size_bytes: int
    checksum_sha256: str
    created_at: datetime
    updated_at: datetime


class FileListQuery(BaseModel):
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_field: FileSortField = "created_at"
    sort_direction: FileSortDirection = "desc"
    search: str | None = Field(default=None, max_length=255)
    mime_type: str | None = Field(default=None, max_length=255)
    size_bytes_min: int | None = Field(default=None, ge=0)
    size_bytes_max: int | None = Field(default=None, ge=0)
    created_after: datetime | None = None
    created_before: datetime | None = None


class FileListResponse(BaseModel):
    items: list[FileMetadataResponse]
    total: int
    limit: int
    offset: int
    sort_field: FileSortField
    sort_direction: FileSortDirection
    search: str | None = None
    mime_type: str | None = None
    size_bytes_min: int | None = None
    size_bytes_max: int | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None


class FileUploadResponse(FileMetadataResponse):
    pass
