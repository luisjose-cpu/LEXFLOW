from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import AuditLog, Base, PublicApiKey, Tenant
from app.db.seed import seed_demo_database
from app.main import app
from app.services.seed import DEMO_SEED, seed_demo_data


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture()
def api(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def login(api: TestClient, email: str) -> dict[str, str]:
    response = api.post(
        "/api/v1/auth/login",
        json={"email": email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def seed_level4(api: TestClient, db_session: Session) -> tuple[dict[str, str], str]:
    seed_demo_data()
    headers = login(api, DEMO_SEED.admin_email)
    tenant_id = api.get("/api/v1/auth/me", headers=headers).json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)
    return headers, tenant_id


def test_enterprise_multi_org_dashboard_and_creation(api: TestClient, db_session: Session) -> None:
    headers, tenant_id = seed_level4(api, db_session)

    created = api.post(
        "/api/v1/organizations",
        headers=headers,
        json={"name": "Nivel 4 Holding", "slug": f"nivel4-{tenant_id[:8]}", "country_scope": ["PE", "CO"], "brand_name": "Nivel 4"},
    )
    dashboard = api.get("/api/v1/enterprise/dashboard", headers=headers)
    organizations = api.get("/api/v1/organizations", headers=headers)

    assert created.status_code == 201
    assert dashboard.status_code == 200
    assert dashboard.json()["global_analytics"]["cases"] >= 3
    assert dashboard.json()["cross_graph"]["nodes"] >= 2
    assert organizations.json()["total"] >= 2
    assert db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.action == "enterprise.organization_created")).all()


def test_legal_data_platform_ingest_index_and_search(api: TestClient, db_session: Session) -> None:
    headers, tenant_id = seed_level4(api, db_session)

    event = api.post(
        "/api/v1/data-platform/events",
        headers=headers,
        json={"event_type": "case.updated", "entity_type": "case", "entity_id": "case-demo", "idempotency_key": "case-demo-update", "payload": {"source": "test"}},
    )
    duplicate = api.post(
        "/api/v1/data-platform/events",
        headers=headers,
        json={"event_type": "case.updated", "entity_type": "case", "entity_id": "case-demo", "idempotency_key": "case-demo-update"},
    )
    indexed = api.post("/api/v1/data-platform/index", headers=headers)
    searched = api.get("/api/v1/data-platform/search?q=case", headers=headers)

    assert event.status_code == 201
    assert duplicate.json()["status"] == "duplicate"
    assert indexed.json()["events_indexed"] >= 1
    assert searched.json()["total"] >= 1
    assert db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.action == "data_platform.indexed")).all()


def test_orchestration_ai_swarm_and_telemetry(api: TestClient, db_session: Session) -> None:
    headers, tenant_id = seed_level4(api, db_session)
    api.post("/api/v1/intelligence/memory/index", headers=headers)

    orchestration = api.post("/api/v1/orchestration/dispatch", headers=headers, json={"event_key": "SINOE_UPDATE_APPROVED", "payload": {"case_id": "demo"}})
    swarm = api.post("/api/v1/ai-swarm/run", headers=headers, json={"objective": "Evaluar riesgo SINOE Nova con fuentes"})
    metric = api.post("/api/v1/telemetry/metrics", headers=headers, json={"component": "api", "metric_key": "latency_p95_ms", "metric_value": 180, "unit": "ms"})
    telemetry = api.get("/api/v1/telemetry", headers=headers)

    assert orchestration.status_code == 200
    assert "refresh_case_timeline" in orchestration.json()["result"]["actions"]
    assert swarm.status_code == 200
    assert swarm.json()["run"]["review_required"] is True
    assert metric.status_code == 201
    assert any(item["component"] == "api" for item in telemetry.json()["components"])
    assert db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.action == "ai_swarm.run_completed")).all()


def test_integrations_governance_revenue_and_cloud(api: TestClient, db_session: Session) -> None:
    headers, tenant_id = seed_level4(api, db_session)

    api_key = api.post("/api/v1/integrations/api-keys", headers=headers, json={"name": "Partner API", "scopes": ["cases:read", "webhooks:write"]})
    webhook = api.post("/api/v1/integrations/webhooks", headers=headers, json={"name": "Partner hook", "target_url": "https://hooks.example.com/partner", "event_types": ["case.updated"]})
    governance = api.post("/api/v1/governance/policies", headers=headers, json={"policy_type": "retention", "name": "Retencion documental", "rules": {"days": 3650}})
    evidence = api.post("/api/v1/governance/evidence", headers=headers, json={"entity_type": "case", "entity_id": "case-demo", "storage_ref": "evidence/case-demo.json"})
    revenue = api.get("/api/v1/revenue", headers=headers)
    cloud = api.get("/api/v1/cloud/control", headers=headers)
    backup = api.post("/api/v1/cloud/backups", headers=headers, json={"environment_id": cloud.json()["environment_manager"][0]["id"], "backup_type": "database", "restore_tested": True})
    stored_key = db_session.scalars(select(PublicApiKey).where(PublicApiKey.tenant_id == tenant_id, PublicApiKey.name == "Partner API")).first()

    assert api_key.status_code == 201
    assert api_key.json()["api_key"].startswith("lf_")
    assert stored_key is not None
    assert stored_key.key_hash != api_key.json()["api_key"]
    assert webhook.status_code == 201
    assert governance.status_code == 201
    assert evidence.status_code == 201
    assert revenue.json()["enterprise_proposal"]["status"] == "prepared"
    assert backup.status_code == 201


def test_level4_permissions_and_cross_tenant_guard(api: TestClient, db_session: Session) -> None:
    seed_level4(api, db_session)
    client_headers = login(api, DEMO_SEED.client_email)
    lawyer_headers = login(api, DEMO_SEED.lawyer_email)
    other_tenant = Tenant(name="N4 Other", slug="n4-other")
    db_session.add(other_tenant)
    db_session.commit()

    blocked_client = api.get("/api/v1/enterprise/dashboard", headers=client_headers)
    blocked_cross_tenant = api.get("/api/v1/data-platform", headers={**lawyer_headers, "X-Tenant-Id": other_tenant.id})

    assert blocked_client.status_code == 403
    assert blocked_cross_tenant.status_code == 403
