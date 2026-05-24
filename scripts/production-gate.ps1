param(
  [switch]$Fast
)

$ErrorActionPreference = "Stop"

function Run-Step {
  param(
    [string]$Name,
    [scriptblock]$Command
  )
  Write-Host "==> $Name"
  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw "Step failed: $Name"
  }
}

if (-not (Test-Path ".env.production.example")) {
  throw ".env.production.example is required"
}

if (-not (Test-Path "infra/docker/docker-compose.production.yml")) {
  throw "infra/docker/docker-compose.production.yml is required"
}

$envExample = Get-Content ".env.production.example" -Raw
$required = @(
  "APP_ENV=production",
  "REQUIRE_PRODUCTION_READY=true",
  "SEED_DEMO_ON_STARTUP=false",
  "LEXFLOW_WEB_URL=",
  "DATABASE_URL=",
  "JWT_SECRET=",
  "CREDENTIAL_ENCRYPTION_KEY=",
  "S3_SECRET_KEY=",
  "REQUIRE_OWNER_MFA=",
  "FAILED_LOGIN_LIMIT=",
  "FAILED_LOGIN_WINDOW_MINUTES=",
  "ALLOWED_ORIGINS="
)

foreach ($item in $required) {
  if ($envExample -notlike "*$item*") {
    throw "Missing production env key: $item"
  }
}

if ($Fast) {
  Write-Host "Fast production gate passed."
  exit 0
}

Run-Step "lint" { npm run lint }
Run-Step "frontend tests" { npm run test }
Run-Step "web build" { npm run build }
Run-Step "api tests" { npm run test:api }

Write-Host "Production gate passed."
