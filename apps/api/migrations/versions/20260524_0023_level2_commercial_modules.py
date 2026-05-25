"""Level 2 commercial modules.

Revision ID: 20260524_0023
Revises: 20260524_0022
Create Date: 2026-05-24
"""

from alembic import op

revision = "20260524_0023"
down_revision = "20260524_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    from app.db.models import CaseExpense, CaseFinancial, CaseHour, CrmLead, DemoSnapshot

    for model in [CrmLead, CaseFinancial, CaseExpense, CaseHour, DemoSnapshot]:
        model.__table__.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    for table in ["demo_snapshots", "case_hours", "case_expenses", "case_financials", "crm_leads"]:
        op.drop_table(table)

