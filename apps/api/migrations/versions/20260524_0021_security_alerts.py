"""Security alerts.

Revision ID: 20260524_0021
Revises: 20260524_0020
Create Date: 2026-05-24
"""

import sqlalchemy as sa
from alembic import op

revision = "20260524_0021"
down_revision = "20260524_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "security_alerts" not in inspector.get_table_names():
        op.create_table(
            "security_alerts",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("scope", sa.String(length=40), nullable=False),
            sa.Column("tenant_id", sa.String(length=36), nullable=True),
            sa.Column("actor_user_id", sa.String(length=36), nullable=True),
            sa.Column("owner_user_id", sa.String(length=36), nullable=True),
            sa.Column("owner_email", sa.String(length=240), nullable=True),
            sa.Column("severity", sa.String(length=40), nullable=False),
            sa.Column("event_type", sa.String(length=120), nullable=False),
            sa.Column("title", sa.String(length=240), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=40), nullable=False),
            sa.Column("request_id", sa.String(length=120), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=False),
            sa.Column("acknowledged_by_user_id", sa.String(length=36), nullable=True),
            sa.Column("acknowledged_by_owner_user_id", sa.String(length=36), nullable=True),
            sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["acknowledged_by_owner_user_id"], ["owner_users.id"]),
            sa.ForeignKeyConstraint(["acknowledged_by_user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["owner_user_id"], ["owner_users.id"]),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("security_alerts")}
    for name, column in {
        "ix_security_alerts_scope": "scope",
        "ix_security_alerts_tenant_id": "tenant_id",
        "ix_security_alerts_owner_user_id": "owner_user_id",
        "ix_security_alerts_event_type": "event_type",
        "ix_security_alerts_status": "status",
        "ix_security_alerts_created_at": "created_at",
    }.items():
        if name not in indexes:
            op.create_index(name, "security_alerts", [column])


def downgrade() -> None:
    bind = op.get_bind()
    if "security_alerts" in sa.inspect(bind).get_table_names():
        op.drop_table("security_alerts")
