from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings


LOCAL_ORIGIN_MARKERS = ("localhost", "127.0.0.1", "::1")
WEAK_SECRET_VALUES = {"", "change-me", "change-me-locally", "lexflow", "minioadmin"}
POSTGRES_URL_PREFIXES = ("postgres://", "postgresql://", "postgresql+psycopg://")


@dataclass(frozen=True)
class ReadinessCheck:
    key: str
    ok: bool
    severity: str
    message: str

    def as_dict(self) -> dict[str, object]:
        return {"key": self.key, "ok": self.ok, "severity": self.severity, "message": self.message}


def _is_production(settings: Settings) -> bool:
    return settings.app_env.lower() == "production"


def _secret_is_strong(value: str | None, *, min_length: int = 32) -> bool:
    if value is None:
        return False
    cleaned = value.strip()
    return len(cleaned) >= min_length and cleaned not in WEAK_SECRET_VALUES and "change-me" not in cleaned.lower()


def _origins(settings: Settings) -> list[str]:
    return [origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()]


def production_readiness_checks(settings: Settings) -> list[ReadinessCheck]:
    origins = _origins(settings)
    checks = [
        ReadinessCheck(
            key="database_postgresql",
            ok=settings.database_url.startswith(POSTGRES_URL_PREFIXES),
            severity="blocker",
            message="Production must use PostgreSQL, not in-memory SQLite.",
        ),
        ReadinessCheck(
            key="jwt_secret_strong",
            ok=_secret_is_strong(settings.jwt_secret),
            severity="blocker",
            message="JWT_SECRET must be unique, private, and at least 32 characters.",
        ),
        ReadinessCheck(
            key="cors_no_wildcard",
            ok="*" not in origins,
            severity="blocker",
            message="ALLOWED_ORIGINS must not contain wildcard in production.",
        ),
        ReadinessCheck(
            key="cors_no_localhost",
            ok=all(marker not in origin for origin in origins for marker in LOCAL_ORIGIN_MARKERS),
            severity="blocker",
            message="Production origins must not point to localhost or loopback hosts.",
        ),
        ReadinessCheck(
            key="s3_secret_configured",
            ok=_secret_is_strong(settings.s3_secret_key),
            severity="blocker",
            message="S3_SECRET_KEY must be configured with a strong value.",
        ),
        ReadinessCheck(
            key="s3_access_key_configured",
            ok=settings.storage_backend == "local" or bool(settings.s3_access_key),
            severity="blocker",
            message="S3_ACCESS_KEY must be configured when STORAGE_BACKEND is not local.",
        ),
        ReadinessCheck(
            key="storage_backend_public_ready",
            ok=settings.storage_backend != "local",
            severity="warning",
            message="Public production should use STORAGE_BACKEND=s3 or another S3-compatible backend.",
        ),
        ReadinessCheck(
            key="demo_seed_disabled",
            ok=settings.seed_demo_on_startup is False,
            severity="blocker",
            message="SEED_DEMO_ON_STARTUP must be false in production.",
        ),
        ReadinessCheck(
            key="rate_limit_enabled",
            ok=settings.rate_limit_per_minute > 0 and settings.rate_limit_per_minute <= 300,
            severity="warning",
            message="Production rate limit should be enabled and conservative.",
        ),
        ReadinessCheck(
            key="openai_configured",
            ok=_secret_is_strong(settings.openai_api_key, min_length=20),
            severity="warning",
            message="OpenAI key is required before enabling real AI providers.",
        ),
        ReadinessCheck(
            key="whatsapp_configured",
            ok=_secret_is_strong(settings.whatsapp_business_token, min_length=20),
            severity="warning",
            message="WhatsApp Business token is required before real WhatsApp dispatch.",
        ),
        ReadinessCheck(
            key="billing_configured",
            ok=_secret_is_strong(settings.billing_provider_secret, min_length=20),
            severity="warning",
            message="Billing provider secret is required before paid SaaS subscriptions.",
        ),
        ReadinessCheck(
            key="email_configured",
            ok=settings.email_provider == "prepared"
            or (
                settings.email_provider == "http_json"
                and bool(settings.email_api_url)
                and _secret_is_strong(settings.email_api_key, min_length=20)
                and "@" in settings.email_from
                and not settings.lexflow_web_url.startswith("http://localhost")
            ),
            severity="warning",
            message="Transactional email requires EMAIL_PROVIDER=http_json, EMAIL_API_URL, EMAIL_API_KEY, EMAIL_FROM, and a public LEXFLOW_WEB_URL.",
        ),
    ]
    if not _is_production(settings):
        return [
            ReadinessCheck(
                key="non_production_mode",
                ok=True,
                severity="info",
                message=f"Readiness report is informational because APP_ENV={settings.app_env}.",
            ),
            *checks,
        ]
    return checks


def production_readiness_report(settings: Settings) -> dict[str, object]:
    checks = production_readiness_checks(settings)
    blockers = [check for check in checks if check.severity == "blocker" and not check.ok]
    warnings = [check for check in checks if check.severity == "warning" and not check.ok]
    return {
        "app_env": settings.app_env,
        "phase": settings.release_phase,
        "release": settings.release_name,
        "production_ready": _is_production(settings) and not blockers,
        "status": "ready" if _is_production(settings) and not blockers else "blocked",
        "blockers": [check.as_dict() for check in blockers],
        "warnings": [check.as_dict() for check in warnings],
        "checks": [check.as_dict() for check in checks],
    }


def assert_startup_readiness(settings: Settings) -> None:
    if not settings.require_production_ready:
        return
    report = production_readiness_report(settings)
    if report["status"] != "ready":
        blocker_keys = ", ".join(str(item["key"]) for item in report["blockers"])
        raise RuntimeError(f"Production readiness blocked: {blocker_keys}")
