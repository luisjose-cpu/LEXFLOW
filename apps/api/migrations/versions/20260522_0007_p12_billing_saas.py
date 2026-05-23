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


def upgrade() -> None:
    op.create_table(
        "billing_plans",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("monthly_price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trial_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="active"),
        sa.Column("limits_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.UniqueConstraint("tenant_id", "code", name="uq_billing_plans_tenant_code"),
    )
    op.create_index("ix_billing_plans_tenant_id", "billing_plans", ["tenant_id"])
    op.create_index("ix_billing_plans_code", "billing_plans", ["code"])
    op.create_index("ix_billing_plans_status", "billing_plans", ["status"])
    op.create_index("ix_billing_plans_created_at", "billing_plans", ["created_at"])

    op.create_table(
        "plan_features",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("plan_id", sa.String(length=36), sa.ForeignKey("billing_plans.id"), nullable=False),
        sa.Column("feature_key", sa.String(length=120), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("limit_value", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        *timestamps(),
        sa.UniqueConstraint("tenant_id", "plan_id", "feature_key", name="uq_plan_features_plan_feature"),
    )
    op.create_index("ix_plan_features_tenant_id", "plan_features", ["tenant_id"])
    op.create_index("ix_plan_features_plan_id", "plan_features", ["plan_id"])
    op.create_index("ix_plan_features_feature_key", "plan_features", ["feature_key"])

    op.create_table(
        "tenant_subscriptions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("plan_id", sa.String(length=36), sa.ForeignKey("billing_plans.id"), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="trialing"),
        sa.Column("seats", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider", sa.String(length=80), nullable=False, server_default="mock"),
        sa.Column("provider_subscription_id", sa.String(length=180), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_tenant_subscriptions_tenant_id", "tenant_subscriptions", ["tenant_id"])
    op.create_index("ix_tenant_subscriptions_plan_id", "tenant_subscriptions", ["plan_id"])
    op.create_index("ix_tenant_subscriptions_status", "tenant_subscriptions", ["status"])
    op.create_index("ix_tenant_subscriptions_created_at", "tenant_subscriptions", ["created_at"])

    op.create_table(
        "tenant_usage",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("feature_key", sa.String(length=120), nullable=False),
        sa.Column("period_key", sa.String(length=40), nullable=False),
        sa.Column("used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("limit_value", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        *timestamps(),
        sa.UniqueConstraint("tenant_id", "feature_key", "period_key", name="uq_tenant_usage_feature_period"),
    )
    op.create_index("ix_tenant_usage_tenant_id", "tenant_usage", ["tenant_id"])
    op.create_index("ix_tenant_usage_feature_key", "tenant_usage", ["feature_key"])
    op.create_index("ix_tenant_usage_period_key", "tenant_usage", ["period_key"])
    op.create_index("ix_tenant_usage_created_at", "tenant_usage", ["created_at"])

    op.create_table(
        "billing_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("subscription_id", sa.String(length=36), sa.ForeignKey("tenant_subscriptions.id"), nullable=True),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="processed"),
        sa.Column("payload_json", sa.JSON(), nullable=False, server_default="{}"),
        *timestamps(),
    )
    op.create_index("ix_billing_events_tenant_id", "billing_events", ["tenant_id"])
    op.create_index("ix_billing_events_subscription_id", "billing_events", ["subscription_id"])
    op.create_index("ix_billing_events_event_type", "billing_events", ["event_type"])
    op.create_index("ix_billing_events_status", "billing_events", ["status"])
    op.create_index("ix_billing_events_created_at", "billing_events", ["created_at"])

    op.create_table(
        "invoices",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("subscription_id", sa.String(length=36), sa.ForeignKey("tenant_subscriptions.id"), nullable=True),
        sa.Column("invoice_number", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="draft"),
        sa.Column("amount_due_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=12), nullable=False, server_default="USD"),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        *timestamps(),
        sa.UniqueConstraint("tenant_id", "invoice_number", name="uq_invoices_tenant_number"),
    )
    op.create_index("ix_invoices_tenant_id", "invoices", ["tenant_id"])
    op.create_index("ix_invoices_subscription_id", "invoices", ["subscription_id"])
    op.create_index("ix_invoices_status", "invoices", ["status"])
    op.create_index("ix_invoices_created_at", "invoices", ["created_at"])


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
