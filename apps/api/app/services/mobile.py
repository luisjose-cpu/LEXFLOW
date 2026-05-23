from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as dbm
from app.domain.models import RoleName, User
from app.services.ai_practical import AI_REVIEW_DISCLAIMER
from app.services.case_overview import build_case_overview, get_case_or_404
from app.services.client_portal import client_portal_service
from app.services.command_center import dashboard_service


class MobileClientService:
    def home(self, db: Session, *, actor: User) -> dict[str, object]:
        report = client_portal_service.reports(db, actor=actor)
        notifications = client_portal_service.notifications(db, actor=actor)
        return {
            "profile": client_portal_service.me(db, actor=actor),
            "metrics": report["metrics"],
            "cases": report["cases"],
            "notifications": notifications[:5],
            "next_steps": ["Revisar proxima audiencia", "Responder solicitud documental"],
        }

    def cases(self, db: Session, *, actor: User) -> list[dict[str, object]]:
        return client_portal_service.cases(db, actor=actor)

    def case_detail(self, db: Session, *, actor: User, case_id: UUID | str) -> dict[str, object]:
        return client_portal_service.case_detail(db, actor=actor, case_id=case_id)

    def documents(self, db: Session, *, actor: User) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        for legal_case in client_portal_service.cases(db, actor=actor):
            items.extend(client_portal_service.documents(db, actor=actor, case_id=str(legal_case["id"])))
        return items

    def messages(self, db: Session, *, actor: User) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        for legal_case in client_portal_service.cases(db, actor=actor):
            items.extend(client_portal_service.messages(db, actor=actor, case_id=str(legal_case["id"])))
        return items

    def notifications(self, db: Session, *, actor: User) -> list[dict[str, object]]:
        return client_portal_service.notifications(db, actor=actor)


class MobileLawyerService:
    def require_lawyer_mobile(self, actor: User) -> None:
        if actor.role not in {RoleName.tenant_admin, RoleName.partner, RoleName.lawyer, RoleName.assistant}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Lawyer mobile workspace requires an internal user")

    def home(self, db: Session, *, actor: User) -> dict[str, object]:
        self.require_lawyer_mobile(actor)
        return {
            "profile": {"id": str(actor.id), "email": actor.email, "full_name": actor.full_name, "role": actor.role.value},
            "dashboard": dashboard_service.overview(db, tenant_id=actor.tenant_id),
            "alerts": self.notifications(db, actor=actor)[:5],
            "assigned_cases": self.cases(db, actor=actor)[:5],
        }

    def cases(self, db: Session, *, actor: User) -> list[dict[str, object]]:
        self.require_lawyer_mobile(actor)
        rows = db.scalars(
            select(dbm.Case)
            .where(dbm.Case.tenant_id == str(actor.tenant_id), dbm.Case.deleted_at.is_(None))
            .order_by(dbm.Case.updated_at.desc())
        ).all()
        return [
            {
                "id": row.id,
                "title": row.title,
                "status": row.status,
                "external_case_number": row.external_case_number,
                "updated_at": row.updated_at.isoformat(),
            }
            for row in rows
        ]

    def case_detail(self, db: Session, *, actor: User, case_id: UUID | str) -> dict[str, object]:
        self.require_lawyer_mobile(actor)
        overview = build_case_overview(db, tenant_id=actor.tenant_id, case_id=case_id)
        latest_ai = db.scalars(
            select(dbm.AiJob)
            .where(dbm.AiJob.tenant_id == str(actor.tenant_id), dbm.AiJob.case_id == str(case_id))
            .order_by(dbm.AiJob.created_at.desc())
        ).first()
        overview["ai_summary"] = {
            "status": latest_ai.status if latest_ai else "not_requested",
            "summary": latest_ai.result_json.get("summary") if latest_ai and latest_ai.result_json else None,
            "disclaimer": AI_REVIEW_DISCLAIMER,
        }
        return overview

    def tasks(self, db: Session, *, actor: User) -> list[dict[str, object]]:
        self.require_lawyer_mobile(actor)
        rows = db.scalars(
            select(dbm.Task)
            .where(dbm.Task.tenant_id == str(actor.tenant_id), dbm.Task.deleted_at.is_(None), dbm.Task.status != "done")
            .order_by(dbm.Task.due_at.asc().nullslast(), dbm.Task.created_at.desc())
        ).all()
        return [
            {"id": row.id, "case_id": row.case_id, "title": row.title, "status": row.status, "due_at": row.due_at.isoformat() if row.due_at else None}
            for row in rows
        ]

    def hearings(self, db: Session, *, actor: User) -> list[dict[str, object]]:
        self.require_lawyer_mobile(actor)
        rows = db.scalars(
            select(dbm.Hearing)
            .where(dbm.Hearing.tenant_id == str(actor.tenant_id), dbm.Hearing.deleted_at.is_(None))
            .order_by(dbm.Hearing.starts_at.asc())
        ).all()
        return [
            {"id": row.id, "case_id": row.case_id, "title": row.title, "starts_at": row.starts_at.isoformat(), "location": row.location, "status": row.status}
            for row in rows
        ]

    def notifications(self, db: Session, *, actor: User) -> list[dict[str, object]]:
        self.require_lawyer_mobile(actor)
        rows = db.scalars(
            select(dbm.Notification)
            .where(dbm.Notification.tenant_id == str(actor.tenant_id))
            .order_by(dbm.Notification.created_at.desc())
        ).all()
        return [
            {"id": row.id, "case_id": row.case_id, "title": row.title, "body": row.body, "status": row.status, "created_at": row.created_at.isoformat()}
            for row in rows
        ]

    def judicial_updates(self, db: Session, *, actor: User) -> list[dict[str, object]]:
        self.require_lawyer_mobile(actor)
        rows = db.scalars(
            select(dbm.JudicialUpdate)
            .where(dbm.JudicialUpdate.tenant_id == str(actor.tenant_id))
            .order_by(dbm.JudicialUpdate.checked_at.desc())
        ).all()
        return [
            {
                "id": row.id,
                "case_id": row.case_id,
                "title": row.title,
                "status": row.status,
                "captcha_required": row.captcha_required,
                "requires_human_intervention": row.requires_human_intervention,
            }
            for row in rows
        ]


mobile_client_service = MobileClientService()
mobile_lawyer_service = MobileLawyerService()
