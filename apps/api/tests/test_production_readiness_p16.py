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
    assert report["status"] == "ready"
    assert report["blockers"] == []
    assert_startup_readiness(settings) is None


def test_readiness_endpoint_reports_current_environment() -> None:
    client = TestClient(app)

    response = client.get("/readiness")
    api_response = client.get("/api/v1/readiness")

    assert response.status_code == 200
    assert api_response.status_code == 200
    assert response.json()["phase"] == "P24"
    assert response.json()["release"] == "CLOUD-DEPLOY-PACK"
