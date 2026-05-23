from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as dbm
from app.services.case_overview import audit_case_action, get_case_or_404
from app.services.judicial_adapters import get_adapter


class JudicialSourceService:
    def create_source(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        case_id: UUID | str,
        source_type: str,
        external_case_number: str,
        court_name: str | None,
        source_url: str | None,
        actor_user_id: UUID | str,
        request_id: str | None = None,
    ) -> dbm.CaseSource:
        get_case_or_404(db, tenant_id=tenant_id, case_id=case_id)
        source = dbm.CaseSource(
            tenant_id=str(tenant_id),
            case_id=str(case_id),
            source_type=source_type,
            external_case_number=external_case_number,
            court_name=court_name,
            source_url=source_url,
        )
        db.add(source)
        db.flush()
        audit_case_action(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="create",
            entity_type="case_source",
            entity_id=source.id,
            request_id=request_id,
            metadata={"case_id": str(case_id), "source_type": source_type},
        )
        db.commit()
        return source

    def list_sources(self, db: Session, *, tenant_id: UUID | str, case_id: UUID | str) -> list[dbm.CaseSource]:
        get_case_or_404(db, tenant_id=tenant_id, case_id=case_id)
        return db.scalars(
            select(dbm.CaseSource).where(
                dbm.CaseSource.tenant_id == str(tenant_id),
                dbm.CaseSource.case_id == str(case_id),
                dbm.CaseSource.deleted_at.is_(None),
            )
        ).all()

    def get_source_or_404(self, db: Session, *, tenant_id: UUID | str, source_id: UUID | str) -> dbm.CaseSource:
        source = db.scalar(
            select(dbm.CaseSource).where(
                dbm.CaseSource.tenant_id == str(tenant_id),
                dbm.CaseSource.id == str(source_id),
                dbm.CaseSource.deleted_at.is_(None),
            )
        )
        if not source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case source not found")
        return source


class JudicialEvidenceService:
    def record_evidence(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        case_id: UUID | str,
        case_source_id: UUID | str,
        payload: dict[str, object],
        judicial_update_id: str | None = None,
    ) -> dbm.JudicialEvidence:
        evidence = dbm.JudicialEvidence(
            tenant_id=str(tenant_id),
            case_id=str(case_id),
            case_source_id=str(case_source_id),
            judicial_update_id=judicial_update_id,
            evidence_type="adapter_payload",
            metadata_json=payload,
        )
        db.add(evidence)
        return evidence


class JudicialNotificationService:
    def notify_captcha(self, db: Session, *, tenant_id: UUID | str, case_id: UUID | str, actor_user_id: UUID | str | None) -> dbm.Notification:
        notification = dbm.Notification(
            tenant_id=str(tenant_id),
            user_id=str(actor_user_id) if actor_user_id else None,
            case_id=str(case_id),
            title="CAPTCHA requiere intervencion humana",
            body="La consulta judicial fue pausada. No se evadira CAPTCHA ni controles anti-bot.",
            channel="in_app",
            status="pending",
        )
        db.add(notification)
        return notification


class CaptchaCheckpointService:
    def create_checkpoint(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        case_id: UUID | str,
        case_source_id: UUID | str,
        actor_user_id: UUID | str | None,
        request_id: str | None = None,
    ) -> dbm.CaptchaCheckpoint:
        checkpoint = dbm.CaptchaCheckpoint(
            tenant_id=str(tenant_id),
            case_id=str(case_id),
            case_source_id=str(case_source_id),
            status="pending",
            reason="captcha_required",
        )
        db.add(checkpoint)
        db.flush()
        audit_case_action(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="captcha_checkpoint_created",
            entity_type="captcha_checkpoint",
            entity_id=checkpoint.id,
            request_id=request_id,
            metadata={"case_id": str(case_id), "case_source_id": str(case_source_id)},
        )
        return checkpoint

    def resolve_checkpoint(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        checkpoint_id: UUID | str,
        actor_user_id: UUID | str,
        resolution_note: str,
        request_id: str | None = None,
    ) -> dbm.CaptchaCheckpoint:
        checkpoint = db.scalar(
            select(dbm.CaptchaCheckpoint).where(
                dbm.CaptchaCheckpoint.tenant_id == str(tenant_id),
                dbm.CaptchaCheckpoint.id == str(checkpoint_id),
            )
        )
        if not checkpoint:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Captcha checkpoint not found")
        checkpoint.status = "resolved"
        checkpoint.resolution_note = resolution_note
        checkpoint.resolved_by_user_id = str(actor_user_id)
        checkpoint.resolved_at = dbm.now_utc()
        source = db.get(dbm.CaseSource, checkpoint.case_source_id)
        if source and source.tenant_id == str(tenant_id):
            source.status = "active"
            source.captcha_required = False
        audit_case_action(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="captcha_checkpoint_resolved",
            entity_type="captcha_checkpoint",
            entity_id=checkpoint.id,
            request_id=request_id,
            metadata={"case_id": checkpoint.case_id},
        )
        db.commit()
        return checkpoint


class JudicialUpdateService:
    def __init__(
        self,
        *,
        source_service: JudicialSourceService,
        evidence_service: JudicialEvidenceService,
        checkpoint_service: CaptchaCheckpointService,
        notification_service: JudicialNotificationService,
    ) -> None:
        self.source_service = source_service
        self.evidence_service = evidence_service
        self.checkpoint_service = checkpoint_service
        self.notification_service = notification_service

    def check_source(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        source_id: UUID | str,
        actor_user_id: UUID | str,
        request_id: str | None = None,
    ) -> dict[str, object]:
        source = self.source_service.get_source_or_404(db, tenant_id=tenant_id, source_id=source_id)
        adapter = get_adapter(source.source_type)
        result = adapter.check(external_case_number=source.external_case_number)
        source.last_checked_at = dbm.now_utc()

        if result.captcha_required:
            source.status = "paused_captcha"
            source.captcha_required = True
            update = dbm.JudicialUpdate(
                tenant_id=source.tenant_id,
                case_id=source.case_id,
                case_source_id=source.id,
                update_type="captcha_required",
                title=result.title,
                summary="Consulta pausada por CAPTCHA. Requiere intervencion humana.",
                status="paused",
                captcha_required=True,
                requires_human_intervention=True,
                raw_payload={"policy": "no_captcha_evasion"},
            )
            db.add(update)
            db.flush()
            evidence = self.evidence_service.record_evidence(
                db,
                tenant_id=source.tenant_id,
                case_id=source.case_id,
                case_source_id=source.id,
                judicial_update_id=update.id,
                payload=result.evidence_payload,
            )
            checkpoint = self.checkpoint_service.create_checkpoint(
                db,
                tenant_id=source.tenant_id,
                case_id=source.case_id,
                case_source_id=source.id,
                actor_user_id=actor_user_id,
                request_id=request_id,
            )
            self.notification_service.notify_captcha(db, tenant_id=source.tenant_id, case_id=source.case_id, actor_user_id=actor_user_id)
            audit_case_action(
                db,
                tenant_id=source.tenant_id,
                actor_user_id=actor_user_id,
                action="captcha_required",
                entity_type="case_source",
                entity_id=source.id,
                request_id=request_id,
                metadata={"case_id": source.case_id, "checkpoint_id": checkpoint.id, "policy": "human_in_the_loop"},
            )
            db.commit()
            return {"status": "captcha_required", "update_id": update.id, "checkpoint_id": checkpoint.id, "evidence_id": evidence.id}

        update = dbm.JudicialUpdate(
            tenant_id=source.tenant_id,
            case_id=source.case_id,
            case_source_id=source.id,
            update_type="judicial_update",
            title=result.title,
            summary=result.summary,
            status="pending_approval",
            captcha_required=False,
            requires_human_intervention=False,
            raw_payload=result.evidence_payload,
        )
        db.add(update)
        db.flush()
        evidence = self.evidence_service.record_evidence(
            db,
            tenant_id=source.tenant_id,
            case_id=source.case_id,
            case_source_id=source.id,
            judicial_update_id=update.id,
            payload=result.evidence_payload,
        )
        audit_case_action(
            db,
            tenant_id=source.tenant_id,
            actor_user_id=actor_user_id,
            action="check",
            entity_type="case_source",
            entity_id=source.id,
            request_id=request_id,
            metadata={"case_id": source.case_id, "update_id": update.id},
        )
        db.commit()
        return {"status": "pending_approval", "update_id": update.id, "evidence_id": evidence.id}

    def list_updates(self, db: Session, *, tenant_id: UUID | str, source_id: UUID | str) -> list[dbm.JudicialUpdate]:
        source = self.source_service.get_source_or_404(db, tenant_id=tenant_id, source_id=source_id)
        return db.scalars(
            select(dbm.JudicialUpdate).where(
                dbm.JudicialUpdate.tenant_id == str(tenant_id),
                dbm.JudicialUpdate.case_source_id == source.id,
            )
        ).all()

    def decide_update(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        update_id: UUID | str,
        actor_user_id: UUID | str,
        decision: str,
        note: str | None = None,
        request_id: str | None = None,
    ) -> dbm.JudicialUpdate:
        update = db.scalar(
            select(dbm.JudicialUpdate).where(
                dbm.JudicialUpdate.tenant_id == str(tenant_id),
                dbm.JudicialUpdate.id == str(update_id),
            )
        )
        if not update:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Judicial update not found")
        if update.captcha_required:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CAPTCHA update requires checkpoint resolution")
        update.status = "approved" if decision == "approve" else "rejected"
        update.raw_payload = {**(update.raw_payload or {}), "decision_note": note}
        audit_case_action(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action=f"judicial_update_{decision}",
            entity_type="judicial_update",
            entity_id=update.id,
            request_id=request_id,
            metadata={"case_id": update.case_id},
        )
        db.commit()
        return update


judicial_source_service = JudicialSourceService()
judicial_evidence_service = JudicialEvidenceService()
captcha_checkpoint_service = CaptchaCheckpointService()
judicial_notification_service = JudicialNotificationService()
judicial_update_service = JudicialUpdateService(
    source_service=judicial_source_service,
    evidence_service=judicial_evidence_service,
    checkpoint_service=captcha_checkpoint_service,
    notification_service=judicial_notification_service,
)
