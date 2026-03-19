from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base_class import Base
from app.models.file import File
from app.models.user import User
from app.repositories.file import FileQueryFilters, SQLAlchemyFileRepository
from app.repositories.user import SQLAlchemyUserRepository


def test_file_repository_lists_owner_scoped_results_with_search_filters() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine, tables=[User.__table__, File.__table__])

    with Session(engine) as session:
        user_repository = SQLAlchemyUserRepository(db=session)
        file_repository = SQLAlchemyFileRepository(db=session)
        owner = user_repository.create(
            email="owner@example.com",
            hashed_password="password-hash",
        )
        other_user = user_repository.create(
            email="other@example.com",
            hashed_password="password-hash",
        )

        matching_file = file_repository.create(
            owner_id=owner.id,
            original_name="Atlas Notes.txt",
            storage_key="owner/atlas-notes.txt",
            size_bytes=128,
            checksum_sha256="a" * 64,
            mime_type="text/plain",
        )
        file_repository.create(
            owner_id=owner.id,
            original_name="holiday-photo.jpg",
            storage_key="owner/holiday-photo.jpg",
            size_bytes=512,
            checksum_sha256="b" * 64,
            mime_type="image/jpeg",
        )
        file_repository.create(
            owner_id=other_user.id,
            original_name="atlas-secrets.txt",
            storage_key="other/atlas-secrets.txt",
            size_bytes=256,
            checksum_sha256="c" * 64,
            mime_type="text/plain",
        )

        results = file_repository.list_for_owner(
            owner.id,
            filters=FileQueryFilters(
                search=" atlas ",
                mime_type="text/plain",
                size_bytes_min=100,
                size_bytes_max=200,
            ),
        )
        total = file_repository.count_for_owner(
            owner.id,
            filters=FileQueryFilters(
                search="atlas",
                mime_type="text/plain",
                size_bytes_min=100,
                size_bytes_max=200,
            ),
        )

    assert [file_record.id for file_record in results] == [matching_file.id]
    assert total == 1


def test_file_repository_applies_sort_pagination_and_excludes_deleted_rows() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine, tables=[User.__table__, File.__table__])

    with Session(engine) as session:
        user_repository = SQLAlchemyUserRepository(db=session)
        file_repository = SQLAlchemyFileRepository(db=session)
        owner = user_repository.create(
            email="owner@example.com",
            hashed_password="password-hash",
        )

        alpha = file_repository.create(
            owner_id=owner.id,
            original_name="alpha.txt",
            storage_key="owner/alpha.txt",
            size_bytes=100,
            checksum_sha256="a" * 64,
            mime_type="text/plain",
        )
        beta = file_repository.create(
            owner_id=owner.id,
            original_name="beta.txt",
            storage_key="owner/beta.txt",
            size_bytes=200,
            checksum_sha256="b" * 64,
            mime_type="text/plain",
        )
        gamma = file_repository.create(
            owner_id=owner.id,
            original_name="gamma.txt",
            storage_key="owner/gamma.txt",
            size_bytes=300,
            checksum_sha256="c" * 64,
            mime_type="text/plain",
        )

        gamma.is_deleted = True
        session.add(gamma)
        session.commit()

        first_page = file_repository.list_for_owner(
            owner.id,
            limit=1,
            offset=0,
            sort_field="original_name",
            sort_direction="asc",
        )
        second_page = file_repository.list_for_owner(
            owner.id,
            limit=1,
            offset=1,
            sort_field="original_name",
            sort_direction="asc",
        )
        total = file_repository.count_for_owner(owner.id)

    assert [file_record.id for file_record in first_page] == [alpha.id]
    assert [file_record.id for file_record in second_page] == [beta.id]
    assert total == 2


def test_file_repository_filters_by_created_at_window() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine, tables=[User.__table__, File.__table__])

    with Session(engine) as session:
        user_repository = SQLAlchemyUserRepository(db=session)
        file_repository = SQLAlchemyFileRepository(db=session)
        owner = user_repository.create(
            email="owner@example.com",
            hashed_password="password-hash",
        )

        base_time = datetime(2026, 3, 18, 12, 0, tzinfo=UTC)

        older_file = file_repository.create(
            owner_id=owner.id,
            original_name="older.txt",
            storage_key="owner/older.txt",
            size_bytes=100,
            checksum_sha256="a" * 64,
            mime_type="text/plain",
        )
        newer_file = file_repository.create(
            owner_id=owner.id,
            original_name="newer.txt",
            storage_key="owner/newer.txt",
            size_bytes=100,
            checksum_sha256="b" * 64,
            mime_type="text/plain",
        )

        older_file.created_at = base_time - timedelta(days=2)
        newer_file.created_at = base_time
        session.add(older_file)
        session.add(newer_file)
        session.commit()

        results = file_repository.list_for_owner(
            owner.id,
            filters=FileQueryFilters(
                created_after=base_time - timedelta(days=1),
                created_before=base_time + timedelta(hours=1),
            ),
            sort_field="created_at",
            sort_direction="asc",
        )

    assert [file_record.id for file_record in results] == [newer_file.id]
