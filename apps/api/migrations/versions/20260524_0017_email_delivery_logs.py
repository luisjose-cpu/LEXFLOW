"""Email delivery logs.

Revision ID: 20260524_0017
Revises: 20260524_0016
Create Date: 2026-05-24
"""

import sqlalchemy as sa
from alembic import op

revision = "20260524_0017"
down_revision = "20260524_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "email_delivery_logs" not in inspector.get_table_names():
        op.create_table(
            "email_delivery_logs",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("tenant_id", sa.String(length=36), nullable=False),
            sa.Column("template", sa.String(length=80), nullable=False),
            sa.Column("provider", sa.String(length=80), nullable=False),
            sa.Column("status", sa.String(length=40), nullable=False),
            sa.Column("recipient_hash", sa.String(length=128), nullable=False),
            sa.Column("recipient_hint", sa.String(length=120), nullable=False),
            sa.Column("request_id", sa.String(length=80), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("email_delivery_logs")}
    for name, column in {
        "ix_email_delivery_logs_tenant_id": "tenant_id",
        "ix_email_delivery_logs_template": "template",
        "ix_email_delivery_logs_status": "status",
        "ix_email_delivery_logs_created_at": "created_at",
    }.items():
        if name not in indexes:
            op.create_index(name, "email_delivery_logs", [column])


def downgrade() -> None:
    bind = op.get_bind()
    if "email_delivery_logs" in sa.inspect(bind).get_table_names():
        op.drop_table("email_delivery_logs")
