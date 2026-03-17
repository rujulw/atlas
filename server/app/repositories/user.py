"""User repository interfaces and SQLAlchemy implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository(Protocol):
    def get_by_id(self, user_id: int) -> User | None:
        """Find a user by internal id."""

    def get_by_email(self, email: str) -> User | None:
        """Find a user by email address."""

    def get_by_email_blind_index(self, email_blind_index: str) -> User | None:
        """Find a user by blind-indexed email."""

    def create(
        self,
        email: str,
        hashed_password: str,
        full_name: str | None = None,
        *,
        email_ciphertext: str | None = None,
        email_blind_index: str | None = None,
        username_ciphertext: str | None = None,
        username_blind_index: str | None = None,
        full_name_ciphertext: str | None = None,
        identity_key_version: str | None = None,
    ) -> User:
        """Create and persist a new user."""


@dataclass
class SQLAlchemyUserRepository:
    """User repository backed by a SQLAlchemy session."""

    db: Session

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

    def get_by_email(self, email: str) -> User | None:
        return self.db.execute(select(User).where(User.email == email)).scalar_one_or_none()

    def get_by_email_blind_index(self, email_blind_index: str) -> User | None:
        return self.db.execute(
            select(User).where(User.email_blind_index == email_blind_index)
        ).scalar_one_or_none()

    def create(
        self,
        email: str,
        hashed_password: str,
        full_name: str | None = None,
        *,
        email_ciphertext: str | None = None,
        email_blind_index: str | None = None,
        username_ciphertext: str | None = None,
        username_blind_index: str | None = None,
        full_name_ciphertext: str | None = None,
        identity_key_version: str | None = None,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            email_ciphertext=email_ciphertext,
            email_blind_index=email_blind_index,
            username_ciphertext=username_ciphertext,
            username_blind_index=username_blind_index,
            full_name_ciphertext=full_name_ciphertext,
            identity_key_version=identity_key_version,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
