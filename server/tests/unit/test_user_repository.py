from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base_class import Base
from app.models.user import User
from app.repositories.user import SQLAlchemyUserRepository


def test_user_repository_creates_and_fetches_user() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine, tables=[User.__table__])

    with Session(engine) as session:
        user_repository = SQLAlchemyUserRepository(db=session)

        created_user = user_repository.create(
            email="user@example.com",
            hashed_password="password-hash",
            full_name="Atlas User",
        )
        fetched_user = user_repository.get_by_email("user@example.com")

    assert created_user.id is not None
    assert fetched_user is not None
    assert fetched_user.email == "user@example.com"
    assert fetched_user.full_name == "Atlas User"
    assert fetched_user.hashed_password == "password-hash"


def test_user_repository_persists_identity_scaffolding_fields() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine, tables=[User.__table__])

    with Session(engine) as session:
        user_repository = SQLAlchemyUserRepository(db=session)

        created_user = user_repository.create(
            email="user@example.com",
            hashed_password="password-hash",
            full_name="Atlas User",
            email_ciphertext="enc:email",
            email_blind_index="bidx:email",
            username_ciphertext="enc:username",
            username_blind_index="bidx:username",
            full_name_ciphertext="enc:full-name",
            identity_key_version="v1",
        )

    assert created_user.email_ciphertext == "enc:email"
    assert created_user.email_blind_index == "bidx:email"
    assert created_user.username_ciphertext == "enc:username"
    assert created_user.username_blind_index == "bidx:username"
    assert created_user.full_name_ciphertext == "enc:full-name"
    assert created_user.identity_key_version == "v1"
