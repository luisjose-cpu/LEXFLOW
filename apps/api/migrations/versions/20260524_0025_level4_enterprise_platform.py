"""Level 4 enterprise legal intelligence platform.

Revision ID: 20260524_0025
Revises: 20260524_0024
Create Date: 2026-05-24
"""

from alembic import op

revision = "20260524_0025"
down_revision = "20260524_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    from app.db.models import (
        BackupRecord,
        CloudEnvironment,
        Department,
        EnterpriseAiSwarmRun,
        EvidenceVaultItem,
        GovernancePolicy,
        LegalDataEvent,
        Organization,
        OrganizationTenant,
        OrchestrationEvent,
        PublicApiKey,
        RetentionPolicy,
        RevenueInsight,
        Team,
        TeamMember,
        TelemetryMetric,
        WebhookSubscription,
    )

    for model in [
        Organization,
        OrganizationTenant,
        Department,
        Team,
        TeamMember,
        LegalDataEvent,
        OrchestrationEvent,
        EnterpriseAiSwarmRun,
        TelemetryMetric,
        PublicApiKey,
        WebhookSubscription,
        GovernancePolicy,
        EvidenceVaultItem,
        RetentionPolicy,
        CloudEnvironment,
        BackupRecord,
        RevenueInsight,
    ]:
        model.__table__.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    for table in [
        "revenue_insights",
        "backup_records",
        "cloud_environments",
        "retention_policies",
        "evidence_vault_items",
        "governance_policies",
        "webhook_subscriptions",
        "public_api_keys",
        "telemetry_metrics",
        "enterprise_ai_swarm_runs",
        "orchestration_events",
        "legal_data_events",
        "team_members",
        "teams",
        "departments",
        "organization_tenants",
        "organizations",
    ]:
        op.drop_table(table)
