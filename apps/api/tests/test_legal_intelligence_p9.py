from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import AuditLog, Base, Case, LegalNews, Tenant
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


def seed_for_intelligence(api: TestClient, db_session: Session) -> tuple[str, str, str]:
    seed_demo_data()
    headers = login(api, DEMO_SEED.admin_email)
    tenant_id = api.get("/api/v1/auth/me", headers=headers).json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)
    legal_case = db_session.scalars(select(Case).where(Case.tenant_id == tenant_id)).first()
    news = db_session.scalars(select(LegalNews).where(LegalNews.tenant_id == tenant_id)).first()
    assert legal_case is not None
    assert news is not None
    return tenant_id, legal_case.id, news.id


def test_sources_create_and_sync_mock_news(api: TestClient, db_session: Session) -> None:
    tenant_id, _, _ = seed_for_intelligence(api, db_session)
    headers = login(api, DEMO_SEED.admin_email)

    created = api.post(
        "/api/v1/legal-intelligence/sources",
        headers=headers,
        json={"name": "LP Derecho", "source_url": "https://lpderecho.pe", "category": "news", "adapter_key": "lp_derecho"},
    )
    sources = api.get("/api/v1/legal-intelligence/sources", headers=headers)
    synced = api.post(f"/api/v1/legal-intelligence/sources/{created.json()['id']}/sync", headers=headers)
    news = api.get("/api/v1/legal-intelligence/news?tag=procesal", headers=headers)

    assert created.status_code == 201
    assert sources.status_code == 200
    assert synced.json()["created"] == 1
    assert news.status_code == 200
    assert any(item["title"].startswith("LP Derecho") for item in news.json())
    audits = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.entity_type == "legal_news_source")).all()
    assert any(item.action == "legal_news_source_synced" for item in audits)


def test_news_summary_favorite_link_alerts_and_trends(api: TestClient, db_session: Session) -> None:
    _, case_id, news_id = seed_for_intelligence(api, db_session)
    headers = login(api, DEMO_SEED.lawyer_email)

    listed = api.get("/api/v1/legal-intelligence/news", headers=headers)
    detail = api.get(f"/api/v1/legal-intelligence/news/{news_id}", headers=headers)
    summary = api.post(f"/api/v1/legal-intelligence/news/{news_id}/summarize", headers=headers)
    favorite = api.post(f"/api/v1/legal-intelligence/news/{news_id}/favorite", headers=headers)
    linked = api.post(f"/api/v1/legal-intelligence/news/{news_id}/link-case", headers=headers, json={"case_id": case_id, "note": "Relacionado al debido proceso."})
    overview = api.get(f"/api/v1/cases/{case_id}/overview", headers=headers)
    alerts = api.get("/api/v1/legal-intelligence/alerts", headers=headers)
    trends = api.get("/api/v1/legal-intelligence/trends", headers=headers)

    assert listed.status_code == 200
    assert detail.json()["id"] == news_id
    assert "Requiere" in summary.json()["ai_summary"]
    assert favorite.json()["favorite"] is True
    assert linked.json()["case_id"] == case_id
    assert overview.json()["related_intelligence"][0]["id"] == news_id
    assert alerts.json()
    assert trends.json()[0]["tag"] in {"jurisprudencia", "debido-proceso"}


def test_intelligence_permissions_and_tenant_isolation(api: TestClient, db_session: Session) -> None:
    _, _, news_id = seed_for_intelligence(api, db_session)
    client_headers = login(api, DEMO_SEED.client_email)
    lawyer_headers = login(api, DEMO_SEED.lawyer_email)
    other_tenant = Tenant(name="Intelligence Other", slug="intelligence-other")
    db_session.add(other_tenant)
    db_session.flush()
    other_news = LegalNews(
        tenant_id=other_tenant.id,
        source_id="missing-source",
        title="Other tenant news",
        url="https://other.demo/news",
        category="news",
        tags=["other"],
    )
    db_session.add(other_news)
    db_session.commit()

    blocked_client = api.get("/api/v1/legal-intelligence/news", headers=client_headers)
    blocked_cross_tenant = api.get(f"/api/v1/legal-intelligence/news/{other_news.id}", headers=lawyer_headers)
    allowed = api.get(f"/api/v1/legal-intelligence/news/{news_id}", headers=lawyer_headers)

    assert blocked_client.status_code == 403
    assert blocked_cross_tenant.status_code == 404
    assert allowed.status_code == 200
