from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.owner_dependencies import OwnerPrincipal
from app.core.config import get_settings
from app.core.middleware import REQUEST_METRICS
from app.core.readiness import production_readiness_report
from app.db import models as dbm
from app.db.models import now_utc
from app.services.billing import billing_service
from app.services.security import hash_password
from app.services.storage import storage_service


DEFAULT_FEATURES = [
    "expediente360",
    "client_portal",
    "whatsapp",
    "ai",
    "ocr",
    "sinoe",
    "judicial_automation",
    "legal_intelligence",
    "automation_studio",
    "dashboard",
    "mobile_pwa",
    "custom_branding",
    "custom_domain",
    "api_access",
]

OWNER_PLAN_CATALOG_SLUG = "lexflow-owner-catalog"


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
        plan = str(payload.get("plan", "START")).upper()
        tenant = dbm.Tenant(name=str(payload["name"]), slug=slug, plan=plan, status="trial" if payload.get("trial", True) else "active")
        db.add(tenant)
        db.flush()
        self._ensure_default_features(db, tenant.id, plan=tenant.plan, modules=list(payload.get("modules") or []))
        self._ensure_default_limits(db, tenant)
        admin = self._ensure_initial_admin(db, tenant=tenant, payload=payload)
        subscription = self._ensure_plan_subscription(db, tenant=tenant, seats=int(payload.get("seats") or self._default_limits_for_plan(tenant.plan).get("users", 3)))
        self._ensure_health(db, tenant.id)
        if payload.get("demo_data"):
            db.add(dbm.DemoTenant(tenant_id=tenant.id, demo_type=str(payload.get("demo_type", "general")), status="ready"))
        self.audit(
            db,
            owner=owner,
            action="tenant_created",
            entity_type="tenant",
            entity_id=tenant.id,
            tenant_id=tenant.id,
            reason="owner onboarding",
            metadata={"plan": tenant.plan, "admin_created": bool(admin), "subscription_id": subscription.id},
            request_id=request_id,
        )
        if admin:
            db.add(
                dbm.AuditLog(
                    tenant_id=tenant.id,
                    actor_user_id=admin.id,
                    action="create",
                    entity_type="tenant_onboarding",
                    entity_id=tenant.id,
                    request_id=request_id,
                    metadata_json={"admin_email": admin.email, "plan": tenant.plan, "owner": owner.email, "password_present": bool(payload.get("admin_password"))},
                )
            )
        db.commit()
        return self._tenant_detail(db, tenant)

    def tenant_detail(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        return self._tenant_detail(db, self._tenant_or_404(db, tenant_id))

    def onboarding_summary(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        tenant = self._tenant_or_404(db, tenant_id)
        return self._onboarding_summary(db, tenant)

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
        self._ensure_default_features(db, tenant.id, plan=tenant.plan)
        self._ensure_plan_subscription(db, tenant=tenant, seats=self._current_seats(db, tenant.id))
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

    def limits(self, db: Session, *, tenant_id: UUID | str) -> list[dict[str, object]]:
        tenant = self._tenant_or_404(db, tenant_id)
        self._ensure_default_limits(db, tenant)
        db.commit()
        rows = db.scalars(select(dbm.TenantLimit).where(dbm.TenantLimit.tenant_id == tenant.id).order_by(dbm.TenantLimit.limit_key)).all()
        return [self._limit(row) for row in rows]

    def update_limits(self, db: Session, *, owner: OwnerPrincipal, tenant_id: UUID | str, limits: dict[str, int], hard_limit: bool, reason: str, request_id: str | None = None) -> list[dict[str, object]]:
        tenant = self._tenant_or_404(db, tenant_id)
        self._ensure_default_limits(db, tenant)
        db.flush()
        for key, value in limits.items():
            row = db.scalar(select(dbm.TenantLimit).where(dbm.TenantLimit.tenant_id == tenant.id, dbm.TenantLimit.limit_key == key))
            if not row:
                row = dbm.TenantLimit(tenant_id=tenant.id, limit_key=key)
                db.add(row)
            row.limit_value = int(value)
            row.hard_limit = hard_limit
        self.audit(db, owner=owner, action="tenant_limits_updated", entity_type="tenant_limits", entity_id=tenant.id, tenant_id=tenant.id, reason=reason, metadata={"limits": limits, "hard_limit": hard_limit}, request_id=request_id)
        db.commit()
        return self.limits(db, tenant_id=tenant.id)

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
        catalog = self._plan_catalog_tenant(db)
        existing = db.scalars(select(dbm.BillingPlan).where(dbm.BillingPlan.tenant_id == catalog.id, dbm.BillingPlan.deleted_at.is_(None)).order_by(dbm.BillingPlan.monthly_price_cents)).all()
        if existing:
            return [self._plan(plan) for plan in existing]
        return [
            {"code": "START", "name": "Start", "monthly_price_cents": 9900, "status": "active", "limits": {"users": 5, "ai_tokens": 0}, "features": ["expediente360", "dashboard"]},
            {"code": "PRO", "name": "Pro", "monthly_price_cents": 24900, "status": "active", "limits": {"users": 20, "ai_tokens": 100000}, "features": ["client_portal", "sinoe", "whatsapp"]},
            {"code": "AI", "name": "AI", "monthly_price_cents": 39900, "status": "active", "limits": {"users": 50, "ai_tokens": 500000}, "features": ["ai", "ocr", "automation_studio"]},
            {"code": "ENTERPRISE", "name": "Enterprise", "monthly_price_cents": 0, "status": "active", "limits": {"users": 999, "ai_tokens": 999999}, "features": DEFAULT_FEATURES},
        ]

    def create_plan(self, db: Session, *, owner: OwnerPrincipal, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        catalog = self._plan_catalog_tenant(db)
        code = str(payload["code"]).strip().upper()
        if db.scalar(select(dbm.BillingPlan).where(dbm.BillingPlan.tenant_id == catalog.id, dbm.BillingPlan.code == code, dbm.BillingPlan.deleted_at.is_(None))):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Owner plan code already exists")
        plan = dbm.BillingPlan(
            tenant_id=catalog.id,
            code=code,
            name=str(payload["name"]),
            monthly_price_cents=int(payload.get("monthly_price_cents", 0)),
            status=str(payload.get("status", "active")),
            trial_days=int(payload.get("trial_days", 14)),
            limits_json=dict(payload.get("limits") or {}),
        )
        db.add(plan)
        db.flush()
        self._replace_plan_features(db, plan, list(payload.get("features") or []))
        self.audit(db, owner=owner, action="owner_plan_created", entity_type="billing_plan", entity_id=plan.id, reason="owner plan management", metadata={"code": plan.code}, request_id=request_id)
        db.commit()
        return self._plan(plan)

    def update_plan(self, db: Session, *, owner: OwnerPrincipal, plan_code: str, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        catalog = self._plan_catalog_tenant(db)
        plan = db.scalar(select(dbm.BillingPlan).where(dbm.BillingPlan.tenant_id == catalog.id, dbm.BillingPlan.code == plan_code.upper(), dbm.BillingPlan.deleted_at.is_(None)))
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner plan not found")
        if "name" in payload:
            plan.name = str(payload["name"])
        if "monthly_price_cents" in payload:
            plan.monthly_price_cents = int(payload["monthly_price_cents"])
        if "status" in payload:
            plan.status = str(payload["status"])
        if "trial_days" in payload:
            plan.trial_days = int(payload["trial_days"])
        if "limits" in payload:
            plan.limits_json = dict(payload["limits"] or {})
        if "features" in payload:
            self._replace_plan_features(db, plan, list(payload["features"] or []))
        self.audit(db, owner=owner, action="owner_plan_updated", entity_type="billing_plan", entity_id=plan.id, reason=str(payload.get("reason", "owner plan update")), metadata={"code": plan.code, "status": plan.status}, request_id=request_id)
        db.commit()
        return self._plan(plan)

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
        readiness = production_readiness_report(get_settings())
        storage_status = storage_service.provider_status()
        live_checks = [
            {
                "component": "api_requests",
                "status": "ok",
                "latency_ms": int(REQUEST_METRICS["last_response_time_ms"]),
                "checked_at": now_utc().isoformat(),
                "detail": f"requests={REQUEST_METRICS['requests_total']} errors={REQUEST_METRICS['errors_total']}",
            },
            {
                "component": "readiness",
                "status": str(readiness["status"]),
                "latency_ms": 0,
                "checked_at": now_utc().isoformat(),
                "detail": f"blockers={len(readiness['blockers'])} warnings={len(readiness['warnings'])}",
            },
            {
                "component": "storage_backend",
                "status": "ok" if storage_status["backend"] in {"local", "s3"} else "warning",
                "latency_ms": 0,
                "checked_at": now_utc().isoformat(),
                "detail": f"backend={storage_status['backend']} bucket={storage_status['bucket']}",
            },
        ]
        stored_checks = [{"component": item.component, "status": item.status, "latency_ms": item.latency_ms, "checked_at": item.checked_at.isoformat(), "detail": "stored health check"} for item in checks]
        return {"checks": [*live_checks, *stored_checks]}

    def incidents(self, db: Session) -> list[dict[str, object]]:
        rows = db.scalars(select(dbm.SystemIncident).order_by(dbm.SystemIncident.created_at.desc())).all()
        return [self._incident(row) for row in rows]

    def create_incident(self, db: Session, *, owner: OwnerPrincipal, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        incident = dbm.SystemIncident(
            component=str(payload["component"]).strip().lower(),
            title=str(payload["title"]).strip(),
            severity=str(payload.get("severity", "medium")),
            summary=str(payload.get("summary", "")),
            status="open",
        )
        db.add(incident)
        db.flush()
        self.audit(db, owner=owner, action="system_incident_created", entity_type="system_incident", entity_id=incident.id, reason=incident.title, metadata={"component": incident.component, "severity": incident.severity}, request_id=request_id)
        db.commit()
        return self._incident(incident)

    def resolve_incident(self, db: Session, *, owner: OwnerPrincipal, incident_id: UUID | str, reason: str, request_id: str | None = None) -> dict[str, object]:
        incident = db.get(dbm.SystemIncident, str(incident_id))
        if not incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
        incident.status = "resolved"
        incident.resolved_at = now_utc()
        self.audit(db, owner=owner, action="system_incident_resolved", entity_type="system_incident", entity_id=incident.id, reason=reason, metadata={"component": incident.component, "resolved_at": incident.resolved_at.isoformat()}, request_id=request_id)
        db.commit()
        return self._incident(incident)

    def demos(self, db: Session) -> list[dict[str, object]]:
        demos = db.scalars(select(dbm.DemoTenant).order_by(dbm.DemoTenant.created_at.desc())).all()
        return [self._demo(item) for item in demos]

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

    def reset_demo(self, db: Session, *, owner: OwnerPrincipal, demo_id: UUID | str, reason: str, request_id: str | None = None) -> dict[str, object]:
        demo = db.get(dbm.DemoTenant, str(demo_id))
        if not demo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo tenant not found")
        demo.status = "ready"
        demo.last_reset_at = now_utc()
        demo.metadata_json = {**(demo.metadata_json or {}), "last_reset_reason": reason, "reset_by": owner.email}
        self.audit(db, owner=owner, action="demo_tenant_reset", entity_type="demo_tenant", entity_id=demo.id, tenant_id=demo.tenant_id, reason=reason, metadata={"demo_type": demo.demo_type, "last_reset_at": demo.last_reset_at.isoformat()}, request_id=request_id)
        db.commit()
        return self._demo(demo)

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

    def close_intervention(self, db: Session, *, owner: OwnerPrincipal, intervention_id: UUID | str, reason: str, request_id: str | None = None) -> dict[str, object]:
        intervention = db.get(dbm.TenantIntervention, str(intervention_id))
        if not intervention:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intervention not found")
        intervention.status = "closed"
        intervention.closed_at = now_utc()
        self.audit(db, owner=owner, action="tenant_intervention_closed", entity_type="tenant_intervention", entity_id=intervention.id, tenant_id=intervention.tenant_id, reason=reason, metadata={"closed_at": intervention.closed_at.isoformat()}, request_id=request_id)
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

    def _ensure_initial_admin(self, db: Session, *, tenant: dbm.Tenant, payload: dict[str, object]) -> dbm.User | None:
        admin_email = str(payload.get("admin_email") or "").strip().lower()
        admin_name = str(payload.get("admin_name") or "").strip()
        admin_password = str(payload.get("admin_password") or "")
        if not admin_email and not admin_name and not admin_password:
            return None
        if not admin_email or not admin_name or len(admin_password) < 12:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Admin email, name and 12+ character password are required")

        role = db.scalar(select(dbm.Role).where(dbm.Role.tenant_id == tenant.id, dbm.Role.name == "tenant_admin", dbm.Role.deleted_at.is_(None)))
        if not role:
            role = dbm.Role(tenant_id=tenant.id, name="tenant_admin", description="Tenant administrator", is_system=True)
            db.add(role)
            db.flush()

        existing = db.scalar(select(dbm.User).where(dbm.User.tenant_id == tenant.id, dbm.User.email == admin_email, dbm.User.deleted_at.is_(None)))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Initial admin already exists")
        user = dbm.User(
            tenant_id=tenant.id,
            role_id=role.id,
            email=admin_email,
            full_name=admin_name,
            hashed_password=hash_password(admin_password),
            status="active",
        )
        db.add(user)
        db.flush()
        return user

    def _ensure_plan_subscription(self, db: Session, *, tenant: dbm.Tenant, seats: int) -> dbm.TenantSubscription:
        plan = billing_service.get_plan(db, tenant_id=tenant.id, plan_code=tenant.plan)
        subscription = db.scalars(
            select(dbm.TenantSubscription)
            .where(dbm.TenantSubscription.tenant_id == tenant.id, dbm.TenantSubscription.deleted_at.is_(None))
            .order_by(dbm.TenantSubscription.created_at.desc())
        ).first()
        if not subscription:
            subscription = dbm.TenantSubscription(tenant_id=tenant.id, plan_id=plan.id, provider_subscription_id=f"owner-sub-{tenant.id[:8]}")
            db.add(subscription)
        subscription.plan_id = plan.id
        subscription.seats = max(1, seats)
        subscription.status = "trialing" if tenant.status == "trial" else "active"
        subscription.trial_ends_at = now_utc() + timedelta(days=plan.trial_days) if tenant.status == "trial" else None
        subscription.current_period_ends_at = now_utc() + timedelta(days=30)
        subscription.metadata_json = {"source": "owner_onboarding", "tenant_plan": tenant.plan}
        db.flush()
        return subscription

    def _current_seats(self, db: Session, tenant_id: str) -> int:
        subscription = db.scalars(
            select(dbm.TenantSubscription)
            .where(dbm.TenantSubscription.tenant_id == tenant_id, dbm.TenantSubscription.deleted_at.is_(None))
            .order_by(dbm.TenantSubscription.created_at.desc())
        ).first()
        return subscription.seats if subscription else self._default_limits_for_plan("START").get("users", 3)

    def _onboarding_summary(self, db: Session, tenant: dbm.Tenant) -> dict[str, object]:
        admin = db.scalars(
            select(dbm.User)
            .join(dbm.Role)
            .where(dbm.User.tenant_id == tenant.id, dbm.Role.name == "tenant_admin", dbm.User.deleted_at.is_(None))
            .order_by(dbm.User.created_at.asc())
        ).first()
        subscription = db.scalars(
            select(dbm.TenantSubscription)
            .where(dbm.TenantSubscription.tenant_id == tenant.id, dbm.TenantSubscription.deleted_at.is_(None))
            .order_by(dbm.TenantSubscription.created_at.desc())
        ).first()
        steps = [
            {"key": "tenant", "label": "Tenant creado", "complete": True},
            {"key": "admin", "label": "Admin inicial", "complete": bool(admin)},
            {"key": "subscription", "label": "Suscripcion mock", "complete": bool(subscription)},
            {"key": "features", "label": "Feature flags", "complete": bool(db.scalar(select(func.count()).select_from(dbm.TenantFeatureFlag).where(dbm.TenantFeatureFlag.tenant_id == tenant.id)))},
            {"key": "limits", "label": "Limites SaaS", "complete": bool(db.scalar(select(func.count()).select_from(dbm.TenantLimit).where(dbm.TenantLimit.tenant_id == tenant.id)))},
        ]
        return {
            "tenant_id": tenant.id,
            "tenant_slug": tenant.slug,
            "login_url": "/login",
            "admin_email": admin.email if admin else None,
            "subscription_status": subscription.status if subscription else "missing",
            "trial_ends_at": subscription.trial_ends_at.isoformat() if subscription and subscription.trial_ends_at else None,
            "steps": steps,
            "ready": all(step["complete"] for step in steps),
            "handoff": "Enviar URL de login, slug del tenant, correo admin y password temporal por canal seguro externo.",
        }

    def _ensure_default_features(self, db: Session, tenant_id: str, *, plan: str = "START", modules: list[str] | None = None) -> None:
        existing = {row.feature_key for row in db.scalars(select(dbm.TenantFeatureFlag).where(dbm.TenantFeatureFlag.tenant_id == tenant_id)).all()}
        enabled_features = self._enabled_features_for_plan(plan) | set(modules or [])
        for feature in DEFAULT_FEATURES:
            if feature not in existing:
                db.add(dbm.TenantFeatureFlag(tenant_id=tenant_id, feature_key=feature, enabled=feature in enabled_features, metadata_json={"source_plan": plan}))
            elif feature in enabled_features:
                row = db.scalar(select(dbm.TenantFeatureFlag).where(dbm.TenantFeatureFlag.tenant_id == tenant_id, dbm.TenantFeatureFlag.feature_key == feature))
                if row:
                    row.enabled = True

    @staticmethod
    def _enabled_features_for_plan(plan: str) -> set[str]:
        return {
            "START": {"expediente360", "dashboard", "mobile_pwa"},
            "PRO": {"expediente360", "dashboard", "mobile_pwa", "client_portal", "sinoe", "judicial_automation", "whatsapp"},
            "AI": {"expediente360", "dashboard", "mobile_pwa", "client_portal", "sinoe", "judicial_automation", "whatsapp", "ai", "ocr", "legal_intelligence", "automation_studio"},
            "ENTERPRISE": set(DEFAULT_FEATURES),
        }.get(plan.upper(), {"expediente360", "dashboard"})

    def _ensure_default_limits(self, db: Session, tenant: dbm.Tenant) -> None:
        defaults = self._default_limits_for_plan(tenant.plan)
        existing = {row.limit_key for row in db.scalars(select(dbm.TenantLimit).where(dbm.TenantLimit.tenant_id == tenant.id)).all()}
        for key, value in defaults.items():
            if key not in existing:
                db.add(dbm.TenantLimit(tenant_id=tenant.id, limit_key=key, limit_value=value, hard_limit=True, metadata_json={"source": tenant.plan}))

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
            "onboarding": self._onboarding_summary(db, tenant),
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
    def _limit(row: dbm.TenantLimit) -> dict[str, object]:
        return {"id": row.id, "tenant_id": row.tenant_id, "limit_key": row.limit_key, "limit_value": row.limit_value, "hard_limit": row.hard_limit}

    @staticmethod
    def _plan(plan: dbm.BillingPlan) -> dict[str, object]:
        return {
            "id": plan.id,
            "code": plan.code,
            "name": plan.name,
            "monthly_price_cents": plan.monthly_price_cents,
            "status": plan.status,
            "trial_days": plan.trial_days,
            "limits": plan.limits_json,
            "features": [feature.feature_key for feature in plan.features if feature.enabled],
        }

    def _plan_catalog_tenant(self, db: Session) -> dbm.Tenant:
        tenant = db.scalar(select(dbm.Tenant).where(dbm.Tenant.slug == OWNER_PLAN_CATALOG_SLUG, dbm.Tenant.deleted_at.is_(None)))
        if tenant:
            return tenant
        tenant = dbm.Tenant(name="LEXFLOW Owner Plan Catalog", slug=OWNER_PLAN_CATALOG_SLUG, plan="ENTERPRISE", status="active")
        db.add(tenant)
        db.flush()
        return tenant

    @staticmethod
    def _replace_plan_features(db: Session, plan: dbm.BillingPlan, features: list[str]) -> None:
        desired = {feature.strip() for feature in features if feature.strip()}
        existing = {feature.feature_key: feature for feature in plan.features}
        for feature_key, row in existing.items():
            row.enabled = feature_key in desired
        for feature_key in desired - set(existing):
            db.add(dbm.PlanFeature(tenant_id=plan.tenant_id, plan_id=plan.id, feature_key=feature_key, enabled=True))

    @staticmethod
    def _intervention(row: dbm.TenantIntervention) -> dict[str, object]:
        return {"id": row.id, "tenant_id": row.tenant_id, "requested_by_email": row.requested_by_email, "approved_by_email": row.approved_by_email, "reason": row.reason, "scopes": row.scopes_json, "status": row.status, "expires_at": row.expires_at.isoformat(), "closed_at": row.closed_at.isoformat() if row.closed_at else None}

    @staticmethod
    def _incident(row: dbm.SystemIncident) -> dict[str, object]:
        return {
            "id": row.id,
            "component": row.component,
            "title": row.title,
            "severity": row.severity,
            "status": row.status,
            "summary": row.summary,
            "created_at": row.created_at.isoformat(),
            "resolved_at": row.resolved_at.isoformat() if row.resolved_at else None,
        }

    @staticmethod
    def _demo(row: dbm.DemoTenant) -> dict[str, object]:
        return {"id": row.id, "tenant_id": row.tenant_id, "demo_type": row.demo_type, "status": row.status, "last_reset_at": row.last_reset_at.isoformat() if row.last_reset_at else None}

    @staticmethod
    def _plan_price_cents(plan: str) -> int:
        return {"START": 9900, "PRO": 24900, "AI": 39900, "ENTERPRISE": 0, "DEMO": 0}.get(plan.upper(), 9900)

    @staticmethod
    def _default_limits_for_plan(plan: str) -> dict[str, int]:
        return {
            "START": {"users": 5, "cases": 100, "documents": 500, "storage_mb": 10240, "ai_tokens": 0, "whatsapp_messages": 0, "sinoe_syncs": 100},
            "PRO": {"users": 20, "cases": 500, "documents": 3000, "storage_mb": 102400, "ai_tokens": 100000, "whatsapp_messages": 1000, "sinoe_syncs": 1000},
            "AI": {"users": 50, "cases": 1500, "documents": 10000, "storage_mb": 512000, "ai_tokens": 500000, "whatsapp_messages": 5000, "sinoe_syncs": 5000},
            "ENTERPRISE": {"users": 999, "cases": 99999, "documents": 999999, "storage_mb": 10485760, "ai_tokens": 9999999, "whatsapp_messages": 999999, "sinoe_syncs": 999999},
        }.get(plan.upper(), {"users": 5, "cases": 100, "documents": 500, "storage_mb": 10240, "ai_tokens": 0, "whatsapp_messages": 0, "sinoe_syncs": 100})


owner_console_service = OwnerConsoleService()
