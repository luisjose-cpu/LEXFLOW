param(
  [string]$ApiUrl = $env:LEXFLOW_API_URL,
  [string]$WebUrl = $env:LEXFLOW_WEB_URL,
  [string]$TenantSlug = $env:LEXFLOW_SMOKE_TENANT_SLUG,
  [string]$AdminEmail = $env:LEXFLOW_SMOKE_ADMIN_EMAIL,
  [string]$AdminPassword = $env:LEXFLOW_SMOKE_ADMIN_PASSWORD
)

$ErrorActionPreference = "Stop"

function Normalize-Url {
  param([string]$Url)
  if (-not $Url) {
    return ""
  }
  return $Url.Trim().TrimEnd("/")
}

function Assert-HttpOk {
  param(
    [string]$Name,
    [string]$Url
  )
  Write-Host "==> $Name $Url"
  $response = Invoke-WebRequest -Uri $Url -Method GET -UseBasicParsing -TimeoutSec 30
  if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) {
    throw "$Name failed with HTTP $($response.StatusCode)"
  }
  return $response
}

$ApiUrl = Normalize-Url $ApiUrl
$WebUrl = Normalize-Url $WebUrl

if (-not $ApiUrl) {
  throw "LEXFLOW_API_URL or -ApiUrl is required"
}

Assert-HttpOk "API health" "$ApiUrl/health" | Out-Null
Assert-HttpOk "API version" "$ApiUrl/version" | Out-Null
Assert-HttpOk "API status" "$ApiUrl/api/v1/status" | Out-Null
$readiness = Assert-HttpOk "API readiness" "$ApiUrl/readiness"
$readinessBody = $readiness.Content | ConvertFrom-Json
if ($readinessBody.app_env -eq "production" -and $readinessBody.status -ne "ready") {
  $blockers = ($readinessBody.blockers | ForEach-Object { $_.key }) -join ", "
  throw "Production readiness blocked: $blockers"
}
Write-Host "Readiness status: $($readinessBody.status)"

if ($WebUrl) {
  Assert-HttpOk "Web home" $WebUrl | Out-Null
  Assert-HttpOk "Web login" "$WebUrl/login" | Out-Null
}

$hasLoginInputs = $TenantSlug -and $AdminEmail -and $AdminPassword
if ($hasLoginInputs) {
  Write-Host "==> Tenant admin login"
  $payload = @{
    tenant_slug = $TenantSlug
    email = $AdminEmail
    password = $AdminPassword
  } | ConvertTo-Json
  $response = Invoke-WebRequest -Uri "$ApiUrl/api/v1/auth/login" -Method POST -UseBasicParsing -TimeoutSec 30 -ContentType "application/json" -Body $payload
  if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) {
    throw "Tenant admin login failed with HTTP $($response.StatusCode)"
  }
  $body = $response.Content | ConvertFrom-Json
  if (-not $body.access_token) {
    throw "Tenant admin login did not return access_token"
  }
  Write-Host "Tenant admin login OK: $AdminEmail"
} else {
  Write-Host "Tenant admin login skipped. Set LEXFLOW_SMOKE_TENANT_SLUG, LEXFLOW_SMOKE_ADMIN_EMAIL and LEXFLOW_SMOKE_ADMIN_PASSWORD to enable it."
}

Write-Host "Cloud smoke passed."
