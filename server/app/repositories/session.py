"""Refresh-session repository interfaces and SQLAlchemy implementation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.session import RefreshSession


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)


class RefreshSessionRepository(Protocol):
    def create(
        self,
        *,
        session_identifier: str,
        user_id: int,
        refresh_token_hash: str,
        expires_at: datetime,
        device_name: str | None = None,
        user_agent: str | None = None,
        last_seen_ip: str | None = None,
        last_used_at: datetime | None = None,
    ) -> RefreshSession:
        """Create and persist a refresh session."""

    def get_by_session_identifier(self, session_identifier: str) -> RefreshSession | None:
        """Find a refresh session by its public identifier."""

    def get_by_refresh_token_hash(self, refresh_token_hash: str) -> RefreshSession | None:
        """Find a refresh session by stored refresh-token hash."""

    def list_for_user(self, user_id: int) -> list[RefreshSession]:
        """List refresh sessions for a user ordered by most recent creation time."""

    def touch(
        self,
        session_identifier: str,
        *,
        last_used_at: datetime | None = None,
        last_seen_ip: str | None = None,
        user_agent: str | None = None,
    ) -> RefreshSession | None:
        """Update last-used metadata for a refresh session."""

    def revoke(
        self,
        session_identifier: str,
        *,
        revoked_at: datetime | None = None,
        replaced_by_session_identifier: str | None = None,
    ) -> RefreshSession | None:
        """Mark a refresh session revoked."""

    def revoke_all_for_user(
        self,
        user_id: int,
        *,
        revoked_at: datetime | None = None,
    ) -> int:
        """Revoke all active refresh sessions for a user and return the count."""


@dataclass
class SQLAlchemyRefreshSessionRepository:
    """Refresh-session repository backed by a SQLAlchemy session."""

    db: Session

    def create(
        self,
        *,
        session_identifier: str,
        user_id: int,
        refresh_token_hash: str,
        expires_at: datetime,
        device_name: str | None = None,
        user_agent: str | None = None,
        last_seen_ip: str | None = None,
        last_used_at: datetime | None = None,
    ) -> RefreshSession:
        refresh_session = RefreshSession(
            session_identifier=session_identifier,
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
            device_name=device_name,
            user_agent=user_agent,
            last_seen_ip=last_seen_ip,
            last_used_at=last_used_at,
        )
        self.db.add(refresh_session)
        self.db.commit()
        self.db.refresh(refresh_session)
        return refresh_session

    def get_by_session_identifier(self, session_identifier: str) -> RefreshSession | None:
        statement = select(RefreshSession).where(
            RefreshSession.session_identifier == session_identifier
        )
        return self.db.execute(statement).scalar_one_or_none()

    def get_by_refresh_token_hash(self, refresh_token_hash: str) -> RefreshSession | None:
        statement = select(RefreshSession).where(
            RefreshSession.refresh_token_hash == refresh_token_hash
        )
        return self.db.execute(statement).scalar_one_or_none()

    def list_for_user(self, user_id: int) -> list[RefreshSession]:
        statement = (
            select(RefreshSession)
            .where(RefreshSession.user_id == user_id)
            .order_by(RefreshSession.created_at.desc(), RefreshSession.id.desc())
        )
        return list(self.db.execute(statement).scalars())

    def touch(
        self,
        session_identifier: str,
        *,
        last_used_at: datetime | None = None,
        last_seen_ip: str | None = None,
        user_agent: str | None = None,
    ) -> RefreshSession | None:
        refresh_session = self.get_by_session_identifier(session_identifier)
        if refresh_session is None:
            return None

        refresh_session.last_used_at = last_used_at or _utc_now()
        if last_seen_ip is not None:
            refresh_session.last_seen_ip = last_seen_ip
        if user_agent is not None:
            refresh_session.user_agent = user_agent

        self.db.add(refresh_session)
        self.db.commit()
        self.db.refresh(refresh_session)
        return refresh_session

    def revoke(
        self,
        session_identifier: str,
        *,
        revoked_at: datetime | None = None,
        replaced_by_session_identifier: str | None = None,
    ) -> RefreshSession | None:
        refresh_session = self.get_by_session_identifier(session_identifier)
        if refresh_session is None:
            return None

        refresh_session.revoked_at = revoked_at or _utc_now()
        refresh_session.replaced_by_session_identifier = replaced_by_session_identifier

        self.db.add(refresh_session)
        self.db.commit()
        self.db.refresh(refresh_session)
        return refresh_session

    def revoke_all_for_user(
        self,
        user_id: int,
        *,
        revoked_at: datetime | None = None,
    ) -> int:
        timestamp = revoked_at or _utc_now()
        statement = select(RefreshSession).where(
            RefreshSession.user_id == user_id,
            RefreshSession.revoked_at.is_(None),
        )
        refresh_sessions = list(self.db.execute(statement).scalars())
        for refresh_session in refresh_sessions:
            refresh_session.revoked_at = timestamp
            self.db.add(refresh_session)

        self.db.commit()
        return len(refresh_sessions)
