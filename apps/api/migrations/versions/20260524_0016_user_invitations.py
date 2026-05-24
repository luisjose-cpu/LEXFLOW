"""Tenant user invitations.

Revision ID: 20260524_0016
Revises: 20260524_0015
Create Date: 2026-05-24
"""

import sqlalchemy as sa
from alembic import op

revision = "20260524_0016"
down_revision = "20260524_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "user_invitations" not in inspector.get_table_names():
        op.create_table(
            "user_invitations",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("email", sa.String(length=240), nullable=False),
            sa.Column("full_name", sa.String(length=180), nullable=False),
            sa.Column("role", sa.String(length=80), nullable=False),
            sa.Column("token_hash", sa.String(length=128), nullable=False),
            sa.Column("status", sa.String(length=40), nullable=False),
            sa.Column("invited_by_user_id", sa.String(length=36), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["invited_by_user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("token_hash"),
        )
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("user_invitations")}
    for name, column in {
        "ix_user_invitations_tenant_id": "tenant_id",
        "ix_user_invitations_email": "email",
        "ix_user_invitations_status": "status",
        "ix_user_invitations_token_hash": "token_hash",
        "ix_user_invitations_expires_at": "expires_at",
    }.items():
        if name not in indexes:
            op.create_index(name, "user_invitations", [column])


def downgrade() -> None:
    bind = op.get_bind()
    if "user_invitations" in sa.inspect(bind).get_table_names():
        op.drop_table("user_invitations")
