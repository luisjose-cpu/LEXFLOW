from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import Base, EmailDeliveryLog
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


def login(api: TestClient) -> dict[str, str]:
    response = api.post(
        "/api/v1/auth/login",
        json={"email": DEMO_SEED.admin_email, "password": DEMO_SEED.password, "tenant_slug": DEMO_SEED.tenant_slug},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_email_delivery_logs_are_tenant_scoped_and_redacted(api: TestClient, db_session: Session) -> None:
    seed_demo_data()
    headers = login(api)
    me = api.get("/api/v1/auth/me", headers=headers)
    tenant_id = me.json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)

    reset = api.post(
        "/api/v1/auth/password-reset/request",
        json={"email": DEMO_SEED.admin_email, "tenant_slug": DEMO_SEED.tenant_slug},
    )
    invited = api.post(
        "/api/v1/users/invitations",
        headers=headers,
        json={"email": "delivery@lexflow.com", "full_name": "Delivery Lawyer", "role": "lawyer"},
    )
    deliveries = api.get("/api/v1/settings/email/deliveries", headers=headers)
    stored = db_session.scalars(select(EmailDeliveryLog).where(EmailDeliveryLog.tenant_id == tenant_id)).all()

    assert reset.status_code == 200
    assert invited.status_code == 201
    assert deliveries.status_code == 200
    assert {item["template"] for item in deliveries.json()} == {"password_reset", "user_invitation"}
    assert all("recipient_hash" not in item for item in deliveries.json())
    assert any(item["recipient_hint"] == "ad***@lexflow.demo" for item in deliveries.json())
    assert all(log.recipient_hash and "@" not in log.recipient_hash for log in stored)
