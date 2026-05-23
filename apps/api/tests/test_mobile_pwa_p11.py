from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import Base, Case
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


def seed_for_mobile(api: TestClient, db_session: Session) -> str:
    seed_demo_data()
    headers = login(api, DEMO_SEED.admin_email)
    tenant_id = api.get("/api/v1/auth/me", headers=headers).json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)
    return tenant_id


def test_mobile_client_endpoints_are_client_scoped(api: TestClient, db_session: Session) -> None:
    tenant_id = seed_for_mobile(api, db_session)
    headers = login(api, DEMO_SEED.client_email)
    case_id = db_session.scalars(select(Case.id).where(Case.tenant_id == tenant_id, Case.title.like("%Nova%"))).first()

    home = api.get("/api/v1/mobile/client/home", headers=headers)
    cases = api.get("/api/v1/mobile/client/cases", headers=headers)
    detail = api.get(f"/api/v1/mobile/client/cases/{case_id}", headers=headers)
    documents = api.get("/api/v1/mobile/client/documents", headers=headers)
    messages = api.get("/api/v1/mobile/client/messages", headers=headers)
    notifications = api.get("/api/v1/mobile/client/notifications", headers=headers)

    assert home.status_code == 200
    assert home.json()["metrics"]["cases"] == 1
    assert len(cases.json()) == 1
    assert detail.json()["case"]["id"] == case_id
    assert all(item["case_id"] == case_id for item in documents.json())
    assert messages.status_code == 200
    assert notifications.status_code == 200


def test_mobile_lawyer_endpoints_include_operational_workspace(api: TestClient, db_session: Session) -> None:
    seed_for_mobile(api, db_session)
    headers = login(api, DEMO_SEED.lawyer_email)
    cases = api.get("/api/v1/mobile/lawyer/cases", headers=headers)
    case_id = cases.json()[0]["id"]

    home = api.get("/api/v1/mobile/lawyer/home", headers=headers)
    detail = api.get(f"/api/v1/mobile/lawyer/cases/{case_id}", headers=headers)
    tasks = api.get("/api/v1/mobile/lawyer/tasks", headers=headers)
    hearings = api.get("/api/v1/mobile/lawyer/hearings", headers=headers)
    notifications = api.get("/api/v1/mobile/lawyer/notifications", headers=headers)

    assert home.json()["dashboard"]["kpis"]["active_cases"] == 3
    assert len(cases.json()) == 3
    assert "ai_summary" in detail.json()
    assert len(tasks.json()) >= 3
    assert len(hearings.json()) == 3
    assert notifications.status_code == 200


def test_mobile_permissions_separate_client_and_lawyer(api: TestClient, db_session: Session) -> None:
    seed_for_mobile(api, db_session)
    client_headers = login(api, DEMO_SEED.client_email)
    lawyer_headers = login(api, DEMO_SEED.lawyer_email)

    client_blocked = api.get("/api/v1/mobile/lawyer/home", headers=client_headers)
    lawyer_blocked = api.get("/api/v1/mobile/client/home", headers=lawyer_headers)

    assert client_blocked.status_code == 403
    assert lawyer_blocked.status_code == 403
