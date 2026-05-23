"""P7 communication multichannel tables.

Revision ID: 20260522_0004
Revises: 20260522_0003
Create Date: 2026-05-22
"""

from alembic import op

from app.db.models import CommunicationMessage, CommunicationThread, MessageTemplate, NotificationRule

revision = "20260522_0004"
down_revision = "20260522_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    MessageTemplate.__table__.create(bind=bind, checkfirst=True)
    NotificationRule.__table__.create(bind=bind, checkfirst=True)
    CommunicationThread.__table__.create(bind=bind, checkfirst=True)
    CommunicationMessage.__table__.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    CommunicationMessage.__table__.drop(bind=bind, checkfirst=True)
    CommunicationThread.__table__.drop(bind=bind, checkfirst=True)
    NotificationRule.__table__.drop(bind=bind, checkfirst=True)
    MessageTemplate.__table__.drop(bind=bind, checkfirst=True)
