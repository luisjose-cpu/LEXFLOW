from collections.abc import Generator
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import Base, OwnerAuditLog, OwnerUser, TenantIntervention
from app.main import app
from app.services.seed import DEMO_SEED, seed_demo_data
from app.services.security import hash_password


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool, future=True)
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


def owner_headers(role: str = "owner_admin") -> dict[str, str]:
    return {"X-Owner-Email": "owner@lexflow.com", "X-Owner-Role": role}


def create_owner_user(db_session: Session, *, email: str = "owner@lexflow.com", role: str = "owner_admin", password: str = "OwnerPassword123!") -> OwnerUser:
    owner = OwnerUser(email=email, full_name="Owner Admin", role=role, hashed_password=hash_password(password), status="active")
    db_session.add(owner)
    db_session.commit()
    return owner


def owner_bearer_headers(api: TestClient, db_session: Session, *, email: str = "owner@lexflow.com", role: str = "owner_admin", password: str = "OwnerPassword123!") -> dict[str, str]:
    create_owner_user(db_session, email=email, role=role, password=password)
    response = api.post("/api/v1/owner/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def tenant_headers(api: TestClient) -> dict[str, str]:
    seed_demo_data()
    response = api.post("/api/v1/auth/login", json={"email": DEMO_SEED.admin_email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_owner_tenant(api: TestClient) -> str:
    response = api.post(
        "/api/v1/owner/tenants",
        headers=owner_headers(),
        json={"name": "Owner Pilot", "slug": "owner-pilot", "plan": "START", "trial": True, "demo_data": True},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_owner_admin_access_and_tenant_user_blocked(api: TestClient) -> None:
    assert api.get("/api/v1/owner/dashboard", headers=owner_headers()).status_code == 200
    assert api.get("/api/v1/owner/dashboard", headers=tenant_headers(api)).status_code == 401


def test_owner_jwt_login_refresh_me_logout_and_access_control(api: TestClient, db_session: Session) -> None:
    create_owner_user(db_session)
    logged = api.post("/api/v1/owner/auth/login", json={"email": "owner@lexflow.com", "password": "OwnerPassword123!"})
    access = logged.json()["access_token"]
    refresh = logged.json()["refresh_token"]
    bearer = {"Authorization": f"Bearer {access}"}

    assert logged.status_code == 200
    assert logged.json()["owner"]["role"] == "owner_admin"
    assert api.get("/api/v1/owner/auth/me", headers=bearer).json()["email"] == "owner@lexflow.com"
    assert api.get("/api/v1/owner/dashboard", headers=bearer).status_code == 200
    refreshed = api.post("/api/v1/owner/auth/refresh", json={"refresh_token": refresh})
    assert refreshed.status_code == 200
    assert api.post("/api/v1/owner/auth/logout", headers=bearer).status_code == 204
    assert api.get("/api/v1/owner/dashboard", headers=bearer).status_code == 401


def test_owner_support_limited(api: TestClient) -> None:
    assert api.get("/api/v1/owner/tenants", headers=owner_headers("owner_support")).status_code == 200
    forbidden = api.post("/api/v1/owner/tenants", headers=owner_headers("owner_support"), json={"name": "Nope", "slug": "nope"})
    assert forbidden.status_code == 403


def test_tenant_lifecycle_plan_features_health_and_audit(api: TestClient, db_session: Session) -> None:
    tenant_id = create_owner_tenant(api)

    suspended = api.post(f"/api/v1/owner/tenants/{tenant_id}/suspend", headers=owner_headers(), json={"reason": "morosidad mock"})
    reactivated = api.post(f"/api/v1/owner/tenants/{tenant_id}/reactivate", headers=owner_headers(), json={"reason": "pago regularizado"})
    changed = api.post(f"/api/v1/owner/tenants/{tenant_id}/change-plan", headers=owner_headers(), json={"plan": "AI", "reason": "upgrade piloto"})
    features = api.post(f"/api/v1/owner/tenants/{tenant_id}/features", headers=owner_headers(), json={"features": {"ai": True}, "reason": "activar IA"})
    health = api.get(f"/api/v1/owner/tenants/{tenant_id}/health-score", headers=owner_headers())

    audits = db_session.scalars(select(OwnerAuditLog).where(OwnerAuditLog.tenant_id == tenant_id)).all()
    assert suspended.json()["status"] == "suspended"
    assert reactivated.json()["status"] == "active"
    assert changed.json()["plan"] == "AI"
    assert any(flag["feature_key"] == "ai" and flag["enabled"] for flag in features.json())
    assert health.json()["score"] > 0
    assert {audit.action for audit in audits} >= {"tenant_created", "tenant_suspended", "tenant_reactivated", "tenant_plan_changed", "tenant_features_updated"}


def test_support_ticket_resolution_intervention_expiry_and_owner_surfaces(api: TestClient, db_session: Session) -> None:
    tenant_id = create_owner_tenant(api)
    ticket = api.post("/api/v1/owner/support/tickets", headers=owner_headers(), json={"tenant_id": tenant_id, "title": "Error SINOE", "priority": "high"})
    resolved = api.post(f"/api/v1/owner/support/tickets/{ticket.json()['id']}/resolve", headers=owner_headers(), json={"resolution": "resuelto"})
    intervention = api.post("/api/v1/owner/interventions", headers=owner_headers(), json={"tenant_id": tenant_id, "reason": "diagnostico autorizado", "duration_minutes": 5, "scopes": ["metadata:read"]})

    row = db_session.get(TenantIntervention, intervention.json()["id"])
    assert row is not None
    row.expires_at = row.created_at - timedelta(minutes=1)
    db_session.commit()
    interventions = api.get("/api/v1/owner/interventions", headers=owner_headers())

    assert ticket.status_code == 201
    assert resolved.json()["status"] == "resolved"
    assert any(item["status"] == "expired" for item in interventions.json())
    assert api.get("/api/v1/owner/plans", headers=owner_headers()).status_code == 200
    assert api.get("/api/v1/owner/billing", headers=owner_headers()).status_code == 200
    assert api.get("/api/v1/owner/system/health", headers=owner_headers()).status_code == 200
    assert api.get("/api/v1/owner/demos", headers=owner_headers()).status_code == 200
    assert api.get("/api/v1/owner/audit-logs", headers=owner_headers()).json()


def test_owner_plan_create_update_and_audit(api: TestClient, db_session: Session) -> None:
    created = api.post(
        "/api/v1/owner/plans",
        headers=owner_headers("owner_finance"),
        json={
            "code": "PILOT",
            "name": "Pilot",
            "monthly_price_cents": 19900,
            "status": "active",
            "limits": {"users": 10, "cases": 100},
            "features": ["expediente360", "client_portal"],
        },
    )
    updated = api.patch(
        "/api/v1/owner/plans/PILOT",
        headers=owner_headers("owner_finance"),
        json={"status": "draft", "features": ["expediente360"], "reason": "ajuste comercial"},
    )
    forbidden = api.post("/api/v1/owner/plans", headers=owner_headers("owner_support"), json={"code": "NOPE", "name": "Nope"})

    audits = db_session.scalars(select(OwnerAuditLog).where(OwnerAuditLog.entity_type == "billing_plan")).all()
    assert created.status_code == 201
    assert created.json()["code"] == "PILOT"
    assert updated.status_code == 200
    assert updated.json()["status"] == "draft"
    assert updated.json()["features"] == ["expediente360"]
    assert forbidden.status_code == 403
    assert {audit.action for audit in audits} >= {"owner_plan_created", "owner_plan_updated"}
