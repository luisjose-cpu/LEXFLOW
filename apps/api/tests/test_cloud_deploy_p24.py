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
        "scripts/db-backup.ps1",
        "scripts/db-restore-drill.ps1",
        "scripts/production-gate.ps1",
        "docs/cloud/P24_CLOUD_DEPLOY_PACK.md",
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
    assert "pg_restore" in restore
    assert "--list" in restore
    assert "-Execute" in restore
    assert "RESTORE_DATABASE_URL" in restore
    assert "backups/" in gitignore


def test_cloud_release_evidence_script_writes_safe_report() -> None:
    script = read_repo_file("scripts/cloud-release-evidence.ps1")
    package = json.loads(read_repo_file("package.json"))
    gitignore = read_repo_file(".gitignore")

    assert "cloud:evidence" in package["scripts"]
    assert "scripts/cloud-preflight.ps1" in script
    assert "scripts/cloud-smoke.ps1" in script
    assert "secrets_included = $false" in script
    assert "credentials_included = $false" in script
    assert "tenant_data_included = $false" in script
    assert "lexflow-cloud-release-" in script
    assert "warning_keys" in script
    assert "blocker_keys" in script
    assert "public_production_ready" in script
    assert "reports/" in gitignore
