"""Security alert deliveries.

Revision ID: 20260524_0022
Revises: 20260524_0021
Create Date: 2026-05-24
"""

import sqlalchemy as sa
from alembic import op

revision = "20260524_0022"
down_revision = "20260524_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "security_alert_deliveries" not in inspector.get_table_names():
        op.create_table(
            "security_alert_deliveries",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("alert_id", sa.String(length=36), nullable=False),
            sa.Column("scope", sa.String(length=40), nullable=False),
            sa.Column("tenant_id", sa.String(length=36), nullable=True),
            sa.Column("owner_user_id", sa.String(length=36), nullable=True),
            sa.Column("channel", sa.String(length=40), nullable=False),
            sa.Column("template", sa.String(length=80), nullable=False),
            sa.Column("recipient_email_encrypted", sa.Text(), nullable=False),
            sa.Column("recipient_hash", sa.String(length=128), nullable=False),
            sa.Column("recipient_hint", sa.String(length=120), nullable=False),
            sa.Column("provider", sa.String(length=80), nullable=True),
            sa.Column("status", sa.String(length=40), nullable=False),
            sa.Column("attempts", sa.Integer(), nullable=False),
            sa.Column("max_attempts", sa.Integer(), nullable=False),
            sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["alert_id"], ["security_alerts.id"]),
            sa.ForeignKeyConstraint(["owner_user_id"], ["owner_users.id"]),
            sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("security_alert_deliveries")}
    for name, column in {
        "ix_security_alert_deliveries_alert_id": "alert_id",
        "ix_security_alert_deliveries_scope": "scope",
        "ix_security_alert_deliveries_status": "status",
        "ix_security_alert_deliveries_next_attempt_at": "next_attempt_at",
        "ix_security_alert_deliveries_created_at": "created_at",
    }.items():
        if name not in indexes:
            op.create_index(name, "security_alert_deliveries", [column])


def downgrade() -> None:
    bind = op.get_bind()
    if "security_alert_deliveries" in sa.inspect(bind).get_table_names():
        op.drop_table("security_alert_deliveries")
