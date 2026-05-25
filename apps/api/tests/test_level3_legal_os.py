from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import AiAgentRun, AuditLog, Base, Tenant
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


def seed_level3(api: TestClient, db_session: Session) -> tuple[dict[str, str], str]:
    seed_demo_data()
    headers = login(api, DEMO_SEED.admin_email)
    tenant_id = api.get("/api/v1/auth/me", headers=headers).json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)
    return headers, tenant_id


def test_digital_twin_operational_map_and_risk(api: TestClient, db_session: Session) -> None:
    headers, _tenant_id = seed_level3(api, db_session)

    response = api.get("/api/v1/digital-twin", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["operational_map"]["cases"] == 3
    assert body["lawyer_load"]
    assert body["case_complexity"]
    assert body["simulation"]["recommended_controls"]


def test_knowledge_vault_create_and_search(api: TestClient, db_session: Session) -> None:
    headers, tenant_id = seed_level3(api, db_session)

    created = api.post(
        "/api/v1/knowledge/items",
        headers=headers,
        json={
            "source_type": "prompt",
            "category": "laboral",
            "title": "Prompt laboral exitoso",
            "content_summary": "Busca casos laborales similares y cita documentos fuente.",
            "tags": ["laboral", "similar", "fuentes"],
        },
    )
    searched = api.get("/api/v1/knowledge/search?q=laboral%20fuentes", headers=headers)

    assert created.status_code == 201
    assert searched.status_code == 200
    assert any(item["title"] == "Prompt laboral exitoso" for item in searched.json()["results"])
    assert db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.action == "knowledge.item_created")).all()


def test_memory_index_search_and_rag_citations(api: TestClient, db_session: Session) -> None:
    headers, tenant_id = seed_level3(api, db_session)

    indexed = api.post("/api/v1/intelligence/memory/index", headers=headers)
    memory = api.get("/api/v1/intelligence/memory/search?q=Nova%20demanda", headers=headers)
    rag = api.post("/api/v1/intelligence/rag/query", headers=headers, json={"query": "Nova demanda"})
    missing = api.post("/api/v1/intelligence/rag/query", headers=headers, json={"query": "zzz inexistente total"})

    assert indexed.status_code == 200
    assert indexed.json()["created"] >= 1
    assert memory.json()["results"]
    assert rag.json()["sources"]
    assert rag.json()["pipeline"][-1] == "answer_with_sources"
    assert missing.json()["answer"] == "No encontre evidencia en las fuentes disponibles."
    assert db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.action == "rag.context_query")).all()


def test_graph_relationship_and_search(api: TestClient, db_session: Session) -> None:
    headers, tenant_id = seed_level3(api, db_session)

    graph = api.get("/api/v1/graph", headers=headers)
    nodes = graph.json()["nodes"]
    created = api.post(
        "/api/v1/graph/relationships",
        headers=headers,
        json={"from_node_id": nodes[0]["id"], "to_node_id": nodes[-1]["id"], "relationship": "risk_related", "weight": 7},
    )
    searched = api.get("/api/v1/graph/search?q=Nova", headers=headers)

    assert graph.status_code == 200
    assert created.status_code == 201
    assert created.json()["relationship"] == "risk_related"
    assert searched.json()["results"]
    assert db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.action == "graph.relationship_created")).all()


def test_management_copilot_marketplace_latam_and_agents(api: TestClient, db_session: Session) -> None:
    headers, tenant_id = seed_level3(api, db_session)
    api.post("/api/v1/intelligence/memory/index", headers=headers)

    copilot = api.post("/api/v1/copilot/management", headers=headers, json={"question": "Que expediente es riesgoso y que fuente lo soporta?"})
    catalog = api.get("/api/v1/marketplace/catalog", headers=headers)
    install = api.post("/api/v1/marketplace/install", headers=headers, json={"item_id": catalog.json()["items"][0]["id"]})
    latam = api.post("/api/v1/latam/configs/defaults", headers=headers)
    agent = api.post("/api/v1/agents/case_agent/run", headers=headers, json={"payload": {"case": "Nova"}})

    assert copilot.status_code == 200
    assert copilot.json()["disclaimer"] == "Requiere revision profesional."
    assert catalog.json()["items"]
    assert install.json()["status"] == "installed"
    assert len(latam.json()["configs"]) >= 4
    assert agent.json()["output"]["review_required"] is True
    assert db_session.scalars(select(AiAgentRun).where(AiAgentRun.tenant_id == tenant_id, AiAgentRun.agent_key == "case_agent")).all()


def test_level3_permissions_and_tenant_isolation(api: TestClient, db_session: Session) -> None:
    seed_level3(api, db_session)
    client_headers = login(api, DEMO_SEED.client_email)
    lawyer_headers = login(api, DEMO_SEED.lawyer_email)
    other_tenant = Tenant(name="N3 Other", slug="n3-other")
    db_session.add(other_tenant)
    db_session.commit()

    blocked_client = api.get("/api/v1/digital-twin", headers=client_headers)
    blocked_cross_tenant = api.get("/api/v1/graph", headers={**lawyer_headers, "X-Tenant-Id": other_tenant.id})

    assert blocked_client.status_code == 403
    assert blocked_cross_tenant.status_code == 403
