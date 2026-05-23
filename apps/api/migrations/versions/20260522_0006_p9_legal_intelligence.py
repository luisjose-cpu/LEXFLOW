"""P9 legal intelligence center.

Revision ID: 20260522_0006
Revises: 20260522_0005
Create Date: 2026-05-22
"""

import sqlalchemy as sa
from alembic import op

revision = "20260522_0006"
down_revision = "20260522_0005"
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
    add_column_once("legal_news_sources", sa.Column("adapter_key", sa.String(length=120), nullable=False, server_default="mock"))
    add_column_once("legal_news_sources", sa.Column("config_json", sa.JSON(), nullable=False, server_default="{}"))

    add_column_once("legal_news", sa.Column("external_id", sa.String(length=180), nullable=True))
    add_column_once("legal_news", sa.Column("category", sa.String(length=80), nullable=False, server_default="news"))
    add_column_once("legal_news", sa.Column("ai_summary", sa.Text(), nullable=True))
    add_column_once("legal_news", sa.Column("status", sa.String(length=40), nullable=False, server_default="published"))
    add_column_once("legal_news", sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"))
    add_column_once("legal_news", sa.Column("trend_score", sa.String(length=40), nullable=False, server_default="normal"))
    add_column_once("legal_news", sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"))
    create_index_once("ix_legal_news_status", "legal_news", ["status"])
    create_index_once("ix_legal_news_category", "legal_news", ["category"])

    from app.db.models import LegalAlert, LegalNewsCaseLink, LegalNewsFavorite, LegalTag

    LegalNewsFavorite.__table__.create(bind=bind, checkfirst=True)
    create_index_once("ix_legal_news_favorites_tenant_id", "legal_news_favorites", ["tenant_id"])
    create_index_once("ix_legal_news_favorites_news_id", "legal_news_favorites", ["news_id"])

    LegalNewsCaseLink.__table__.create(bind=bind, checkfirst=True)
    create_index_once("ix_legal_news_case_links_tenant_id", "legal_news_case_links", ["tenant_id"])
    create_index_once("ix_legal_news_case_links_case_id", "legal_news_case_links", ["case_id"])
    create_index_once("ix_legal_news_case_links_news_id", "legal_news_case_links", ["news_id"])

    LegalAlert.__table__.create(bind=bind, checkfirst=True)
    create_index_once("ix_legal_alerts_tenant_id", "legal_alerts", ["tenant_id"])
    create_index_once("ix_legal_alerts_status", "legal_alerts", ["status"])
    create_index_once("ix_legal_alerts_severity", "legal_alerts", ["severity"])
    create_index_once("ix_legal_alerts_created_at", "legal_alerts", ["created_at"])

    LegalTag.__table__.create(bind=bind, checkfirst=True)
    create_index_once("ix_legal_tags_tenant_id", "legal_tags", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_legal_tags_tenant_id", table_name="legal_tags")
    op.drop_table("legal_tags")
    op.drop_index("ix_legal_alerts_created_at", table_name="legal_alerts")
    op.drop_index("ix_legal_alerts_severity", table_name="legal_alerts")
    op.drop_index("ix_legal_alerts_status", table_name="legal_alerts")
    op.drop_index("ix_legal_alerts_tenant_id", table_name="legal_alerts")
    op.drop_table("legal_alerts")
    op.drop_index("ix_legal_news_case_links_news_id", table_name="legal_news_case_links")
    op.drop_index("ix_legal_news_case_links_case_id", table_name="legal_news_case_links")
    op.drop_index("ix_legal_news_case_links_tenant_id", table_name="legal_news_case_links")
    op.drop_table("legal_news_case_links")
    op.drop_index("ix_legal_news_favorites_news_id", table_name="legal_news_favorites")
    op.drop_index("ix_legal_news_favorites_tenant_id", table_name="legal_news_favorites")
    op.drop_table("legal_news_favorites")
    op.drop_index("ix_legal_news_category", table_name="legal_news")
    op.drop_index("ix_legal_news_status", table_name="legal_news")
    op.drop_column("legal_news", "metadata_json")
    op.drop_column("legal_news", "trend_score")
    op.drop_column("legal_news", "tags")
    op.drop_column("legal_news", "status")
    op.drop_column("legal_news", "ai_summary")
    op.drop_column("legal_news", "category")
    op.drop_column("legal_news", "external_id")
    op.drop_column("legal_news_sources", "config_json")
    op.drop_column("legal_news_sources", "adapter_key")
