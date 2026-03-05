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
