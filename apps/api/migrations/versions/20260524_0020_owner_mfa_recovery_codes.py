"""Owner MFA recovery codes.

Revision ID: 20260524_0020
Revises: 20260524_0019
Create Date: 2026-05-24
"""

import sqlalchemy as sa
from alembic import op

revision = "20260524_0020"
down_revision = "20260524_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "owner_mfa_recovery_codes" not in inspector.get_table_names():
        op.create_table(
            "owner_mfa_recovery_codes",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("owner_user_id", sa.String(length=36), nullable=False),
            sa.Column("code_hash", sa.String(length=128), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["owner_user_id"], ["owner_users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("owner_mfa_recovery_codes")}
    for name, column in {
        "ix_owner_mfa_recovery_codes_owner_user_id": "owner_user_id",
        "ix_owner_mfa_recovery_codes_used_at": "used_at",
    }.items():
        if name not in indexes:
            op.create_index(name, "owner_mfa_recovery_codes", [column])


def downgrade() -> None:
    bind = op.get_bind()
    if "owner_mfa_recovery_codes" in sa.inspect(bind).get_table_names():
        op.drop_table("owner_mfa_recovery_codes")
