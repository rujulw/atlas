"""File storage API routes."""

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.routes.auth import get_current_subject
from app.core.config import settings
from app.repositories.file import FileRepository, SQLAlchemyFileRepository
from app.repositories.user import SQLAlchemyUserRepository, UserRepository
from app.schemas.file import FileUploadResponse
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


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_subject: str = Depends(get_current_subject),
    user_repository: UserRepository = Depends(get_user_repository),
    file_repository: FileRepository = Depends(get_file_repository),
    storage_key_service: StorageKeyService = Depends(get_storage_key_service),
    blob_storage_service: BlobStorageService = Depends(get_blob_storage_service),
) -> FileUploadResponse:
    user = user_repository.get_by_email(current_subject)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user not found.",
        )

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
    )
