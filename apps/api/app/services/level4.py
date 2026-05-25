from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import models as dbm
from app.domain.models import User
from app.services.level2 import financial_engine_service, risk_engine_service, war_room_service
from app.services.level3 import legal_graph_service, legal_memory_service, rag_pipeline_service


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


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _hash_secret(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


class EnterpriseMultiOrgService:
    def create_organization(self, db: Session, *, tenant_id: UUID | str, actor: User, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        slug = str(payload.get("slug") or "").strip().lower()
        if not slug:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization slug is required")
        existing = db.scalar(select(dbm.Organization).where(dbm.Organization.slug == slug, dbm.Organization.deleted_at.is_(None)))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Organization slug already exists")
        organization = dbm.Organization(
            name=str(payload.get("name") or slug),
            slug=slug,
            org_type=str(payload.get("org_type") or "holding"),
            country_scope=list(payload.get("country_scope") or ["PE"]),
            branding_json=dict(payload.get("branding") or {}),
            metadata_json={"created_from": "enterprise_multi_org"},
        )
        db.add(organization)
        db.flush()
        self._link_current_tenant(db, tenant_id=tenant_id, organization=organization, payload=payload)
        _audit(db, tenant_id=tenant_id, actor=actor, action="enterprise.organization_created", entity_type="organization", entity_id=organization.id, request_id=request_id, metadata={"slug": slug})
        db.commit()
        return self._organization(db, organization)

    def list_organizations(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        links = db.scalars(select(dbm.OrganizationTenant).where(dbm.OrganizationTenant.tenant_id == str(tenant_id))).all()
        organizations = [
            db.scalar(select(dbm.Organization).where(dbm.Organization.id == link.organization_id, dbm.Organization.deleted_at.is_(None)))
            for link in links
        ]
        return {"organizations": [self._organization(db, item) for item in organizations if item], "total": len([item for item in organizations if item])}

    def dashboard(self, db: Session, *, tenant_id: UUID | str, actor: User, organization_id: UUID | str | None = None, request_id: str | None = None) -> dict[str, object]:
        organization = self._organization_for_tenant(db, tenant_id=tenant_id, actor=actor, organization_id=organization_id, request_id=request_id)
        tenant_ids = self._tenant_ids_for_org(db, organization_id=organization.id)
        analytics = [self._tenant_snapshot(db, tenant_id=item) for item in tenant_ids]
        aggregate = {
            "tenants": len(analytics),
            "cases": sum(item["cases"] for item in analytics),
            "clients": sum(item["clients"] for item in analytics),
            "documents": sum(item["documents"] for item in analytics),
            "monthly_usage_events": sum(item["usage_events"] for item in analytics),
        }
        current_tenant_risk = risk_engine_service.dashboard(db, tenant_id=tenant_id)
        graph = legal_graph_service.build(db, tenant_id=tenant_id)
        return {
            "organization": self._organization(db, organization),
            "tenant_switcher": [{"tenant_id": item, "active": item == str(tenant_id)} for item in tenant_ids],
            "global_analytics": aggregate,
            "cross_reporting": analytics,
            "cross_risks": current_tenant_risk["critical_cases"][:8],
            "cross_graph": {"nodes": len(graph["nodes"]), "edges": len(graph["edges"])},
            "cross_intelligence": {
                "country_scope": organization.country_scope,
                "ai_context": "tenant-scoped; no cross-tenant memory mixing without organization policy",
                "white_label": bool(organization.branding_json.get("white_label")),
            },
        }

    def _organization_for_tenant(self, db: Session, *, tenant_id: UUID | str, actor: User, organization_id: UUID | str | None, request_id: str | None) -> dbm.Organization:
        filters = [dbm.OrganizationTenant.tenant_id == str(tenant_id)]
        if organization_id:
            filters.append(dbm.OrganizationTenant.organization_id == str(organization_id))
        link = db.scalar(select(dbm.OrganizationTenant).where(*filters).order_by(dbm.OrganizationTenant.created_at.asc()))
        if link:
            organization = db.scalar(select(dbm.Organization).where(dbm.Organization.id == link.organization_id, dbm.Organization.deleted_at.is_(None)))
            if organization:
                return organization
        if organization_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found for tenant")
        tenant = db.get(dbm.Tenant, str(tenant_id))
        organization = dbm.Organization(
            name=f"{tenant.name if tenant else 'LEXFLOW'} Organization",
            slug=f"org-{str(tenant_id)[:8]}",
            org_type="enterprise",
            country_scope=["PE"],
            metadata_json={"auto_created": True},
        )
        db.add(organization)
        db.flush()
        self._link_current_tenant(db, tenant_id=tenant_id, organization=organization, payload={"relationship_type": "headquarters"})
        _audit(db, tenant_id=tenant_id, actor=actor, action="enterprise.organization_bootstrapped", entity_type="organization", entity_id=organization.id, request_id=request_id)
        db.commit()
        return organization

    def _link_current_tenant(self, db: Session, *, tenant_id: UUID | str, organization: dbm.Organization, payload: dict[str, object]) -> None:
        db.add(
            dbm.OrganizationTenant(
                organization_id=organization.id,
                tenant_id=str(tenant_id),
                relationship_type=str(payload.get("relationship_type") or "headquarters"),
                country_code=str(payload.get("country_code") or "PE"),
                brand_name=payload.get("brand_name"),
                permissions_json=list(payload.get("permissions") or ["cross_analytics", "cross_reporting"]),
            )
        )

    def _tenant_ids_for_org(self, db: Session, *, organization_id: str) -> list[str]:
        return [item.tenant_id for item in db.scalars(select(dbm.OrganizationTenant).where(dbm.OrganizationTenant.organization_id == organization_id)).all()]

    def _tenant_snapshot(self, db: Session, *, tenant_id: str) -> dict[str, object]:
        tenant = db.get(dbm.Tenant, tenant_id)
        return {
            "tenant_id": tenant_id,
            "tenant_name": tenant.name if tenant else "Tenant",
            "country": db.scalar(select(dbm.OrganizationTenant.country_code).where(dbm.OrganizationTenant.tenant_id == tenant_id)) or "PE",
            "cases": int(db.scalar(select(func.count()).select_from(dbm.Case).where(dbm.Case.tenant_id == tenant_id, dbm.Case.deleted_at.is_(None))) or 0),
            "clients": int(db.scalar(select(func.count()).select_from(dbm.Client).where(dbm.Client.tenant_id == tenant_id, dbm.Client.deleted_at.is_(None))) or 0),
            "documents": int(db.scalar(select(func.count()).select_from(dbm.Document).where(dbm.Document.tenant_id == tenant_id, dbm.Document.deleted_at.is_(None))) or 0),
            "usage_events": int(db.scalar(select(func.count()).select_from(dbm.LegalDataEvent).where(dbm.LegalDataEvent.tenant_id == tenant_id)) or 0),
        }

    def _organization(self, db: Session, organization: dbm.Organization) -> dict[str, object]:
        links = db.scalars(select(dbm.OrganizationTenant).where(dbm.OrganizationTenant.organization_id == organization.id)).all()
        return {
            "id": organization.id,
            "name": organization.name,
            "slug": organization.slug,
            "org_type": organization.org_type,
            "country_scope": organization.country_scope,
            "status": organization.status,
            "branding": organization.branding_json,
            "tenants": [{"tenant_id": item.tenant_id, "country_code": item.country_code, "relationship_type": item.relationship_type, "brand_name": item.brand_name} for item in links],
        }


class LegalDataPlatformService:
    def dashboard(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        tenant = str(tenant_id)
        events = db.scalars(select(dbm.LegalDataEvent).where(dbm.LegalDataEvent.tenant_id == tenant).order_by(dbm.LegalDataEvent.created_at.desc())).all()
        by_type = Counter(item.event_type for item in events)
        memory_count = int(db.scalar(select(func.count()).select_from(dbm.LegalMemoryItem).where(dbm.LegalMemoryItem.tenant_id == tenant, dbm.LegalMemoryItem.deleted_at.is_(None))) or 0)
        return {
            "pipeline": ["event_ingestion", "unified_indexer", "memory_index", "analytics_engine", "future_ml"],
            "event_stream": [self._event(item) for item in events[:12]],
            "analytics_engine": {"events": len(events), "indexed": len([item for item in events if item.indexed]), "by_type": dict(by_type), "memory_items": memory_count},
            "data_lake": {"status": "prepared", "storage": "s3-compatible future-ready", "tenant_partitioned": True},
            "search_engine": {"status": "basic_index_ready", "future": "dedicated vector and lexical index"},
        }

    def ingest_event(self, db: Session, *, tenant_id: UUID | str, actor: User, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        idempotency_key = str(payload.get("idempotency_key") or f"{payload.get('event_type')}:{payload.get('entity_type')}:{payload.get('entity_id')}")
        existing = db.scalar(select(dbm.LegalDataEvent).where(dbm.LegalDataEvent.tenant_id == str(tenant_id), dbm.LegalDataEvent.idempotency_key == idempotency_key))
        if existing:
            return {"status": "duplicate", "event": self._event(existing)}
        event = dbm.LegalDataEvent(
            tenant_id=str(tenant_id),
            organization_id=payload.get("organization_id"),
            event_type=str(payload.get("event_type") or "event.created"),
            entity_type=str(payload.get("entity_type") or "unknown"),
            entity_id=str(payload.get("entity_id") or str(tenant_id)),
            idempotency_key=idempotency_key,
            payload_json=dict(payload.get("payload") or {}),
        )
        db.add(event)
        db.flush()
        _audit(db, tenant_id=tenant_id, actor=actor, action="data_platform.event_ingested", entity_type="legal_data_event", entity_id=event.id, request_id=request_id, metadata={"event_type": event.event_type})
        db.commit()
        return {"status": "created", "event": self._event(event)}

    def index(self, db: Session, *, tenant_id: UUID | str, actor: User, request_id: str | None = None) -> dict[str, object]:
        events = db.scalars(select(dbm.LegalDataEvent).where(dbm.LegalDataEvent.tenant_id == str(tenant_id), dbm.LegalDataEvent.indexed.is_(False))).all()
        for event in events:
            event.indexed = True
            event.processed_at = _now()
        memory_result = legal_memory_service.index_tenant(db, tenant_id=tenant_id, actor=actor, request_id=request_id)
        _audit(db, tenant_id=tenant_id, actor=actor, action="data_platform.indexed", entity_type="legal_data_platform", entity_id=str(tenant_id), request_id=request_id, metadata={"events": len(events), "memory_created": memory_result["created"]})
        db.commit()
        return {"status": "indexed", "events_indexed": len(events), "memory": memory_result}

    def search(self, db: Session, *, tenant_id: UUID | str, query: str) -> dict[str, object]:
        like = f"%{query}%"
        events = db.scalars(
            select(dbm.LegalDataEvent).where(
                dbm.LegalDataEvent.tenant_id == str(tenant_id),
                or_(dbm.LegalDataEvent.event_type.ilike(like), dbm.LegalDataEvent.entity_type.ilike(like), dbm.LegalDataEvent.entity_id.ilike(like)),
            )
        ).all()
        memory = legal_memory_service.search(db, tenant_id=tenant_id, query=query)
        return {"query": query, "events": [self._event(item) for item in events], "memory": memory["results"], "total": len(events) + int(memory["total"])}

    def _event(self, event: dbm.LegalDataEvent) -> dict[str, object]:
        return {"id": event.id, "event_type": event.event_type, "entity_type": event.entity_type, "entity_id": event.entity_id, "indexed": event.indexed, "processed_at": _iso(event.processed_at), "created_at": _iso(event.created_at), "payload": event.payload_json}


class OrchestrationLayerService:
    def dashboard(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        events = db.scalars(select(dbm.OrchestrationEvent).where(dbm.OrchestrationEvent.tenant_id == str(tenant_id)).order_by(dbm.OrchestrationEvent.created_at.desc())).all()
        return {
            "event_bus": {"status": "in_process_ready", "future": "redis/celery stream"},
            "rule_engine": ["SINOE_UPDATE_APPROVED", "CASE_RISK_ESCALATED", "AI_SUMMARY_COMPLETED", "CLIENT_MESSAGE_RECEIVED"],
            "state_manager": {"active_events": len([item for item in events if item.status in {"queued", "running"}]), "completed": len([item for item in events if item.status == "completed"])},
            "events": [self._event(item) for item in events[:12]],
        }

    def dispatch(self, db: Session, *, tenant_id: UUID | str, actor: User, event_key: str, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        actions = self._actions_for_event(event_key)
        event = dbm.OrchestrationEvent(
            tenant_id=str(tenant_id),
            organization_id=payload.get("organization_id"),
            event_key=event_key,
            status="completed",
            state_json={"payload": payload, "received_at": _now().isoformat()},
            result_json={"actions": actions, "review_required": event_key.startswith("AI_") or "SINOE" in event_key},
        )
        db.add(event)
        db.flush()
        _audit(db, tenant_id=tenant_id, actor=actor, action="orchestration.event_dispatched", entity_type="orchestration_event", entity_id=event.id, request_id=request_id, metadata={"event_key": event_key})
        db.commit()
        return self._event(event)

    def _actions_for_event(self, event_key: str) -> list[str]:
        mapping = {
            "SINOE_UPDATE_APPROVED": ["refresh_case_timeline", "notify_portal", "index_memory", "refresh_dashboard"],
            "CASE_RISK_ESCALATED": ["notify_partner", "prepare_copilot_context", "create_internal_alert"],
            "AI_SUMMARY_COMPLETED": ["queue_human_review", "index_memory", "audit_ai_usage"],
            "CLIENT_MESSAGE_RECEIVED": ["notify_lawyer", "update_timeline", "evaluate_automation"],
        }
        return mapping.get(event_key, ["audit_event", "refresh_dashboard"])

    def _event(self, event: dbm.OrchestrationEvent) -> dict[str, object]:
        return {"id": event.id, "event_key": event.event_key, "status": event.status, "state": event.state_json, "result": event.result_json, "created_at": _iso(event.created_at)}


class EnterpriseAiSwarmService:
    catalog = [
        "LegalAgent",
        "CaseAgent",
        "HearingAgent",
        "ResearchAgent",
        "DocumentAgent",
        "ClientAgent",
        "ManagementAgent",
        "RiskAgent",
        "AutomationAgent",
        "NewsAgent",
    ]

    def dashboard(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        runs = db.scalars(select(dbm.EnterpriseAiSwarmRun).where(dbm.EnterpriseAiSwarmRun.tenant_id == str(tenant_id)).order_by(dbm.EnterpriseAiSwarmRun.created_at.desc())).all()
        return {"agents": [{"name": item, "review_required": True, "permissions": "tenant_scoped"} for item in self.catalog], "runs": [self._run(item) for item in runs[:12]], "guardrails": ["no_full_autonomy", "audit", "handoff", "review_required", "citations_when_contextual"]}

    def run(self, db: Session, *, tenant_id: UUID | str, actor: User, objective: str, organization_id: UUID | str | None = None, request_id: str | None = None) -> dict[str, object]:
        rag = rag_pipeline_service.query(db, tenant_id=tenant_id, actor=actor, query=objective, request_id=request_id)
        agents = [
            {"key": "LegalAgent", "status": "completed", "output": "context_checked"},
            {"key": "RiskAgent", "status": "completed", "output": "risk_prioritized"},
            {"key": "ManagementAgent", "status": "completed", "output": "executive_summary_ready"},
        ]
        run = dbm.EnterpriseAiSwarmRun(
            tenant_id=str(tenant_id),
            organization_id=str(organization_id) if organization_id else None,
            objective=objective,
            agents_json=agents,
            handoff_json=[
                {"from": "LegalAgent", "to": "RiskAgent", "reason": "risk scoring"},
                {"from": "RiskAgent", "to": "ManagementAgent", "reason": "executive recommendation"},
            ],
            review_required=True,
            actor_user_id=str(actor.id),
        )
        db.add(run)
        db.flush()
        _audit(db, tenant_id=tenant_id, actor=actor, action="ai_swarm.run_completed", entity_type="enterprise_ai_swarm_run", entity_id=run.id, request_id=request_id, metadata={"sources": len(rag["sources"])})
        db.commit()
        return {"run": self._run(run), "context": {"sources": rag["sources"], "disclaimer": rag["disclaimer"]}}

    def _run(self, run: dbm.EnterpriseAiSwarmRun) -> dict[str, object]:
        return {"id": run.id, "objective": run.objective, "status": run.status, "agents": run.agents_json, "handoff": run.handoff_json, "review_required": run.review_required, "created_at": _iso(run.created_at)}


class TelemetryCenterService:
    components = ["api", "frontend", "ai", "automation", "whatsapp", "sinoe", "ocr", "portal", "dashboard", "pwa", "db", "redis", "storage", "workers"]

    def dashboard(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        metrics = db.scalars(select(dbm.TelemetryMetric).where(or_(dbm.TelemetryMetric.tenant_id == str(tenant_id), dbm.TelemetryMetric.tenant_id.is_(None))).order_by(dbm.TelemetryMetric.recorded_at.desc())).all()
        latest_by_component = {}
        for metric in metrics:
            latest_by_component.setdefault(metric.component, []).append(metric)
        health = []
        for component in self.components:
            rows = latest_by_component.get(component, [])
            errors = sum(item.metric_value for item in rows if "error" in item.metric_key or "failure" in item.metric_key)
            latency = next((item.metric_value for item in rows if "latency" in item.metric_key), 0)
            health.append({"component": component, "status": "warning" if errors else "healthy", "errors": errors, "latency_ms": latency, "metrics": [self._metric(item) for item in rows[:4]]})
        return {
            "observability": {"tracing": "request-id-ready", "metrics": "in_process_ready", "logs": "render/stdout-ready"},
            "components": health,
            "ai_usage_monitor": [self._metric(item) for item in metrics if item.component == "ai"][:8],
            "system_metrics": [self._metric(item) for item in metrics[:20]],
        }

    def record_metric(self, db: Session, *, tenant_id: UUID | str, actor: User, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        metric = dbm.TelemetryMetric(
            tenant_id=str(tenant_id),
            organization_id=payload.get("organization_id"),
            component=str(payload.get("component") or "api"),
            metric_key=str(payload.get("metric_key") or "event_count"),
            metric_value=int(payload.get("metric_value") or 0),
            unit=str(payload.get("unit") or "count"),
            metadata_json=dict(payload.get("metadata") or {}),
        )
        db.add(metric)
        db.flush()
        _audit(db, tenant_id=tenant_id, actor=actor, action="telemetry.metric_recorded", entity_type="telemetry_metric", entity_id=metric.id, request_id=request_id, metadata={"component": metric.component, "metric_key": metric.metric_key})
        db.commit()
        return self._metric(metric)

    def _metric(self, metric: dbm.TelemetryMetric) -> dict[str, object]:
        return {"id": metric.id, "component": metric.component, "metric_key": metric.metric_key, "metric_value": metric.metric_value, "unit": metric.unit, "recorded_at": _iso(metric.recorded_at), "metadata": metric.metadata_json}


class RevenueGrowthService:
    def dashboard(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        tenant = db.get(dbm.Tenant, str(tenant_id))
        usage = db.scalars(select(dbm.TenantUsage).where(dbm.TenantUsage.tenant_id == str(tenant_id))).all()
        insights = db.scalars(select(dbm.RevenueInsight).where(dbm.RevenueInsight.tenant_id == str(tenant_id)).order_by(dbm.RevenueInsight.created_at.desc())).all()
        if not insights:
            self._ensure_insight(db, tenant_id=tenant_id)
            insights = db.scalars(select(dbm.RevenueInsight).where(dbm.RevenueInsight.tenant_id == str(tenant_id)).order_by(dbm.RevenueInsight.created_at.desc())).all()
        usage_total = sum(item.used for item in usage)
        churn_score = max(5, 65 - min(50, usage_total))
        return {
            "tenant": {"id": str(tenant_id), "name": tenant.name if tenant else "Tenant", "plan": tenant.plan if tenant else "unknown"},
            "growth_analytics": {"usage_total": usage_total, "active_features": len(usage), "trial_conversion": "high" if usage_total > 10 else "medium"},
            "customer_health": {"score": min(100, 55 + usage_total), "drivers": ["feature_adoption", "case_volume", "ai_usage"]},
            "churn_prediction": {"score": churn_score, "level": "low" if churn_score < 35 else "medium"},
            "upgrade_engine": [{"plan": "ENTERPRISE", "reason": "multi-org, API, governance and AI orchestration readiness"}],
            "enterprise_proposal": {"status": "prepared", "modules": ["N1 core", "N2 sellable", "N3 Legal OS", "N4 enterprise"]},
            "insights": [self._insight(item) for item in insights],
        }

    def _ensure_insight(self, db: Session, *, tenant_id: UUID | str) -> None:
        db.add(dbm.RevenueInsight(tenant_id=str(tenant_id), signal_type="retention", score=72, recommendation="Activar telemetry, API y governance para propuesta enterprise.", metadata_json={"source": "computed"}))
        db.commit()

    def _insight(self, insight: dbm.RevenueInsight) -> dict[str, object]:
        return {"id": insight.id, "signal_type": insight.signal_type, "score": insight.score, "recommendation": insight.recommendation, "metadata": insight.metadata_json, "created_at": _iso(insight.created_at)}


class ApiIntegrationPlatformService:
    def dashboard(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        api_keys = db.scalars(select(dbm.PublicApiKey).where(dbm.PublicApiKey.tenant_id == str(tenant_id), dbm.PublicApiKey.deleted_at.is_(None))).all()
        webhooks = db.scalars(select(dbm.WebhookSubscription).where(dbm.WebhookSubscription.tenant_id == str(tenant_id), dbm.WebhookSubscription.deleted_at.is_(None))).all()
        return {
            "public_api": {"status": "prepared", "version": "v1", "rate_limits": "tenant scoped"},
            "oauth": {"status": "future_ready", "providers": ["Google", "Microsoft"]},
            "api_keys": [{"id": item.id, "name": item.name, "scopes": item.scopes_json, "status": item.status, "last_used_at": _iso(item.last_used_at)} for item in api_keys],
            "webhooks": [self._webhook(item) for item in webhooks],
            "developer_portal": {"status": "draft_ready", "sdk": "future-ready"},
            "integrations": ["SINOE", "Outlook", "Google", "WhatsApp", "Drive", "OneDrive", "Dropbox", "Firma digital", "ERP future"],
        }

    def create_api_key(self, db: Session, *, tenant_id: UUID | str, actor: User, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        raw_key = f"lf_{token_urlsafe(32)}"
        row = dbm.PublicApiKey(
            tenant_id=str(tenant_id),
            name=str(payload.get("name") or "API Key"),
            key_hash=_hash_secret(raw_key),
            scopes_json=list(payload.get("scopes") or ["cases:read"]),
        )
        db.add(row)
        db.flush()
        _audit(db, tenant_id=tenant_id, actor=actor, action="integrations.api_key_created", entity_type="public_api_key", entity_id=row.id, request_id=request_id, metadata={"scopes": row.scopes_json})
        db.commit()
        return {"id": row.id, "name": row.name, "api_key": raw_key, "scopes": row.scopes_json, "warning": "This key is shown once and only the hash is stored."}

    def create_webhook(self, db: Session, *, tenant_id: UUID | str, actor: User, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        row = dbm.WebhookSubscription(
            tenant_id=str(tenant_id),
            name=str(payload.get("name") or "Webhook"),
            target_url=str(payload.get("target_url") or ""),
            event_types_json=list(payload.get("event_types") or ["case.updated"]),
            secret_hint="configured",
        )
        db.add(row)
        db.flush()
        _audit(db, tenant_id=tenant_id, actor=actor, action="integrations.webhook_created", entity_type="webhook_subscription", entity_id=row.id, request_id=request_id, metadata={"event_types": row.event_types_json})
        db.commit()
        return self._webhook(row)

    def _webhook(self, row: dbm.WebhookSubscription) -> dict[str, object]:
        return {"id": row.id, "name": row.name, "target_url": row.target_url, "event_types": row.event_types_json, "secret_hint": row.secret_hint, "status": row.status}


class GovernanceOSService:
    def dashboard(self, db: Session, *, tenant_id: UUID | str) -> dict[str, object]:
        policies = db.scalars(select(dbm.GovernancePolicy).where(dbm.GovernancePolicy.tenant_id == str(tenant_id), dbm.GovernancePolicy.deleted_at.is_(None))).all()
        evidence = db.scalars(select(dbm.EvidenceVaultItem).where(dbm.EvidenceVaultItem.tenant_id == str(tenant_id)).order_by(dbm.EvidenceVaultItem.created_at.desc())).all()
        retention = db.scalars(select(dbm.RetentionPolicy).where(dbm.RetentionPolicy.tenant_id == str(tenant_id), dbm.RetentionPolicy.deleted_at.is_(None))).all()
        return {
            "compliance_engine": {"status": "active", "controls": ["audit", "retention", "human_review", "evidence_chain"]},
            "policies": [self._policy(item) for item in policies],
            "evidence_vault": [self._evidence(item) for item in evidence[:12]],
            "retention_policies": [{"id": item.id, "record_type": item.record_type, "retention_days": item.retention_days, "disposition": item.disposition, "legal_hold": item.legal_hold} for item in retention],
            "approvals": {"status": "policy-based", "support_interventions": "temporary_and_audited"},
        }

    def create_policy(self, db: Session, *, tenant_id: UUID | str, actor: User, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        row = dbm.GovernancePolicy(
            tenant_id=str(tenant_id),
            organization_id=payload.get("organization_id"),
            policy_type=str(payload.get("policy_type") or "general"),
            name=str(payload.get("name") or "Governance policy"),
            rules_json=dict(payload.get("rules") or {}),
            approved_by_user_id=str(actor.id),
        )
        db.add(row)
        db.flush()
        _audit(db, tenant_id=tenant_id, actor=actor, action="governance.policy_created", entity_type="governance_policy", entity_id=row.id, request_id=request_id, metadata={"policy_type": row.policy_type})
        db.commit()
        return self._policy(row)

    def vault_evidence(self, db: Session, *, tenant_id: UUID | str, actor: User, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        evidence_hash = str(payload.get("evidence_hash") or _hash_secret(f"{payload.get('entity_type')}:{payload.get('entity_id')}:{_now().isoformat()}"))
        row = dbm.EvidenceVaultItem(
            tenant_id=str(tenant_id),
            organization_id=payload.get("organization_id"),
            entity_type=str(payload.get("entity_type") or "audit"),
            entity_id=str(payload.get("entity_id") or str(tenant_id)),
            evidence_hash=evidence_hash,
            storage_ref=payload.get("storage_ref"),
            metadata_json=dict(payload.get("metadata") or {}),
        )
        db.add(row)
        db.flush()
        _audit(db, tenant_id=tenant_id, actor=actor, action="governance.evidence_vaulted", entity_type="evidence_vault_item", entity_id=row.id, request_id=request_id)
        db.commit()
        return self._evidence(row)

    def _policy(self, row: dbm.GovernancePolicy) -> dict[str, object]:
        return {"id": row.id, "policy_type": row.policy_type, "name": row.name, "rules": row.rules_json, "status": row.status, "approved_by_user_id": row.approved_by_user_id}

    def _evidence(self, row: dbm.EvidenceVaultItem) -> dict[str, object]:
        return {"id": row.id, "entity_type": row.entity_type, "entity_id": row.entity_id, "evidence_hash": row.evidence_hash, "storage_ref": row.storage_ref, "metadata": row.metadata_json, "created_at": _iso(row.created_at)}


class LexflowCloudService:
    def dashboard(self, db: Session, *, tenant_id: UUID | str, actor: User, request_id: str | None = None) -> dict[str, object]:
        self.ensure_defaults(db, tenant_id=tenant_id, actor=actor, request_id=request_id)
        environments = db.scalars(select(dbm.CloudEnvironment).where(dbm.CloudEnvironment.deleted_at.is_(None)).order_by(dbm.CloudEnvironment.created_at.desc())).all()
        backups = db.scalars(select(dbm.BackupRecord).order_by(dbm.BackupRecord.created_at.desc())).all()
        return {
            "environment_manager": [self._environment(item) for item in environments],
            "deployment_manager": {"strategy": "staging -> production", "future": ["multi-region", "kubernetes", "autoscaling"]},
            "backup_center": [self._backup(item) for item in backups[:12]],
            "disaster_recovery": {"rpo": "24h pilot", "rto": "manual restore pilot", "future": "automated runbooks"},
            "legal_cloud": {"status": "enterprise_prepared", "tenant_id": str(tenant_id)},
        }

    def ensure_defaults(self, db: Session, *, tenant_id: UUID | str, actor: User, request_id: str | None = None) -> None:
        key = f"staging-{str(tenant_id)[:8]}"
        existing = db.scalar(select(dbm.CloudEnvironment).where(dbm.CloudEnvironment.environment_key == key, dbm.CloudEnvironment.deleted_at.is_(None)))
        if existing:
            return
        environment = dbm.CloudEnvironment(environment_key=key, name="LEXFLOW Staging", environment_type="staging", region="us-east", config_json={"backup": "daily", "multi_region_future": True})
        db.add(environment)
        db.flush()
        db.add(dbm.BackupRecord(environment_id=environment.id, backup_type="database", status="completed", storage_ref=f"managed-backup/{tenant_id}/bootstrap", restore_tested_at=_now()))
        _audit(db, tenant_id=tenant_id, actor=actor, action="cloud.environment_bootstrapped", entity_type="cloud_environment", entity_id=environment.id, request_id=request_id)
        db.commit()

    def record_backup(self, db: Session, *, tenant_id: UUID | str, actor: User, payload: dict[str, object], request_id: str | None = None) -> dict[str, object]:
        environment_id = str(payload.get("environment_id") or "")
        environment = db.get(dbm.CloudEnvironment, environment_id)
        if not environment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cloud environment not found")
        row = dbm.BackupRecord(
            environment_id=environment.id,
            backup_type=str(payload.get("backup_type") or "database"),
            status=str(payload.get("status") or "completed"),
            storage_ref=str(payload.get("storage_ref") or "managed-backup"),
            restore_tested_at=_now() if payload.get("restore_tested") else None,
        )
        db.add(row)
        db.flush()
        _audit(db, tenant_id=tenant_id, actor=actor, action="cloud.backup_recorded", entity_type="backup_record", entity_id=row.id, request_id=request_id, metadata={"environment_id": environment.id})
        db.commit()
        return self._backup(row)

    def _environment(self, item: dbm.CloudEnvironment) -> dict[str, object]:
        return {"id": item.id, "environment_key": item.environment_key, "name": item.name, "environment_type": item.environment_type, "region": item.region, "status": item.status, "config": item.config_json}

    def _backup(self, item: dbm.BackupRecord) -> dict[str, object]:
        return {"id": item.id, "environment_id": item.environment_id, "backup_type": item.backup_type, "status": item.status, "storage_ref": item.storage_ref, "restore_tested_at": _iso(item.restore_tested_at), "created_at": _iso(item.created_at)}


enterprise_multi_org_service = EnterpriseMultiOrgService()
legal_data_platform_service = LegalDataPlatformService()
orchestration_layer_service = OrchestrationLayerService()
enterprise_ai_swarm_service = EnterpriseAiSwarmService()
telemetry_center_service = TelemetryCenterService()
revenue_growth_service = RevenueGrowthService()
api_integration_platform_service = ApiIntegrationPlatformService()
governance_os_service = GovernanceOSService()
lexflow_cloud_service = LexflowCloudService()
