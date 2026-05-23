from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import AuditLog, Base, Tenant
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


def seed_for_os(api: TestClient, db_session: Session) -> str:
    seed_demo_data()
    headers = login(api, DEMO_SEED.admin_email)
    tenant_id = api.get("/api/v1/auth/me", headers=headers).json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)
    return tenant_id


def test_lexflow_os_memory_graph_demo_and_release_status(api: TestClient, db_session: Session) -> None:
    seed_for_os(api, db_session)
    headers = login(api, DEMO_SEED.admin_email)

    memory = api.get("/api/v1/lexflow-os/memory", headers=headers)
    graph = api.get("/api/v1/lexflow-os/graph", headers=headers)
    demo = api.get("/api/v1/lexflow-os/demo", headers=headers)
    release = api.get("/api/v1/lexflow-os/release-status", headers=headers)

    assert memory.status_code == 200
    assert memory.json()["summary"]["cases"] == 3
    assert "CLIENTE" in memory.json()["chain"]
    assert graph.status_code == 200
    assert graph.json()["nodes"]
    assert graph.json()["edges"]
    assert demo.json()["steps"][0]["surface"] == "dashboard"
    assert demo.json()["steps"][-1]["surface"] == "audit_log"
    assert release.json()["pilot_ready"] is True
    assert release.json()["production_ready"] is False
    assert release.json()["status"] == "RELEASE READY FOR PILOT / NOT READY FOR PUBLIC PRODUCTION"


def test_rag_returns_sources_or_no_evidence_and_audits(api: TestClient, db_session: Session) -> None:
    tenant_id = seed_for_os(api, db_session)
    headers = login(api, DEMO_SEED.lawyer_email)

    found = api.post("/api/v1/lexflow-os/rag/query", headers=headers, json={"query": "Nova demanda plazo"})
    missing = api.post("/api/v1/lexflow-os/rag/query", headers=headers, json={"query": "tema inexistente zzz"})

    assert found.status_code == 200
    assert found.json()["sources"]
    assert found.json()["pipeline"][-1] == "answer_with_sources"
    assert found.json()["disclaimer"] == "Requiere revision profesional."
    assert missing.json()["answer"] == "No encontre evidencia en las fuentes disponibles."
    assert missing.json()["sources"] == []
    audits = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.action == "lexflow_os_rag_query")).all()
    assert len(audits) == 2


def test_global_search_copilot_agents_and_marketplace(api: TestClient, db_session: Session) -> None:
    seed_for_os(api, db_session)
    headers = login(api, DEMO_SEED.admin_email)

    search = api.post("/api/v1/lexflow-os/search", headers=headers, json={"query": "Nova"})
    copilot = api.post("/api/v1/lexflow-os/copilot", headers=headers, json={"prompt": "Resume Nova con fuentes"})
    agents = api.get("/api/v1/lexflow-os/agents", headers=headers)
    marketplace = api.get("/api/v1/lexflow-os/marketplace", headers=headers)

    assert search.json()["total"] >= 2
    assert search.json()["results"]["cases"]
    assert copilot.json()["sources"]
    assert copilot.json()["disclaimer"] == "Requiere revision profesional."
    assert len(agents.json()["agents"]) >= 6
    assert "No evade CAPTCHA." in agents.json()["guardrails"]
    assert marketplace.json()["status"] == "future_ready"


def test_p15_permissions_and_tenant_isolation(api: TestClient, db_session: Session) -> None:
    seed_for_os(api, db_session)
    client_headers = login(api, DEMO_SEED.client_email)
    lawyer_headers = login(api, DEMO_SEED.lawyer_email)
    other_tenant = Tenant(name="OS Other", slug="os-other")
    db_session.add(other_tenant)
    db_session.commit()

    blocked_client = api.post("/api/v1/lexflow-os/rag/query", headers=client_headers, json={"query": "Nova"})
    blocked_cross_tenant = api.get("/api/v1/lexflow-os/memory", headers={**lawyer_headers, "X-Tenant-Id": other_tenant.id})

    assert blocked_client.status_code == 403
    assert blocked_cross_tenant.status_code == 403
