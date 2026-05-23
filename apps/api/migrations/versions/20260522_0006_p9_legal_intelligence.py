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


def upgrade() -> None:
    op.add_column("legal_news_sources", sa.Column("adapter_key", sa.String(length=120), nullable=False, server_default="mock"))
    op.add_column("legal_news_sources", sa.Column("config_json", sa.JSON(), nullable=False, server_default="{}"))

    op.add_column("legal_news", sa.Column("external_id", sa.String(length=180), nullable=True))
    op.add_column("legal_news", sa.Column("category", sa.String(length=80), nullable=False, server_default="news"))
    op.add_column("legal_news", sa.Column("ai_summary", sa.Text(), nullable=True))
    op.add_column("legal_news", sa.Column("status", sa.String(length=40), nullable=False, server_default="published"))
    op.add_column("legal_news", sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("legal_news", sa.Column("trend_score", sa.String(length=40), nullable=False, server_default="normal"))
    op.add_column("legal_news", sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"))
    op.create_index("ix_legal_news_status", "legal_news", ["status"])
    op.create_index("ix_legal_news_category", "legal_news", ["category"])

    op.create_table(
        "legal_news_favorites",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("news_id", sa.String(length=36), sa.ForeignKey("legal_news.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "user_id", "news_id", name="uq_legal_news_favorites_user_news"),
    )
    op.create_index("ix_legal_news_favorites_tenant_id", "legal_news_favorites", ["tenant_id"])
    op.create_index("ix_legal_news_favorites_news_id", "legal_news_favorites", ["news_id"])

    op.create_table(
        "legal_news_case_links",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("case_id", sa.String(length=36), sa.ForeignKey("cases.id"), nullable=False),
        sa.Column("news_id", sa.String(length=36), sa.ForeignKey("legal_news.id"), nullable=False),
        sa.Column("linked_by_user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "case_id", "news_id", name="uq_legal_news_case_links_case_news"),
    )
    op.create_index("ix_legal_news_case_links_tenant_id", "legal_news_case_links", ["tenant_id"])
    op.create_index("ix_legal_news_case_links_case_id", "legal_news_case_links", ["case_id"])
    op.create_index("ix_legal_news_case_links_news_id", "legal_news_case_links", ["news_id"])

    op.create_table(
        "legal_alerts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("news_id", sa.String(length=36), sa.ForeignKey("legal_news.id"), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=40), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="open"),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_legal_alerts_tenant_id", "legal_alerts", ["tenant_id"])
    op.create_index("ix_legal_alerts_status", "legal_alerts", ["status"])
    op.create_index("ix_legal_alerts_severity", "legal_alerts", ["severity"])
    op.create_index("ix_legal_alerts_created_at", "legal_alerts", ["created_at"])

    op.create_table(
        "legal_tags",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("color", sa.String(length=40), nullable=False, server_default="blue"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "name", name="uq_legal_tags_tenant_name"),
    )
    op.create_index("ix_legal_tags_tenant_id", "legal_tags", ["tenant_id"])


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
