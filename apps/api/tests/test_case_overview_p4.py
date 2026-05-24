from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import AuditLog, Base, Case, CaseEvent, Document, Hearing, Task, Tenant
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


def seed_db_for_auth_tenant(api: TestClient, db_session: Session, headers: dict[str, str]) -> str:
    me = api.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    tenant_id = me.json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)
    return tenant_id


def first_case_id(db_session: Session, tenant_id: str) -> str:
    legal_case = db_session.scalars(select(Case).where(Case.tenant_id == tenant_id)).first()
    assert legal_case is not None
    return legal_case.id


def test_case_overview_returns_full_expediente_360(api: TestClient, db_session: Session) -> None:
    headers = auth_headers(api)
    tenant_id = seed_db_for_auth_tenant(api, db_session, headers)
    case_id = first_case_id(db_session, tenant_id)

    response = api.get(f"/api/v1/cases/{case_id}/overview", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["case"]["id"] == case_id
    assert body["client"]["name"]
    assert body["timeline"]
    assert body["documents"]
    assert body["hearings"]
    assert body["tasks"]
    assert body["judicial_updates"]
    assert body["communications"]
    assert body["alerts"]
    assert "audit_summary" in body
    assert body["next_actions"]


def test_case_overview_blocks_cross_tenant_access(api: TestClient, db_session: Session) -> None:
    headers = auth_headers(api)
    seed_db_for_auth_tenant(api, db_session, headers)
    other_tenant = Tenant(name="Other", slug="other")
    db_session.add(other_tenant)
    db_session.flush()
    other_case = Case(tenant_id=other_tenant.id, client_id="missing-client", title="Other")
    db_session.add(other_case)
    db_session.commit()

    response = api.get(f"/api/v1/cases/{other_case.id}/overview", headers=headers)

    assert response.status_code == 404


def test_case_event_task_document_and_status_create_audit(api: TestClient, db_session: Session) -> None:
    headers = auth_headers(api)
    tenant_id = seed_db_for_auth_tenant(api, db_session, headers)
    case_id = first_case_id(db_session, tenant_id)

    event = api.post(f"/api/v1/cases/{case_id}/events", headers=headers, json={"title": "Nota de seguimiento", "description": "Cliente envio anexos."})
    task = api.post(f"/api/v1/cases/{case_id}/tasks", headers=headers, json={"title": "Preparar memorial", "due_at": "2026-06-01T10:00:00Z"})
    hearing = api.post(
        f"/api/v1/cases/{case_id}/hearings",
        headers=headers,
        json={"title": "Audiencia de pruebas", "starts_at": "2026-06-03T15:00:00Z", "location": "Virtual"},
    )
    document = api.post(
        f"/api/v1/cases/{case_id}/documents",
        headers=headers,
        json={"filename": "anexo.pdf", "storage_key": f"demo/{case_id}/anexo.pdf", "classification": "evidence"},
    )
    status_change = api.post(f"/api/v1/cases/{case_id}/status", headers=headers, json={"status": "risk"})

    assert event.status_code == 201
    assert task.status_code == 201
    assert task.json()["due_at"].startswith("2026-06-01T10:00:00")
    assert hearing.status_code == 201
    assert document.status_code == 201
    assert status_change.status_code == 200

    task_update = api.patch(f"/api/v1/cases/{case_id}/tasks/{task.json()['id']}", headers=headers, json={"status": "done"})
    hearing_update = api.patch(f"/api/v1/cases/{case_id}/hearings/{hearing.json()['id']}", headers=headers, json={"status": "completed"})
    document_update = api.patch(
        f"/api/v1/cases/{case_id}/documents/{document.json()['id']}",
        headers=headers,
        json={"status": "approved", "is_client_visible": True},
    )

    assert task_update.status_code == 200
    assert task_update.json()["status"] == "done"
    assert hearing_update.status_code == 200
    assert hearing_update.json()["status"] == "completed"
    assert document_update.status_code == 200
    assert document_update.json()["status"] == "approved"
    assert document_update.json()["is_client_visible"] is True

    assert db_session.scalars(select(CaseEvent).where(CaseEvent.title == "Nota de seguimiento")).first() is not None
    assert db_session.scalars(select(Task).where(Task.title == "Preparar memorial")).first().status == "done"
    assert db_session.scalars(select(Hearing).where(Hearing.title == "Audiencia de pruebas")).first().status == "completed"
    assert db_session.scalars(select(Document).where(Document.filename == "anexo.pdf")).first().is_client_visible is True

    audits = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.metadata_json["case_id"].as_string() == case_id)).all()
    assert len(audits) >= 8


def test_case_resource_updates_return_404_for_missing_resource(api: TestClient, db_session: Session) -> None:
    headers = auth_headers(api)
    tenant_id = seed_db_for_auth_tenant(api, db_session, headers)
    case_id = first_case_id(db_session, tenant_id)

    response = api.patch(
        f"/api/v1/cases/{case_id}/tasks/00000000-0000-0000-0000-000000000000",
        headers=headers,
        json={"status": "done"},
    )

    assert response.status_code == 404


def test_case_hearing_rejects_invalid_datetime(api: TestClient, db_session: Session) -> None:
    headers = auth_headers(api)
    tenant_id = seed_db_for_auth_tenant(api, db_session, headers)
    case_id = first_case_id(db_session, tenant_id)

    response = api.post(
        f"/api/v1/cases/{case_id}/hearings",
        headers=headers,
        json={"title": "Audiencia invalida", "starts_at": "manana", "location": "Virtual"},
    )

    assert response.status_code == 422


def test_lawyer_can_read_but_client_user_cannot_write_events(api: TestClient, db_session: Session) -> None:
    admin_headers = auth_headers(api)
    tenant_id = seed_db_for_auth_tenant(api, db_session, admin_headers)
    case_id = first_case_id(db_session, tenant_id)

    lawyer_login = api.post(
        "/api/v1/auth/login",
        json={"email": DEMO_SEED.lawyer_email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug},
    )
    client_login = api.post(
        "/api/v1/auth/login",
        json={"email": DEMO_SEED.client_email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug},
    )
    lawyer_headers = {"Authorization": f"Bearer {lawyer_login.json()['access_token']}"}
    client_headers = {"Authorization": f"Bearer {client_login.json()['access_token']}"}

    read = api.get(f"/api/v1/cases/{case_id}/overview", headers=lawyer_headers)
    write = api.post(f"/api/v1/cases/{case_id}/events", headers=client_headers, json={"title": "No permitido"})

    assert read.status_code == 200
    assert write.status_code == 403


def test_case_overview_returns_404_for_missing_case(api: TestClient, db_session: Session) -> None:
    headers = auth_headers(api)
    seed_db_for_auth_tenant(api, db_session, headers)

    response = api.get("/api/v1/cases/00000000-0000-0000-0000-000000000000/overview", headers=headers)

    assert response.status_code == 404
