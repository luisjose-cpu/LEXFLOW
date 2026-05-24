from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.database import get_db
from app.db.models import AuditLog, Base, Case, Document
from app.db.seed import seed_demo_database
from app.main import app
from app.services import client_portal as client_portal_module
from app.services import storage as storage_module
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
def api(db_session: Session, tmp_path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    settings = Settings(
        jwt_secret="test-lifecycle-secret-value-1234567890",
        storage_local_root=str(tmp_path / "storage"),
        storage_public_base_url="http://testserver/api/v1/storage/mock",
        max_upload_bytes=128,
        storage_signed_url_minutes=15,
    )
    monkeypatch.setattr(storage_module, "get_settings", lambda: settings)

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


def seed_for_lifecycle(api: TestClient, db_session: Session) -> tuple[str, str]:
    seed_demo_data()
    admin_headers = login(api, DEMO_SEED.admin_email)
    tenant_id = api.get("/api/v1/auth/me", headers=admin_headers).json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)
    legal_case = db_session.scalars(select(Case).where(Case.tenant_id == tenant_id, Case.title == "Cobro ejecutivo Nova")).one()
    return tenant_id, legal_case.id


def upload_client_document(api: TestClient, case_id: str, *, content: bytes = b"%PDF-clean") -> dict[str, object]:
    client_headers = login(api, DEMO_SEED.client_email)
    created = api.post(
        f"/api/v1/client-portal/cases/{case_id}/documents",
        headers=client_headers,
        json={"filename": "evidencia.pdf", "content_type": "application/pdf"},
    )
    assert created.status_code == 201
    uploaded = api.put(str(created.json()["upload"]["url"]), headers={"Content-Type": "application/pdf"}, content=content)
    assert uploaded.status_code == 200
    return created.json()


def test_document_verify_and_clean_scan_promotes_trusted_metadata(api: TestClient, db_session: Session) -> None:
    tenant_id, case_id = seed_for_lifecycle(api, db_session)
    admin_headers = login(api, DEMO_SEED.admin_email)
    created = upload_client_document(api, case_id)

    storage_status = api.get(f"/api/v1/documents/{created['id']}/storage", headers=admin_headers)
    verified = api.post(f"/api/v1/documents/{created['id']}/verify-storage", headers=admin_headers)
    scanned = api.post(f"/api/v1/documents/{created['id']}/scan-mock", headers=admin_headers, json={"verdict": "clean"})

    document = db_session.get(Document, created["id"])
    audits = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.entity_id == created["id"])).all()

    assert storage_status.status_code == 200
    assert storage_status.json()["storage"]["exists"] is True
    assert verified.json()["file_size_bytes"] == len(b"%PDF-clean")
    assert scanned.json()["status"] == "verified"
    assert scanned.json()["malware_scan_status"] == "clean"
    assert scanned.json()["checksum_sha256"]
    assert document is not None
    assert document.status == "verified"
    assert document.storage_verified_at is not None
    assert any(item.action == "document_storage_verified" for item in audits)
    assert any(item.action == "document_malware_scan_completed" for item in audits)


def test_document_provider_scan_uses_configured_scanner(api: TestClient, db_session: Session) -> None:
    tenant_id, case_id = seed_for_lifecycle(api, db_session)
    admin_headers = login(api, DEMO_SEED.admin_email)
    created = upload_client_document(api, case_id, content=b"%PDF-clean")

    scanned = api.post(f"/api/v1/documents/{created['id']}/scan", headers=admin_headers)
    audits = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.entity_id == created["id"])).all()

    assert scanned.status_code == 200
    assert scanned.json()["status"] == "verified"
    assert scanned.json()["malware_scan_result"]["engine"] == "mock"
    assert scanned.json()["malware_scan_status"] == "clean"
    assert any(item.action == "document_malware_scan_completed" for item in audits)


def test_verified_download_gate_blocks_unscanned_document(api: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    settings = Settings(
        jwt_secret="test-lifecycle-secret-value-1234567890",
        storage_local_root=str(tmp_path / "gated-storage"),
        storage_public_base_url="http://testserver/api/v1/storage/mock",
        require_verified_document_downloads=True,
    )
    monkeypatch.setattr(client_portal_module, "get_settings", lambda: settings)
    monkeypatch.setattr(storage_module, "get_settings", lambda: settings)
    tenant_id, case_id = seed_for_lifecycle(api, db_session)
    admin_headers = login(api, DEMO_SEED.admin_email)
    client_headers = login(api, DEMO_SEED.client_email)
    created = upload_client_document(api, case_id)

    blocked = api.get(f"/api/v1/client-portal/documents/{created['id']}/download", headers=client_headers)
    api.post(f"/api/v1/documents/{created['id']}/verify-storage", headers=admin_headers)
    api.post(f"/api/v1/documents/{created['id']}/scan-mock", headers=admin_headers, json={"verdict": "clean"})
    allowed = api.get(f"/api/v1/client-portal/documents/{created['id']}/download", headers=client_headers)

    audits = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.entity_id == created["id"])).all()

    assert blocked.status_code == 409
    assert blocked.json()["detail"] == "Document is pending verification"
    assert allowed.status_code == 200
    assert any(item.action == "portal_document_download_blocked_unverified" for item in audits)


def test_infected_scan_hides_document_from_client_portal(api: TestClient, db_session: Session) -> None:
    _, case_id = seed_for_lifecycle(api, db_session)
    admin_headers = login(api, DEMO_SEED.admin_email)
    client_headers = login(api, DEMO_SEED.client_email)
    created = upload_client_document(api, case_id, content=b"bad")

    infected = api.post(f"/api/v1/documents/{created['id']}/scan-mock", headers=admin_headers, json={"verdict": "infected"})
    portal_docs = api.get(f"/api/v1/client-portal/cases/{case_id}/documents", headers=client_headers)
    download = api.get(f"/api/v1/client-portal/documents/{created['id']}/download", headers=client_headers)

    assert infected.status_code == 200
    assert infected.json()["status"] == "rejected"
    assert infected.json()["is_client_visible"] is False
    assert created["id"] not in {item["id"] for item in portal_docs.json()}
    assert download.status_code == 404


def test_manual_reject_hides_document_and_requires_internal_permission(api: TestClient, db_session: Session) -> None:
    _, case_id = seed_for_lifecycle(api, db_session)
    admin_headers = login(api, DEMO_SEED.admin_email)
    client_headers = login(api, DEMO_SEED.client_email)
    created = upload_client_document(api, case_id)

    blocked = api.post(f"/api/v1/documents/{created['id']}/reject", headers=client_headers, json={"reason": "Documento borroso"})
    rejected = api.post(f"/api/v1/documents/{created['id']}/reject", headers=admin_headers, json={"reason": "Documento borroso"})

    assert blocked.status_code == 403
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    assert rejected.json()["is_client_visible"] is False
    assert rejected.json()["malware_scan_result"]["rejection_reason"] == "Documento borroso"
