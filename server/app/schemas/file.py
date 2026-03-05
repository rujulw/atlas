"""File upload/download schemas."""

from datetime import datetime

from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    id: int
    owner_id: int
    original_name: str
    storage_key: str
    mime_type: str | None = None
    size_bytes: int
    checksum_sha256: str
    created_at: datetime
