from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import AuditLog, Base, Case, Client, Document, Tenant
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


def tenant_id_from_auth(api: TestClient, headers: dict[str, str]) -> str:
    response = api.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    return response.json()["tenant_id"]


def test_bootstrap_current_tenant_and_import_clients_cases_documents(api: TestClient, db_session: Session) -> None:
    seed_demo_data()
    headers = login(api, DEMO_SEED.admin_email)
    tenant_id = tenant_id_from_auth(api, headers)

    bootstrapped = api.post(
        "/api/v1/ops/bootstrap/current-tenant",
        headers=headers,
        json={"name": "Estudio Piloto", "slug": "estudio-piloto", "plan": "pilot"},
    )
    clients_csv = "name,contact_email,risk_profile,tags\nAcme Legal,legal@acme.test,high,corporate;pilot\nBeta Corp,legal@beta.test,standard,contracts\n"
    preview_clients = api.post("/api/v1/ops/import/clients", headers=headers, json={"csv_text": clients_csv, "dry_run": True})
    preview_client_rows = db_session.scalars(select(Client).where(Client.tenant_id == tenant_id)).all()
    imported_clients = api.post("/api/v1/ops/import/clients", headers=headers, json={"csv_text": clients_csv, "dry_run": False})

    cases_csv = "client_email,title,external_case_number,status,description\nlegal@acme.test,Cobro Acme,ACME-001,active,Expediente piloto\n"
    imported_cases = api.post("/api/v1/ops/import/cases", headers=headers, json={"csv_text": cases_csv, "dry_run": False})

    documents_csv = "case_external_case_number,filename,content_type,classification,is_client_visible\nACME-001,demanda-acme.pdf,application/pdf,pleading,true\n"
    imported_documents = api.post("/api/v1/ops/import/documents", headers=headers, json={"csv_text": documents_csv, "dry_run": False})

    tenant = db_session.get(Tenant, tenant_id)
    clients = db_session.scalars(select(Client).where(Client.tenant_id == tenant_id)).all()
    legal_case = db_session.scalars(select(Case).where(Case.tenant_id == tenant_id, Case.external_case_number == "ACME-001")).one()
    document = db_session.scalars(select(Document).where(Document.tenant_id == tenant_id, Document.filename == "demanda-acme.pdf")).one()
    audits = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id)).all()

    assert bootstrapped.status_code == 200
    assert bootstrapped.json()["created"] is True
    assert tenant is not None
    assert tenant.slug == "estudio-piloto"
    assert preview_clients.json()["created"] == 2
    assert preview_client_rows == []
    assert imported_clients.status_code == 200
    assert imported_clients.json()["created"] == 2
    assert len(clients) == 2
    assert imported_cases.json()["created"] == 1
    assert legal_case.client_id == clients[0].id
    assert imported_documents.json()["created"] == 1
    assert document.status == "pending_upload"
    assert document.is_client_visible is True
    assert document.storage_key.startswith(f"tenants/{tenant_id}/cases/{legal_case.id}/documents/{document.id}/")
    assert any(item.action == "tenant_bootstrapped" for item in audits)
    assert any(item.action == "clients_imported" for item in audits)
    assert any(item.action == "cases_imported" for item in audits)
    assert any(item.action == "documents_manifest_imported" for item in audits)


def test_import_reports_errors_without_partial_commit(api: TestClient, db_session: Session) -> None:
    seed_demo_data()
    headers = login(api, DEMO_SEED.admin_email)
    tenant_id = tenant_id_from_auth(api, headers)
    api.post("/api/v1/ops/bootstrap/current-tenant", headers=headers, json={"name": "Estudio Piloto", "slug": "pilot", "plan": "pilot"})

    bad_cases_csv = "client_email,title,external_case_number\nmissing@example.test,Caso sin cliente,NOPE-001\n"
    response = api.post("/api/v1/ops/import/cases", headers=headers, json={"csv_text": bad_cases_csv, "dry_run": False})

    assert response.status_code == 200
    assert response.json()["errors"][0]["error"] == "client not found"
    assert db_session.scalars(select(Case).where(Case.tenant_id == tenant_id)).all() == []


def test_import_permissions_and_cross_tenant_guard(api: TestClient, db_session: Session) -> None:
    seed_demo_data()
    admin_headers = login(api, DEMO_SEED.admin_email)
    client_headers = login(api, DEMO_SEED.client_email)
    tenant_id = tenant_id_from_auth(api, admin_headers)
    other_tenant = Tenant(name="Other Import", slug="other-import")
    db_session.add(other_tenant)
    db_session.commit()

    clients_csv = "name,contact_email\nAcme Legal,legal@acme.test\n"
    blocked_client = api.post("/api/v1/ops/import/clients", headers=client_headers, json={"csv_text": clients_csv, "dry_run": True})
    blocked_cross_tenant = api.post(
        "/api/v1/ops/import/clients",
        headers={**admin_headers, "X-Tenant-Id": other_tenant.id},
        json={"csv_text": clients_csv, "dry_run": True},
    )

    assert blocked_client.status_code == 403
    assert blocked_cross_tenant.status_code == 403
    assert tenant_id != other_tenant.id
