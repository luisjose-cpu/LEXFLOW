from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as dbm


def get_case_or_404(db: Session, *, tenant_id: UUID | str, case_id: UUID | str) -> dbm.Case:
    legal_case = db.scalar(
        select(dbm.Case).where(
            dbm.Case.id == str(case_id),
            dbm.Case.tenant_id == str(tenant_id),
            dbm.Case.deleted_at.is_(None),
        )
    )
    if not legal_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return legal_case


def audit_case_action(
    db: Session,
    *,
    tenant_id: UUID | str,
    actor_user_id: UUID | str | None,
    action: str,
    entity_type: str,
    entity_id: UUID | str,
    request_id: str | None = None,
    metadata: dict[str, object] | None = None,
) -> dbm.AuditLog:
    audit = dbm.AuditLog(
        tenant_id=str(tenant_id),
        actor_user_id=str(actor_user_id) if actor_user_id else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        request_id=request_id,
        metadata_json=metadata or {},
    )
    db.add(audit)
    return audit


def build_case_overview(db: Session, *, tenant_id: UUID | str, case_id: UUID | str) -> dict[str, object]:
    legal_case = get_case_or_404(db, tenant_id=tenant_id, case_id=case_id)
    client = db.get(dbm.Client, legal_case.client_id)
    if not client or client.tenant_id != str(tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    events = db.scalars(select(dbm.CaseEvent).where(dbm.CaseEvent.tenant_id == str(tenant_id), dbm.CaseEvent.case_id == legal_case.id).order_by(dbm.CaseEvent.occurred_at.desc())).all()
    documents = db.scalars(select(dbm.Document).where(dbm.Document.tenant_id == str(tenant_id), dbm.Document.case_id == legal_case.id, dbm.Document.deleted_at.is_(None)).order_by(dbm.Document.created_at.desc())).all()
    hearings = db.scalars(select(dbm.Hearing).where(dbm.Hearing.tenant_id == str(tenant_id), dbm.Hearing.case_id == legal_case.id, dbm.Hearing.deleted_at.is_(None)).order_by(dbm.Hearing.starts_at.asc())).all()
    tasks = db.scalars(select(dbm.Task).where(dbm.Task.tenant_id == str(tenant_id), dbm.Task.case_id == legal_case.id, dbm.Task.deleted_at.is_(None)).order_by(dbm.Task.created_at.desc())).all()
    updates = db.scalars(select(dbm.JudicialUpdate).where(dbm.JudicialUpdate.tenant_id == str(tenant_id), dbm.JudicialUpdate.case_id == legal_case.id).order_by(dbm.JudicialUpdate.checked_at.desc())).all()
    messages = db.scalars(select(dbm.WhatsAppMessage).where(dbm.WhatsAppMessage.tenant_id == str(tenant_id), dbm.WhatsAppMessage.case_id == legal_case.id).order_by(dbm.WhatsAppMessage.created_at.desc())).all()
    communication_messages = db.scalars(select(dbm.CommunicationMessage).where(dbm.CommunicationMessage.tenant_id == str(tenant_id), dbm.CommunicationMessage.case_id == legal_case.id).order_by(dbm.CommunicationMessage.created_at.desc())).all()
    alerts = db.scalars(select(dbm.Notification).where(dbm.Notification.tenant_id == str(tenant_id), dbm.Notification.case_id == legal_case.id).order_by(dbm.Notification.created_at.desc())).all()
    audits = db.scalars(select(dbm.AuditLog).where(dbm.AuditLog.tenant_id == str(tenant_id), dbm.AuditLog.metadata_json["case_id"].as_string() == legal_case.id).order_by(dbm.AuditLog.created_at.desc())).all()
    intelligence_links = db.scalars(select(dbm.LegalNewsCaseLink).where(dbm.LegalNewsCaseLink.tenant_id == str(tenant_id), dbm.LegalNewsCaseLink.case_id == legal_case.id)).all()
    linked_news_ids = [item.news_id for item in intelligence_links]
    related_intelligence = (
        db.scalars(select(dbm.LegalNews).where(dbm.LegalNews.tenant_id == str(tenant_id), dbm.LegalNews.id.in_(linked_news_ids)).order_by(dbm.LegalNews.created_at.desc())).all()
        if linked_news_ids
        else []
    )

    open_tasks = [task for task in tasks if task.status != "done"]
    risk_level = "high" if legal_case.status == "risk" or any(update.requires_human_intervention for update in updates) else client.risk_profile
    next_action = open_tasks[0].title if open_tasks else "Revisar proxima actuacion"

    return {
        "case": {
            "id": legal_case.id,
            "title": legal_case.title,
            "status": legal_case.status,
            "priority": "high" if risk_level == "high" else "normal",
            "risk": risk_level,
            "responsible": "Equipo legal asignado",
            "next_action": next_action,
            "external_case_number": legal_case.external_case_number,
            "description": legal_case.description,
        },
        "client": {
            "id": client.id,
            "name": client.name,
            "contact_email": client.contact_email,
            "risk_profile": client.risk_profile,
            "tags": client.tags,
        },
        "timeline": [{"id": item.id, "type": item.event_type, "title": item.title, "description": item.description, "occurred_at": item.occurred_at.isoformat()} for item in events],
        "documents": [
            {
                "id": item.id,
                "filename": item.filename,
                "classification": item.classification,
                "status": item.status,
                "file_size_bytes": item.file_size_bytes,
                "checksum_sha256": item.checksum_sha256,
                "storage_verified_at": item.storage_verified_at.isoformat() if item.storage_verified_at else None,
                "malware_scan_status": item.malware_scan_status,
                "created_at": item.created_at.isoformat(),
            }
            for item in documents
        ],
        "hearings": [{"id": item.id, "title": item.title, "starts_at": item.starts_at.isoformat(), "location": item.location, "status": item.status} for item in hearings],
        "tasks": [{"id": item.id, "title": item.title, "status": item.status, "due_at": item.due_at.isoformat() if item.due_at else None} for item in tasks],
        "judicial_updates": [{"id": item.id, "title": item.title, "summary": item.summary, "status": item.status, "captcha_required": item.captcha_required, "requires_human_intervention": item.requires_human_intervention, "checked_at": item.checked_at.isoformat()} for item in updates],
        "communications": [
            {"id": item.id, "direction": item.direction, "channel": "whatsapp", "body": item.body, "status": item.status, "created_at": item.created_at.isoformat()}
            for item in messages
        ]
        + [
            {"id": item.id, "direction": item.direction, "channel": item.channel, "body": item.body, "status": item.status, "created_at": item.created_at.isoformat()}
            for item in communication_messages
        ],
        "alerts": [{"id": item.id, "title": item.title, "body": item.body, "status": item.status, "created_at": item.created_at.isoformat()} for item in alerts],
        "related_intelligence": [
            {
                "id": item.id,
                "title": item.title,
                "category": item.category,
                "summary": item.summary,
                "ai_summary": item.ai_summary,
                "tags": item.tags,
                "published_at": item.published_at.isoformat() if item.published_at else None,
            }
            for item in related_intelligence
        ],
        "audit_summary": {
            "total": len(audits),
            "latest": [{"id": item.id, "action": item.action, "entity_type": item.entity_type, "created_at": item.created_at.isoformat()} for item in audits[:5]],
        },
        "next_actions": [{"id": item.id, "title": item.title, "status": item.status} for item in open_tasks[:5]],
    }


def now() -> datetime:
    return datetime.now(UTC)
