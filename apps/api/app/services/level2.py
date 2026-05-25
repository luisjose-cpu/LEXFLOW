from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models as dbm
from app.domain.models import User


def _now() -> datetime:
    return datetime.now(UTC)


def _audit(db: Session, *, tenant_id: UUID | str, actor: User, action: str, entity_type: str, entity_id: str, request_id: str | None = None, metadata: dict[str, object] | None = None) -> None:
    db.add(
        dbm.AuditLog(
            tenant_id=str(tenant_id),
            actor_user_id=str(actor.id),
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            request_id=request_id,
            metadata_json=metadata or {},
        )
    )


def _money(cents: int) -> dict[str, object]:
    return {"cents": cents, "amount": round(cents / 100, 2)}


class RiskEngineService:
    def case_score(self, db: Session, *, tenant_id: UUID | str, case_id: UUID | str) -> dict[str, object]:
        tenant = str(tenant_id)
        legal_case = db.scalars(select(dbm.Case).where(dbm.Case.id == str(case_id), dbm.Case.tenant_id == tenant, dbm.Case.deleted_at.is_(None))).first()
        if not legal_case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        return self._score_case(db, legal_case)

    def client_score(self, db: Session, *, tenant_id: UUID | str, client_id: UUID | str) -> dict[str, object]:
        tenant = str(tenant_id)
        client = db.scalars(select(dbm.Client).where(dbm.Client.id == str(client_id), dbm.Client.tenant_id == tenant, dbm.Client.deleted_at.is_(None))).first()
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        cases = db.scalars(select(dbm.Case).where(dbm.Case.tenant_id == tenant, dbm.Case.client_id == client.id, dbm.Case.deleted_at.is_(None))).all()
        scores = [self._score_case(db, item) for item in cases]
        score = round(sum(item["score"] for item in scores) / len(scores)) if scores else 20
        return {"client_id": client.id, "client_name": client.name, "score": score, "level": self._level(score), "cases": scores}

    def dashboard(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        cases = db.scalars(select(dbm.Case).where(dbm.Case.tenant_id == str(tenant_id), dbm.Case.deleted_at.is_(None))).all()
        case_scores = [self._score_case(db, item) for item in cases]
        client_ids = {item.client_id for item in cases}
        client_scores = [self.client_score(db, tenant_id=tenant_id, client_id=client_id) for client_id in client_ids]
        study_score = round(sum(item["score"] for item in case_scores) / len(case_scores)) if case_scores else 20
        heatmap = Counter(item["level"] for item in case_scores)
        return {
            "study_score": study_score,
            "level": self._level(study_score),
            "heatmap": [{"level": key, "count": value} for key, value in heatmap.items()],
            "critical_cases": [item for item in case_scores if item["score"] >= 71],
            "cases": case_scores,
            "clients": client_scores,
            "explanation": "El score combina plazos, documentos, audiencias, CAPTCHA, IA pendiente, carga operativa e inactividad. Requiere revision profesional.",
        }

    def _score_case(self, db: Session, legal_case: dbm.Case) -> dict[str, object]:
        now = _now()
        factors: list[dict[str, object]] = []
        score = 10
        if legal_case.status == "risk":
            score += 25
            factors.append({"key": "status", "label": "Expediente marcado en riesgo", "points": 25})
        overdue_tasks = db.scalars(select(dbm.Task).where(dbm.Task.case_id == legal_case.id, dbm.Task.deleted_at.is_(None), dbm.Task.status != "done", dbm.Task.due_at < now)).all()
        if overdue_tasks:
            points = min(25, len(overdue_tasks) * 10)
            score += points
            factors.append({"key": "tasks", "label": "Pendientes vencidos", "points": points})
        pending_captcha = db.scalars(select(dbm.CaptchaCheckpoint).where(dbm.CaptchaCheckpoint.case_id == legal_case.id, dbm.CaptchaCheckpoint.status == "pending")).all()
        if pending_captcha:
            points = min(25, len(pending_captcha) * 15)
            score += points
            factors.append({"key": "captcha", "label": "CAPTCHA requiere verificacion humana", "points": points})
        missing_documents = db.scalars(select(dbm.Document).where(dbm.Document.case_id == legal_case.id, dbm.Document.deleted_at.is_(None), dbm.Document.status.in_(["observed", "pending"]))).all()
        if missing_documents:
            points = min(15, len(missing_documents) * 5)
            score += points
            factors.append({"key": "documents", "label": "Documentos observados o pendientes", "points": points})
        ai_pending = db.scalars(select(dbm.AiJob).where(dbm.AiJob.case_id == legal_case.id, dbm.AiJob.status.in_(["pending_review", "queued", "running"]))).all()
        if ai_pending:
            points = min(15, len(ai_pending) * 5)
            score += points
            factors.append({"key": "ai", "label": "IA pendiente de revision", "points": points})
        failed_runs = db.scalars(select(dbm.AutomationRun).where(dbm.AutomationRun.tenant_id == legal_case.tenant_id, dbm.AutomationRun.status == "failed")).all()
        if failed_runs:
            score += 10
            factors.append({"key": "automation", "label": "Automatizaciones fallidas del tenant", "points": 10})
        recent_event = db.scalars(select(dbm.CaseEvent).where(dbm.CaseEvent.case_id == legal_case.id).order_by(dbm.CaseEvent.occurred_at.desc())).first()
        recent_at = recent_event.occurred_at if recent_event else None
        if recent_at and recent_at.tzinfo is None:
            recent_at = recent_at.replace(tzinfo=UTC)
        if not recent_at or recent_at < now - timedelta(days=21):
            score += 10
            factors.append({"key": "inactivity", "label": "Inactividad operativa", "points": 10})
        score = min(100, score)
        return {"case_id": legal_case.id, "title": legal_case.title, "client_id": legal_case.client_id, "score": score, "level": self._level(score), "factors": factors}

    def _level(self, score: int) -> str:
        if score <= 30:
            return "green"
        if score <= 70:
            return "amber"
        return "red"


class FinancialEngineService:
    def overview(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        cases = db.scalars(select(dbm.Case).where(dbm.Case.tenant_id == str(tenant_id), dbm.Case.deleted_at.is_(None))).all()
        cards = [self.case_profitability(db, tenant_id=tenant_id, case_id=item.id) for item in cases]
        totals = {
            "fees_cents": sum(item["fees"]["cents"] for item in cards),
            "costs_cents": sum(item["costs"]["cents"] for item in cards),
            "margin_cents": sum(item["margin"]["cents"] for item in cards),
        }
        return {
            "summary": {
                "fees": _money(totals["fees_cents"]),
                "costs": _money(totals["costs_cents"]),
                "margin": _money(totals["margin_cents"]),
                "roi": round((totals["margin_cents"] / totals["costs_cents"]) * 100, 2) if totals["costs_cents"] else 100,
                "loss_cases": len([item for item in cards if item["status"] == "loss"]),
            },
            "cases": cards,
            "by_status": dict(Counter(item["status"] for item in cards)),
            "alerts": [item for item in cards if item["status"] == "loss" or item["budget_exceeded"]],
        }

    def case_profitability(self, db: Session, *, tenant_id: UUID | str, case_id: UUID | str) -> dict[str, object]:
        tenant = str(tenant_id)
        legal_case = db.scalars(select(dbm.Case).where(dbm.Case.id == str(case_id), dbm.Case.tenant_id == tenant, dbm.Case.deleted_at.is_(None))).first()
        if not legal_case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        financial = self._ensure_financial(db, tenant_id=tenant, legal_case=legal_case)
        expenses = db.scalars(select(dbm.CaseExpense).where(dbm.CaseExpense.tenant_id == tenant, dbm.CaseExpense.case_id == legal_case.id)).all()
        hours = db.scalars(select(dbm.CaseHour).where(dbm.CaseHour.tenant_id == tenant, dbm.CaseHour.case_id == legal_case.id)).all()
        expense_cost = sum(item.amount_cents for item in expenses)
        hour_cost = sum(round((item.minutes / 60) * item.hourly_rate_cents) for item in hours)
        costs = expense_cost + hour_cost
        margin = financial.fees_cents - costs
        status_label = "loss" if margin < 0 else "profitable" if margin > financial.fees_cents * 0.25 else "neutral"
        budget_exceeded = bool(financial.budget_cents and costs > financial.budget_cents)
        return {
            "case_id": legal_case.id,
            "title": legal_case.title,
            "client_id": legal_case.client_id,
            "fees": _money(financial.fees_cents),
            "budget": _money(financial.budget_cents),
            "invoiced": _money(financial.invoiced_cents),
            "pending": _money(financial.pending_cents),
            "costs": _money(costs),
            "margin": _money(margin),
            "roi": round((margin / costs) * 100, 2) if costs else 100,
            "status": status_label,
            "budget_exceeded": budget_exceeded,
            "hours": round(sum(item.minutes for item in hours) / 60, 2),
            "expenses": [{"id": item.id, "category": item.category, "description": item.description, "amount": _money(item.amount_cents)} for item in expenses],
        }

    def add_expense(self, db: Session, *, tenant_id: UUID | str, case_id: UUID | str, actor: User, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        self.case_profitability(db, tenant_id=tenant_id, case_id=case_id)
        expense = dbm.CaseExpense(
            tenant_id=str(tenant_id),
            case_id=str(case_id),
            category=str(payload.get("category") or "general"),
            description=str(payload.get("description") or "Gasto operativo"),
            amount_cents=int(payload.get("amount_cents") or 0),
            provider=payload.get("provider"),
        )
        db.add(expense)
        _audit(db, tenant_id=tenant_id, actor=actor, action="financial.expense_created", entity_type="case_expense", entity_id=expense.id, request_id=request_id, metadata={"case_id": str(case_id)})
        db.commit()
        return self.case_profitability(db, tenant_id=tenant_id, case_id=case_id)

    def add_hours(self, db: Session, *, tenant_id: UUID | str, case_id: UUID | str, actor: User, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        self.case_profitability(db, tenant_id=tenant_id, case_id=case_id)
        entry = dbm.CaseHour(
            tenant_id=str(tenant_id),
            case_id=str(case_id),
            user_id=str(actor.id),
            minutes=int(payload.get("minutes") or 0),
            hourly_rate_cents=int(payload.get("hourly_rate_cents") or 0),
            description=payload.get("description"),
        )
        db.add(entry)
        _audit(db, tenant_id=tenant_id, actor=actor, action="financial.hours_logged", entity_type="case_hour", entity_id=entry.id, request_id=request_id, metadata={"case_id": str(case_id)})
        db.commit()
        return self.case_profitability(db, tenant_id=tenant_id, case_id=case_id)

    def _ensure_financial(self, db: Session, *, tenant_id: str, legal_case: dbm.Case) -> dbm.CaseFinancial:
        financial = db.scalars(select(dbm.CaseFinancial).where(dbm.CaseFinancial.tenant_id == tenant_id, dbm.CaseFinancial.case_id == legal_case.id)).first()
        if financial:
            return financial
        base = max(120000, len(legal_case.title) * 10000)
        financial = dbm.CaseFinancial(tenant_id=tenant_id, case_id=legal_case.id, fees_cents=base, budget_cents=round(base * 0.55), invoiced_cents=round(base * 0.4), pending_cents=round(base * 0.6))
        db.add(financial)
        db.flush()
        return financial


class CrmService:
    stages = ["lead", "contact", "meeting", "proposal", "negotiation", "won", "client", "case"]

    def list_leads(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        leads = db.scalars(select(dbm.CrmLead).where(dbm.CrmLead.tenant_id == str(tenant_id), dbm.CrmLead.deleted_at.is_(None)).order_by(dbm.CrmLead.created_at.desc())).all()
        return {"stages": self.stages, "leads": [self._lead(item) for item in leads], "analytics": self.analytics(db, tenant_id=tenant_id)}

    def create_lead(self, db: Session, *, tenant_id: UUID | str, actor: User, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        lead = dbm.CrmLead(
            tenant_id=str(tenant_id),
            owner_user_id=str(actor.id),
            company=str(payload.get("company") or payload.get("person_name") or "Nuevo lead"),
            person_name=str(payload.get("person_name") or payload.get("company") or "Contacto"),
            ruc=payload.get("ruc"),
            dni=payload.get("dni"),
            email=payload.get("email"),
            phone=payload.get("phone"),
            sector=payload.get("sector"),
            source=str(payload.get("source") or "direct"),
            campaign=payload.get("campaign"),
            expected_value_cents=int(payload.get("expected_value_cents") or 0),
            probability=int(payload.get("probability") or 25),
            stage=str(payload.get("stage") or "lead"),
            next_action=payload.get("next_action"),
            notes=payload.get("notes"),
        )
        lead.score = self._score(lead)
        db.add(lead)
        _audit(db, tenant_id=tenant_id, actor=actor, action="crm.lead_created", entity_type="crm_lead", entity_id=lead.id, request_id=request_id)
        db.commit()
        return self._lead(lead)

    def move_stage(self, db: Session, *, tenant_id: UUID | str, lead_id: UUID | str, actor: User, stage: str, request_id: str | None = None) -> dict[str, object]:
        lead = self._lead_or_404(db, tenant_id=tenant_id, lead_id=lead_id)
        if stage not in self.stages:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid CRM stage")
        lead.stage = stage
        lead.probability = max(lead.probability, min(95, (self.stages.index(stage) + 1) * 12))
        lead.score = self._score(lead)
        _audit(db, tenant_id=tenant_id, actor=actor, action="crm.stage_changed", entity_type="crm_lead", entity_id=lead.id, request_id=request_id, metadata={"stage": stage})
        db.commit()
        return self._lead(lead)

    def convert(self, db: Session, *, tenant_id: UUID | str, lead_id: UUID | str, actor: User, request_id: str | None = None) -> dict[str, object]:
        lead = self._lead_or_404(db, tenant_id=tenant_id, lead_id=lead_id)
        client = dbm.Client(tenant_id=str(tenant_id), name=lead.company, contact_email=lead.email, risk_profile="standard", tags=["crm", lead.sector or "lead"])
        db.add(client)
        db.flush()
        legal_case = dbm.Case(tenant_id=str(tenant_id), client_id=client.id, title=f"Expediente inicial {lead.company}", status="active", description="Creado desde Legal CRM.")
        db.add(legal_case)
        db.flush()
        db.add(dbm.CaseEvent(tenant_id=str(tenant_id), case_id=legal_case.id, event_type="crm_conversion", title="Lead convertido", description=f"{lead.company} convertido en cliente y expediente.", is_client_visible=False))
        db.add(dbm.Notification(tenant_id=str(tenant_id), user_id=str(actor.id), case_id=legal_case.id, title="Lead ganado", body=f"{lead.company} ya tiene cliente y expediente.", channel="in_app", status="sent"))
        lead.stage = "case"
        lead.converted_client_id = client.id
        lead.converted_case_id = legal_case.id
        _audit(db, tenant_id=tenant_id, actor=actor, action="crm.lead_converted", entity_type="crm_lead", entity_id=lead.id, request_id=request_id, metadata={"client_id": client.id, "case_id": legal_case.id})
        db.commit()
        return {"lead": self._lead(lead), "client_id": client.id, "case_id": legal_case.id}

    def analytics(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        leads = db.scalars(select(dbm.CrmLead).where(dbm.CrmLead.tenant_id == str(tenant_id), dbm.CrmLead.deleted_at.is_(None))).all()
        weighted = sum(round(lead.expected_value_cents * (lead.probability / 100)) for lead in leads)
        return {"total": len(leads), "by_stage": dict(Counter(lead.stage for lead in leads)), "weighted_pipeline": _money(weighted), "won": len([lead for lead in leads if lead.stage in {"won", "client", "case"}])}

    def _lead_or_404(self, db: Session, *, tenant_id: UUID | str, lead_id: UUID | str) -> dbm.CrmLead:
        lead = db.scalars(select(dbm.CrmLead).where(dbm.CrmLead.id == str(lead_id), dbm.CrmLead.tenant_id == str(tenant_id), dbm.CrmLead.deleted_at.is_(None))).first()
        if not lead:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
        return lead

    def _score(self, lead: dbm.CrmLead) -> int:
        return min(100, 20 + lead.probability + (20 if lead.expected_value_cents > 500000 else 0) + (10 if lead.email else 0) + (10 if lead.next_action else 0))

    def _lead(self, lead: dbm.CrmLead) -> dict[str, object]:
        return {
            "id": lead.id,
            "company": lead.company,
            "person_name": lead.person_name,
            "ruc": lead.ruc,
            "dni": lead.dni,
            "email": lead.email,
            "phone": lead.phone,
            "sector": lead.sector,
            "source": lead.source,
            "campaign": lead.campaign,
            "owner_user_id": lead.owner_user_id,
            "expected_value": _money(lead.expected_value_cents),
            "probability": lead.probability,
            "stage": lead.stage,
            "next_action": lead.next_action,
            "notes": lead.notes,
            "score": lead.score,
            "converted_client_id": lead.converted_client_id,
            "converted_case_id": lead.converted_case_id,
            "created_at": lead.created_at.isoformat(),
        }


class WarRoomService:
    def dashboard(self, db: Session, *, tenant_id: UUID | str, mode: str = "partner") -> dict[str, object]:
        tenant = str(tenant_id)
        risk = risk_engine_service.dashboard(db, tenant_id=tenant_id)
        financial = financial_engine_service.overview(db, tenant_id=tenant_id)
        cases = db.scalars(select(dbm.Case).where(dbm.Case.tenant_id == tenant, dbm.Case.deleted_at.is_(None))).all()
        hearings = db.scalars(select(dbm.Hearing).where(dbm.Hearing.tenant_id == tenant, dbm.Hearing.deleted_at.is_(None)).order_by(dbm.Hearing.starts_at.asc())).all()
        captcha = db.scalars(select(dbm.CaptchaCheckpoint).where(dbm.CaptchaCheckpoint.tenant_id == tenant, dbm.CaptchaCheckpoint.status == "pending")).all()
        updates = db.scalars(select(dbm.JudicialUpdate).where(dbm.JudicialUpdate.tenant_id == tenant).order_by(dbm.JudicialUpdate.checked_at.desc())).all()
        ai_pending = db.scalars(select(dbm.AiJob).where(dbm.AiJob.tenant_id == tenant, dbm.AiJob.status.in_(["pending_review", "queued", "running"]))).all()
        failed_runs = db.scalars(select(dbm.AutomationRun).where(dbm.AutomationRun.tenant_id == tenant, dbm.AutomationRun.status == "failed")).all()
        docs_observed = db.scalars(select(dbm.Document).where(dbm.Document.tenant_id == tenant, dbm.Document.deleted_at.is_(None), dbm.Document.status.in_(["observed", "pending"]))).all()
        tickets = db.scalars(select(dbm.SupportTicket).where(dbm.SupportTicket.tenant_id == tenant, dbm.SupportTicket.status.in_(["open", "in_progress"]))).all()
        users = db.scalars(select(dbm.User).where(dbm.User.tenant_id == tenant, dbm.User.deleted_at.is_(None))).all()
        task_load = Counter(task.assigned_user_id or "unassigned" for task in db.scalars(select(dbm.Task).where(dbm.Task.tenant_id == tenant, dbm.Task.deleted_at.is_(None), dbm.Task.status != "done")).all())
        score = max(0, 100 - risk["study_score"] - len(captcha) * 5 - len(failed_runs) * 4 - financial["summary"]["loss_cases"] * 6)
        return {
            "mode": mode,
            "generated_at": _now().isoformat(),
            "study_health": {"score": score, "level": "green" if score >= 75 else "amber" if score >= 45 else "red"},
            "critical_cases": risk["critical_cases"] or risk["cases"][:5],
            "risk_heatmap": risk["heatmap"],
            "upcoming_hearings": [{"id": item.id, "title": item.title, "case_id": item.case_id, "starts_at": item.starts_at.isoformat(), "status": item.status} for item in hearings[:6]],
            "pending_captcha": [{"id": item.id, "case_id": item.case_id, "provider": item.provider, "reason": item.reason, "status": item.status} for item in captcha],
            "judicial_live_feed": [{"id": item.id, "case_id": item.case_id, "title": item.title, "status": item.status, "checked_at": item.checked_at.isoformat()} for item in updates[:8]],
            "ai_review": [{"id": item.id, "job_type": item.job_type, "status": item.status, "case_id": item.case_id} for item in ai_pending[:8]],
            "lawyer_load": [{"user_id": user.id, "name": user.full_name, "open_tasks": task_load.get(user.id, 0), "status": "saturated" if task_load.get(user.id, 0) >= 5 else "available"} for user in users],
            "live_alerts": [
                {"type": "captcha", "title": "CAPTCHA pendientes", "count": len(captcha)},
                {"type": "automation", "title": "Automatizaciones fallidas", "count": len(failed_runs)},
                {"type": "documents", "title": "Documentos observados", "count": len(docs_observed)},
                {"type": "support", "title": "Tickets abiertos", "count": len(tickets)},
            ],
            "financial_alerts": financial["alerts"][:5],
            "cases_total": len(cases),
        }


class Level2DemoService:
    def overview(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        tenant = str(tenant_id)
        return {
            "tenant_id": tenant,
            "datasets": ["small_firm", "corporate", "litigation", "enterprise"],
            "current": {
                "clients": int(db.scalar(select(func.count()).select_from(dbm.Client).where(dbm.Client.tenant_id == tenant, dbm.Client.deleted_at.is_(None))) or 0),
                "cases": int(db.scalar(select(func.count()).select_from(dbm.Case).where(dbm.Case.tenant_id == tenant, dbm.Case.deleted_at.is_(None))) or 0),
                "crm_leads": int(db.scalar(select(func.count()).select_from(dbm.CrmLead).where(dbm.CrmLead.tenant_id == tenant, dbm.CrmLead.deleted_at.is_(None))) or 0),
                "snapshots": int(db.scalar(select(func.count()).select_from(dbm.DemoSnapshot).where(dbm.DemoSnapshot.tenant_id == tenant)) or 0),
            },
            "tour": ["dashboard", "war-room", "crm", "case-360", "sinoe", "ai", "portal", "automation", "risk", "financial", "audit"],
        }

    def reset(self, db: Session, *, tenant_id: UUID | str, actor: User, demo_type: str = "litigation", request_id: str | None = None) -> dict[str, object]:
        if not db.scalars(select(dbm.CrmLead).where(dbm.CrmLead.tenant_id == str(tenant_id), dbm.CrmLead.deleted_at.is_(None))).first():
            crm_service.create_lead(
                db,
                tenant_id=tenant_id,
                actor=actor,
                payload={"company": "Demo Litigation Studio", "person_name": "Sponsor Demo", "email": "demo@lexflow.test", "sector": "litigios", "expected_value_cents": 950000, "probability": 70, "stage": "proposal", "next_action": "Presentar demo War Room"},
                request_id=request_id,
            )
        snapshot = self.snapshot(db, tenant_id=tenant_id, actor=actor, demo_type=demo_type, request_id=request_id)
        _audit(db, tenant_id=tenant_id, actor=actor, action="demo.level2_reset", entity_type="demo_snapshot", entity_id=snapshot["id"], request_id=request_id, metadata={"demo_type": demo_type})
        db.commit()
        return {"status": "ready", "demo_type": demo_type, "snapshot": snapshot, "overview": self.overview(db, tenant_id=tenant_id)}

    def snapshot(self, db: Session, *, tenant_id: UUID | str, actor: User, demo_type: str = "general", request_id: str | None = None) -> dict[str, object]:
        payload = {
            "war_room": war_room_service.dashboard(db, tenant_id=tenant_id),
            "risk": risk_engine_service.dashboard(db, tenant_id=tenant_id),
            "financial": financial_engine_service.overview(db, tenant_id=tenant_id)["summary"],
            "crm": crm_service.analytics(db, tenant_id=tenant_id),
        }
        snapshot = dbm.DemoSnapshot(tenant_id=str(tenant_id), demo_type=demo_type, status="ready", snapshot_json=payload)
        db.add(snapshot)
        _audit(db, tenant_id=tenant_id, actor=actor, action="demo.snapshot_created", entity_type="demo_snapshot", entity_id=snapshot.id, request_id=request_id, metadata={"demo_type": demo_type})
        db.commit()
        return {"id": snapshot.id, "demo_type": snapshot.demo_type, "status": snapshot.status, "created_at": snapshot.created_at.isoformat(), "summary": payload}


risk_engine_service = RiskEngineService()
financial_engine_service = FinancialEngineService()
crm_service = CrmService()
war_room_service = WarRoomService()
level2_demo_service = Level2DemoService()
