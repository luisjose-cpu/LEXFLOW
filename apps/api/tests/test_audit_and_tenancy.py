from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_p1_status_endpoints() -> None:
    health = client.get("/health")
    version = client.get("/version")
    status = client.get("/api/v1/status")

    assert health.status_code == 200
    assert version.status_code == 200
    assert status.status_code == 200
    assert "revision" in version.json()
    assert "revision" in status.json()
    assert status.json()["phase"] == "P24"
    assert status.json()["release"] == "CLOUD-DEPLOY-PACK"
    assert status.json()["external_providers"]["ai"] == "mock"
    assert status.json()["external_providers"]["whatsapp"] == "mock"
    assert status.json()["external_providers"]["billing"] == "mock"
    assert status.json()["external_providers"]["malware_scanner"] == "mock"
    assert "secret" not in status.text.lower()


def test_p14_security_headers_metrics_and_origin_guard() -> None:
    response = client.get("/api/v1/health")
    metrics = client.get("/metrics")
    blocked = client.post("/api/v1/auth/login", headers={"Origin": "https://evil.example"}, json={})

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "includeSubDomains" in response.headers["Strict-Transport-Security"]
    assert blocked.headers["X-Content-Type-Options"] == "nosniff"
    assert blocked.headers["X-Frame-Options"] == "DENY"
    assert blocked.headers["X-Request-Id"]
    assert metrics.status_code == 200
    assert metrics.json()["release"] == "CLOUD-DEPLOY-PACK"
    assert blocked.status_code == 403


def test_matter_creation_is_tenant_scoped_and_audited() -> None:
    tenant_id = uuid4()
    other_tenant_id = uuid4()
    payload = {
        "client_id": str(uuid4()),
        "title": "Cobro ejecutivo",
        "next_action": "Preparar memorial",
    }

    created = client.post("/api/v1/matters", json=payload, headers={"X-Tenant-Id": str(tenant_id)})
    assert created.status_code == 200
    assert created.json()["tenant_id"] == str(tenant_id)

    tenant_matters = client.get("/api/v1/matters", headers={"X-Tenant-Id": str(tenant_id)})
    other_matters = client.get("/api/v1/matters", headers={"X-Tenant-Id": str(other_tenant_id)})
    audit_log = client.get("/api/v1/audit-log", headers={"X-Tenant-Id": str(tenant_id)})

    assert len(tenant_matters.json()) == 1
    assert other_matters.json() == []
    assert len(audit_log.json()) == 1
    assert audit_log.json()[0]["action"] == "create"
