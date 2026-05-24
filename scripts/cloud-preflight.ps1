$ErrorActionPreference = "Stop"

$requiredFiles = @(
  "render.yaml",
  "vercel.json",
  ".github/workflows/cloud-ci.yml",
  ".env.production.example",
  "apps/api/Dockerfile",
  "infra/docker/web.Dockerfile",
  "scripts/production-gate.ps1"
)

foreach ($file in $requiredFiles) {
  if (-not (Test-Path $file)) {
    throw "Missing cloud deploy file: $file"
  }
}

$render = Get-Content "render.yaml" -Raw
foreach ($needle in @("lexflow-api", "lexflow-postgres", "lexflow-redis", "REQUIRE_PRODUCTION_READY", "SEED_DEMO_ON_STARTUP")) {
  if ($render -notlike "*$needle*") {
    throw "render.yaml missing: $needle"
  }
}

foreach ($needle in @("lexflow-security-alert-deliveries", "type: cron", "process_security_alert_deliveries.py")) {
  if ($render -notlike "*$needle*") {
    throw "render.yaml missing cron delivery processor: $needle"
  }
}

$vercel = Get-Content "vercel.json" -Raw
foreach ($needle in @("nextjs", "apps/web/.next", "npm --workspace apps/web run build")) {
  if ($vercel -notlike "*$needle*") {
    throw "vercel.json missing: $needle"
  }
}

powershell -NoProfile -ExecutionPolicy Bypass -File scripts/production-gate.ps1 -Fast
if ($LASTEXITCODE -ne 0) {
  throw "production-gate fast failed"
}

Write-Host "Cloud preflight passed."
