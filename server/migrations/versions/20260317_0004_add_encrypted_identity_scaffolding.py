"""add encrypted identity scaffolding

Revision ID: 20260317_0004
Revises: 20260305_0003
Create Date: 2026-03-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260317_0004"
down_revision = "20260305_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_ciphertext", sa.String(length=1024), nullable=True))
    op.add_column("users", sa.Column("email_blind_index", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("username_ciphertext", sa.String(length=1024), nullable=True))
    op.add_column("users", sa.Column("username_blind_index", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("full_name_ciphertext", sa.String(length=1024), nullable=True))
    op.add_column("users", sa.Column("identity_key_version", sa.String(length=32), nullable=True))

    op.create_index(
        op.f("ix_users_email_blind_index"),
        "users",
        ["email_blind_index"],
        unique=False,
    )
    op.create_index(
        op.f("ix_users_username_blind_index"),
        "users",
        ["username_blind_index"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_users_username_blind_index"), table_name="users")
    op.drop_index(op.f("ix_users_email_blind_index"), table_name="users")

    op.drop_column("users", "identity_key_version")
    op.drop_column("users", "full_name_ciphertext")
    op.drop_column("users", "username_blind_index")
    op.drop_column("users", "username_ciphertext")
    op.drop_column("users", "email_blind_index")
    op.drop_column("users", "email_ciphertext")
