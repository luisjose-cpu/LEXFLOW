"""P6 client portal visibility flags.

Revision ID: 20260522_0003
Revises: 20260522_0002
Create Date: 2026-05-22
"""

import sqlalchemy as sa
from alembic import op

revision = "20260522_0003"
down_revision = "20260522_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("case_events", sa.Column("is_client_visible", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("documents", sa.Column("is_client_visible", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("documents", sa.Column("uploaded_by_client", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("documents", "uploaded_by_client")
    op.drop_column("documents", "is_client_visible")
    op.drop_column("case_events", "is_client_visible")
