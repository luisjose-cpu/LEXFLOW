from collections.abc import Generator
from io import BytesIO
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import AuditLog, Base, Case, Document
from app.db.seed import seed_demo_database
from app.main import app
from app.services.seed import DEMO_SEED, seed_demo_data
from app.core.config import Settings
from app.services import storage as storage_module
from app.services.storage import sanitize_storage_filename, tenant_storage_key
from app.services.storage import storage_service


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


def seed_for_storage(api: TestClient, db_session: Session) -> tuple[str, str]:
    seed_demo_data()
    admin_headers = login(api, DEMO_SEED.admin_email)
    tenant_id = api.get("/api/v1/auth/me", headers=admin_headers).json()["tenant_id"]
    seed_demo_database(db_session, tenant_id=tenant_id)
    legal_case = db_session.scalars(select(Case).where(Case.tenant_id == tenant_id, Case.title == "Cobro ejecutivo Nova")).one()
    return tenant_id, legal_case.id


def test_storage_key_is_tenant_and_case_scoped() -> None:
    key = tenant_storage_key(tenant_id="tenant-1", case_id="case-1", document_id="doc-1", filename="../Mi documento final.pdf")

    assert key == "tenants/tenant-1/cases/case-1/documents/doc-1/Mi-documento-final.pdf"
    assert sanitize_storage_filename("../payload.pdf") == "payload.pdf"


def test_client_upload_returns_storage_contract_and_audit(api: TestClient, db_session: Session) -> None:
    tenant_id, case_id = seed_for_storage(api, db_session)
    headers = login(api, DEMO_SEED.client_email)

    response = api.post(
        f"/api/v1/client-portal/cases/{case_id}/documents",
        headers=headers,
        json={"filename": "comprobante pago.pdf", "content_type": "application/pdf"},
    )

    body = response.json()
    document = db_session.scalars(select(Document).where(Document.id == body["id"])).one()
    audits = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.entity_id == body["id"])).all()

    assert response.status_code == 201
    assert document.storage_key.startswith(f"tenants/{tenant_id}/cases/{case_id}/documents/{document.id}/")
    assert body["upload"]["method"] == "PUT"
    assert body["upload"]["headers"]["Content-Type"] == "application/pdf"
    assert body["upload"]["max_bytes"] > 0
    assert any(item.action == "portal_document_uploaded" for item in audits)


def test_client_download_link_is_signed_and_scoped(api: TestClient, db_session: Session) -> None:
    tenant_id, case_id = seed_for_storage(api, db_session)
    headers = login(api, DEMO_SEED.client_email)
    document = db_session.scalars(select(Document).where(Document.tenant_id == tenant_id, Document.case_id == case_id, Document.is_client_visible.is_(True))).first()
    assert document is not None

    response = api.get(f"/api/v1/client-portal/documents/{document.id}/download", headers=headers)

    body = response.json()
    audits = db_session.scalars(select(AuditLog).where(AuditLog.tenant_id == tenant_id, AuditLog.entity_id == document.id)).all()

    assert response.status_code == 200
    assert body["document_id"] == document.id
    assert body["method"] == "GET"
    assert "token=" in body["url"]
    assert body["storage_key"] == document.storage_key
    assert any(item.action == "portal_document_download_link_created" for item in audits)


def test_client_cannot_download_other_client_document(api: TestClient, db_session: Session) -> None:
    tenant_id, _ = seed_for_storage(api, db_session)
    headers = login(api, DEMO_SEED.client_email)
    other_document = db_session.scalars(
        select(Document)
        .join(Case, Case.id == Document.case_id)
        .where(Document.tenant_id == tenant_id, Case.title == "Laboral colectivo Andes", Document.is_client_visible.is_(True))
    ).first()
    if other_document is None:
        other_case = db_session.scalars(select(Case).where(Case.tenant_id == tenant_id, Case.title == "Laboral colectivo Andes")).one()
        other_document = Document(
            tenant_id=tenant_id,
            case_id=other_case.id,
            client_id=other_case.client_id,
            filename="andes-visible.pdf",
            storage_key="tenants/demo/andes-visible.pdf",
            is_client_visible=True,
        )
        db_session.add(other_document)
        db_session.commit()

    response = api.get(f"/api/v1/client-portal/documents/{other_document.id}/download", headers=headers)

    assert response.status_code == 404


def test_storage_status_requires_internal_permission(api: TestClient, db_session: Session) -> None:
    seed_for_storage(api, db_session)
    admin_headers = login(api, DEMO_SEED.admin_email)
    client_headers = login(api, DEMO_SEED.client_email)

    allowed = api.get("/api/v1/storage/status", headers=admin_headers)
    blocked = api.get("/api/v1/storage/status", headers=client_headers)

    assert allowed.status_code == 200
    assert allowed.json()["provider"] == "s3-compatible"
    assert blocked.status_code == 403


class FakeS3Client:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], dict[str, object]] = {}

    def put_object(self, *, Bucket: str, Key: str, Body: bytes, ContentType: str, Metadata: dict[str, str]) -> None:
        self.objects[(Bucket, Key)] = {"body": Body, "content_type": ContentType, "metadata": Metadata}

    def head_object(self, *, Bucket: str, Key: str) -> dict[str, object]:
        stored = self.objects[(Bucket, Key)]
        body = stored["body"]
        assert isinstance(body, bytes)
        return {"ContentLength": len(body), "Metadata": stored["metadata"], "ETag": '"fake-etag"'}

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, object]:
        stored = self.objects[(Bucket, Key)]
        body = stored["body"]
        assert isinstance(body, bytes)
        return {"Body": BytesIO(body), "ContentType": stored["content_type"], "Metadata": stored["metadata"]}


def test_s3_backend_stores_metadata_and_downloads_via_api_proxy(monkeypatch: pytest.MonkeyPatch, db_session: Session) -> None:
    fake_s3 = FakeS3Client()
    settings = Settings(
        storage_backend="s3",
        s3_endpoint="https://r2.example.test",
        s3_access_key="access",
        s3_secret_key="a-strong-s3-secret-value-for-tests",
        s3_bucket="lexflow-test",
        storage_public_base_url="https://api.example.test/api/v1/storage/mock",
        jwt_secret="a-strong-jwt-secret-for-storage-tests-123",
    )
    monkeypatch.setattr(storage_module, "get_settings", lambda: settings)
    monkeypatch.setattr(storage_module, "_s3_client", lambda _: fake_s3)

    document = Document(
        id="doc-s3",
        tenant_id="tenant-s3",
        case_id="case-s3",
        client_id="client-s3",
        filename="prueba.pdf",
        storage_key=tenant_storage_key(tenant_id="tenant-s3", case_id="case-s3", document_id="doc-s3", filename="prueba.pdf"),
        content_type="application/pdf",
    )
    db_session.add(document)
    db_session.commit()
    contract = storage_service.upload_contract(
        tenant_id="tenant-s3",
        case_id="case-s3",
        document_id=document.id,
        filename=document.filename,
        content_type=document.content_type,
    )
    upload_token = parse_qs(urlparse(contract["upload"]["url"]).query)["token"][0]

    uploaded = storage_service.store_signed_upload(
        db_session,
        document_id=document.id,
        token=upload_token,
        body=b"document bytes",
        content_type="application/pdf",
    )
    metadata = storage_service.object_metadata(storage_key=document.storage_key)
    download = storage_service.signed_download_url(document=document, actor_user_id="user-s3")
    download_token = parse_qs(urlparse(download["url"]).query)["token"][0]
    body, download_metadata = storage_service.read_signed_download(db_session, document_id=document.id, token=download_token)

    assert uploaded["status"] == "uploaded"
    assert uploaded["sha256"] == metadata["sha256"]
    assert metadata["exists"] is True
    assert metadata["bytes"] == len(b"document bytes")
    assert body == b"document bytes"
    assert download_metadata["content_type"] == "application/pdf"
