"""SINOE integration credentials and metadata.

Revision ID: 20260524_0010
Revises: 20260522_0009
Create Date: 2026-05-24
"""

import sqlalchemy as sa
from alembic import op

revision = "20260524_0010"
down_revision = "20260522_0009"
branch_labels = None
depends_on = None


def inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def table_exists(table_name: str) -> bool:
    return table_name in inspector().get_table_names()


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
    bind = op.get_bind()
    from app.db.models import IntegrationCredential

    IntegrationCredential.__table__.create(bind=bind, checkfirst=True)
    create_index_once("ix_integration_credentials_tenant_id", "integration_credentials", ["tenant_id"])
    create_index_once("ix_integration_credentials_provider", "integration_credentials", ["provider"])
    create_index_once("ix_integration_credentials_status", "integration_credentials", ["status"])

    add_column_once("case_sources", sa.Column("source_name", sa.String(length=180), nullable=True))
    add_column_once("case_sources", sa.Column("last_result", sa.Text(), nullable=True))
    add_column_once("captcha_checkpoints", sa.Column("provider", sa.String(length=80), nullable=False, server_default="judicial"))
    add_column_once("captcha_checkpoints", sa.Column("screenshot_url", sa.String(length=500), nullable=True))
    add_column_once("captcha_checkpoints", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("captcha_checkpoints", "expires_at")
    op.drop_column("captcha_checkpoints", "screenshot_url")
    op.drop_column("captcha_checkpoints", "provider")
    op.drop_column("case_sources", "last_result")
    op.drop_column("case_sources", "source_name")
    op.drop_index("ix_integration_credentials_status", table_name="integration_credentials")
    op.drop_index("ix_integration_credentials_provider", table_name="integration_credentials")
    op.drop_index("ix_integration_credentials_tenant_id", table_name="integration_credentials")
    op.drop_table("integration_credentials")
