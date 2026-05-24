"""User refresh token version for tenant session revocation.

Revision ID: 20260524_0013
Revises: 20260524_0012
Create Date: 2026-05-24
"""

import sqlalchemy as sa
from alembic import op

revision = "20260524_0013"
down_revision = "20260524_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = {column["name"] for column in sa.inspect(bind).get_columns("users")}
    with op.batch_alter_table("users") as batch:
        if "refresh_token_version" not in existing:
            batch.add_column(sa.Column("refresh_token_version", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    bind = op.get_bind()
    existing = {column["name"] for column in sa.inspect(bind).get_columns("users")}
    with op.batch_alter_table("users") as batch:
        if "refresh_token_version" in existing:
            batch.drop_column("refresh_token_version")
