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


def index_exists(table_name: str, index_name: str) -> bool:
    return index_name in {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table_name)}


def create_index_once(index_name: str, table_name: str, columns: list[str]) -> None:
    if not index_exists(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def upgrade() -> None:
    bind = op.get_bind()
    from app.db.models import AutomationAction, AutomationCondition, AutomationRun, AutomationRunStep, AutomationWorkflow

    AutomationWorkflow.__table__.create(bind=bind, checkfirst=True)
    create_index_once("ix_automation_workflows_tenant_id", "automation_workflows", ["tenant_id"])
    create_index_once("ix_automation_workflows_trigger_key", "automation_workflows", ["trigger_key"])
    create_index_once("ix_automation_workflows_status", "automation_workflows", ["status"])
    create_index_once("ix_automation_workflows_created_at", "automation_workflows", ["created_at"])

    AutomationCondition.__table__.create(bind=bind, checkfirst=True)
    create_index_once("ix_automation_conditions_tenant_id", "automation_conditions", ["tenant_id"])
    create_index_once("ix_automation_conditions_workflow_id", "automation_conditions", ["workflow_id"])

    AutomationAction.__table__.create(bind=bind, checkfirst=True)
    create_index_once("ix_automation_actions_tenant_id", "automation_actions", ["tenant_id"])
    create_index_once("ix_automation_actions_workflow_id", "automation_actions", ["workflow_id"])

    AutomationRun.__table__.create(bind=bind, checkfirst=True)
    create_index_once("ix_automation_runs_tenant_id", "automation_runs", ["tenant_id"])
    create_index_once("ix_automation_runs_workflow_id", "automation_runs", ["workflow_id"])
    create_index_once("ix_automation_runs_trigger_key", "automation_runs", ["trigger_key"])
    create_index_once("ix_automation_runs_status", "automation_runs", ["status"])
    create_index_once("ix_automation_runs_created_at", "automation_runs", ["created_at"])

    AutomationRunStep.__table__.create(bind=bind, checkfirst=True)
    create_index_once("ix_automation_run_steps_tenant_id", "automation_run_steps", ["tenant_id"])
    create_index_once("ix_automation_run_steps_run_id", "automation_run_steps", ["run_id"])
    create_index_once("ix_automation_run_steps_status", "automation_run_steps", ["status"])


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
