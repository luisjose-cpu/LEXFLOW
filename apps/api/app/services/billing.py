from __future__ import annotations

import hashlib
import hmac
import json
from datetime import timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import models as dbm
from app.domain.models import User


FEATURE_GATES = [
    "expediente360",
    "client_portal",
    "whatsapp",
    "ai",
    "legal_intelligence",
    "judicial_automation",
    "dashboard",
    "mobile_pwa",
    "automation_studio",
    "custom_branding",
    "custom_domain",
    "api_access",
]

PLAN_CATALOG: dict[str, dict[str, object]] = {
    "START": {
        "name": "Start",
        "description": "Para estudios pequenos que necesitan Expediente 360, portal cliente y PWA.",
        "monthly_price_cents": 4900,
        "trial_days": 14,
        "limits": {"users": 3, "cases": 50, "ai_jobs": 0, "whatsapp_messages": 0, "storage_gb": 10},
        "features": {
            "expediente360": 50,
            "client_portal": 50,
            "mobile_pwa": 50,
            "dashboard": 1,
        },
    },
    "PRO": {
        "name": "Pro",
        "description": "Operacion legal completa con WhatsApp mock, monitoreo judicial y dashboard.",
        "monthly_price_cents": 14900,
        "trial_days": 14,
        "limits": {"users": 12, "cases": 300, "ai_jobs": 50, "whatsapp_messages": 1000, "storage_gb": 100},
        "features": {
            "expediente360": 300,
            "client_portal": 300,
            "whatsapp": 1000,
            "judicial_automation": 300,
            "dashboard": 1,
            "mobile_pwa": 300,
            "automation_studio": 25,
        },
    },
    "AI": {
        "name": "AI",
        "description": "LEXFLOW con IA practica legal, inteligencia juridica y automatizacion ampliada.",
        "monthly_price_cents": 29900,
        "trial_days": 14,
        "limits": {"users": 30, "cases": 1000, "ai_jobs": 500, "whatsapp_messages": 5000, "storage_gb": 500},
        "features": {
            "expediente360": 1000,
            "client_portal": 1000,
            "whatsapp": 5000,
            "ai": 500,
            "legal_intelligence": 1,
            "judicial_automation": 1000,
            "dashboard": 1,
            "mobile_pwa": 1000,
            "automation_studio": 100,
            "custom_branding": 1,
        },
    },
    "ENTERPRISE": {
        "name": "Enterprise",
        "description": "Gobierno, dominio propio, API access y limites acordados por contrato.",
        "monthly_price_cents": 0,
        "trial_days": 30,
        "limits": {"users": None, "cases": None, "ai_jobs": None, "whatsapp_messages": None, "storage_gb": None},
        "features": {feature: None for feature in FEATURE_GATES},
    },
}


class BillingService:
    def ensure_catalog(self, db: Session, *, tenant_id: UUID | str) -> None:
        tenant = str(tenant_id)
        existing = {plan.code: plan for plan in db.scalars(select(dbm.BillingPlan).where(dbm.BillingPlan.tenant_id == tenant)).all()}
        for code, spec in PLAN_CATALOG.items():
            plan = existing.get(code)
            if not plan:
                plan = dbm.BillingPlan(
                    tenant_id=tenant,
                    code=code,
                    name=str(spec["name"]),
                    description=str(spec["description"]),
                    monthly_price_cents=int(spec["monthly_price_cents"]),
                    trial_days=int(spec["trial_days"]),
                    limits_json=spec["limits"],
                )
                db.add(plan)
                db.flush()
            feature_rows = {feature.feature_key: feature for feature in plan.features}
            enabled_features = spec["features"]
            for feature_key in FEATURE_GATES:
                limit_value = enabled_features.get(feature_key) if isinstance(enabled_features, dict) else None
                enabled = feature_key in enabled_features
                row = feature_rows.get(feature_key)
                if row:
                    row.enabled = enabled
                    row.limit_value = limit_value if isinstance(limit_value, int) else None
                else:
                    db.add(
                        dbm.PlanFeature(
                            tenant_id=tenant,
                            plan_id=plan.id,
                            feature_key=feature_key,
                            enabled=enabled,
                            limit_value=limit_value if isinstance(limit_value, int) else None,
                            metadata_json={"unlimited": enabled and limit_value is None},
                        )
                    )

    def list_plans(self, db: Session, *, tenant_id: UUID | str) -> list[dict[str, object]]:
        self.ensure_catalog(db, tenant_id=tenant_id)
        db.flush()
        plans = db.scalars(select(dbm.BillingPlan).where(dbm.BillingPlan.tenant_id == str(tenant_id), dbm.BillingPlan.deleted_at.is_(None))).all()
        return [self.serialize_plan(plan) for plan in sorted(plans, key=lambda item: item.monthly_price_cents)]

    def current(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        subscription = self.ensure_subscription(db, tenant_id=tenant_id)
        return self.serialize_subscription(subscription)

    def subscribe_mock(self, db: Session, *, tenant_id: UUID | str, actor: User, plan_code: str, seats: int, request_id: str | None = None) -> dict[str, object]:
        subscription = self.upsert_subscription(db, tenant_id=tenant_id, actor=actor, plan_code=plan_code, seats=seats, status_value="trialing", request_id=request_id, event_type="subscribe_mock")
        return self.serialize_subscription(subscription)

    def change_plan(self, db: Session, *, tenant_id: UUID | str, actor: User, plan_code: str, seats: int | None = None, request_id: str | None = None) -> dict[str, object]:
        current = self.ensure_subscription(db, tenant_id=tenant_id)
        subscription = self.upsert_subscription(
            db,
            tenant_id=tenant_id,
            actor=actor,
            plan_code=plan_code,
            seats=seats or current.seats,
            status_value="active",
            request_id=request_id,
            event_type="change_plan",
        )
        return self.serialize_subscription(subscription)

    def usage(self, db: Session, *, tenant_id: UUID | str) -> list[dict[str, object]]:
        subscription = self.ensure_subscription(db, tenant_id=tenant_id)
        features = {feature.feature_key: feature for feature in subscription.plan.features}
        period_key = dbm.now_utc().strftime("%Y-%m")
        rows = db.scalars(select(dbm.TenantUsage).where(dbm.TenantUsage.tenant_id == str(tenant_id), dbm.TenantUsage.period_key == period_key)).all()
        existing = {row.feature_key: row for row in rows}
        defaults = {"expediente360": 3, "client_portal": 1, "whatsapp": 8, "ai": 6, "legal_intelligence": 4, "judicial_automation": 2, "mobile_pwa": 12}
        for feature_key, used in defaults.items():
            if feature_key not in existing:
                feature = features.get(feature_key)
                row = dbm.TenantUsage(
                    tenant_id=str(tenant_id),
                    feature_key=feature_key,
                    period_key=period_key,
                    used=used if feature and feature.enabled else 0,
                    limit_value=feature.limit_value if feature and feature.enabled else 0,
                    metadata_json={"source": "mock_meter"},
                )
                db.add(row)
                existing[feature_key] = row
        db.flush()
        return [self.serialize_usage(row) for row in sorted(existing.values(), key=lambda item: item.feature_key)]

    def features(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        subscription = self.ensure_subscription(db, tenant_id=tenant_id)
        usage_by_feature = {item["feature_key"]: item for item in self.usage(db, tenant_id=tenant_id)}
        return {
            "plan": subscription.plan.code,
            "features": [
                {
                    "feature_key": feature.feature_key,
                    "enabled": feature.enabled,
                    "limit_value": feature.limit_value,
                    "unlimited": feature.enabled and feature.limit_value is None,
                    "used": usage_by_feature.get(feature.feature_key, {}).get("used", 0),
                    "upgrade_required": not feature.enabled,
                }
                for feature in sorted(subscription.plan.features, key=lambda item: item.feature_key)
            ],
        }

    def webhook_mock(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        actor: User,
        event_type: str,
        payload: dict[str, object],
        idempotency_key: str | None = None,
        signature: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, object]:
        try:
            self.verify_webhook_signature(event_type=event_type, payload=payload, idempotency_key=idempotency_key, signature=signature)
        except HTTPException:
            self.record_audit(
                db,
                tenant_id=tenant_id,
                actor=actor,
                action="billing.webhook_signature_invalid",
                entity_type="billing_event",
                entity_id=str(tenant_id),
                request_id=request_id,
                metadata={"event_type": event_type, "idempotency_key": idempotency_key or ""},
            )
            db.commit()
            raise
        subscription = self.ensure_subscription(db, tenant_id=tenant_id)
        if idempotency_key:
            existing_events = db.scalars(select(dbm.BillingEvent).where(dbm.BillingEvent.tenant_id == str(tenant_id), dbm.BillingEvent.event_type == event_type)).all()
            existing = next((event for event in existing_events if event.payload_json.get("idempotency_key") == idempotency_key), None)
            if existing:
                self.record_audit(
                    db,
                    tenant_id=tenant_id,
                    actor=actor,
                    action="billing.webhook_mock_duplicate",
                    entity_type="billing_event",
                    entity_id=existing.id,
                    request_id=request_id,
                    metadata={"event_type": event_type, "idempotency_key": idempotency_key},
                )
                db.commit()
                return {"id": existing.id, "status": "duplicate", "event_type": existing.event_type}
        event_payload = dict(payload)
        if idempotency_key:
            event_payload["idempotency_key"] = idempotency_key
        event = dbm.BillingEvent(tenant_id=str(tenant_id), subscription_id=subscription.id, event_type=event_type, status="processed", payload_json=event_payload)
        db.add(event)
        db.flush()
        self.record_audit(db, tenant_id=tenant_id, actor=actor, action="billing.webhook_mock", entity_type="billing_event", entity_id=event.id, request_id=request_id, metadata={"event_type": event_type, "idempotency_key": idempotency_key or ""})
        db.commit()
        return {"id": event.id, "status": event.status, "event_type": event.event_type}

    def verify_webhook_signature(self, *, event_type: str, payload: dict[str, object], idempotency_key: str | None, signature: str | None) -> None:
        settings = get_settings()
        if not settings.require_billing_webhook_signature:
            return
        secret = settings.billing_provider_secret
        if not secret:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Billing webhook signature secret is not configured")
        expected = self.webhook_signature(event_type=event_type, payload=payload, idempotency_key=idempotency_key, secret=secret)
        if not signature or not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid billing webhook signature")

    @staticmethod
    def webhook_signature(*, event_type: str, payload: dict[str, object], idempotency_key: str | None, secret: str) -> str:
        canonical = json.dumps(
            {"event_type": event_type, "idempotency_key": idempotency_key or "", "payload": payload},
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"sha256={digest}"

    def ensure_subscription(self, db: Session, *, tenant_id: UUID | str) -> dbm.TenantSubscription:
        self.ensure_catalog(db, tenant_id=tenant_id)
        subscription = db.scalars(
            select(dbm.TenantSubscription)
            .where(dbm.TenantSubscription.tenant_id == str(tenant_id), dbm.TenantSubscription.deleted_at.is_(None))
            .order_by(dbm.TenantSubscription.created_at.desc())
        ).first()
        if subscription:
            return subscription
        start_plan = self.get_plan(db, tenant_id=tenant_id, plan_code="START")
        subscription = dbm.TenantSubscription(
            tenant_id=str(tenant_id),
            plan_id=start_plan.id,
            status="trialing",
            seats=3,
            trial_ends_at=dbm.now_utc() + timedelta(days=start_plan.trial_days),
            current_period_ends_at=dbm.now_utc() + timedelta(days=30),
            provider_subscription_id=f"mock-sub-{str(tenant_id)[:8]}",
            metadata_json={"source": "auto_trial"},
        )
        db.add(subscription)
        db.flush()
        return subscription

    def upsert_subscription(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        actor: User,
        plan_code: str,
        seats: int,
        status_value: str,
        event_type: str,
        request_id: str | None,
    ) -> dbm.TenantSubscription:
        if seats < 1:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="At least one seat is required")
        plan = self.get_plan(db, tenant_id=tenant_id, plan_code=plan_code)
        subscription = self.ensure_subscription(db, tenant_id=tenant_id)
        subscription.plan_id = plan.id
        subscription.status = status_value
        subscription.seats = seats
        subscription.current_period_ends_at = dbm.now_utc() + timedelta(days=30)
        if status_value == "trialing":
            subscription.trial_ends_at = dbm.now_utc() + timedelta(days=plan.trial_days)
        event = dbm.BillingEvent(
            tenant_id=str(tenant_id),
            subscription_id=subscription.id,
            event_type=event_type,
            status="processed",
            payload_json={"plan_code": plan.code, "seats": seats, "provider": "mock"},
        )
        invoice = dbm.Invoice(
            tenant_id=str(tenant_id),
            subscription_id=subscription.id,
            invoice_number=f"MOCK-{dbm.now_utc().strftime('%Y%m%d%H%M%S')}-{plan.code}",
            status="open" if plan.monthly_price_cents else "quote_required",
            amount_due_cents=plan.monthly_price_cents * seats,
            due_at=dbm.now_utc() + timedelta(days=15),
            metadata_json={"mock": True, "plan_code": plan.code},
        )
        db.add_all([event, invoice])
        db.flush()
        self.record_audit(db, tenant_id=tenant_id, actor=actor, action=f"billing.{event_type}", entity_type="tenant_subscription", entity_id=subscription.id, request_id=request_id, metadata={"plan_code": plan.code, "seats": str(seats)})
        db.commit()
        db.refresh(subscription)
        return subscription

    def get_plan(self, db: Session, *, tenant_id: UUID | str, plan_code: str) -> dbm.BillingPlan:
        self.ensure_catalog(db, tenant_id=tenant_id)
        plan = db.scalars(select(dbm.BillingPlan).where(dbm.BillingPlan.tenant_id == str(tenant_id), dbm.BillingPlan.code == plan_code.upper())).first()
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        return plan

    def serialize_plan(self, plan: dbm.BillingPlan) -> dict[str, object]:
        return {
            "id": plan.id,
            "code": plan.code,
            "name": plan.name,
            "description": plan.description,
            "monthly_price_cents": plan.monthly_price_cents,
            "trial_days": plan.trial_days,
            "limits": plan.limits_json,
            "features": [self.serialize_feature(feature) for feature in sorted(plan.features, key=lambda item: item.feature_key)],
        }

    def serialize_feature(self, feature: dbm.PlanFeature) -> dict[str, object]:
        return {
            "feature_key": feature.feature_key,
            "enabled": feature.enabled,
            "limit_value": feature.limit_value,
            "unlimited": feature.enabled and feature.limit_value is None,
        }

    def serialize_subscription(self, subscription: dbm.TenantSubscription) -> dict[str, object]:
        return {
            "id": subscription.id,
            "tenant_id": subscription.tenant_id,
            "status": subscription.status,
            "seats": subscription.seats,
            "provider": subscription.provider,
            "provider_subscription_id": subscription.provider_subscription_id,
            "trial_ends_at": subscription.trial_ends_at.isoformat() if subscription.trial_ends_at else None,
            "current_period_ends_at": subscription.current_period_ends_at.isoformat() if subscription.current_period_ends_at else None,
            "plan": self.serialize_plan(subscription.plan),
            "latest_invoice": self.serialize_invoice(subscription.invoices[-1]) if subscription.invoices else None,
        }

    def serialize_usage(self, row: dbm.TenantUsage) -> dict[str, object]:
        return {"feature_key": row.feature_key, "period_key": row.period_key, "used": row.used, "limit_value": row.limit_value}

    def serialize_invoice(self, invoice: dbm.Invoice) -> dict[str, object]:
        return {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "status": invoice.status,
            "amount_due_cents": invoice.amount_due_cents,
            "currency": invoice.currency,
            "due_at": invoice.due_at.isoformat() if invoice.due_at else None,
        }

    def record_audit(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        actor: User,
        action: str,
        entity_type: str,
        entity_id: str,
        request_id: str | None,
        metadata: dict[str, object],
    ) -> None:
        db.add(
            dbm.AuditLog(
                tenant_id=str(tenant_id),
                actor_user_id=str(actor.id),
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                request_id=request_id,
                metadata_json=metadata,
            )
        )


billing_service = BillingService()
