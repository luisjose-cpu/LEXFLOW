from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import Base, Tenant
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


def seed_for_dashboard(api: TestClient, db_session: Session) -> str:
    seed_demo_data()
    headers = login(api, DEMO_SEED.admin_email)
    tenant_id = api.get("/api/v1/auth/me", headers=headers).json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)
    return tenant_id


def test_dashboard_overview_and_snapshot(api: TestClient, db_session: Session) -> None:
    seed_for_dashboard(api, db_session)
    headers = login(api, DEMO_SEED.admin_email)

    overview = api.get("/api/v1/dashboard/overview", headers=headers)
    kpis = api.get("/api/v1/dashboard/kpis", headers=headers)
    snapshot = api.get("/api/v1/dashboard/snapshot", headers=headers)

    assert overview.status_code == 200
    assert overview.json()["kpis"]["active_cases"] == 3
    assert kpis.json()["clients"] == 3
    assert snapshot.json()["executive_state"] in {"controlled", "attention_required"}
    assert "decision_queue" in snapshot.json()


def test_dashboard_domain_endpoints(api: TestClient, db_session: Session) -> None:
    seed_for_dashboard(api, db_session)
    headers = login(api, DEMO_SEED.lawyer_email)

    risks = api.get("/api/v1/dashboard/risks", headers=headers)
    productivity = api.get("/api/v1/dashboard/productivity", headers=headers)
    monitoring = api.get("/api/v1/dashboard/judicial-monitoring", headers=headers)
    communications = api.get("/api/v1/dashboard/communications", headers=headers)
    ai = api.get("/api/v1/dashboard/ai", headers=headers)
    intelligence = api.get("/api/v1/dashboard/legal-intelligence", headers=headers)
    trends = api.get("/api/v1/dashboard/trends", headers=headers)

    assert risks.json()["critical_cases"]
    assert productivity.json()["open_tasks"] >= 3
    assert monitoring.json()["sources"] == 3
    assert communications.json()["total"] >= 6
    assert ai.json()["total"] == 3
    assert intelligence.json()["news"] == 1
    assert trends.json()["top_tags"]


def test_dashboard_permissions_and_tenant_isolation(api: TestClient, db_session: Session) -> None:
    seed_for_dashboard(api, db_session)
    client_headers = login(api, DEMO_SEED.client_email)
    lawyer_headers = login(api, DEMO_SEED.lawyer_email)
    other_tenant = Tenant(name="Dashboard Other", slug="dashboard-other")
    db_session.add(other_tenant)
    db_session.commit()

    blocked_client = api.get("/api/v1/dashboard/kpis", headers=client_headers)
    blocked_cross_tenant = api.get("/api/v1/dashboard/kpis", headers={**lawyer_headers, "X-Tenant-Id": other_tenant.id})

    assert blocked_client.status_code == 403
    assert blocked_cross_tenant.status_code == 403
