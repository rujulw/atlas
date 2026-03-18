"""SQLAlchemy metadata registry.

Import model modules here so Alembic can discover them.
"""

from app.db.base_class import Base
from app.models import file, session, user  # noqa: F401

__all__ = ["Base"]
