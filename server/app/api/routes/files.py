"""File storage API routes."""

from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.routes.auth import get_current_subject
from app.core.config import settings
from app.models.file import File as FileModel
from app.models.user import User
from app.repositories.file import (
    FileQueryFilters,
    FileRepository,
    SQLAlchemyFileRepository,
)
from app.repositories.user import SQLAlchemyUserRepository, UserRepository
from app.schemas.file import (
    FileListResponse,
    FileMetadataResponse,
    FileSortDirection,
    FileSortField,
    FileUploadResponse,
)
from app.services.storage import (
    BlobStorageService,
    LocalBlobStorageService,
    StorageKeyService,
    UUIDStorageKeyService,
)

router = APIRouter(prefix="/files", tags=["files"])


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return SQLAlchemyUserRepository(db=db)


def get_file_repository(db: Session = Depends(get_db)) -> FileRepository:
    return SQLAlchemyFileRepository(db=db)


def get_storage_key_service() -> StorageKeyService:
    return UUIDStorageKeyService()


def get_blob_storage_service() -> BlobStorageService:
    return LocalBlobStorageService(root_path=Path(settings.STORAGE_ROOT_PATH))


def _resolve_current_user(
    current_subject: int,
    user_repository: UserRepository,
) -> User:
    user = user_repository.get_by_id(current_subject)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user not found.",
        )
    return user


def _serialize_file_metadata(file_record: FileModel) -> FileMetadataResponse:
    return FileMetadataResponse(
        id=file_record.id,
        owner_id=file_record.owner_id,
        original_name=file_record.original_name,
        storage_key=file_record.storage_key,
        mime_type=file_record.mime_type,
        size_bytes=file_record.size_bytes,
        checksum_sha256=file_record.checksum_sha256,
        created_at=file_record.created_at,
        updated_at=file_record.updated_at,
    )


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_subject: int = Depends(get_current_subject),
    user_repository: UserRepository = Depends(get_user_repository),
    file_repository: FileRepository = Depends(get_file_repository),
    storage_key_service: StorageKeyService = Depends(get_storage_key_service),
    blob_storage_service: BlobStorageService = Depends(get_blob_storage_service),
) -> FileUploadResponse:
    user = _resolve_current_user(current_subject, user_repository)

    original_name = file.filename or "upload.bin"
    storage_key = storage_key_service.generate_storage_key(
        owner_id=user.id,
        original_name=original_name,
    )
    file_bytes = await file.read()
    try:
        stored_object = blob_storage_service.write_bytes(
            storage_key=storage_key,
            data=file_bytes,
            mime_type=file.content_type,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    file_record = file_repository.create(
        owner_id=user.id,
        original_name=original_name,
        storage_key=stored_object.storage_key,
        mime_type=stored_object.mime_type,
        size_bytes=stored_object.size_bytes,
        checksum_sha256=stored_object.checksum_sha256,
    )
    return FileUploadResponse(
        id=file_record.id,
        owner_id=file_record.owner_id,
        original_name=file_record.original_name,
        storage_key=file_record.storage_key,
        mime_type=file_record.mime_type,
        size_bytes=file_record.size_bytes,
        checksum_sha256=file_record.checksum_sha256,
        created_at=file_record.created_at,
        updated_at=file_record.updated_at,
    )


@router.get("", response_model=FileListResponse)
async def list_files(
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    sort_field: FileSortField = "created_at",
    sort_direction: FileSortDirection = "desc",
    search: Annotated[str | None, Query(max_length=255)] = None,
    mime_type: Annotated[str | None, Query(max_length=255)] = None,
    size_bytes_min: Annotated[int | None, Query(ge=0)] = None,
    size_bytes_max: Annotated[int | None, Query(ge=0)] = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    current_subject: int = Depends(get_current_subject),
    user_repository: UserRepository = Depends(get_user_repository),
    file_repository: FileRepository = Depends(get_file_repository),
) -> FileListResponse:
    user = _resolve_current_user(current_subject, user_repository)
    normalized_search = search.strip() if search is not None else None
    if normalized_search == "":
        normalized_search = None

    if (
        size_bytes_min is not None
        and size_bytes_max is not None
        and size_bytes_min > size_bytes_max
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="size_bytes_min cannot be greater than size_bytes_max.",
        )

    if (
        created_after is not None
        and created_before is not None
        and created_after > created_before
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="created_after cannot be later than created_before.",
        )

    filters = FileQueryFilters(
        search=normalized_search,
        mime_type=mime_type,
        size_bytes_min=size_bytes_min,
        size_bytes_max=size_bytes_max,
        created_after=created_after,
        created_before=created_before,
    )

    files = file_repository.list_for_owner(
        owner_id=user.id,
        filters=filters,
        limit=limit,
        offset=offset,
        sort_field=sort_field,
        sort_direction=sort_direction,
    )
    total = file_repository.count_for_owner(
        owner_id=user.id,
        filters=filters,
    )

    return FileListResponse(
        items=[_serialize_file_metadata(file_record) for file_record in files],
        total=total,
        limit=limit,
        offset=offset,
        sort_field=sort_field,
        sort_direction=sort_direction,
        search=normalized_search,
        mime_type=mime_type,
        size_bytes_min=size_bytes_min,
        size_bytes_max=size_bytes_max,
        created_after=created_after,
        created_before=created_before,
    )


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    current_subject: int = Depends(get_current_subject),
    user_repository: UserRepository = Depends(get_user_repository),
    file_repository: FileRepository = Depends(get_file_repository),
    blob_storage_service: BlobStorageService = Depends(get_blob_storage_service),
) -> Response:
    user = _resolve_current_user(current_subject, user_repository)
    file_record = file_repository.get_by_id_for_owner(file_id=file_id, owner_id=user.id)
    if file_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found.",
        )

    try:
        file_bytes = blob_storage_service.read_bytes(file_record.storage_key)
    except (FileNotFoundError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File content not found.",
        ) from None

    content_disposition = f'attachment; filename="{file_record.original_name}"'
    return Response(
        content=file_bytes,
        media_type=file_record.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": content_disposition,
            "X-Checksum-SHA256": file_record.checksum_sha256,
        },
    )
