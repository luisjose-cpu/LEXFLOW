from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import models as dbm


def _count(db: Session, query) -> int:
    return int(db.scalar(query) or 0)


class KPIService:
    def kpis(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        tenant = str(tenant_id)
        stale_before = datetime.now(UTC) - timedelta(days=14)
        case_ids_with_recent_events = db.scalars(
            select(dbm.CaseEvent.case_id).where(dbm.CaseEvent.tenant_id == tenant, dbm.CaseEvent.occurred_at >= stale_before)
        ).all()
        active_cases = _count(db, select(func.count()).select_from(dbm.Case).where(dbm.Case.tenant_id == tenant, dbm.Case.deleted_at.is_(None), dbm.Case.status != "closed"))
        critical_cases = _count(db, select(func.count()).select_from(dbm.Case).where(dbm.Case.tenant_id == tenant, dbm.Case.status == "risk", dbm.Case.deleted_at.is_(None)))
        stale_cases = _count(
            db,
            select(func.count()).select_from(dbm.Case).where(
                dbm.Case.tenant_id == tenant,
                dbm.Case.deleted_at.is_(None),
                dbm.Case.id.not_in(case_ids_with_recent_events or ["none"]),
            ),
        )
        return {
            "active_cases": active_cases,
            "critical_cases": critical_cases,
            "stale_cases": stale_cases,
            "hearings": _count(db, select(func.count()).select_from(dbm.Hearing).where(dbm.Hearing.tenant_id == tenant, dbm.Hearing.deleted_at.is_(None))),
            "pending_documents": _count(db, select(func.count()).select_from(dbm.Document).where(dbm.Document.tenant_id == tenant, dbm.Document.deleted_at.is_(None), dbm.Document.classification.is_(None))),
            "clients": _count(db, select(func.count()).select_from(dbm.Client).where(dbm.Client.tenant_id == tenant, dbm.Client.deleted_at.is_(None))),
            "messages": _count(db, select(func.count()).select_from(dbm.CommunicationMessage).where(dbm.CommunicationMessage.tenant_id == tenant))
            + _count(db, select(func.count()).select_from(dbm.WhatsAppMessage).where(dbm.WhatsAppMessage.tenant_id == tenant)),
            "ai_jobs": _count(db, select(func.count()).select_from(dbm.AiJob).where(dbm.AiJob.tenant_id == tenant)),
            "legal_news": _count(db, select(func.count()).select_from(dbm.LegalNews).where(dbm.LegalNews.tenant_id == tenant)),
            "captcha_pending": _count(db, select(func.count()).select_from(dbm.CaptchaCheckpoint).where(dbm.CaptchaCheckpoint.tenant_id == tenant, dbm.CaptchaCheckpoint.status == "pending"))
            + _count(db, select(func.count()).select_from(dbm.JudicialUpdate).where(dbm.JudicialUpdate.tenant_id == tenant, dbm.JudicialUpdate.captcha_required.is_(True))),
        }


class RiskService:
    def risks(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        tenant = str(tenant_id)
        risky_cases = db.scalars(select(dbm.Case).where(dbm.Case.tenant_id == tenant, dbm.Case.deleted_at.is_(None), dbm.Case.status == "risk")).all()
        captcha_updates = db.scalars(select(dbm.JudicialUpdate).where(dbm.JudicialUpdate.tenant_id == tenant, dbm.JudicialUpdate.requires_human_intervention.is_(True))).all()
        overdue_tasks = db.scalars(select(dbm.Task).where(dbm.Task.tenant_id == tenant, dbm.Task.deleted_at.is_(None), dbm.Task.status != "done", dbm.Task.due_at < datetime.now(UTC))).all()
        return {
            "score": min(100, len(risky_cases) * 25 + len(captcha_updates) * 20 + len(overdue_tasks) * 10),
            "critical_cases": [{"id": item.id, "title": item.title, "status": item.status} for item in risky_cases[:5]],
            "captcha_pending": len(captcha_updates),
            "overdue_tasks": len(overdue_tasks),
        }


class ProductivityService:
    def productivity(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        tenant = str(tenant_id)
        tasks = db.scalars(select(dbm.Task).where(dbm.Task.tenant_id == tenant, dbm.Task.deleted_at.is_(None))).all()
        users = db.scalars(select(dbm.User).where(dbm.User.tenant_id == tenant, dbm.User.deleted_at.is_(None))).all()
        by_user = Counter(task.assigned_user_id or "unassigned" for task in tasks)
        return {
            "open_tasks": len([task for task in tasks if task.status != "done"]),
            "completed_tasks": len([task for task in tasks if task.status == "done"]),
            "workload": [
                {"user_id": user.id, "name": user.full_name, "open_tasks": by_user.get(user.id, 0)}
                for user in users
            ],
            "cycle_time_days": 5,
        }


class JudicialMonitoringAnalyticsService:
    def monitoring(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        tenant = str(tenant_id)
        sources = db.scalars(select(dbm.CaseSource).where(dbm.CaseSource.tenant_id == tenant, dbm.CaseSource.deleted_at.is_(None))).all()
        updates = db.scalars(select(dbm.JudicialUpdate).where(dbm.JudicialUpdate.tenant_id == tenant)).all()
        return {
            "sources": len(sources),
            "updates": len(updates),
            "captcha_pending": len([item for item in updates if item.captcha_required]),
            "last_checked": max((source.last_checked_at for source in sources if source.last_checked_at), default=None).isoformat() if sources else None,
        }


class AIAnalyticsService:
    def analytics(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        jobs = db.scalars(select(dbm.AiJob).where(dbm.AiJob.tenant_id == str(tenant_id))).all()
        by_status = Counter(job.status for job in jobs)
        by_type = Counter(job.job_type for job in jobs)
        return {"total": len(jobs), "by_status": dict(by_status), "by_type": dict(by_type), "review_pending": by_status.get("pending_review", 0)}


class CommunicationAnalyticsService:
    def analytics(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        tenant = str(tenant_id)
        messages = db.scalars(select(dbm.CommunicationMessage).where(dbm.CommunicationMessage.tenant_id == tenant)).all()
        whatsapp = db.scalars(select(dbm.WhatsAppMessage).where(dbm.WhatsAppMessage.tenant_id == tenant)).all()
        by_channel = Counter([message.channel for message in messages] + ["whatsapp" for _ in whatsapp])
        return {"total": len(messages) + len(whatsapp), "by_channel": dict(by_channel), "unread_or_pending": len([item for item in messages if item.status in {"queued", "received"}])}


class LegalTrendAnalyticsService:
    def analytics(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        news = db.scalars(select(dbm.LegalNews).where(dbm.LegalNews.tenant_id == str(tenant_id))).all()
        tags = Counter(tag for item in news for tag in item.tags)
        return {"news": len(news), "top_tags": [{"tag": tag, "count": count} for tag, count in tags.most_common(6)]}


class DashboardService:
    def overview(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        return {
            "kpis": kpi_service.kpis(db, tenant_id=tenant_id),
            "risks": risk_service.risks(db, tenant_id=tenant_id),
            "productivity": productivity_service.productivity(db, tenant_id=tenant_id),
            "judicial_monitoring": judicial_monitoring_service.monitoring(db, tenant_id=tenant_id),
            "communications": communication_analytics_service.analytics(db, tenant_id=tenant_id),
            "ai": ai_analytics_service.analytics(db, tenant_id=tenant_id),
            "legal_intelligence": legal_trend_analytics_service.analytics(db, tenant_id=tenant_id),
        }


class CommandCenterService:
    def snapshot(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        overview = dashboard_service.overview(db, tenant_id=tenant_id)
        return {
            "tenant_id": str(tenant_id),
            "generated_at": datetime.now(UTC).isoformat(),
            "executive_state": "attention_required" if overview["risks"]["score"] >= 50 else "controlled",
            "overview": overview,
            "decision_queue": [
                "Revisar expedientes criticos",
                "Resolver CAPTCHA pendientes",
                "Aprobar salidas IA en revision",
                "Vincular inteligencia juridica a expedientes activos",
            ],
        }


kpi_service = KPIService()
risk_service = RiskService()
productivity_service = ProductivityService()
judicial_monitoring_service = JudicialMonitoringAnalyticsService()
ai_analytics_service = AIAnalyticsService()
communication_analytics_service = CommunicationAnalyticsService()
legal_trend_analytics_service = LegalTrendAnalyticsService()
dashboard_service = DashboardService()
command_center_service = CommandCenterService()
