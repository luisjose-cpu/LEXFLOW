import pytest

from app.core.config import Settings
from app.core.readiness import assert_startup_readiness, production_readiness_report
from app.main import app
from fastapi.testclient import TestClient


def production_settings(**overrides: object) -> Settings:
    base = {
        "app_env": "production",
        "require_production_ready": True,
        "seed_demo_on_startup": False,
        "database_url": "postgresql+psycopg://lexflow:secret@postgres:5432/lexflow",
        "jwt_secret": "a-strong-production-jwt-secret-value-123456",
        "allowed_origins": "https://app.lexflow.example,https://admin.lexflow.example",
        "s3_secret_key": "a-strong-production-s3-secret-value-123456",
        "rate_limit_per_minute": 120,
    }
    base.update(overrides)
    return Settings(**base)


def test_production_readiness_blocks_unsafe_defaults() -> None:
    settings = Settings(app_env="production", require_production_ready=True)
    report = production_readiness_report(settings)

    blocker_keys = {item["key"] for item in report["blockers"]}

    assert report["production_ready"] is False
    assert report["public_production_ready"] is False
    assert "database_postgresql" in blocker_keys
    assert "jwt_secret_strong" in blocker_keys
    assert "cors_no_localhost" in blocker_keys
    assert "s3_secret_configured" in blocker_keys
    assert "demo_seed_disabled" in blocker_keys
    with pytest.raises(RuntimeError):
        assert_startup_readiness(settings)


def test_production_readiness_accepts_hardened_core_settings() -> None:
    settings = production_settings()
    report = production_readiness_report(settings)

    assert report["production_ready"] is True
    assert report["public_production_ready"] is False
    assert report["status"] == "ready"
    assert report["blockers"] == []
    assert_startup_readiness(settings) is None


def test_public_production_readiness_requires_no_warnings() -> None:
    settings = production_settings(
        storage_backend="s3",
        s3_access_key="production-access-key",
        s3_endpoint="https://r2.example.test",
        s3_bucket="lexflow-prod",
        openai_api_key="sk-production-openai-key-value-123456",
        whatsapp_business_token="production-whatsapp-token-value-123456",
        billing_provider_secret="production-billing-secret-value-123456",
        malware_scanner_provider="clamav",
    )
    report = production_readiness_report(settings)

    assert report["production_ready"] is True
    assert report["public_production_ready"] is True
    assert report["warnings"] == []


def test_production_readiness_rejects_placeholder_secrets() -> None:
    settings = production_settings(
        storage_backend="s3",
        s3_access_key="replace-with-production-access-key",
        s3_secret_key="replace-with-strong-production-secret-at-least-32-chars",
        jwt_secret="replace-with-strong-random-secret-at-least-32-chars",
    )
    report = production_readiness_report(settings)
    blocker_keys = {item["key"] for item in report["blockers"]}

    assert report["production_ready"] is False
    assert "jwt_secret_strong" in blocker_keys
    assert "s3_secret_configured" in blocker_keys
    assert "s3_access_key_configured" in blocker_keys


def test_production_readiness_reports_email_provider_configuration() -> None:
    unconfigured = production_settings(email_provider="http_json")
    configured = production_settings(
        email_provider="http_json",
        email_api_url="https://email-provider.example/send",
        email_api_key="strong-email-provider-key-value-123456",
        email_from="no-reply@lexflow.example",
        lexflow_web_url="https://app.lexflow.example",
    )

    unconfigured_warnings = {item["key"] for item in production_readiness_report(unconfigured)["warnings"]}
    configured_warnings = {item["key"] for item in production_readiness_report(configured)["warnings"]}

    assert "email_configured" in unconfigured_warnings
    assert "email_configured" not in configured_warnings


def test_production_readiness_warns_when_storage_is_local_and_accepts_s3() -> None:
    local_report = production_readiness_report(production_settings(storage_backend="local"))
    s3_report = production_readiness_report(
        production_settings(
            storage_backend="s3",
            s3_access_key="production-access-key",
            s3_endpoint="https://r2.example.test",
            s3_bucket="lexflow-prod",
        )
    )

    local_warnings = {item["key"] for item in local_report["warnings"]}
    s3_blockers = {item["key"] for item in s3_report["blockers"]}
    s3_warnings = {item["key"] for item in s3_report["warnings"]}

    assert "storage_backend_public_ready" in local_warnings
    assert "s3_access_key_configured" not in s3_blockers
    assert "storage_backend_public_ready" not in s3_warnings


def test_readiness_endpoint_reports_current_environment() -> None:
    client = TestClient(app)

    response = client.get("/readiness")
    api_response = client.get("/api/v1/readiness")

    assert response.status_code == 200
    assert api_response.status_code == 200
    assert response.json()["phase"] == "P24"
    assert response.json()["release"] == "CLOUD-DEPLOY-PACK"
