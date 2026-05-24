from datetime import timedelta
from hashlib import sha256
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import models as dbm
from app.domain.models import User
from app.services.email_delivery import get_email_provider
from app.services.sinoe_integration import CredentialCipher


ALERT_EMAIL_SEVERITIES = {"high", "critical"}


class SecurityAlertService:
    def create_tenant_alert(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        actor_user_id: UUID | str | None,
        event_type: str,
        title: str,
        body: str,
        severity: str = "medium",
        request_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> dbm.SecurityAlert | None:
        try:
            alert = dbm.SecurityAlert(
                scope="tenant",
                tenant_id=str(tenant_id),
                actor_user_id=str(actor_user_id) if actor_user_id else None,
                event_type=event_type,
                title=title,
                body=body,
                severity=severity,
                status="open",
                request_id=request_id,
                metadata_json=metadata or {},
            )
            db.add(alert)
            db.flush()
            self._queue_tenant_email_deliveries(db, alert=alert)
            db.flush()
            self.process_pending_deliveries(db, alert_id=alert.id, limit=10)
            return alert
        except SQLAlchemyError:
            db.rollback()
            return None

    def create_owner_alert(
        self,
        db: Session,
        *,
        owner: dbm.OwnerUser,
        event_type: str,
        title: str,
        body: str,
        severity: str = "medium",
        request_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> dbm.SecurityAlert | None:
        try:
            alert = dbm.SecurityAlert(
                scope="owner",
                owner_user_id=owner.id,
                owner_email=owner.email,
                event_type=event_type,
                title=title,
                body=body,
                severity=severity,
                status="open",
                request_id=request_id,
                metadata_json=metadata or {},
            )
            db.add(alert)
            db.flush()
            self._queue_owner_email_deliveries(db, alert=alert, owner=owner)
            db.flush()
            self.process_pending_deliveries(db, alert_id=alert.id, limit=10)
            return alert
        except SQLAlchemyError:
            db.rollback()
            return None

    def list_tenant(self, db: Session, *, tenant_id: UUID | str, limit: int = 50) -> list[dict[str, object]]:
        rows = db.scalars(
            select(dbm.SecurityAlert)
            .where(dbm.SecurityAlert.scope == "tenant", dbm.SecurityAlert.tenant_id == str(tenant_id))
            .order_by(dbm.SecurityAlert.created_at.desc())
            .limit(limit)
        ).all()
        return [self.serialize(row) for row in rows]

    def list_owner(self, db: Session, *, limit: int = 50) -> list[dict[str, object]]:
        rows = db.scalars(
            select(dbm.SecurityAlert)
            .where(dbm.SecurityAlert.scope == "owner")
            .order_by(dbm.SecurityAlert.created_at.desc())
            .limit(limit)
        ).all()
        return [self.serialize(row) for row in rows]

    def acknowledge_tenant(self, db: Session, *, tenant_id: UUID | str, alert_id: UUID | str, actor: User) -> dict[str, object]:
        alert = db.scalar(select(dbm.SecurityAlert).where(dbm.SecurityAlert.scope == "tenant", dbm.SecurityAlert.tenant_id == str(tenant_id), dbm.SecurityAlert.id == str(alert_id)))
        if not alert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Security alert not found")
        alert.status = "acknowledged"
        alert.acknowledged_by_user_id = str(actor.id)
        alert.acknowledged_at = dbm.now_utc()
        db.commit()
        db.refresh(alert)
        return self.serialize(alert)

    def acknowledge_owner(self, db: Session, *, alert_id: UUID | str, owner: dbm.OwnerUser) -> dict[str, object]:
        alert = db.scalar(select(dbm.SecurityAlert).where(dbm.SecurityAlert.scope == "owner", dbm.SecurityAlert.id == str(alert_id)))
        if not alert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Security alert not found")
        alert.status = "acknowledged"
        alert.acknowledged_by_owner_user_id = owner.id
        alert.acknowledged_at = dbm.now_utc()
        db.commit()
        db.refresh(alert)
        return self.serialize(alert)

    def process_pending_deliveries(self, db: Session, *, alert_id: UUID | str | None = None, scope: str | None = None, tenant_id: UUID | str | None = None, limit: int = 25) -> dict[str, object]:
        now = dbm.now_utc()
        query = select(dbm.SecurityAlertDelivery).where(
            dbm.SecurityAlertDelivery.status.in_(["pending", "retry_pending"]),
            (dbm.SecurityAlertDelivery.next_attempt_at.is_(None)) | (dbm.SecurityAlertDelivery.next_attempt_at <= now),
        )
        if alert_id:
            query = query.where(dbm.SecurityAlertDelivery.alert_id == str(alert_id))
        if scope:
            query = query.where(dbm.SecurityAlertDelivery.scope == scope)
        if tenant_id:
            query = query.where(dbm.SecurityAlertDelivery.tenant_id == str(tenant_id))
        rows = db.scalars(query.order_by(dbm.SecurityAlertDelivery.created_at.asc()).limit(limit)).all()
        processed = 0
        for delivery in rows:
            alert = db.get(dbm.SecurityAlert, delivery.alert_id)
            if not alert:
                delivery.status = "failed"
                delivery.last_error = "alert_not_found"
                continue
            self._attempt_delivery(delivery, alert)
            processed += 1
        return {"processed": processed}

    def list_deliveries(self, db: Session, *, scope: str, tenant_id: UUID | str | None = None, limit: int = 50) -> list[dict[str, object]]:
        query = select(dbm.SecurityAlertDelivery).where(dbm.SecurityAlertDelivery.scope == scope)
        if tenant_id:
            query = query.where(dbm.SecurityAlertDelivery.tenant_id == str(tenant_id))
        rows = db.scalars(query.order_by(dbm.SecurityAlertDelivery.created_at.desc()).limit(limit)).all()
        return [self.serialize_delivery(row) for row in rows]

    @staticmethod
    def serialize(alert: dbm.SecurityAlert) -> dict[str, object]:
        return {
            "id": alert.id,
            "scope": alert.scope,
            "tenant_id": alert.tenant_id,
            "owner_email": alert.owner_email,
            "severity": alert.severity,
            "event_type": alert.event_type,
            "title": alert.title,
            "body": alert.body,
            "status": alert.status,
            "request_id": alert.request_id,
            "metadata": alert.metadata_json,
            "created_at": alert.created_at.isoformat(),
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        }

    @staticmethod
    def serialize_delivery(delivery: dbm.SecurityAlertDelivery) -> dict[str, object]:
        return {
            "id": delivery.id,
            "alert_id": delivery.alert_id,
            "scope": delivery.scope,
            "channel": delivery.channel,
            "template": delivery.template,
            "recipient_hint": delivery.recipient_hint,
            "provider": delivery.provider,
            "status": delivery.status,
            "attempts": delivery.attempts,
            "max_attempts": delivery.max_attempts,
            "last_attempt_at": delivery.last_attempt_at.isoformat() if delivery.last_attempt_at else None,
            "next_attempt_at": delivery.next_attempt_at.isoformat() if delivery.next_attempt_at else None,
            "created_at": delivery.created_at.isoformat(),
        }

    def _queue_tenant_email_deliveries(self, db: Session, *, alert: dbm.SecurityAlert) -> None:
        if alert.severity not in ALERT_EMAIL_SEVERITIES or not alert.tenant_id:
            return
        rows = db.scalars(
            select(dbm.User)
            .join(dbm.Role)
            .where(
                dbm.User.tenant_id == alert.tenant_id,
                dbm.User.status == "active",
                dbm.User.deleted_at.is_(None),
                dbm.Role.name.in_(["tenant_admin", "partner"]),
            )
        ).all()
        emails = sorted({row.email for row in rows})
        for email in emails:
            db.add(self._delivery(alert=alert, to_email=email, tenant_id=alert.tenant_id))

    def _queue_owner_email_deliveries(self, db: Session, *, alert: dbm.SecurityAlert, owner: dbm.OwnerUser) -> None:
        if alert.severity not in ALERT_EMAIL_SEVERITIES:
            return
        db.add(self._delivery(alert=alert, to_email=owner.email, owner_user_id=owner.id))

    def _delivery(self, *, alert: dbm.SecurityAlert, to_email: str, tenant_id: str | None = None, owner_user_id: str | None = None) -> dbm.SecurityAlertDelivery:
        return dbm.SecurityAlertDelivery(
            alert_id=alert.id,
            scope=alert.scope,
            tenant_id=tenant_id,
            owner_user_id=owner_user_id,
            channel="email",
            template="security_alert",
            recipient_email_encrypted=CredentialCipher().encrypt(to_email.lower()),
            recipient_hash=self._hash_email(to_email),
            recipient_hint=self._hint_email(to_email),
            status="pending",
            max_attempts=3,
        )

    def _attempt_delivery(self, delivery: dbm.SecurityAlertDelivery, alert: dbm.SecurityAlert) -> None:
        delivery.attempts += 1
        delivery.last_attempt_at = dbm.now_utc()
        to_email = CredentialCipher().decrypt(delivery.recipient_email_encrypted)
        result = get_email_provider().send_security_alert(
            to_email=to_email,
            title=alert.title,
            body=alert.body,
            severity=alert.severity,
            event_type=alert.event_type,
        )
        delivery.provider = result.provider
        if result.status in {"sent", "prepared"}:
            delivery.status = result.status
            delivery.next_attempt_at = None
            delivery.last_error = None
            return
        delivery.last_error = result.status
        if delivery.attempts < delivery.max_attempts:
            delivery.status = "retry_pending"
            delivery.next_attempt_at = dbm.now_utc() + timedelta(minutes=delivery.attempts * 5)
        else:
            delivery.status = "failed"
            delivery.next_attempt_at = None

    @staticmethod
    def _hash_email(email: str) -> str:
        return sha256(email.lower().encode("utf-8")).hexdigest()

    @staticmethod
    def _hint_email(email: str) -> str:
        local, _, domain = email.lower().partition("@")
        if not domain:
            return "***"
        visible = local[:2] if len(local) >= 2 else local[:1]
        return f"{visible}***@{domain}"


security_alert_service = SecurityAlertService()
