"""Tenant security policy.

Revision ID: 20260524_0018
Revises: 20260524_0017
Create Date: 2026-05-24
"""

import sqlalchemy as sa
from alembic import op

revision = "20260524_0018"
down_revision = "20260524_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "tenant_security_policies" not in inspector.get_table_names():
        op.create_table(
            "tenant_security_policies",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("enforce_mfa", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("mfa_required_roles", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("grace_period_hours", sa.Integer(), nullable=False, server_default="72"),
            sa.Column("allow_client_user_mfa_bypass", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_by", sa.String(length=36), nullable=True),
            sa.Column("updated_by", sa.String(length=36), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
            sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("tenant_id", name="uq_tenant_security_policies_tenant_id"),
        )
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("tenant_security_policies")}
    for name, column in {
        "ix_tenant_security_policies_tenant_id": "tenant_id",
        "ix_tenant_security_policies_enforce_mfa": "enforce_mfa",
    }.items():
        if name not in indexes:
            op.create_index(name, "tenant_security_policies", [column])


def downgrade() -> None:
    bind = op.get_bind()
    if "tenant_security_policies" in sa.inspect(bind).get_table_names():
        op.drop_table("tenant_security_policies")
