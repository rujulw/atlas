from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base_class import Base
from app.models.session import RefreshSession
from app.models.user import User
from app.repositories.session import SQLAlchemyRefreshSessionRepository
from app.repositories.user import SQLAlchemyUserRepository


def test_refresh_session_repository_creates_and_fetches_session() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine, tables=[User.__table__, RefreshSession.__table__])

    with Session(engine) as session:
        user_repository = SQLAlchemyUserRepository(db=session)
        refresh_session_repository = SQLAlchemyRefreshSessionRepository(db=session)
        user = user_repository.create(
            email="user@example.com",
            hashed_password="password-hash",
        )
        user_id = user.id

        created_session = refresh_session_repository.create(
            session_identifier="session-123",
            user_id=user_id,
            refresh_token_hash="hash-123",
            expires_at=datetime.now(tz=UTC) + timedelta(days=7),
            device_name="MacBook Pro",
            user_agent="pytest-agent",
            last_seen_ip="127.0.0.1",
        )
        fetched_by_identifier = refresh_session_repository.get_by_session_identifier(
            "session-123"
        )
        fetched_by_token_hash = refresh_session_repository.get_by_refresh_token_hash("hash-123")

    assert created_session.id is not None
    assert fetched_by_identifier is not None
    assert fetched_by_identifier.user_id == user_id
    assert fetched_by_identifier.device_name == "MacBook Pro"
    assert fetched_by_token_hash is not None
    assert fetched_by_token_hash.session_identifier == "session-123"


def test_refresh_session_repository_lists_and_touches_user_sessions() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine, tables=[User.__table__, RefreshSession.__table__])

    with Session(engine) as session:
        user_repository = SQLAlchemyUserRepository(db=session)
        refresh_session_repository = SQLAlchemyRefreshSessionRepository(db=session)
        user = user_repository.create(
            email="user@example.com",
            hashed_password="password-hash",
        )
        user_id = user.id

        refresh_session_repository.create(
            session_identifier="session-older",
            user_id=user_id,
            refresh_token_hash="hash-older",
            expires_at=datetime.now(tz=UTC) + timedelta(days=7),
        )
        refresh_session_repository.create(
            session_identifier="session-newer",
            user_id=user_id,
            refresh_token_hash="hash-newer",
            expires_at=datetime.now(tz=UTC) + timedelta(days=7),
        )

        sessions = refresh_session_repository.list_for_user(user_id)
        session_identifiers = [
            refresh_session.session_identifier for refresh_session in sessions
        ]
        touched_session = refresh_session_repository.touch(
            "session-newer",
            last_seen_ip="10.0.0.1",
            user_agent="updated-agent",
        )

    assert session_identifiers == [
        "session-newer",
        "session-older",
    ]
    assert touched_session is not None
    assert touched_session.last_used_at is not None
    assert touched_session.last_seen_ip == "10.0.0.1"
    assert touched_session.user_agent == "updated-agent"


def test_refresh_session_repository_revokes_single_and_all_user_sessions() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine, tables=[User.__table__, RefreshSession.__table__])

    with Session(engine) as session:
        user_repository = SQLAlchemyUserRepository(db=session)
        refresh_session_repository = SQLAlchemyRefreshSessionRepository(db=session)
        user = user_repository.create(
            email="user@example.com",
            hashed_password="password-hash",
        )
        user_id = user.id

        refresh_session_repository.create(
            session_identifier="session-a",
            user_id=user_id,
            refresh_token_hash="hash-a",
            expires_at=datetime.now(tz=UTC) + timedelta(days=7),
        )
        refresh_session_repository.create(
            session_identifier="session-b",
            user_id=user_id,
            refresh_token_hash="hash-b",
            expires_at=datetime.now(tz=UTC) + timedelta(days=7),
        )

        revoked_session = refresh_session_repository.revoke(
            "session-a",
            replaced_by_session_identifier="session-b",
        )
        revoked_count = refresh_session_repository.revoke_all_for_user(user_id)
        sessions = refresh_session_repository.list_for_user(user_id)
        all_revoked = all(
            refresh_session.revoked_at is not None for refresh_session in sessions
        )

    assert revoked_session is not None
    assert revoked_session.revoked_at is not None
    assert revoked_session.replaced_by_session_identifier == "session-b"
    assert revoked_count == 1
    assert all_revoked
