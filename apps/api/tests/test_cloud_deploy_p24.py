import json
from pathlib import Path

from app.db.database import normalize_database_url


ROOT = Path(__file__).resolve().parents[3]


def read_repo_file(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_normalize_database_url_accepts_cloud_postgres_variants() -> None:
    assert (
        normalize_database_url("postgres://user:pass@host:5432/lexflow")
        == "postgresql+psycopg://user:pass@host:5432/lexflow"
    )
    assert (
        normalize_database_url("postgresql://user:pass@host:5432/lexflow")
        == "postgresql+psycopg://user:pass@host:5432/lexflow"
    )
    assert normalize_database_url("sqlite:///./lexflow.db") == "sqlite:///./lexflow.db"


def test_cloud_deploy_pack_files_are_present() -> None:
    required_files = [
        "render.yaml",
        "vercel.json",
        ".github/workflows/cloud-ci.yml",
        ".env.production.example",
        "apps/api/Dockerfile",
        "infra/docker/web.Dockerfile",
        "scripts/cloud-preflight.ps1",
        "scripts/cloud-smoke.ps1",
        "scripts/cloud-release-evidence.ps1",
        "scripts/cloud-revision.ps1",
        "scripts/cloud-wait-revision.ps1",
        "scripts/cloud-public-ready.ps1",
        "scripts/db-backup.ps1",
        "scripts/db-restore-drill.ps1",
        "scripts/production-gate.ps1",
        "docs/cloud/P24_CLOUD_DEPLOY_PACK.md",
        "docs/cloud/P25_PUBLIC_PRODUCTION_GAPS.md",
        "docs/cloud/POST_DEPLOY_RUNBOOK.md",
        "docs/cloud/ROLLBACK_RUNBOOK.md",
        "infra/cloud/s3-lifecycle-policy.json",
        "infra/cloud/s3-cors-policy.json",
        "docs/cloud/S3_STORAGE_POLICY.md",
    ]

    missing = [path for path in required_files if not (ROOT / path).exists()]

    assert missing == []


def test_render_blueprint_declares_required_runtime_contracts() -> None:
    render_yaml = read_repo_file("render.yaml")

    assert "lexflow-api" in render_yaml
    assert "apps/api/Dockerfile" in render_yaml
    assert "/health" in render_yaml
    assert "lexflow-postgres" in render_yaml
    assert "lexflow-redis" in render_yaml
    assert "autoDeployTrigger: checksPass" in render_yaml
    assert "REQUIRE_PRODUCTION_READY" in render_yaml
    assert "SEED_DEMO_ON_STARTUP" in render_yaml
    assert "ALLOWED_ORIGINS" in render_yaml
    assert "STORAGE_LOCAL_ROOT" in render_yaml
    assert "lexflow-security-alert-deliveries" in render_yaml
    assert "type: cron" in render_yaml
    assert "process_security_alert_deliveries.py" in render_yaml


def test_vercel_config_targets_nextjs_workspace_build() -> None:
    config = json.loads(read_repo_file("vercel.json"))

    assert config["framework"] == "nextjs"
    assert "npm --workspace apps/web run build" in config["buildCommand"]
    assert config["outputDirectory"] == "apps/web/.next"


def test_cloud_ci_runs_release_gates() -> None:
    workflow = read_repo_file(".github/workflows/cloud-ci.yml")

    assert "npm run lint" in workflow
    assert "npm run test" in workflow
    assert "npm run build" in workflow
    assert "pytest -q" in workflow
    assert "production-gate.ps1 -Fast" in workflow
    assert "cloud-release-evidence.ps1" in workflow
    assert "cloud-revision.ps1" in workflow
    assert "cloud-wait-revision.ps1" in workflow
    assert "cloud-public-ready.ps1" in workflow
    assert "public_ready_gate" in workflow
    assert "wait_for_revision" in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert "lexflow-cloud-release-evidence" in workflow


def test_backup_restore_scripts_are_safe_by_default() -> None:
    backup = read_repo_file("scripts/db-backup.ps1")
    restore = read_repo_file("scripts/db-restore-drill.ps1")
    gitignore = read_repo_file(".gitignore")

    assert "pg_dump" in backup
    assert "--format custom" in backup
    assert "DATABASE_URL" in backup
    assert "Write-Host \"Backup ready" in backup
    assert "reports/backup" in backup
    assert "database_urls_included = $false" in backup
    assert "credentials_included = $false" in backup
    assert "lexflow-backup-" in backup
    assert "pg_restore" in restore
    assert "--list" in restore
    assert "-Execute" in restore
    assert "RESTORE_DATABASE_URL" in restore
    assert "reports/restore" in restore
    assert "database_urls_included = $false" in restore
    assert "credentials_included = $false" in restore
    assert "lexflow-restore-drill-" in restore
    assert "backups/" in gitignore
    assert "reports/" in gitignore


def test_cloud_smoke_checks_external_provider_modes() -> None:
    smoke = read_repo_file("scripts/cloud-smoke.ps1")

    assert "external_providers" in smoke
    assert "API revision" in smoke
    assert "Provider modes" in smoke
    assert "Provider modes unavailable on deployed API" in smoke
    assert "Invoke-WebRequestWithRetry" in smoke
    assert "Transient request failure" in smoke
    assert "Assert-HeaderValue" in smoke
    assert "Strict-Transport-Security" in smoke
    assert "X-Content-Type-Options" in smoke


def test_cloud_revision_script_compares_expected_commit_safely() -> None:
    script = read_repo_file("scripts/cloud-revision.ps1")
    wait_script = read_repo_file("scripts/cloud-wait-revision.ps1")
    package = json.loads(read_repo_file("package.json"))

    assert "cloud:revision" in package["scripts"]
    assert "cloud:wait-revision" in package["scripts"]
    assert "LEXFLOW_EXPECTED_REVISION" in script
    assert "rev-parse HEAD" in script
    assert "/version" in script
    assert "Cloud revision mismatch" in script
    assert "Strict" in script
    assert "Invoke-WebRequestWithRetry" in script
    assert "TimeoutSeconds" in wait_script
    assert "IntervalSeconds" in wait_script
    assert "Start-Sleep" in wait_script
    assert "Cloud revision did not match" in wait_script


def test_cloud_release_evidence_script_writes_safe_report() -> None:
    script = read_repo_file("scripts/cloud-release-evidence.ps1")
    package = json.loads(read_repo_file("package.json"))
    gitignore = read_repo_file(".gitignore")

    assert "cloud:evidence" in package["scripts"]
    assert "scripts/cloud-preflight.ps1" in script
    assert "scripts/cloud-smoke.ps1" in script
    assert "api/v1/status" in script
    assert "external_providers" in script
    assert "matches_expected" in script
    assert "security_headers" in script
    assert "Get-SecurityHeaders" in script
    assert "Strict-Transport-Security" in script
    assert "LEXFLOW_EXPECTED_REVISION" in script
    assert "revision" in script
    assert "secrets_included = $false" in script
    assert "credentials_included = $false" in script
    assert "tenant_data_included = $false" in script
    assert "lexflow-cloud-release-" in script
    assert "warning_keys" in script
    assert "blocker_keys" in script
    assert "public_production_ready" in script
    assert "reports/" in gitignore


def test_public_production_gate_script_blocks_warnings() -> None:
    script = read_repo_file("scripts/cloud-public-ready.ps1")
    package = json.loads(read_repo_file("package.json"))

    assert "cloud:public-ready" in package["scripts"]
    assert "/readiness" in script
    assert "/api/v1/status" in script
    assert "/version" in script
    assert "public_production_ready" in script
    assert "External providers" in script
    assert "Public production gate failed" in script


def test_cloud_rollback_runbook_documents_safe_recovery() -> None:
    runbook = read_repo_file("docs/cloud/ROLLBACK_RUNBOOK.md")

    assert "Render" in runbook
    assert "Vercel" in runbook
    assert "Owner Console" in runbook
    assert "cloud:smoke" in runbook
    assert "db:restore-drill" in runbook
    assert "No pegar secretos" in runbook


def test_s3_storage_policy_templates_are_safe() -> None:
    lifecycle = json.loads(read_repo_file("infra/cloud/s3-lifecycle-policy.json"))
    cors = json.loads(read_repo_file("infra/cloud/s3-cors-policy.json"))
    docs = read_repo_file("docs/cloud/S3_STORAGE_POLICY.md")

    assert lifecycle["Rules"][0]["Filter"]["Prefix"] == "tenants/"
    assert lifecycle["Rules"][0]["AbortIncompleteMultipartUpload"]["DaysAfterInitiation"] == 7
    assert "PUT" in cors[0]["AllowedMethods"]
    assert "*" not in cors[0]["AllowedOrigins"]
    assert "No contiene access keys" in docs
