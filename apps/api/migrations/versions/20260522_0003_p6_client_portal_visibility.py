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


def column_exists(table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def add_column_once(table_name: str, column: sa.Column) -> None:
    if not column_exists(table_name, column.name):
        op.add_column(table_name, column)


def upgrade() -> None:
    add_column_once("case_events", sa.Column("is_client_visible", sa.Boolean(), nullable=False, server_default=sa.false()))
    add_column_once("documents", sa.Column("is_client_visible", sa.Boolean(), nullable=False, server_default=sa.false()))
    add_column_once("documents", sa.Column("uploaded_by_client", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("documents", "uploaded_by_client")
    op.drop_column("documents", "is_client_visible")
    op.drop_column("case_events", "is_client_visible")
