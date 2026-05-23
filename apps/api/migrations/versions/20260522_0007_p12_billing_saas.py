"""P12 billing SaaS.

Revision ID: 20260522_0007
Revises: 20260522_0006
Create Date: 2026-05-22
"""

import sqlalchemy as sa
from alembic import op

revision = "20260522_0007"
down_revision = "20260522_0006"
branch_labels = None
depends_on = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def index_exists(table_name: str, index_name: str) -> bool:
    return index_name in {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table_name)}


def create_index_once(index_name: str, table_name: str, columns: list[str]) -> None:
    if not index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def upgrade() -> None:
    bind = op.get_bind()
    from app.db.models import BillingEvent, BillingPlan, Invoice, PlanFeature, TenantSubscription, TenantUsage

    BillingPlan.__table__.create(bind=bind, checkfirst=True)
    create_index_once("ix_billing_plans_tenant_id", "billing_plans", ["tenant_id"])
    create_index_once("ix_billing_plans_code", "billing_plans", ["code"])
    create_index_once("ix_billing_plans_status", "billing_plans", ["status"])
    create_index_once("ix_billing_plans_created_at", "billing_plans", ["created_at"])

    PlanFeature.__table__.create(bind=bind, checkfirst=True)
    create_index_once("ix_plan_features_tenant_id", "plan_features", ["tenant_id"])
    create_index_once("ix_plan_features_plan_id", "plan_features", ["plan_id"])
    create_index_once("ix_plan_features_feature_key", "plan_features", ["feature_key"])

    TenantSubscription.__table__.create(bind=bind, checkfirst=True)
    create_index_once("ix_tenant_subscriptions_tenant_id", "tenant_subscriptions", ["tenant_id"])
    create_index_once("ix_tenant_subscriptions_plan_id", "tenant_subscriptions", ["plan_id"])
    create_index_once("ix_tenant_subscriptions_status", "tenant_subscriptions", ["status"])
    create_index_once("ix_tenant_subscriptions_created_at", "tenant_subscriptions", ["created_at"])

    TenantUsage.__table__.create(bind=bind, checkfirst=True)
    create_index_once("ix_tenant_usage_tenant_id", "tenant_usage", ["tenant_id"])
    create_index_once("ix_tenant_usage_feature_key", "tenant_usage", ["feature_key"])
    create_index_once("ix_tenant_usage_period_key", "tenant_usage", ["period_key"])
    create_index_once("ix_tenant_usage_created_at", "tenant_usage", ["created_at"])

    BillingEvent.__table__.create(bind=bind, checkfirst=True)
    create_index_once("ix_billing_events_tenant_id", "billing_events", ["tenant_id"])
    create_index_once("ix_billing_events_subscription_id", "billing_events", ["subscription_id"])
    create_index_once("ix_billing_events_event_type", "billing_events", ["event_type"])
    create_index_once("ix_billing_events_status", "billing_events", ["status"])
    create_index_once("ix_billing_events_created_at", "billing_events", ["created_at"])

    Invoice.__table__.create(bind=bind, checkfirst=True)
    create_index_once("ix_invoices_tenant_id", "invoices", ["tenant_id"])
    create_index_once("ix_invoices_subscription_id", "invoices", ["subscription_id"])
    create_index_once("ix_invoices_status", "invoices", ["status"])
    create_index_once("ix_invoices_created_at", "invoices", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_invoices_created_at", table_name="invoices")
    op.drop_index("ix_invoices_status", table_name="invoices")
    op.drop_index("ix_invoices_subscription_id", table_name="invoices")
    op.drop_index("ix_invoices_tenant_id", table_name="invoices")
    op.drop_table("invoices")
    op.drop_index("ix_billing_events_created_at", table_name="billing_events")
    op.drop_index("ix_billing_events_status", table_name="billing_events")
    op.drop_index("ix_billing_events_event_type", table_name="billing_events")
    op.drop_index("ix_billing_events_subscription_id", table_name="billing_events")
    op.drop_index("ix_billing_events_tenant_id", table_name="billing_events")
    op.drop_table("billing_events")
    op.drop_index("ix_tenant_usage_created_at", table_name="tenant_usage")
    op.drop_index("ix_tenant_usage_period_key", table_name="tenant_usage")
    op.drop_index("ix_tenant_usage_feature_key", table_name="tenant_usage")
    op.drop_index("ix_tenant_usage_tenant_id", table_name="tenant_usage")
    op.drop_table("tenant_usage")
    op.drop_index("ix_tenant_subscriptions_created_at", table_name="tenant_subscriptions")
    op.drop_index("ix_tenant_subscriptions_status", table_name="tenant_subscriptions")
    op.drop_index("ix_tenant_subscriptions_plan_id", table_name="tenant_subscriptions")
    op.drop_index("ix_tenant_subscriptions_tenant_id", table_name="tenant_subscriptions")
    op.drop_table("tenant_subscriptions")
    op.drop_index("ix_plan_features_feature_key", table_name="plan_features")
    op.drop_index("ix_plan_features_plan_id", table_name="plan_features")
    op.drop_index("ix_plan_features_tenant_id", table_name="plan_features")
    op.drop_table("plan_features")
    op.drop_index("ix_billing_plans_created_at", table_name="billing_plans")
    op.drop_index("ix_billing_plans_status", table_name="billing_plans")
    op.drop_index("ix_billing_plans_code", table_name="billing_plans")
    op.drop_index("ix_billing_plans_tenant_id", table_name="billing_plans")
    op.drop_table("billing_plans")
