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


def upgrade() -> None:
    op.add_column("documents", sa.Column("file_size_bytes", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("documents", sa.Column("checksum_sha256", sa.String(length=96), nullable=True))
    op.add_column("documents", sa.Column("storage_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("documents", sa.Column("malware_scan_status", sa.String(length=40), nullable=False, server_default="pending"))
    op.add_column("documents", sa.Column("malware_scan_result", sa.JSON(), nullable=False, server_default="{}"))
    op.create_index("ix_documents_checksum_sha256", "documents", ["checksum_sha256"])
    op.create_index("ix_documents_malware_scan_status", "documents", ["malware_scan_status"])


def downgrade() -> None:
    op.drop_index("ix_documents_malware_scan_status", table_name="documents")
    op.drop_index("ix_documents_checksum_sha256", table_name="documents")
    op.drop_column("documents", "malware_scan_result")
    op.drop_column("documents", "malware_scan_status")
    op.drop_column("documents", "storage_verified_at")
    op.drop_column("documents", "checksum_sha256")
    op.drop_column("documents", "file_size_bytes")
