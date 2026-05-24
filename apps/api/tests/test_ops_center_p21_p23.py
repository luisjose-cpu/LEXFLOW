from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import Base
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


def seed_for_ops(api: TestClient, db_session: Session) -> str:
    seed_demo_data()
    headers = login(api, DEMO_SEED.admin_email)
    tenant_id = api.get("/api/v1/auth/me", headers=headers).json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)
    return tenant_id


def test_import_templates_endpoint(api: TestClient, db_session: Session) -> None:
    seed_for_ops(api, db_session)
    headers = login(api, DEMO_SEED.admin_email)

    response = api.get("/api/v1/ops/import/templates", headers=headers)

    assert response.status_code == 200
    kinds = {item["kind"] for item in response.json()["templates"]}
    assert {"clients", "cases", "documents"}.issubset(kinds)
    assert "import document manifest" in response.json()["flow"]


def test_pilot_readiness_endpoint_counts_tenant_data(api: TestClient, db_session: Session) -> None:
    tenant_id = seed_for_ops(api, db_session)
    headers = login(api, DEMO_SEED.admin_email)

    response = api.get("/api/v1/ops/pilot/readiness", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == tenant_id
    assert body["metrics"]["clients"] == 3
    assert body["metrics"]["cases"] == 3
    assert body["metrics"]["documents"] == 3
    assert any(item["key"] == "storage" and item["ok"] for item in body["checklist"])


def test_production_gate_and_permissions(api: TestClient, db_session: Session) -> None:
    seed_for_ops(api, db_session)
    admin_headers = login(api, DEMO_SEED.admin_email)
    client_headers = login(api, DEMO_SEED.client_email)

    gate = api.get("/api/v1/ops/production-gate", headers=admin_headers)
    blocked = api.get("/api/v1/ops/production-gate", headers=client_headers)

    assert gate.status_code == 200
    assert gate.json()["gate"] == "P23 Production Gate"
    assert "npm run test:api" in gate.json()["commands"]
    assert "npm run cloud:public-ready" in gate.json()["commands"]
    assert gate.json()["status"] == "blocked"
    assert gate.json()["public_production_status"] == "blocked"
    assert "revision" in gate.json()
    assert gate.json()["external_providers"]["ai"] == "mock"
    assert any("database_postgresql" in item for item in gate.json()["required_before_public_production"])
    assert "HTTPS-only public origins" in gate.json()["required_before_public_production"]
    assert blocked.status_code == 403
