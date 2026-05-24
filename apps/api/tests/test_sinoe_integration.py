from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import AuditLog, Base, CaptchaCheckpoint, Case, CaseEvent, IntegrationCredential, JudicialUpdate, Notification
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


def auth_headers(api: TestClient, *, email: str = DEMO_SEED.admin_email) -> dict[str, str]:
    seed_demo_data()
    response = api.post(
        "/api/v1/auth/login",
        json={"email": email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def seed_db_for_auth_tenant(api: TestClient, db_session: Session, headers: dict[str, str]) -> tuple[str, str]:
    me = api.get("/api/v1/auth/me", headers=headers)
    tenant_id = me.json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)
    legal_case = db_session.scalars(select(Case).where(Case.tenant_id == tenant_id)).first()
    assert legal_case is not None
    return tenant_id, legal_case.id


def configure_sinoe(api: TestClient, headers: dict[str, str]) -> dict[str, object]:
    response = api.post(
        "/api/v1/settings/integrations/sinoe",
        headers=headers,
        json={"username": "demo.sinoe.authorized", "password": "SinoeMockPassword123!"},
    )
    assert response.status_code == 200
    return response.json()


def test_saves_encrypted_credentials_and_never_returns_password(api: TestClient, db_session: Session) -> None:
    headers = auth_headers(api)
    tenant_id, _ = seed_db_for_auth_tenant(api, db_session, headers)

    saved = configure_sinoe(api, headers)
    status_response = api.get("/api/v1/settings/integrations/sinoe", headers=headers)
    credential = db_session.scalar(select(IntegrationCredential).where(IntegrationCredential.tenant_id == tenant_id))
    audit = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.entity_type == "integration_credentials")).all()

    assert saved["configured"] is True
    assert "password" not in saved
    assert "password" not in status_response.text.lower()
    assert credential is not None
    assert credential.username_encrypted != "demo.sinoe.authorized"
    assert credential.password_encrypted != "SinoeMockPassword123!"
    assert any(item.action == "sinoe_credentials_created" for item in audit)


def test_sinoe_connection_mock_updates_status(api: TestClient, db_session: Session) -> None:
    headers = auth_headers(api)
    tenant_id, _ = seed_db_for_auth_tenant(api, db_session, headers)
    configure_sinoe(api, headers)

    tested = api.post("/api/v1/settings/integrations/sinoe/test", headers=headers)
    credential = db_session.scalar(select(IntegrationCredential).where(IntegrationCredential.tenant_id == tenant_id))

    assert tested.status_code == 200
    assert tested.json()["status"] == "connected"
    assert tested.json()["last_checked_at"] is not None
    assert credential is not None
    assert credential.status == "connected"


def test_links_sinoe_source_and_successful_check_creates_operational_records(api: TestClient, db_session: Session) -> None:
    headers = auth_headers(api)
    tenant_id, case_id = seed_db_for_auth_tenant(api, db_session, headers)
    configure_sinoe(api, headers)

    created = api.post(
        f"/api/v1/cases/{case_id}/sources/sinoe",
        headers=headers,
        json={"external_case_number": "SINOE-2026-001", "district": "Lima", "site": "Sede Central", "reference": "Casilla autorizada"},
    )
    checked = api.post(f"/api/v1/case-sources/{created.json()['id']}/sinoe/check", headers=headers)
    updates = api.get(f"/api/v1/case-sources/{created.json()['id']}/sinoe/updates", headers=headers)

    judicial_updates = db_session.scalars(select(JudicialUpdate).where(JudicialUpdate.tenant_id == tenant_id)).all()
    events = db_session.scalars(select(CaseEvent).where(CaseEvent.tenant_id == tenant_id, CaseEvent.event_type == "sinoe_update")).all()
    notifications = db_session.scalars(select(Notification).where(Notification.tenant_id == tenant_id, Notification.case_id == case_id)).all()
    audits = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id)).all()

    assert created.status_code == 201
    assert created.json()["source_type"] == "sinoe"
    assert checked.status_code == 200
    assert checked.json()["status"] == "updates_found"
    assert updates.json()[0]["status"] == "recorded"
    assert any(update.update_type == "sinoe_update" for update in judicial_updates)
    assert events
    assert any(notification.title == "Nueva actualizacion SINOE" for notification in notifications)
    assert any(item.action == "sinoe_case_source_checked" for item in audits)


def test_sinoe_captcha_flow_creates_checkpoint_notification_and_audit(api: TestClient, db_session: Session) -> None:
    headers = auth_headers(api)
    tenant_id, case_id = seed_db_for_auth_tenant(api, db_session, headers)
    configure_sinoe(api, headers)
    created = api.post(
        f"/api/v1/cases/{case_id}/sources/sinoe",
        headers=headers,
        json={"external_case_number": "SINOE-CAPTCHA-001"},
    )

    checked = api.post(f"/api/v1/case-sources/{created.json()['id']}/sinoe/check", headers=headers)
    checkpoint_id = checked.json()["checkpoint_id"]
    resolved = api.post(
        f"/api/v1/captcha-checkpoints/{checkpoint_id}/resolve",
        headers=headers,
        json={"resolution_note": "Usuario autorizado completo verificacion humana en SINOE."},
    )

    checkpoint = db_session.get(CaptchaCheckpoint, checkpoint_id)
    notifications = db_session.scalars(select(Notification).where(Notification.tenant_id == tenant_id, Notification.case_id == case_id)).all()
    audits = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id)).all()

    assert checked.status_code == 200
    assert checked.json()["status"] == "captcha_required"
    assert checkpoint is not None
    assert checkpoint.provider == "SINOE"
    assert checkpoint.status == "resolved"
    assert resolved.json()["status"] == "resolved"
    assert any("SINOE requiere verificacion humana" in notification.title for notification in notifications)
    assert any(item.action == "sinoe_captcha_checkpoint_created" for item in audits)


def test_sinoe_blocks_client_user_and_cross_tenant_access(api: TestClient, db_session: Session) -> None:
    admin_headers = auth_headers(api)
    _, case_id = seed_db_for_auth_tenant(api, db_session, admin_headers)
    configure_sinoe(api, admin_headers)
    client_login = api.post(
        "/api/v1/auth/login",
        json={"email": DEMO_SEED.client_email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug},
    )
    assert client_login.status_code == 200
    client_headers = {"Authorization": f"Bearer {client_login.json()['access_token']}"}

    forbidden = api.get("/api/v1/settings/integrations/sinoe", headers=client_headers)
    created = api.post(f"/api/v1/cases/{case_id}/sources/sinoe", headers=admin_headers, json={"external_case_number": "SINOE-2026-002"})
    cross_tenant = api.post(
        f"/api/v1/case-sources/{created.json()['id']}/sinoe/check",
        headers={**admin_headers, "X-Tenant-Id": "00000000-0000-0000-0000-000000000999"},
    )

    assert forbidden.status_code == 403
    assert cross_tenant.status_code == 403
