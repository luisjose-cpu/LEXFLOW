from hashlib import sha256
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import models as dbm
from app.services.email_delivery import EmailDeliveryResult


class EmailDeliveryLogService:
    def record(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        template: str,
        to_email: str,
        result: EmailDeliveryResult,
        request_id: str | None = None,
    ) -> None:
        try:
            db.add(
                dbm.EmailDeliveryLog(
                    tenant_id=str(tenant_id),
                    template=template,
                    provider=result.provider,
                    status=result.status,
                    recipient_hash=self._hash_email(to_email),
                    recipient_hint=self._hint(to_email),
                    request_id=request_id,
                )
            )
            db.commit()
        except SQLAlchemyError:
            db.rollback()

    def list_for_tenant(self, db: Session, *, tenant_id: UUID | str, limit: int = 25) -> list[dict[str, object]]:
        try:
            rows = db.scalars(
                select(dbm.EmailDeliveryLog)
                .where(dbm.EmailDeliveryLog.tenant_id == str(tenant_id))
                .order_by(dbm.EmailDeliveryLog.created_at.desc())
                .limit(limit)
            ).all()
        except SQLAlchemyError:
            return []
        return [
            {
                "id": row.id,
                "template": row.template,
                "provider": row.provider,
                "status": row.status,
                "recipient_hint": row.recipient_hint,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]

    @staticmethod
    def _hash_email(email: str) -> str:
        return sha256(email.lower().encode("utf-8")).hexdigest()

    @staticmethod
    def _hint(email: str) -> str:
        local, _, domain = email.lower().partition("@")
        if not domain:
            return "***"
        visible = local[:2] if len(local) >= 2 else local[:1]
        return f"{visible}***@{domain}"


email_delivery_log_service = EmailDeliveryLogService()
