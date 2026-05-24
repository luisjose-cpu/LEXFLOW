from functools import lru_cache
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LEXFLOW API"
    api_version: str = "0.1.0"
    app_env: str = "local"
    release_phase: str = "P24"
    release_name: str = "CLOUD-DEPLOY-PACK"
    release_revision: str | None = None
    require_production_ready: bool = False
    seed_demo_on_startup: bool = True
    lexflow_web_url: str = "http://localhost:3000"
    database_url: str = "sqlite+pysqlite:///:memory:"
    redis_url: str = "redis://localhost:6379/0"
    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_bucket: str = "lexflow"
    storage_public_base_url: str = "http://localhost:8000/api/v1/storage/mock"
    storage_signed_url_minutes: int = 15
    max_upload_bytes: int = 25 * 1024 * 1024
    storage_backend: str = "local"
    storage_local_root: str = ".lexflow-storage"
    require_verified_document_downloads: bool = False
    malware_scanner_provider: str = "mock"
    clamav_host: str = "localhost"
    clamav_port: int = 3310
    clamav_timeout_seconds: float = 2.0
    openai_api_key: str | None = None
    whatsapp_business_token: str | None = None
    billing_provider_secret: str | None = None
    require_billing_webhook_signature: bool = False
    restore_drill_verified_at: str | None = None
    restore_drill_max_age_hours: int = 720
    email_provider: str = "prepared"
    email_api_url: str | None = None
    email_api_key: str | None = None
    email_from: str = "no-reply@lexflow.local"
    credential_encryption_key: str | None = None
    jwt_secret: str = "change-me-locally"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_minutes: int = 60 * 24 * 7
    failed_login_backend: str = "memory"
    failed_login_limit: int = 10
    failed_login_window_minutes: int = 15
    password_reset_token_minutes: int = 30
    user_invitation_token_minutes: int = 60 * 24 * 7
    require_owner_mfa: bool = False
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    rate_limit_per_minute: int = 600
    max_upload_filename_length: int = 180
    allowed_upload_content_types: str = "application/pdf,image/png,image/jpeg,application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def deployment_revision(settings: Settings | None = None) -> str:
    current = settings or get_settings()
    return (
        current.release_revision
        or os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or os.getenv("GITHUB_SHA")
        or "unknown"
    )
