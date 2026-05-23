"""P13 automation studio.

Revision ID: 20260522_0008
Revises: 20260522_0007
Create Date: 2026-05-22
"""

import sqlalchemy as sa
from alembic import op

revision = "20260522_0008"
down_revision = "20260522_0007"
branch_labels = None
depends_on = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "automation_workflows",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("trigger_key", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="draft"),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_automation_workflows_tenant_id", "automation_workflows", ["tenant_id"])
    op.create_index("ix_automation_workflows_trigger_key", "automation_workflows", ["trigger_key"])
    op.create_index("ix_automation_workflows_status", "automation_workflows", ["status"])
    op.create_index("ix_automation_workflows_created_at", "automation_workflows", ["created_at"])

    op.create_table(
        "automation_conditions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("workflow_id", sa.String(length=36), sa.ForeignKey("automation_workflows.id"), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("condition_type", sa.String(length=120), nullable=False, server_default="ALWAYS"),
        sa.Column("config_json", sa.JSON(), nullable=False, server_default="{}"),
        *timestamps(),
    )
    op.create_index("ix_automation_conditions_tenant_id", "automation_conditions", ["tenant_id"])
    op.create_index("ix_automation_conditions_workflow_id", "automation_conditions", ["workflow_id"])

    op.create_table(
        "automation_actions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("workflow_id", sa.String(length=36), sa.ForeignKey("automation_workflows.id"), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("action_type", sa.String(length=120), nullable=False),
        sa.Column("config_json", sa.JSON(), nullable=False, server_default="{}"),
        *timestamps(),
    )
    op.create_index("ix_automation_actions_tenant_id", "automation_actions", ["tenant_id"])
    op.create_index("ix_automation_actions_workflow_id", "automation_actions", ["workflow_id"])

    op.create_table(
        "automation_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("workflow_id", sa.String(length=36), sa.ForeignKey("automation_workflows.id"), nullable=False),
        sa.Column("trigger_key", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="running"),
        sa.Column("event_payload_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("result_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_automation_runs_tenant_id", "automation_runs", ["tenant_id"])
    op.create_index("ix_automation_runs_workflow_id", "automation_runs", ["workflow_id"])
    op.create_index("ix_automation_runs_trigger_key", "automation_runs", ["trigger_key"])
    op.create_index("ix_automation_runs_status", "automation_runs", ["status"])
    op.create_index("ix_automation_runs_created_at", "automation_runs", ["created_at"])

    op.create_table(
        "automation_run_steps",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("automation_runs.id"), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("step_type", sa.String(length=40), nullable=False),
        sa.Column("key", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("result_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_automation_run_steps_tenant_id", "automation_run_steps", ["tenant_id"])
    op.create_index("ix_automation_run_steps_run_id", "automation_run_steps", ["run_id"])
    op.create_index("ix_automation_run_steps_status", "automation_run_steps", ["status"])


def downgrade() -> None:
    op.drop_index("ix_automation_run_steps_status", table_name="automation_run_steps")
    op.drop_index("ix_automation_run_steps_run_id", table_name="automation_run_steps")
    op.drop_index("ix_automation_run_steps_tenant_id", table_name="automation_run_steps")
    op.drop_table("automation_run_steps")
    op.drop_index("ix_automation_runs_created_at", table_name="automation_runs")
    op.drop_index("ix_automation_runs_status", table_name="automation_runs")
    op.drop_index("ix_automation_runs_trigger_key", table_name="automation_runs")
    op.drop_index("ix_automation_runs_workflow_id", table_name="automation_runs")
    op.drop_index("ix_automation_runs_tenant_id", table_name="automation_runs")
    op.drop_table("automation_runs")
    op.drop_index("ix_automation_actions_workflow_id", table_name="automation_actions")
    op.drop_index("ix_automation_actions_tenant_id", table_name="automation_actions")
    op.drop_table("automation_actions")
    op.drop_index("ix_automation_conditions_workflow_id", table_name="automation_conditions")
    op.drop_index("ix_automation_conditions_tenant_id", table_name="automation_conditions")
    op.drop_table("automation_conditions")
    op.drop_index("ix_automation_workflows_created_at", table_name="automation_workflows")
    op.drop_index("ix_automation_workflows_status", table_name="automation_workflows")
    op.drop_index("ix_automation_workflows_trigger_key", table_name="automation_workflows")
    op.drop_index("ix_automation_workflows_tenant_id", table_name="automation_workflows")
    op.drop_table("automation_workflows")
