"""P19 document trust lifecycle.

Revision ID: 20260522_0009
Revises: 20260522_0008
Create Date: 2026-05-22
"""

import sqlalchemy as sa
from alembic import op

revision = "20260522_0009"
down_revision = "20260522_0008"
branch_labels = None
depends_on = None


def inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def column_exists(table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector().get_columns(table_name)}


def index_exists(table_name: str, index_name: str) -> bool:
    return index_name in {index["name"] for index in inspector().get_indexes(table_name)}


def add_column_once(table_name: str, column: sa.Column) -> None:
    if not column_exists(table_name, column.name):
        op.add_column(table_name, column)


def create_index_once(index_name: str, table_name: str, columns: list[str]) -> None:
    if not index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def upgrade() -> None:
    add_column_once("documents", sa.Column("file_size_bytes", sa.Integer(), nullable=False, server_default="0"))
    add_column_once("documents", sa.Column("checksum_sha256", sa.String(length=96), nullable=True))
    add_column_once("documents", sa.Column("storage_verified_at", sa.DateTime(timezone=True), nullable=True))
    add_column_once("documents", sa.Column("malware_scan_status", sa.String(length=40), nullable=False, server_default="pending"))
    add_column_once("documents", sa.Column("malware_scan_result", sa.JSON(), nullable=False, server_default="{}"))
    create_index_once("ix_documents_checksum_sha256", "documents", ["checksum_sha256"])
    create_index_once("ix_documents_malware_scan_status", "documents", ["malware_scan_status"])


def downgrade() -> None:
    op.drop_index("ix_documents_malware_scan_status", table_name="documents")
    op.drop_index("ix_documents_checksum_sha256", table_name="documents")
    op.drop_column("documents", "malware_scan_result")
    op.drop_column("documents", "malware_scan_status")
    op.drop_column("documents", "storage_verified_at")
    op.drop_column("documents", "checksum_sha256")
    op.drop_column("documents", "file_size_bytes")
