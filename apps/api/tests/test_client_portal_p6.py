from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import AuditLog, Base, Case, CaseEvent, CaseSource, Document, JudicialUpdate, WhatsAppMessage, now_utc
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


def seed_for_portal(api: TestClient, db_session: Session) -> tuple[str, str, str]:
    seed_demo_data()
    admin_headers = login(api, DEMO_SEED.admin_email)
    me = api.get("/api/v1/auth/me", headers=admin_headers)
    tenant_id = me.json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)
    client_case = db_session.scalars(select(Case).where(Case.tenant_id == tenant_id, Case.title == "Cobro ejecutivo Nova")).one()
    other_case = db_session.scalars(select(Case).where(Case.tenant_id == tenant_id, Case.title == "Laboral colectivo Andes")).one()
    return tenant_id, client_case.id, other_case.id


def test_client_portal_me_cases_and_reports_are_scoped(api: TestClient, db_session: Session) -> None:
    tenant_id, client_case_id, other_case_id = seed_for_portal(api, db_session)
    client_headers = login(api, DEMO_SEED.client_email)

    me = api.get("/api/v1/client-portal/me", headers=client_headers)
    cases = api.get("/api/v1/client-portal/cases", headers=client_headers)
    reports = api.get("/api/v1/client-portal/reports", headers=client_headers)
    blocked_other = api.get(f"/api/v1/client-portal/cases/{other_case_id}", headers=client_headers)

    assert me.status_code == 200
    assert me.json()["client"]["name"] == "Nova Capital"
    assert {item["id"] for item in cases.json()} == {client_case_id}
    assert reports.json()["metrics"]["cases"] == 1
    assert blocked_other.status_code == 404
    assert db_session.scalars(select(Case).where(Case.tenant_id == tenant_id)).all()


def test_document_visibility_blocks_private_and_other_client_docs(api: TestClient, db_session: Session) -> None:
    _, client_case_id, other_case_id = seed_for_portal(api, db_session)
    client_headers = login(api, DEMO_SEED.client_email)
    client_case = db_session.get(Case, client_case_id)
    other_case = db_session.get(Case, other_case_id)
    assert client_case is not None
    assert other_case is not None
    db_session.add(
        Document(
            tenant_id=client_case.tenant_id,
            case_id=client_case.id,
            client_id=client_case.client_id,
            filename="estrategia-interna.pdf",
            storage_key="private/internal.pdf",
            status="private",
            classification="strategy",
            is_client_visible=False,
        )
    )
    db_session.add(
        Document(
            tenant_id=other_case.tenant_id,
            case_id=other_case.id,
            client_id=other_case.client_id,
            filename="andes-visible.pdf",
            storage_key="other/visible.pdf",
            is_client_visible=True,
        )
    )
    db_session.commit()

    response = api.get(f"/api/v1/client-portal/cases/{client_case_id}/documents", headers=client_headers)

    filenames = {item["filename"] for item in response.json()}
    assert response.status_code == 200
    assert "Cobro ejecutivo Nova.pdf" in filenames
    assert "estrategia-interna.pdf" not in filenames
    assert "andes-visible.pdf" not in filenames


def test_public_timeline_hides_internal_events_and_unapproved_updates(api: TestClient, db_session: Session) -> None:
    _, client_case_id, _ = seed_for_portal(api, db_session)
    client_headers = login(api, DEMO_SEED.client_email)
    legal_case = db_session.get(Case, client_case_id)
    assert legal_case is not None
    source = db_session.scalars(select(CaseSource).where(CaseSource.case_id == client_case_id)).first()
    assert source is not None
    db_session.add_all(
        [
            CaseEvent(tenant_id=legal_case.tenant_id, case_id=legal_case.id, event_type="portal", title="Hito publico", is_client_visible=True),
            CaseEvent(tenant_id=legal_case.tenant_id, case_id=legal_case.id, event_type="strategy", title="Estrategia interna", is_client_visible=False),
            JudicialUpdate(
                tenant_id=legal_case.tenant_id,
                case_id=legal_case.id,
                case_source_id=source.id,
                update_type="mock",
                title="Actualizacion aprobada",
                summary="Visible para cliente.",
                status="approved",
                checked_at=now_utc(),
            ),
            JudicialUpdate(
                tenant_id=legal_case.tenant_id,
                case_id=legal_case.id,
                case_source_id=source.id,
                update_type="mock",
                title="Actualizacion no aprobada",
                summary="No visible.",
                status="pending_approval",
                checked_at=now_utc(),
            ),
        ]
    )
    db_session.commit()

    response = api.get(f"/api/v1/client-portal/cases/{client_case_id}/timeline", headers=client_headers)

    titles = {item["title"] for item in response.json()}
    assert "Hito publico" in titles
    assert "Actualizacion aprobada" in titles
    assert "Estrategia interna" not in titles
    assert "Actualizacion no aprobada" not in titles


def test_client_messages_uploads_notifications_and_audit(api: TestClient, db_session: Session) -> None:
    tenant_id, client_case_id, _ = seed_for_portal(api, db_session)
    client_headers = login(api, DEMO_SEED.client_email)

    message = api.post(f"/api/v1/client-portal/cases/{client_case_id}/messages", headers=client_headers, json={"body": "Adjunto comprobante."})
    upload = api.post(
        f"/api/v1/client-portal/cases/{client_case_id}/documents",
        headers=client_headers,
        json={"filename": "comprobante.pdf", "content_type": "application/pdf"},
    )
    notifications = api.get("/api/v1/client-portal/notifications", headers=client_headers)

    stored_message = db_session.scalars(select(WhatsAppMessage).where(WhatsAppMessage.body == "Adjunto comprobante.")).first()
    stored_upload = db_session.scalars(select(Document).where(Document.filename == "comprobante.pdf")).first()
    audits = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id)).all()

    assert message.status_code == 201
    assert upload.status_code == 201
    assert stored_message is not None
    assert stored_message.direction == "inbound"
    assert stored_upload is not None
    assert stored_upload.is_client_visible is True
    assert stored_upload.uploaded_by_client is True
    assert upload.json()["download_available"] is True
    assert upload.json()["upload"]["method"] == "PUT"
    assert any(item["title"] == "Resumen disponible" for item in notifications.json())
    assert any(item.action == "portal_message_created" for item in audits)
    assert any(item.action == "portal_document_uploaded" for item in audits)


def test_client_upload_security_rejects_unsafe_files(api: TestClient, db_session: Session) -> None:
    _, client_case_id, _ = seed_for_portal(api, db_session)
    client_headers = login(api, DEMO_SEED.client_email)

    blocked_content_type = api.post(
        f"/api/v1/client-portal/cases/{client_case_id}/documents",
        headers=client_headers,
        json={"filename": "payload.pdf", "content_type": "text/html"},
    )
    blocked_extension = api.post(
        f"/api/v1/client-portal/cases/{client_case_id}/documents",
        headers=client_headers,
        json={"filename": "../payload.exe", "content_type": "application/pdf"},
    )
    sanitized = api.post(
        f"/api/v1/client-portal/cases/{client_case_id}/documents",
        headers=client_headers,
        json={"filename": "../comprobante.pdf", "content_type": "application/pdf"},
    )

    assert blocked_content_type.status_code == 415
    assert blocked_extension.status_code == 415
    assert sanitized.status_code == 201
    assert sanitized.json()["filename"] == "comprobante.pdf"


def test_lawyer_cannot_use_client_portal(api: TestClient, db_session: Session) -> None:
    seed_for_portal(api, db_session)
    lawyer_headers = login(api, DEMO_SEED.lawyer_email)

    response = api.get("/api/v1/client-portal/me", headers=lawyer_headers)

    assert response.status_code == 403
