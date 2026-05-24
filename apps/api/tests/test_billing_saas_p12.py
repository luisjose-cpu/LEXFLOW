from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.database import get_db
from app.db.models import AuditLog, Base, BillingEvent, BillingPlan, TenantUsage
from app.db.seed import seed_demo_database
from app.main import app
from app.services import billing as billing_module
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


def seed_for_billing(api: TestClient, db_session: Session) -> str:
    seed_demo_data()
    headers = login(api, DEMO_SEED.admin_email)
    tenant_id = api.get("/api/v1/auth/me", headers=headers).json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)
    return tenant_id


def test_billing_plans_and_feature_gates(api: TestClient, db_session: Session) -> None:
    tenant_id = seed_for_billing(api, db_session)
    headers = login(api, DEMO_SEED.admin_email)

    plans = api.get("/api/v1/billing/plans", headers=headers)
    features = api.get("/api/v1/billing/features", headers=headers)

    assert plans.status_code == 200
    assert [item["code"] for item in plans.json()] == ["ENTERPRISE", "START", "PRO", "AI"]
    assert db_session.scalar(select(BillingPlan).where(BillingPlan.tenant_id == tenant_id, BillingPlan.code == "AI")) is not None
    assert features.json()["plan"] == "AI"
    assert any(item["feature_key"] == "ai" and item["enabled"] for item in features.json()["features"])
    assert any(item["feature_key"] == "api_access" and item["upgrade_required"] for item in features.json()["features"])


def test_subscribe_change_plan_usage_and_audit(api: TestClient, db_session: Session) -> None:
    tenant_id = seed_for_billing(api, db_session)
    headers = login(api, DEMO_SEED.admin_email)

    subscribed = api.post("/api/v1/billing/subscribe-mock", headers=headers, json={"plan_code": "PRO", "seats": 5})
    changed = api.post("/api/v1/billing/change-plan", headers=headers, json={"plan_code": "ENTERPRISE", "seats": 9})
    usage = api.get("/api/v1/billing/usage", headers=headers)
    current = api.get("/api/v1/billing/current", headers=headers)

    assert subscribed.status_code == 201
    assert subscribed.json()["plan"]["code"] == "PRO"
    assert changed.status_code == 200
    assert current.json()["plan"]["code"] == "ENTERPRISE"
    assert current.json()["seats"] == 9
    assert any(item["feature_key"] == "ai" for item in usage.json())
    assert db_session.scalar(select(TenantUsage).where(TenantUsage.tenant_id == tenant_id, TenantUsage.feature_key == "ai")) is not None
    assert db_session.scalar(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.action == "billing.change_plan")) is not None


def test_billing_permissions_tenant_and_webhook(api: TestClient, db_session: Session) -> None:
    seed_for_billing(api, db_session)
    admin_headers = login(api, DEMO_SEED.admin_email)
    lawyer_headers = login(api, DEMO_SEED.lawyer_email)
    client_headers = login(api, DEMO_SEED.client_email)

    lawyer_read = api.get("/api/v1/billing/current", headers=lawyer_headers)
    lawyer_write = api.post("/api/v1/billing/change-plan", headers=lawyer_headers, json={"plan_code": "AI"})
    client_read = api.get("/api/v1/billing/current", headers=client_headers)
    webhook = api.post("/api/v1/billing/webhook/mock", headers=admin_headers, json={"event_type": "invoice.payment_succeeded", "payload": {"invoice": "mock"}})

    assert lawyer_read.status_code == 200
    assert lawyer_write.status_code == 403
    assert client_read.status_code == 403
    assert webhook.status_code == 200
    assert db_session.scalar(select(BillingEvent).where(BillingEvent.event_type == "invoice.payment_succeeded")) is not None


def test_billing_webhook_mock_is_idempotent_and_audited(api: TestClient, db_session: Session) -> None:
    tenant_id = seed_for_billing(api, db_session)
    headers = login(api, DEMO_SEED.admin_email)
    payload = {
        "event_type": "invoice.payment_succeeded",
        "idempotency_key": "evt_mock_123456",
        "payload": {"invoice": "mock-123"},
    }

    first = api.post("/api/v1/billing/webhook/mock", headers=headers, json=payload)
    duplicate = api.post("/api/v1/billing/webhook/mock", headers=headers, json=payload)
    events = db_session.scalars(select(BillingEvent).where(BillingEvent.tenant_id == tenant_id, BillingEvent.event_type == "invoice.payment_succeeded")).all()
    audits = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.entity_type == "billing_event")).all()

    assert first.status_code == 200
    assert duplicate.status_code == 200
    assert duplicate.json()["status"] == "duplicate"
    assert duplicate.json()["id"] == first.json()["id"]
    assert len(events) == 1
    assert events[0].payload_json["idempotency_key"] == "evt_mock_123456"
    assert {audit.action for audit in audits} >= {"billing.webhook_mock", "billing.webhook_mock_duplicate"}


def test_billing_webhook_signature_is_required_when_enabled(api: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    seed_for_billing(api, db_session)
    headers = login(api, DEMO_SEED.admin_email)
    secret = "billing-webhook-secret-value-123456"
    monkeypatch.setattr(billing_module, "get_settings", lambda: Settings(require_billing_webhook_signature=True, billing_provider_secret=secret))
    payload = {
        "event_type": "invoice.payment_succeeded",
        "idempotency_key": "evt_signed_123456",
        "payload": {"invoice": "mock-signed"},
    }
    signature = billing_module.billing_service.webhook_signature(
        event_type=payload["event_type"],
        payload=payload["payload"],
        idempotency_key=payload["idempotency_key"],
        secret=secret,
    )

    unsigned = api.post("/api/v1/billing/webhook/mock", headers=headers, json=payload)
    signed = api.post("/api/v1/billing/webhook/mock", headers={**headers, "X-Lexflow-Billing-Signature": signature}, json=payload)

    assert unsigned.status_code == 401
    assert unsigned.json()["detail"] == "Invalid billing webhook signature"
    assert signed.status_code == 200
