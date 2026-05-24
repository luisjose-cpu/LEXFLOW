"""Tenant user MFA TOTP fields.

Revision ID: 20260524_0015
Revises: 20260524_0014
Create Date: 2026-05-24
"""

import sqlalchemy as sa
from alembic import op

revision = "20260524_0015"
down_revision = "20260524_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing = {column["name"] for column in sa.inspect(bind).get_columns("users")}
    with op.batch_alter_table("users") as batch:
        if "mfa_secret_encrypted" not in existing:
            batch.add_column(sa.Column("mfa_secret_encrypted", sa.Text(), nullable=True))
        if "mfa_confirmed_at" not in existing:
            batch.add_column(sa.Column("mfa_confirmed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    existing = {column["name"] for column in sa.inspect(bind).get_columns("users")}
    with op.batch_alter_table("users") as batch:
        if "mfa_confirmed_at" in existing:
            batch.drop_column("mfa_confirmed_at")
        if "mfa_secret_encrypted" in existing:
            batch.drop_column("mfa_secret_encrypted")
