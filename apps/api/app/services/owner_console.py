from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.owner_dependencies import OwnerPrincipal
from app.db import models as dbm
from app.db.models import now_utc


DEFAULT_FEATURES = [
    "client_portal",
    "whatsapp",
    "ai",
    "ocr",
    "sinoe",
    "legal_intelligence",
    "automation_studio",
    "dashboard",
    "mobile_pwa",
]


class OwnerConsoleService:
    def dashboard(self, db: Session) -> dict[str, object]:
        tenants = db.scalars(select(dbm.Tenant).where(dbm.Tenant.deleted_at.is_(None))).all()
        tickets = db.scalars(select(dbm.SupportTicket).where(dbm.SupportTicket.deleted_at.is_(None))).all()
        incidents = db.scalars(select(dbm.SystemIncident)).all()
        usage = db.scalars(select(dbm.TenantUsageDaily)).all()
        mrr_cents = sum(self._plan_price_cents(tenant.plan) for tenant in tenants if tenant.status == "active")
        return {
            "tenants": {
                "active": sum(1 for tenant in tenants if tenant.status == "active"),
                "trial": sum(1 for tenant in tenants if tenant.status == "trial"),
                "suspended": sum(1 for tenant in tenants if tenant.status == "suspended"),
                "total": len(tenants),
            },
            "revenue": {"mrr_cents": mrr_cents, "arr_cents": mrr_cents * 12, "churn": "0.8%"},
            "support": {"open_tickets": sum(1 for ticket in tickets if ticket.status == "open"), "sla_risk": sum(1 for ticket in tickets if ticket.priority == "high")},
            "system": {
                "critical_errors": sum(1 for incident in incidents if incident.severity == "critical" and incident.status != "resolved"),
                "jobs_failed": sum(item.used for item in usage if item.metric_key == "jobs_failed"),
            },
            "usage": {
                "ai_tokens": sum(item.used for item in usage if item.metric_key == "ai_tokens"),
                "whatsapp_messages": sum(item.used for item in usage if item.metric_key == "whatsapp_messages"),
                "storage_mb": sum(item.used for item in usage if item.metric_key == "storage_mb"),
            },
        }

    def list_tenants(self, db: Session) -> list[dict[str, object]]:
        tenants = db.scalars(select(dbm.Tenant).where(dbm.Tenant.deleted_at.is_(None)).order_by(dbm.Tenant.created_at.desc())).all()
        return [self._tenant_summary(db, tenant) for tenant in tenants]

    def create_tenant(self, db: Session, *, owner: OwnerPrincipal, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        slug = str(payload["slug"]).strip().lower()
        if db.scalar(select(dbm.Tenant).where(dbm.Tenant.slug == slug)):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tenant slug already exists")
        tenant = dbm.Tenant(name=str(payload["name"]), slug=slug, plan=str(payload.get("plan", "START")).upper(), status="trial" if payload.get("trial", True) else "active")
        db.add(tenant)
        db.flush()
        self._ensure_default_features(db, tenant.id)
        self._ensure_health(db, tenant.id)
        if payload.get("demo_data"):
            db.add(dbm.DemoTenant(tenant_id=tenant.id, demo_type=str(payload.get("demo_type", "general")), status="ready"))
        self.audit(db, owner=owner, action="tenant_created", entity_type="tenant", entity_id=tenant.id, tenant_id=tenant.id, reason="owner onboarding", request_id=request_id)
        db.commit()
        return self._tenant_detail(db, tenant)

    def tenant_detail(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        return self._tenant_detail(db, self._tenant_or_404(db, tenant_id))

    def suspend_tenant(self, db: Session, *, owner: OwnerPrincipal, tenant_id: UUID | str, reason: str, request_id: str | None = None) -> dict[str, object]:
        tenant = self._tenant_or_404(db, tenant_id)
        tenant.status = "suspended"
        self.audit(db, owner=owner, action="tenant_suspended", entity_type="tenant", entity_id=tenant.id, tenant_id=tenant.id, reason=reason, request_id=request_id)
        db.commit()
        return self._tenant_detail(db, tenant)

    def reactivate_tenant(self, db: Session, *, owner: OwnerPrincipal, tenant_id: UUID | str, reason: str, request_id: str | None = None) -> dict[str, object]:
        tenant = self._tenant_or_404(db, tenant_id)
        tenant.status = "active"
        self.audit(db, owner=owner, action="tenant_reactivated", entity_type="tenant", entity_id=tenant.id, tenant_id=tenant.id, reason=reason, request_id=request_id)
        db.commit()
        return self._tenant_detail(db, tenant)

    def change_plan(self, db: Session, *, owner: OwnerPrincipal, tenant_id: UUID | str, plan: str, reason: str, request_id: str | None = None) -> dict[str, object]:
        tenant = self._tenant_or_404(db, tenant_id)
        tenant.plan = plan.upper()
        self.audit(db, owner=owner, action="tenant_plan_changed", entity_type="tenant", entity_id=tenant.id, tenant_id=tenant.id, reason=reason, metadata={"plan": tenant.plan}, request_id=request_id)
        db.commit()
        return self._tenant_detail(db, tenant)

    def features(self, db: Session, *, tenant_id: UUID | str) -> list[dict[str, object]]:
        self._tenant_or_404(db, tenant_id)
        self._ensure_default_features(db, str(tenant_id))
        db.commit()
        flags = db.scalars(select(dbm.TenantFeatureFlag).where(dbm.TenantFeatureFlag.tenant_id == str(tenant_id)).order_by(dbm.TenantFeatureFlag.feature_key)).all()
        return [{"feature_key": flag.feature_key, "enabled": flag.enabled, "source": flag.source} for flag in flags]

    def update_features(self, db: Session, *, owner: OwnerPrincipal, tenant_id: UUID | str, features: dict[str, bool], reason: str, request_id: str | None = None) -> list[dict[str, object]]:
        self._tenant_or_404(db, tenant_id)
        for key, enabled in features.items():
            flag = db.scalar(select(dbm.TenantFeatureFlag).where(dbm.TenantFeatureFlag.tenant_id == str(tenant_id), dbm.TenantFeatureFlag.feature_key == key))
            if not flag:
                flag = dbm.TenantFeatureFlag(tenant_id=str(tenant_id), feature_key=key)
                db.add(flag)
            flag.enabled = bool(enabled)
        self.audit(db, owner=owner, action="tenant_features_updated", entity_type="tenant_feature_flags", entity_id=str(tenant_id), tenant_id=str(tenant_id), reason=reason, metadata={"features": features}, request_id=request_id)
        db.commit()
        return self.features(db, tenant_id=tenant_id)

    def usage(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        self._tenant_or_404(db, tenant_id)
        rows = db.scalars(select(dbm.TenantUsageDaily).where(dbm.TenantUsageDaily.tenant_id == str(tenant_id))).all()
        return {
            "tenant_id": str(tenant_id),
            "metrics": [{"date": row.usage_date, "metric_key": row.metric_key, "used": row.used, "cost_cents": row.cost_cents} for row in rows],
            "totals": {
                "users": db.scalar(select(func.count()).select_from(dbm.User).where(dbm.User.tenant_id == str(tenant_id), dbm.User.deleted_at.is_(None))) or 0,
                "cases": db.scalar(select(func.count()).select_from(dbm.Case).where(dbm.Case.tenant_id == str(tenant_id), dbm.Case.deleted_at.is_(None))) or 0,
                "documents": db.scalar(select(func.count()).select_from(dbm.Document).where(dbm.Document.tenant_id == str(tenant_id), dbm.Document.deleted_at.is_(None))) or 0,
            },
        }

    def health_score(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        tenant = self._tenant_or_404(db, tenant_id)
        score = self._calculate_health(db, tenant)
        row = self._ensure_health(db, tenant.id)
        row.score = score["score"]
        row.adoption_score = score["adoption_score"]
        row.payment_score = score["payment_score"]
        row.support_score = score["support_score"]
        row.risk_level = score["risk_level"]
        row.signals_json = score["signals"]
        row.calculated_at = now_utc()
        db.commit()
        return score

    def plans(self, db: Session) -> list[dict[str, object]]:
        existing = db.scalars(select(dbm.BillingPlan).where(dbm.BillingPlan.deleted_at.is_(None))).all()
        if existing:
            return [{"id": plan.id, "code": plan.code, "name": plan.name, "monthly_price_cents": plan.monthly_price_cents, "status": plan.status, "limits": plan.limits_json} for plan in existing]
        return [
            {"code": "START", "name": "Start", "monthly_price_cents": 9900, "status": "active", "limits": {"users": 5, "ai_tokens": 0}},
            {"code": "PRO", "name": "Pro", "monthly_price_cents": 24900, "status": "active", "limits": {"users": 20, "ai_tokens": 100000}},
            {"code": "AI", "name": "AI", "monthly_price_cents": 39900, "status": "active", "limits": {"users": 50, "ai_tokens": 500000}},
            {"code": "ENTERPRISE", "name": "Enterprise", "monthly_price_cents": 0, "status": "active", "limits": {"users": 999, "ai_tokens": 999999}},
        ]

    def billing(self, db: Session) -> dict[str, object]:
        invoices = db.scalars(select(dbm.Invoice)).all()
        return {
            "subscriptions": db.scalar(select(func.count()).select_from(dbm.TenantSubscription)) or 0,
            "invoices": [{"tenant_id": item.tenant_id, "invoice_number": item.invoice_number, "status": item.status, "amount_cents": item.amount_cents} for item in invoices],
            "past_due": sum(1 for item in invoices if item.status in {"past_due", "overdue"}),
        }

    def create_ticket(self, db: Session, *, owner: OwnerPrincipal, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        ticket = dbm.SupportTicket(
            tenant_id=str(payload["tenant_id"]) if payload.get("tenant_id") else None,
            title=str(payload["title"]),
            category=str(payload.get("category", "support")),
            priority=str(payload.get("priority", "medium")),
            assigned_owner_email=owner.email,
        )
        db.add(ticket)
        db.flush()
        db.add(dbm.SupportTicketMessage(ticket_id=ticket.id, author_email=owner.email, body=str(payload.get("body", "Ticket creado")), is_internal=True))
        self.audit(db, owner=owner, action="support_ticket_created", entity_type="support_ticket", entity_id=ticket.id, tenant_id=ticket.tenant_id, reason="support workflow", request_id=request_id)
        db.commit()
        return self._ticket(ticket)

    def tickets(self, db: Session) -> list[dict[str, object]]:
        return [self._ticket(ticket) for ticket in db.scalars(select(dbm.SupportTicket).where(dbm.SupportTicket.deleted_at.is_(None)).order_by(dbm.SupportTicket.created_at.desc())).all()]

    def resolve_ticket(self, db: Session, *, owner: OwnerPrincipal, ticket_id: UUID | str, resolution: str, request_id: str | None = None) -> dict[str, object]:
        ticket = db.get(dbm.SupportTicket, str(ticket_id))
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        ticket.status = "resolved"
        ticket.resolution = resolution
        self.audit(db, owner=owner, action="support_ticket_resolved", entity_type="support_ticket", entity_id=ticket.id, tenant_id=ticket.tenant_id, reason=resolution, request_id=request_id)
        db.commit()
        return self._ticket(ticket)

    def system_health(self, db: Session) -> dict[str, object]:
        checks = db.scalars(select(dbm.SystemHealthCheck).order_by(dbm.SystemHealthCheck.component)).all()
        if not checks:
            checks = [dbm.SystemHealthCheck(component=component, status="ok", latency_ms=20 + index * 5) for index, component in enumerate(["api", "db", "redis", "storage", "ai", "whatsapp", "sinoe", "jobs", "backups"])]
            db.add_all(checks)
            db.commit()
        return {"checks": [{"component": item.component, "status": item.status, "latency_ms": item.latency_ms, "checked_at": item.checked_at.isoformat()} for item in checks]}

    def incidents(self, db: Session) -> list[dict[str, object]]:
        return [{"id": item.id, "component": item.component, "title": item.title, "severity": item.severity, "status": item.status} for item in db.scalars(select(dbm.SystemIncident)).all()]

    def demos(self, db: Session) -> list[dict[str, object]]:
        demos = db.scalars(select(dbm.DemoTenant).order_by(dbm.DemoTenant.created_at.desc())).all()
        return [{"id": item.id, "tenant_id": item.tenant_id, "demo_type": item.demo_type, "status": item.status, "last_reset_at": item.last_reset_at.isoformat() if item.last_reset_at else None} for item in demos]

    def create_demo(self, db: Session, *, owner: OwnerPrincipal, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        tenant_payload = {
            "name": payload.get("name", "LEXFLOW Demo Tenant"),
            "slug": payload.get("slug", f"demo-{now_utc().strftime('%Y%m%d%H%M%S')}"),
            "plan": payload.get("plan", "AI"),
            "trial": True,
            "demo_data": True,
            "demo_type": payload.get("demo_type", "general"),
        }
        detail = self.create_tenant(db, owner=owner, payload=tenant_payload, request_id=request_id)
        return {"tenant": detail, "demo": self.demos(db)[0]}

    def interventions(self, db: Session) -> list[dict[str, object]]:
        self.expire_interventions(db)
        rows = db.scalars(select(dbm.TenantIntervention).order_by(dbm.TenantIntervention.created_at.desc())).all()
        return [self._intervention(row) for row in rows]

    def create_intervention(self, db: Session, *, owner: OwnerPrincipal, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        tenant = self._tenant_or_404(db, str(payload["tenant_id"]))
        duration = int(payload.get("duration_minutes", 60))
        intervention = dbm.TenantIntervention(
            tenant_id=tenant.id,
            requested_by_email=owner.email,
            approved_by_email=owner.email if owner.role == "owner_admin" else None,
            reason=str(payload["reason"]),
            scopes_json=list(payload.get("scopes", ["metadata:read"])),
            status="active",
            expires_at=now_utc() + timedelta(minutes=duration),
        )
        db.add(intervention)
        db.flush()
        self.audit(db, owner=owner, action="tenant_intervention_created", entity_type="tenant_intervention", entity_id=intervention.id, tenant_id=tenant.id, reason=intervention.reason, metadata={"expires_at": intervention.expires_at.isoformat(), "scopes": intervention.scopes_json}, request_id=request_id)
        db.commit()
        return self._intervention(intervention)

    def expire_interventions(self, db: Session) -> int:
        now = now_utc()
        rows = db.scalars(select(dbm.TenantIntervention).where(dbm.TenantIntervention.status == "active", dbm.TenantIntervention.expires_at <= now)).all()
        for row in rows:
            row.status = "expired"
            row.closed_at = now
        if rows:
            db.commit()
        return len(rows)

    def audit_logs(self, db: Session) -> list[dict[str, object]]:
        rows = db.scalars(select(dbm.OwnerAuditLog).order_by(dbm.OwnerAuditLog.created_at.desc()).limit(100)).all()
        return [{"id": row.id, "owner_email": row.owner_email, "tenant_id": row.tenant_id, "action": row.action, "entity_type": row.entity_type, "reason": row.reason, "created_at": row.created_at.isoformat()} for row in rows]

    def audit(self, db: Session, *, owner: OwnerPrincipal, action: str, entity_type: str, entity_id: str | None = None, tenant_id: str | None = None, reason: str = "", metadata: dict[str, object] | None = None, request_id: str | None = None) -> None:
        user = self._ensure_owner_user(db, owner)
        db.add(dbm.OwnerAuditLog(owner_user_id=user.id, owner_email=owner.email, tenant_id=tenant_id, action=action, entity_type=entity_type, entity_id=entity_id, reason=reason, metadata_json=metadata or {}, request_id=request_id))

    def _ensure_owner_user(self, db: Session, owner: OwnerPrincipal) -> dbm.OwnerUser:
        user = db.scalar(select(dbm.OwnerUser).where(dbm.OwnerUser.email == owner.email))
        if user:
            user.role = owner.role
            return user
        user = dbm.OwnerUser(email=owner.email, full_name=owner.email.split("@")[0], role=owner.role)
        db.add(user)
        db.flush()
        return user

    def _ensure_default_features(self, db: Session, tenant_id: str) -> None:
        existing = {row.feature_key for row in db.scalars(select(dbm.TenantFeatureFlag).where(dbm.TenantFeatureFlag.tenant_id == tenant_id)).all()}
        for feature in DEFAULT_FEATURES:
            if feature not in existing:
                db.add(dbm.TenantFeatureFlag(tenant_id=tenant_id, feature_key=feature, enabled=feature in {"dashboard", "client_portal"}))

    def _ensure_health(self, db: Session, tenant_id: str) -> dbm.TenantHealthScore:
        row = db.scalar(select(dbm.TenantHealthScore).where(dbm.TenantHealthScore.tenant_id == tenant_id))
        if row:
            return row
        row = dbm.TenantHealthScore(tenant_id=tenant_id, score=82, signals_json=["onboarding pendiente"])
        db.add(row)
        db.flush()
        return row

    def _tenant_or_404(self, db: Session, tenant_id: UUID | str) -> dbm.Tenant:
        tenant = db.scalar(select(dbm.Tenant).where(dbm.Tenant.id == str(tenant_id), dbm.Tenant.deleted_at.is_(None)))
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        return tenant

    def _tenant_summary(self, db: Session, tenant: dbm.Tenant) -> dict[str, object]:
        return {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
            "status": tenant.status,
            "plan": tenant.plan,
            "users": db.scalar(select(func.count()).select_from(dbm.User).where(dbm.User.tenant_id == tenant.id, dbm.User.deleted_at.is_(None))) or 0,
            "cases": db.scalar(select(func.count()).select_from(dbm.Case).where(dbm.Case.tenant_id == tenant.id, dbm.Case.deleted_at.is_(None))) or 0,
            "health_score": (db.scalar(select(dbm.TenantHealthScore.score).where(dbm.TenantHealthScore.tenant_id == tenant.id)) or 82),
        }

    def _tenant_detail(self, db: Session, tenant: dbm.Tenant) -> dict[str, object]:
        return {
            **self._tenant_summary(db, tenant),
            "features": self.features(db, tenant_id=tenant.id),
            "usage": self.usage(db, tenant_id=tenant.id),
            "health": self.health_score(db, tenant_id=tenant.id),
            "sensitive_data": "redacted",
        }

    def _calculate_health(self, db: Session, tenant: dbm.Tenant) -> dict[str, object]:
        cases = db.scalar(select(func.count()).select_from(dbm.Case).where(dbm.Case.tenant_id == tenant.id, dbm.Case.deleted_at.is_(None))) or 0
        open_tickets = db.scalar(select(func.count()).select_from(dbm.SupportTicket).where(dbm.SupportTicket.tenant_id == tenant.id, dbm.SupportTicket.status == "open", dbm.SupportTicket.deleted_at.is_(None))) or 0
        payment_score = 40 if tenant.status == "suspended" else 90
        adoption_score = min(100, 55 + cases * 8)
        support_score = max(30, 90 - open_tickets * 15)
        score = int((adoption_score + payment_score + support_score) / 3)
        risk_level = "high" if score < 60 else "medium" if score < 78 else "low"
        signals = [f"{cases} expedientes", f"{open_tickets} tickets abiertos", f"estado {tenant.status}"]
        return {"tenant_id": tenant.id, "score": score, "adoption_score": adoption_score, "payment_score": payment_score, "support_score": support_score, "risk_level": risk_level, "signals": signals}

    @staticmethod
    def _ticket(ticket: dbm.SupportTicket) -> dict[str, object]:
        return {"id": ticket.id, "tenant_id": ticket.tenant_id, "title": ticket.title, "category": ticket.category, "priority": ticket.priority, "status": ticket.status, "assigned_owner_email": ticket.assigned_owner_email, "resolution": ticket.resolution}

    @staticmethod
    def _intervention(row: dbm.TenantIntervention) -> dict[str, object]:
        return {"id": row.id, "tenant_id": row.tenant_id, "requested_by_email": row.requested_by_email, "approved_by_email": row.approved_by_email, "reason": row.reason, "scopes": row.scopes_json, "status": row.status, "expires_at": row.expires_at.isoformat(), "closed_at": row.closed_at.isoformat() if row.closed_at else None}

    @staticmethod
    def _plan_price_cents(plan: str) -> int:
        return {"START": 9900, "PRO": 24900, "AI": 39900, "ENTERPRISE": 0, "DEMO": 0}.get(plan.upper(), 9900)


owner_console_service = OwnerConsoleService()
