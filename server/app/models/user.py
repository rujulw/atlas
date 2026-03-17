"""User domain model."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email_ciphertext: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    email_blind_index: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    username_ciphertext: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    username_blind_index: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name_ciphertext: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    identity_key_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
