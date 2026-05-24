from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import Base, Case, Client
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


def seed_operational(api: TestClient, db_session: Session, headers: dict[str, str]) -> tuple[str, str, str]:
    me = api.get("/api/v1/auth/me", headers=headers)
    tenant_id = me.json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)
    client = db_session.scalars(select(Client).where(Client.tenant_id == tenant_id)).first()
    legal_case = db_session.scalars(select(Case).where(Case.tenant_id == tenant_id)).first()
    assert client is not None
    assert legal_case is not None
    return tenant_id, client.id, legal_case.id


def test_global_clients_and_cases_search(api: TestClient, db_session: Session) -> None:
    headers = auth_headers(api)
    seed_operational(api, db_session, headers)

    global_search = api.get("/api/v1/dashboard/search?q=Nova", headers=headers)
    client_search = api.get("/api/v1/clients/search?q=Nova", headers=headers)
    case_search = api.get("/api/v1/cases/search?q=11001", headers=headers)

    assert global_search.status_code == 200
    assert global_search.json()["quick_results"]
    assert global_search.json()["ai_future_ready"] is True
    assert client_search.status_code == 200
    assert client_search.json()[0]["name"] == "Nova Capital"
    assert case_search.status_code == 200
    assert case_search.json()[0]["external_case_number"].startswith("11001")


def test_client_operational_profile_timeline_metrics_and_risk(api: TestClient, db_session: Session) -> None:
    headers = auth_headers(api)
    _, client_id, _ = seed_operational(api, db_session, headers)

    profile = api.get(f"/api/v1/clients/{client_id}/profile", headers=headers)
    timeline = api.get(f"/api/v1/clients/{client_id}/timeline", headers=headers)
    documents = api.get(f"/api/v1/clients/{client_id}/documents", headers=headers)
    metrics = api.get(f"/api/v1/clients/{client_id}/metrics", headers=headers)
    risk = api.get(f"/api/v1/clients/{client_id}/risk", headers=headers)

    assert profile.status_code == 200
    assert profile.json()["client"]["name"] == "Nova Capital"
    assert timeline.status_code == 200
    assert timeline.json()
    assert documents.status_code == 200
    assert documents.json()
    assert metrics.json()["active_cases"] >= 1
    assert "level" in risk.json()


def test_case_operational_resources_consume_sinoe_and_adjacent_modules(api: TestClient, db_session: Session) -> None:
    headers = auth_headers(api)
    _, _, case_id = seed_operational(api, db_session, headers)

    documents = api.get(f"/api/v1/cases/{case_id}/documents", headers=headers)
    hearings = api.get(f"/api/v1/cases/{case_id}/hearings", headers=headers)
    judicial = api.get(f"/api/v1/cases/{case_id}/judicial", headers=headers)
    automation = api.get(f"/api/v1/cases/{case_id}/automation", headers=headers)
    intelligence = api.get(f"/api/v1/cases/{case_id}/intelligence", headers=headers)

    assert documents.status_code == 200
    assert hearings.status_code == 200
    assert judicial.status_code == 200
    assert judicial.json()["sinoe_module"] == "consumed"
    assert automation.status_code == 200
    assert "available_triggers" in automation.json()
    assert intelligence.status_code == 200
    assert "linked_news" in intelligence.json()


def test_operational_core_blocks_cross_tenant(api: TestClient, db_session: Session) -> None:
    headers = auth_headers(api)
    _, _, case_id = seed_operational(api, db_session, headers)

    blocked = api.get(
        f"/api/v1/cases/{case_id}/judicial",
        headers={**headers, "X-Tenant-Id": "00000000-0000-0000-0000-000000000999"},
    )

    assert blocked.status_code == 403
