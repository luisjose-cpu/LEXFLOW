"""Level 3 Legal OS intelligence.

Revision ID: 20260524_0024
Revises: 20260524_0023
Create Date: 2026-05-24
"""

from alembic import op

revision = "20260524_0024"
down_revision = "20260524_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    from app.db.models import (
        AiAgentRun,
        CountryConfig,
        KnowledgeVaultItem,
        LegalGraphEdge,
        LegalGraphNode,
        LegalMemoryItem,
        MarketplaceInstallation,
        MarketplaceItem,
    )

    for model in [
        KnowledgeVaultItem,
        LegalMemoryItem,
        LegalGraphNode,
        LegalGraphEdge,
        MarketplaceItem,
        MarketplaceInstallation,
        CountryConfig,
        AiAgentRun,
    ]:
        model.__table__.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    for table in [
        "ai_agent_runs",
        "country_configs",
        "marketplace_installations",
        "marketplace_items",
        "legal_graph_edges",
        "legal_graph_nodes",
        "legal_memory_items",
        "knowledge_vault_items",
    ]:
        op.drop_table(table)
