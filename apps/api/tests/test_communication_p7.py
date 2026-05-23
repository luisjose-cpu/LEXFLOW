from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import AuditLog, Base, Case, CommunicationMessage, MessageTemplate, Notification
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


def seed_for_auth_tenant(api: TestClient, db_session: Session) -> tuple[str, str]:
    seed_demo_data()
    admin_headers = login(api, DEMO_SEED.admin_email)
    me = api.get("/api/v1/auth/me", headers=admin_headers)
    tenant_id = me.json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)
    legal_case = db_session.scalars(select(Case).where(Case.tenant_id == tenant_id, Case.title == "Cobro ejecutivo Nova")).one()
    return tenant_id, legal_case.id


def test_templates_crud_and_render_test(api: TestClient, db_session: Session) -> None:
    _, _ = seed_for_auth_tenant(api, db_session)
    headers = login(api, DEMO_SEED.admin_email)

    listed = api.get("/api/v1/message-templates", headers=headers)
    created = api.post(
        "/api/v1/message-templates",
        headers=headers,
        json={"code": "custom_update", "name": "Custom update", "channel": "portal", "body": "Hola {{client_name}}"},
    )
    template_id = created.json()["id"]
    updated = api.patch(f"/api/v1/message-templates/{template_id}", headers=headers, json={"body": "Hola {{client_name}}, informe listo"})
    rendered = api.post(f"/api/v1/notifications/test", headers=headers, json={"template_id": template_id, "variables": {"client_name": "Nova"}})

    assert listed.status_code == 200
    assert any(item["code"] == "audiencia_proxima" for item in listed.json())
    assert created.status_code == 201
    assert updated.json()["body"] == "Hola {{client_name}}, informe listo"
    assert rendered.json()["body"] == "Hola Nova, informe listo"


def test_whatsapp_mock_creates_message_and_audit(api: TestClient, db_session: Session) -> None:
    tenant_id, case_id = seed_for_auth_tenant(api, db_session)
    headers = login(api, DEMO_SEED.lawyer_email)

    response = api.post(
        f"/api/v1/cases/{case_id}/communications",
        headers=headers,
        json={"body": "Recordatorio WhatsApp mock", "channel": "whatsapp", "direction": "outbound", "to_number": "+571111111111"},
    )

    stored = db_session.scalars(select(CommunicationMessage).where(CommunicationMessage.body == "Recordatorio WhatsApp mock")).first()
    audits = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.entity_type == "communication_message")).all()

    assert response.status_code == 201
    assert response.json()["status"] == "sent"
    assert response.json()["provider_message_id"].startswith("mock-whatsapp-")
    assert stored is not None
    assert stored.channel == "whatsapp"
    assert any(item.action == "communication_message_created" for item in audits)


def test_notifications_send_list_mark_read_and_audit(api: TestClient, db_session: Session) -> None:
    tenant_id, case_id = seed_for_auth_tenant(api, db_session)
    headers = login(api, DEMO_SEED.admin_email)
    template = db_session.scalars(select(MessageTemplate).where(MessageTemplate.tenant_id == tenant_id, MessageTemplate.code == "informe_disponible")).one()

    sent = api.post(
        "/api/v1/notifications/send",
        headers=headers,
        json={
            "case_id": case_id,
            "title": "Informe disponible",
            "channel": "portal",
            "template_id": template.id,
            "variables": {"case_title": "Cobro ejecutivo Nova"},
        },
    )
    notification_id = sent.json()["id"]
    listed = api.get("/api/v1/notifications", headers=headers)
    read = api.post(f"/api/v1/notifications/{notification_id}/mark-read", headers=headers)

    stored = db_session.get(Notification, notification_id)
    audits = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id)).all()

    assert sent.status_code == 201
    assert "Cobro ejecutivo Nova" in sent.json()["body"]
    assert any(item["id"] == notification_id for item in listed.json())
    assert read.json()["status"] == "read"
    assert stored is not None
    assert stored.read_at is not None
    assert any(item.action == "notification_sent" for item in audits)
    assert any(item.action == "notification_marked_read" for item in audits)


def test_client_to_lawyer_e2e_message_bridge(api: TestClient, db_session: Session) -> None:
    _, case_id = seed_for_auth_tenant(api, db_session)
    client_headers = login(api, DEMO_SEED.client_email)
    lawyer_headers = login(api, DEMO_SEED.lawyer_email)

    client_message = api.post(
        f"/api/v1/client-portal/cases/{case_id}/messages",
        headers=client_headers,
        json={"body": "Necesito confirmar la audiencia."},
    )
    communications = api.get(f"/api/v1/cases/{case_id}/communications", headers=lawyer_headers)

    assert client_message.status_code == 201
    assert communications.status_code == 200
    thread_messages = [message for thread in communications.json() for message in thread["messages"]]
    assert any(message["body"] == "Necesito confirmar la audiencia." and message["direction"] == "inbound" for message in thread_messages)


def test_client_user_cannot_use_internal_communication_endpoint(api: TestClient, db_session: Session) -> None:
    _, case_id = seed_for_auth_tenant(api, db_session)
    client_headers = login(api, DEMO_SEED.client_email)

    blocked = api.post(
        f"/api/v1/cases/{case_id}/communications",
        headers=client_headers,
        json={"body": "No debe pasar", "channel": "portal"},
    )

    assert blocked.status_code == 403
