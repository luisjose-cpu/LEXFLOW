"""P8 AI job result and review fields.

Revision ID: 20260522_0005
Revises: 20260522_0004
Create Date: 2026-05-22
"""

import sqlalchemy as sa
from alembic import op

revision = "20260522_0005"
down_revision = "20260522_0004"
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def add_column_once(table_name: str, column: sa.Column) -> None:
    if not column_exists(table_name, column.name):
        op.add_column(table_name, column)


def upgrade() -> None:
    add_column_once("ai_jobs", sa.Column("result_json", sa.JSON(), nullable=False, server_default="{}"))
    add_column_once("ai_jobs", sa.Column("reviewed_by_user_id", sa.String(length=36), nullable=True))
    add_column_once("ai_jobs", sa.Column("review_note", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("ai_jobs", "review_note")
    op.drop_column("ai_jobs", "reviewed_by_user_id")
    op.drop_column("ai_jobs", "result_json")
