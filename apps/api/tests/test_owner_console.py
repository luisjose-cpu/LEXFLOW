from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.database import get_db
from app.db.models import Base, OwnerAuditLog, OwnerUser, TenantFeatureFlag, TenantIntervention, TenantSubscription, User
from app.main import app
from app.services import owner_auth as owner_auth_module
from app.services.seed import DEMO_SEED, seed_demo_data
from app.services.mfa import totp_code
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


def test_owner_login_blocks_when_owner_mfa_required_and_not_enrolled(api: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    create_owner_user(db_session)
    monkeypatch.setattr(owner_auth_module, "get_settings", lambda: Settings(require_owner_mfa=True))

    response = api.post("/api/v1/owner/auth/login", json={"email": "owner@lexflow.com", "password": "OwnerPassword123!"})

    assert response.status_code == 403
    assert response.json()["detail"] == "Owner MFA enrollment required"


def test_owner_login_temporarily_blocks_repeated_failures(api: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    create_owner_user(db_session)
    owner_auth_module.owner_auth_service._failed_logins.clear()
    monkeypatch.setattr(owner_auth_module, "get_settings", lambda: Settings(failed_login_limit=2, failed_login_window_minutes=15))
    payload = {"email": "owner@lexflow.com", "password": "wrong-password"}

    first = api.post("/api/v1/owner/auth/login", json=payload)
    second = api.post("/api/v1/owner/auth/login", json=payload)
    blocked = api.post("/api/v1/owner/auth/login", json={"email": "owner@lexflow.com", "password": "OwnerPassword123!"})

    assert first.status_code == 401
    assert second.status_code == 401
    assert blocked.status_code == 429
    assert blocked.json()["detail"] == "Too many failed login attempts"


def test_owner_security_alerts_are_created_and_acknowledged(api: TestClient, db_session: Session) -> None:
    create_owner_user(db_session)
    logged = api.post("/api/v1/owner/auth/login", json={"email": "owner@lexflow.com", "password": "OwnerPassword123!"})
    headers = {"Authorization": f"Bearer {logged.json()['access_token']}"}
    alerts = api.get("/api/v1/owner/security-alerts", headers=headers)
    alert_id = alerts.json()[0]["id"]
    acknowledged = api.post(f"/api/v1/owner/security-alerts/{alert_id}/acknowledge", headers=headers)

    assert alerts.status_code == 200
    assert alerts.json()[0]["event_type"] == "owner.owner_login"
    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "acknowledged"


def test_owner_mfa_enrollment_requires_totp_and_can_be_disabled(api: TestClient, db_session: Session) -> None:
    create_owner_user(db_session)
    logged = api.post("/api/v1/owner/auth/login", json={"email": "owner@lexflow.com", "password": "OwnerPassword123!"})
    access = logged.json()["access_token"]
    headers = {"Authorization": f"Bearer {access}"}

    status_before = api.get("/api/v1/owner/auth/mfa/status", headers=headers)
    enrollment = api.post("/api/v1/owner/auth/mfa/enroll", headers=headers)
    secret = enrollment.json()["secret"]
    code = totp_code(secret, int(datetime.now(UTC).timestamp() // 30))
    verified = api.post("/api/v1/owner/auth/mfa/verify", headers=headers, json={"code": code})
    rotated_headers = {"Authorization": f"Bearer {verified.json()['access_token']}"}
    recovery_code = verified.json()["recovery_codes"][0]
    no_mfa_login = api.post("/api/v1/owner/auth/login", json={"email": "owner@lexflow.com", "password": "OwnerPassword123!"})
    bad_mfa_login = api.post("/api/v1/owner/auth/login", json={"email": "owner@lexflow.com", "password": "OwnerPassword123!", "mfa_code": "000000"})
    good_mfa_login = api.post("/api/v1/owner/auth/login", json={"email": "owner@lexflow.com", "password": "OwnerPassword123!", "mfa_code": code})
    recovery_login = api.post("/api/v1/owner/auth/login", json={"email": "owner@lexflow.com", "password": "OwnerPassword123!", "mfa_code": recovery_code})
    reused_recovery_login = api.post("/api/v1/owner/auth/login", json={"email": "owner@lexflow.com", "password": "OwnerPassword123!", "mfa_code": recovery_code})
    regenerated = api.post("/api/v1/owner/auth/mfa/recovery-codes", headers=rotated_headers, json={"current_password": "OwnerPassword123!", "code": code})
    deliveries = api.get("/api/v1/owner/security-alert-deliveries", headers=rotated_headers)
    disabled = api.post("/api/v1/owner/auth/mfa/disable", headers=rotated_headers, json={"current_password": "OwnerPassword123!", "code": code})
    login_after_disable = api.post("/api/v1/owner/auth/login", json={"email": "owner@lexflow.com", "password": "OwnerPassword123!"})
    audits = db_session.scalars(select(OwnerAuditLog).where(OwnerAuditLog.entity_type == "owner_mfa")).all()

    assert status_before.json()["mfa_enabled"] is False
    assert enrollment.status_code == 200
    assert enrollment.json()["otpauth_url"].startswith("otpauth://totp/")
    assert verified.status_code == 200
    assert verified.json()["owner"]["mfa_enabled"] is True
    assert len(verified.json()["recovery_codes"]) == 10
    assert no_mfa_login.status_code == 401
    assert bad_mfa_login.status_code == 401
    assert good_mfa_login.status_code == 200
    assert recovery_login.status_code == 200
    assert reused_recovery_login.status_code == 401
    assert regenerated.status_code == 200
    assert len(regenerated.json()["recovery_codes"]) == 10
    assert deliveries.status_code == 200
    assert any(item["template"] == "security_alert" and item["status"] == "prepared" for item in deliveries.json())
    assert disabled.status_code == 200
    assert disabled.json()["owner"]["mfa_enabled"] is False
    assert login_after_disable.status_code == 200
    assert {audit.action for audit in audits} >= {
        "owner_mfa_enrollment_started",
        "owner_mfa_enabled",
        "owner_mfa_recovery_code_used",
        "owner_mfa_recovery_codes_regenerated",
        "owner_mfa_disabled",
    }


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
    limits = api.post(f"/api/v1/owner/tenants/{tenant_id}/limits", headers=owner_headers(), json={"limits": {"users": 25, "cases": 700}, "reason": "piloto ampliado"})
    health = api.get(f"/api/v1/owner/tenants/{tenant_id}/health-score", headers=owner_headers())

    audits = db_session.scalars(select(OwnerAuditLog).where(OwnerAuditLog.tenant_id == tenant_id)).all()
    assert suspended.json()["status"] == "suspended"
    assert reactivated.json()["status"] == "active"
    assert changed.json()["plan"] == "AI"
    assert any(flag["feature_key"] == "ai" and flag["enabled"] for flag in features.json())
    assert any(item["limit_key"] == "users" and item["limit_value"] == 25 for item in limits.json())
    assert health.json()["score"] > 0
    assert {audit.action for audit in audits} >= {"tenant_created", "tenant_suspended", "tenant_reactivated", "tenant_plan_changed", "tenant_features_updated", "tenant_limits_updated"}


def test_owner_tenant_onboarding_creates_admin_subscription_features_and_handoff(api: TestClient, db_session: Session) -> None:
    created = api.post(
        "/api/v1/owner/tenants",
        headers=owner_headers(),
        json={
            "name": "Estudio Onboarding",
            "slug": "estudio-onboarding",
            "plan": "AI",
            "trial": True,
            "admin_email": "admin@onboarding.lexflow.com",
            "admin_name": "Admin Onboarding",
            "admin_password": "OnboardingPassword123!",
            "seats": 9,
            "modules": ["custom_branding"],
            "send_access_email": True,
        },
    )
    body = created.json()
    tenant_id = body["id"]
    onboarding = api.get(f"/api/v1/owner/tenants/{tenant_id}/onboarding", headers=owner_headers())
    admin = db_session.scalars(select(User).where(User.tenant_id == tenant_id, User.email == "admin@onboarding.lexflow.com")).first()
    subscription = db_session.scalars(select(TenantSubscription).where(TenantSubscription.tenant_id == tenant_id)).first()
    enabled_flags = db_session.scalars(select(TenantFeatureFlag).where(TenantFeatureFlag.tenant_id == tenant_id, TenantFeatureFlag.enabled.is_(True))).all()

    assert created.status_code == 201
    assert body["onboarding"]["ready"] is True
    assert body["onboarding"]["admin_email"] == "admin@onboarding.lexflow.com"
    assert admin is not None
    assert subscription is not None
    assert subscription.seats == 9
    assert subscription.status == "trialing"
    assert {flag.feature_key for flag in enabled_flags} >= {"ai", "ocr", "automation_studio", "custom_branding"}
    assert onboarding.json()["handoff"].startswith("Enviar URL")


def test_support_ticket_resolution_intervention_expiry_and_owner_surfaces(api: TestClient, db_session: Session) -> None:
    tenant_id = create_owner_tenant(api)
    ticket = api.post("/api/v1/owner/support/tickets", headers=owner_headers(), json={"tenant_id": tenant_id, "title": "Error SINOE", "priority": "high"})
    resolved = api.post(f"/api/v1/owner/support/tickets/{ticket.json()['id']}/resolve", headers=owner_headers(), json={"resolution": "resuelto"})
    intervention = api.post("/api/v1/owner/interventions", headers=owner_headers(), json={"tenant_id": tenant_id, "reason": "diagnostico autorizado", "duration_minutes": 5, "scopes": ["metadata:read"]})
    closed = api.post(f"/api/v1/owner/interventions/{intervention.json()['id']}/close", headers=owner_headers(), json={"reason": "soporte finalizado"})

    row = db_session.get(TenantIntervention, intervention.json()["id"])
    assert row is not None
    assert closed.json()["status"] == "closed"
    row.expires_at = row.created_at - timedelta(minutes=1)
    row.status = "active"
    db_session.commit()
    interventions = api.get("/api/v1/owner/interventions", headers=owner_headers())

    assert ticket.status_code == 201
    assert resolved.json()["status"] == "resolved"
    assert any(item["status"] == "expired" for item in interventions.json())
    assert any(audit.action == "tenant_intervention_closed" for audit in db_session.scalars(select(OwnerAuditLog)).all())
    assert api.get("/api/v1/owner/plans", headers=owner_headers()).status_code == 200
    assert api.get("/api/v1/owner/billing", headers=owner_headers()).status_code == 200
    health = api.get("/api/v1/owner/system/health", headers=owner_headers())
    health_components = {item["component"] for item in health.json()["checks"]}
    assert health.status_code == 200
    assert {"api_requests", "readiness", "storage_backend", "external_providers"}.issubset(health_components)
    assert any("ai=mock" in item["detail"] and "malware_scanner=mock" in item["detail"] for item in health.json()["checks"] if item["component"] == "external_providers")
    assert api.get("/api/v1/owner/demos", headers=owner_headers()).status_code == 200
    assert api.get("/api/v1/owner/audit-logs", headers=owner_headers()).json()


def test_owner_system_incident_lifecycle_and_audit(api: TestClient, db_session: Session) -> None:
    created = api.post(
        "/api/v1/owner/system/incidents",
        headers=owner_headers("owner_devops"),
        json={"component": "api", "title": "Error rate elevado", "severity": "high", "summary": "Aumento de 5xx en ventana piloto."},
    )
    listed = api.get("/api/v1/owner/system/incidents", headers=owner_headers("owner_readonly"))
    resolved = api.post(f"/api/v1/owner/system/incidents/{created.json()['id']}/resolve", headers=owner_headers("owner_devops"), json={"reason": "rollback aplicado"})
    forbidden = api.post("/api/v1/owner/system/incidents", headers=owner_headers("owner_support"), json={"component": "db", "title": "No autorizado"})

    audits = db_session.scalars(select(OwnerAuditLog).where(OwnerAuditLog.entity_type == "system_incident")).all()
    assert created.status_code == 201
    assert created.json()["status"] == "open"
    assert any(item["title"] == "Error rate elevado" for item in listed.json())
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["resolved_at"]
    assert forbidden.status_code == 403
    assert {audit.action for audit in audits} >= {"system_incident_created", "system_incident_resolved"}


def test_owner_demo_reset_and_audit(api: TestClient, db_session: Session) -> None:
    created = api.post(
        "/api/v1/owner/demos",
        headers=owner_headers("owner_sales"),
        json={"name": "Demo Laboral", "slug": "demo-laboral-reset", "demo_type": "labor"},
    )
    reset = api.post(f"/api/v1/owner/demos/{created.json()['demo']['id']}/reset", headers=owner_headers("owner_sales"), json={"reason": "preparar demo comercial"})
    forbidden = api.post(f"/api/v1/owner/demos/{created.json()['demo']['id']}/reset", headers=owner_headers("owner_support"), json={"reason": "sin permiso"})

    audits = db_session.scalars(select(OwnerAuditLog).where(OwnerAuditLog.action == "demo_tenant_reset")).all()
    assert created.status_code == 201
    assert reset.status_code == 200
    assert reset.json()["status"] == "ready"
    assert reset.json()["last_reset_at"]
    assert forbidden.status_code == 403
    assert audits


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
