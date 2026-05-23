from sqlalchemy.orm import Session

from app.db.models import AuditLog, CaseSource, JudicialUpdate, Notification, now_utc


def record_judicial_update(
    db: Session,
    *,
    tenant_id: str,
    case_id: str,
    case_source_id: str,
    title: str,
    summary: str,
    actor_user_id: str | None = None,
    captcha_required: bool = False,
) -> JudicialUpdate:
    case_source = db.get(CaseSource, case_source_id)
    if not case_source or case_source.tenant_id != tenant_id or case_source.case_id != case_id:
        raise ValueError("Case source not found for tenant/case")

    if captcha_required:
        case_source.captcha_required = True
        case_source.status = "paused_captcha"
        case_source.last_checked_at = now_utc()
        update = JudicialUpdate(
            tenant_id=tenant_id,
            case_id=case_id,
            case_source_id=case_source_id,
            update_type="captcha_required",
            title=title,
            summary=summary,
            status="paused",
            captcha_required=True,
            requires_human_intervention=True,
            raw_payload={"reason": "captcha_required", "policy": "no_captcha_evasion"},
        )
        notification = Notification(
            tenant_id=tenant_id,
            user_id=actor_user_id,
            case_id=case_id,
            title="Intervencion humana requerida",
            body="La fuente judicial requiere CAPTCHA. LEXFLOW pauso la actualizacion y no intentara evadirlo.",
            channel="in_app",
            status="pending",
        )
        audit = AuditLog(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="captcha_required",
            entity_type="case_source",
            entity_id=case_source_id,
            metadata_json={"case_id": case_id, "policy": "paused_notified_human_intervention"},
        )
        db.add_all([update, notification, audit])
        db.flush()
        return update

    case_source.last_checked_at = now_utc()
    update = JudicialUpdate(
        tenant_id=tenant_id,
        case_id=case_id,
        case_source_id=case_source_id,
        update_type="judicial_update",
        title=title,
        summary=summary,
        status="recorded",
        captcha_required=False,
        requires_human_intervention=False,
        raw_payload={},
    )
    db.add(update)
    db.flush()
    audit = AuditLog(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        action="create",
        entity_type="judicial_update",
        entity_id=update.id,
        metadata_json={"case_id": case_id},
    )
    db.add(audit)
    db.flush()
    return update
