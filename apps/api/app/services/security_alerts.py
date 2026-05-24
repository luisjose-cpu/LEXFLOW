from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import models as dbm
from app.domain.models import User


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


security_alert_service = SecurityAlertService()
