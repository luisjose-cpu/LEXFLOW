from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import AiJob, AuditLog, Base, Case, Document, Tenant
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


def seed_for_ai(api: TestClient, db_session: Session) -> tuple[str, str, str]:
    seed_demo_data()
    headers = login(api, DEMO_SEED.admin_email)
    me = api.get("/api/v1/auth/me", headers=headers)
    tenant_id = me.json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)
    document = db_session.scalars(select(Document).where(Document.tenant_id == tenant_id)).first()
    legal_case = db_session.scalars(select(Case).where(Case.tenant_id == tenant_id)).first()
    assert document is not None
    assert legal_case is not None
    return tenant_id, document.id, legal_case.id


def assert_review_required(body: dict[str, object]) -> None:
    result = body["result"]
    assert isinstance(result, dict)
    assert result["disclaimer"] == "Requiere revisión profesional."
    assert body["status"] == "pending_review"


def test_ocr_summary_classification_and_extraction_create_reviewable_jobs(api: TestClient, db_session: Session) -> None:
    tenant_id, document_id, _ = seed_for_ai(api, db_session)
    headers = login(api, DEMO_SEED.lawyer_email)

    ocr = api.post(f"/api/v1/ai/documents/{document_id}/ocr", headers=headers)
    summary = api.post(f"/api/v1/ai/documents/{document_id}/summarize", headers=headers)
    classification = api.post(f"/api/v1/ai/documents/{document_id}/classify", headers=headers)
    extraction = api.post(f"/api/v1/ai/documents/{document_id}/extract", headers=headers)

    for response in [ocr, summary, classification, extraction]:
        assert response.status_code == 201
        assert_review_required(response.json())

    assert "text" in ocr.json()["result"]
    assert "summary" in summary.json()["result"]
    assert classification.json()["result"]["classification"] == "evidence"
    assert "dates" in extraction.json()["result"]
    assert "parties" in extraction.json()["result"]
    assert "deadlines" in extraction.json()["result"]
    assert "obligations" in extraction.json()["result"]
    jobs = db_session.scalars(select(AiJob).where(AiJob.tenant_id == tenant_id, AiJob.document_id == document_id)).all()
    audits = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.entity_type == "ai_job")).all()
    assert len(jobs) >= 4
    assert any(item.action == "ai_job_created" for item in audits)


def test_case_summary_search_and_human_review_flow(api: TestClient, db_session: Session) -> None:
    _, _, case_id = seed_for_ai(api, db_session)
    headers = login(api, DEMO_SEED.admin_email)

    summary = api.post(f"/api/v1/ai/cases/{case_id}/summary", headers=headers)
    search = api.post(f"/api/v1/ai/cases/{case_id}/search", headers=headers, json={"query": "demanda"})
    job_id = summary.json()["id"]
    fetched = api.get(f"/api/v1/ai/jobs/{job_id}", headers=headers)
    approved = api.post(f"/api/v1/ai/jobs/{job_id}/approve", headers=headers, json={"note": "Revisado por abogado."})
    rejected = api.post(f"/api/v1/ai/jobs/{search.json()['id']}/reject", headers=headers, json={"note": "Busqueda insuficiente."})

    assert summary.status_code == 201
    assert search.status_code == 201
    assert_review_required(summary.json())
    assert fetched.json()["id"] == job_id
    assert approved.json()["status"] == "approved"
    assert approved.json()["review_note"] == "Revisado por abogado."
    assert rejected.json()["status"] == "rejected"
    assert "matches" in search.json()["result"]


def test_ai_permissions_and_tenant_isolation(api: TestClient, db_session: Session) -> None:
    _, document_id, _ = seed_for_ai(api, db_session)
    client_headers = login(api, DEMO_SEED.client_email)
    lawyer_headers = login(api, DEMO_SEED.lawyer_email)
    other_tenant = Tenant(name="AI Other", slug="ai-other")
    db_session.add(other_tenant)
    db_session.flush()
    other_document = Document(
        tenant_id=other_tenant.id,
        case_id="missing-case",
        client_id="missing-client",
        filename="other.pdf",
        storage_key="other.pdf",
    )
    db_session.add(other_document)
    db_session.commit()

    blocked_client = api.post(f"/api/v1/ai/documents/{document_id}/ocr", headers=client_headers)
    blocked_cross_tenant = api.post(f"/api/v1/ai/documents/{other_document.id}/ocr", headers=lawyer_headers)

    assert blocked_client.status_code == 403
    assert blocked_cross_tenant.status_code == 404
