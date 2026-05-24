"""Owner console operational tables.

Revision ID: 20260524_0011
Revises: 20260524_0010
Create Date: 2026-05-24
"""

from alembic import op

revision = "20260524_0011"
down_revision = "20260524_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    from app.db.models import (
        DemoTenant,
        OwnerAuditLog,
        OwnerRole,
        OwnerUser,
        SupportTicket,
        SupportTicketMessage,
        SystemHealthCheck,
        SystemIncident,
        TenantFeatureFlag,
        TenantHealthScore,
        TenantIntervention,
        TenantLimit,
        TenantUsageDaily,
    )

    for model in [
        OwnerRole,
        OwnerUser,
        OwnerAuditLog,
        TenantHealthScore,
        SupportTicket,
        SupportTicketMessage,
        TenantFeatureFlag,
        TenantLimit,
        TenantUsageDaily,
        TenantIntervention,
        DemoTenant,
        SystemHealthCheck,
        SystemIncident,
    ]:
        model.__table__.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    for table in [
        "system_incidents",
        "system_health_checks",
        "demo_tenants",
        "tenant_interventions",
        "tenant_usage_daily",
        "tenant_limits",
        "tenant_feature_flags",
        "support_ticket_messages",
        "support_tickets",
        "tenant_health_scores",
        "owner_audit_logs",
        "owner_users",
        "owner_roles",
    ]:
        op.drop_table(table)
