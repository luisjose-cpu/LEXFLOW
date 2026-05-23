"""P5 judicial automation checkpoints and evidence.

Revision ID: 20260522_0002
Revises: 20260522_0001
Create Date: 2026-05-22
"""

from alembic import op

from app.db.models import CaptchaCheckpoint, JudicialEvidence

revision = "20260522_0002"
down_revision = "20260522_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    CaptchaCheckpoint.__table__.create(bind=bind, checkfirst=True)
    JudicialEvidence.__table__.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    JudicialEvidence.__table__.drop(bind=bind, checkfirst=True)
    CaptchaCheckpoint.__table__.drop(bind=bind, checkfirst=True)
