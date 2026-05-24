"""Owner MFA TOTP.

Revision ID: 20260524_0019
Revises: 20260524_0018
Create Date: 2026-05-24
"""

import sqlalchemy as sa
from alembic import op

revision = "20260524_0019"
down_revision = "20260524_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("owner_users")}
    if "mfa_secret_encrypted" not in columns:
        op.add_column("owner_users", sa.Column("mfa_secret_encrypted", sa.Text(), nullable=True))
    if "mfa_confirmed_at" not in columns:
        op.add_column("owner_users", sa.Column("mfa_confirmed_at", sa.DateTime(timezone=True), nullable=True))
    try:
        op.alter_column("owner_users", "mfa_enabled", server_default=sa.false(), existing_type=sa.Boolean(), existing_nullable=False)
    except Exception:
        pass


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("owner_users")}
    if "mfa_confirmed_at" in columns:
        op.drop_column("owner_users", "mfa_confirmed_at")
    if "mfa_secret_encrypted" in columns:
        op.drop_column("owner_users", "mfa_secret_encrypted")
