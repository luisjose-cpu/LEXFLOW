from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import AuditLog, Base, CaptchaCheckpoint, Case, JudicialEvidence, Notification
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


def auth_headers(api: TestClient) -> dict[str, str]:
    seed_demo_data()
    response = api.post(
        "/api/v1/auth/login",
        json={"email": DEMO_SEED.admin_email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug},
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


def test_sources_create_check_updates_evidence_and_approve(api: TestClient, db_session: Session) -> None:
    headers = auth_headers(api)
    tenant_id, case_id = seed_db_for_auth_tenant(api, db_session, headers)

    created = api.post(
        f"/api/v1/cases/{case_id}/sources",
        headers=headers,
        json={"source_type": "poder_judicial", "external_case_number": "PJ-2026-001", "court_name": "Juzgado Demo"},
    )
    assert created.status_code == 201
    source_id = created.json()["id"]

    listed = api.get(f"/api/v1/cases/{case_id}/sources", headers=headers)
    checked = api.post(f"/api/v1/case-sources/{source_id}/check", headers=headers)
    update_id = checked.json()["update_id"]
    updates = api.get(f"/api/v1/case-sources/{source_id}/updates", headers=headers)
    approved = api.post(f"/api/v1/judicial-updates/{update_id}/approve", headers=headers, json={"note": "Validado por abogado"})

    evidence = db_session.scalars(select(JudicialEvidence).where(JudicialEvidence.tenant_id == tenant_id, JudicialEvidence.case_source_id == source_id)).all()
    audit = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.entity_type == "case_source")).all()

    assert len(listed.json()) >= 1
    assert checked.status_code == 200
    assert checked.json()["status"] == "pending_approval"
    assert updates.json()[0]["status"] == "pending_approval"
    assert approved.json()["status"] == "approved"
    assert evidence
    assert any(item.action == "check" for item in audit)


def test_captcha_flow_pauses_notifies_audits_and_resolves_human_in_loop(api: TestClient, db_session: Session) -> None:
    headers = auth_headers(api)
    tenant_id, case_id = seed_db_for_auth_tenant(api, db_session, headers)
    created = api.post(
        f"/api/v1/cases/{case_id}/sources",
        headers=headers,
        json={"source_type": "cej", "external_case_number": "CEJ-CAPTCHA", "court_name": "CEJ Demo"},
    )
    source_id = created.json()["id"]

    checked = api.post(f"/api/v1/case-sources/{source_id}/check", headers=headers)
    body = checked.json()
    checkpoint_id = body["checkpoint_id"]
    resolved = api.post(
        f"/api/v1/captcha-checkpoints/{checkpoint_id}/resolve",
        headers=headers,
        json={"resolution_note": "Humano verifico la fuente oficial sin evadir CAPTCHA."},
    )

    checkpoint = db_session.get(CaptchaCheckpoint, checkpoint_id)
    notifications = db_session.scalars(select(Notification).where(Notification.tenant_id == tenant_id, Notification.case_id == case_id)).all()
    audit = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id)).all()

    assert body["status"] == "captcha_required"
    assert checkpoint is not None
    assert checkpoint.status == "resolved"
    assert resolved.json()["status"] == "resolved"
    assert any("CAPTCHA" in notification.title for notification in notifications)
    assert any(item.action == "captcha_required" for item in audit)
    assert any(item.action == "captcha_checkpoint_resolved" for item in audit)


def test_captcha_update_cannot_be_approved_before_checkpoint_resolution(api: TestClient, db_session: Session) -> None:
    headers = auth_headers(api)
    _, case_id = seed_db_for_auth_tenant(api, db_session, headers)
    created = api.post(
        f"/api/v1/cases/{case_id}/sources",
        headers=headers,
        json={"source_type": "sinoe", "external_case_number": "SINOE-CAPTCHA"},
    )
    checked = api.post(f"/api/v1/case-sources/{created.json()['id']}/check", headers=headers)

    blocked = api.post(f"/api/v1/judicial-updates/{checked.json()['update_id']}/approve", headers=headers, json={})

    assert blocked.status_code == 409


def test_case_source_tenant_isolation(api: TestClient, db_session: Session) -> None:
    headers = auth_headers(api)
    _, case_id = seed_db_for_auth_tenant(api, db_session, headers)
    created = api.post(
        f"/api/v1/cases/{case_id}/sources",
        headers=headers,
        json={"source_type": "mpfn", "external_case_number": "MPFN-001"},
    )

    blocked = api.post(
        f"/api/v1/case-sources/{created.json()['id']}/check",
        headers={**headers, "X-Tenant-Id": "00000000-0000-0000-0000-000000000999"},
    )

    assert blocked.status_code == 403
