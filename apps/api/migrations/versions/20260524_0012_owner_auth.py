"""Owner console authentication fields.

Revision ID: 20260524_0012
Revises: 20260524_0011
Create Date: 2026-05-24
"""

import sqlalchemy as sa
from alembic import op

revision = "20260524_0012"
down_revision = "20260524_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = {column["name"] for column in sa.inspect(bind).get_columns("owner_users")}
    with op.batch_alter_table("owner_users") as batch:
        if "hashed_password" not in existing:
            batch.add_column(sa.Column("hashed_password", sa.String(length=255), nullable=True))
        if "refresh_token_version" not in existing:
            batch.add_column(sa.Column("refresh_token_version", sa.Integer(), nullable=False, server_default="0"))
        if "last_login_at" not in existing:
            batch.add_column(sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    existing = {column["name"] for column in sa.inspect(bind).get_columns("owner_users")}
    with op.batch_alter_table("owner_users") as batch:
        if "last_login_at" in existing:
            batch.drop_column("last_login_at")
        if "refresh_token_version" in existing:
            batch.drop_column("refresh_token_version")
        if "hashed_password" in existing:
            batch.drop_column("hashed_password")
