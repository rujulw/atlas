"""User repository interfaces and SQLAlchemy implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository(Protocol):
    def get_by_email(self, email: str) -> User | None:
        """Find a user by email address."""

    def create(self, email: str, hashed_password: str, full_name: str | None = None) -> User:
        """Create and persist a new user."""


@dataclass
class SQLAlchemyUserRepository:
    """User repository backed by a SQLAlchemy session."""

    db: Session

    def get_by_email(self, email: str) -> User | None:
        return self.db.execute(select(User).where(User.email == email)).scalar_one_or_none()

    def create(self, email: str, hashed_password: str, full_name: str | None = None) -> User:
        user = User(email=email, hashed_password=hashed_password, full_name=full_name)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
