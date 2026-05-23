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
        jwt_secret="test-storage-secret-value-1234567890",
        storage_local_root=str(tmp_path / "storage"),
        storage_public_base_url="http://testserver/api/v1/storage/mock",
        max_upload_bytes=64,
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


def seed_for_storage(api: TestClient, db_session: Session) -> tuple[str, str]:
    seed_demo_data()
    admin_headers = login(api, DEMO_SEED.admin_email)
    tenant_id = api.get("/api/v1/auth/me", headers=admin_headers).json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)
    legal_case = db_session.scalars(select(Case).where(Case.tenant_id == tenant_id, Case.title == "Cobro ejecutivo Nova")).one()
    return tenant_id, legal_case.id


def create_upload(api: TestClient, case_id: str) -> dict[str, object]:
    headers = login(api, DEMO_SEED.client_email)
    response = api.post(
        f"/api/v1/client-portal/cases/{case_id}/documents",
        headers=headers,
        json={"filename": "recibo.pdf", "content_type": "application/pdf"},
    )
    assert response.status_code == 201
    return response.json()


def test_signed_upload_persists_bytes_and_signed_download_returns_file(api: TestClient, db_session: Session) -> None:
    tenant_id, case_id = seed_for_storage(api, db_session)
    client_headers = login(api, DEMO_SEED.client_email)
    created = create_upload(api, case_id)
    body = b"%PDF-lexflow-pilot"

    uploaded = api.put(str(created["upload"]["url"]), headers={"Content-Type": "application/pdf"}, content=body)
    download_link = api.get(f"/api/v1/client-portal/documents/{created['id']}/download", headers=client_headers)
    downloaded = api.get(download_link.json()["url"])

    document = db_session.get(Document, created["id"])
    audits = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.entity_id == created["id"])).all()

    assert uploaded.status_code == 200
    assert uploaded.json()["bytes"] == len(body)
    assert uploaded.json()["sha256"] == "407e390574196ccda2e0366cd124a6f1d4c9dcb33b1c8151f2efa9023265b8ab"
    assert downloaded.status_code == 200
    assert downloaded.content == body
    assert downloaded.headers["X-Content-SHA256"] == uploaded.json()["sha256"]
    assert document is not None
    assert document.status == "pending_review"
    assert any(item.action == "storage_object_uploaded" for item in audits)
    assert any(item.action == "storage_object_downloaded" for item in audits)


def test_signed_upload_rejects_tampered_token_oversize_and_wrong_content_type(api: TestClient, db_session: Session) -> None:
    _, case_id = seed_for_storage(api, db_session)
    created = create_upload(api, case_id)
    upload_url = str(created["upload"]["url"])

    tampered = upload_url.replace("token=", "token=x")
    bad_token = api.put(tampered, headers={"Content-Type": "application/pdf"}, content=b"ok")
    too_large = api.put(upload_url, headers={"Content-Type": "application/pdf"}, content=b"x" * 65)
    wrong_type = api.put(upload_url, headers={"Content-Type": "image/png"}, content=b"ok")

    assert bad_token.status_code == 401
    assert too_large.status_code == 413
    assert wrong_type.status_code == 415


def test_signed_download_requires_stored_object(api: TestClient, db_session: Session) -> None:
    _, case_id = seed_for_storage(api, db_session)
    client_headers = login(api, DEMO_SEED.client_email)
    created = create_upload(api, case_id)

    download_link = api.get(f"/api/v1/client-portal/documents/{created['id']}/download", headers=client_headers)
    downloaded = api.get(download_link.json()["url"])

    assert download_link.status_code == 200
    assert downloaded.status_code == 404
    assert downloaded.json()["detail"] == "Stored object not found"
