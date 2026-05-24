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

function Invoke-WebRequestWithRetry {
  param(
    [string]$Uri,
    [string]$Method = "GET",
    [hashtable]$Headers = @{},
    [string]$ContentType = "",
    [string]$Body = "",
    [int]$Attempts = 3
  )
  for ($attempt = 1; $attempt -le $Attempts; $attempt += 1) {
    try {
      $parameters = @{
        Uri = $Uri
        Method = $Method
        UseBasicParsing = $true
        TimeoutSec = 30
      }
      if ($Headers.Count -gt 0) {
        $parameters.Headers = $Headers
      }
      if ($ContentType) {
        $parameters.ContentType = $ContentType
      }
      if ($Body) {
        $parameters.Body = $Body
      }
      return Invoke-WebRequest @parameters
    } catch {
      if ($attempt -eq $Attempts) {
        throw
      }
      Write-Host "Transient request failure for $Uri. Retrying attempt $($attempt + 1)/$Attempts..."
      Start-Sleep -Seconds (5 * $attempt)
    }
  }
}

function Assert-HttpOk {
  param(
    [string]$Name,
    [string]$Url
  )
  Write-Host "==> $Name $Url"
  $response = Invoke-WebRequestWithRetry -Uri $Url
  if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) {
    throw "$Name failed with HTTP $($response.StatusCode)"
  }
  return $response
}

function Assert-HeaderValue {
  param(
    [object]$Response,
    [string]$Name,
    [string]$Header,
    [string]$Expected
  )
  $actual = "$($Response.Headers[$Header])"
  if ($actual -ne $Expected) {
    throw "$Name missing expected header $Header=$Expected"
  }
}

function Assert-HeaderContains {
  param(
    [object]$Response,
    [string]$Name,
    [string]$Header,
    [string]$ExpectedFragment
  )
  $actual = "$($Response.Headers[$Header])"
  if (-not $actual.Contains($ExpectedFragment)) {
    throw "$Name missing expected header fragment $Header contains $ExpectedFragment"
  }
}

$ApiUrl = Normalize-Url $ApiUrl
$WebUrl = Normalize-Url $WebUrl

if (-not $ApiUrl) {
  throw "LEXFLOW_API_URL or -ApiUrl is required"
}

$healthResponse = Assert-HttpOk "API health" "$ApiUrl/health"
Assert-HeaderValue $healthResponse "API health" "X-Content-Type-Options" "nosniff"
Assert-HeaderValue $healthResponse "API health" "X-Frame-Options" "DENY"
Assert-HeaderValue $healthResponse "API health" "Referrer-Policy" "no-referrer"
Assert-HeaderContains $healthResponse "API health" "Content-Security-Policy" "default-src 'none'"
Assert-HeaderContains $healthResponse "API health" "Strict-Transport-Security" "includeSubDomains"
$versionResponse = Assert-HttpOk "API version" "$ApiUrl/version"
$versionBody = $versionResponse.Content | ConvertFrom-Json
if ($versionBody.revision) {
  Write-Host "API revision: $($versionBody.revision)"
} else {
  Write-Host "API revision unavailable on deployed API; redeploy latest master to enable this check."
}
$statusResponse = Assert-HttpOk "API status" "$ApiUrl/api/v1/status"
$statusBody = $statusResponse.Content | ConvertFrom-Json
if (-not $statusBody.external_providers) {
  Write-Host "Provider modes unavailable on deployed API; redeploy latest master to enable this check."
} else {
  Write-Host "Provider modes: ai=$($statusBody.external_providers.ai) whatsapp=$($statusBody.external_providers.whatsapp) billing=$($statusBody.external_providers.billing)"
}
Assert-HttpOk "API metrics" "$ApiUrl/metrics" | Out-Null
$readiness = Assert-HttpOk "API readiness" "$ApiUrl/readiness"
$readinessBody = $readiness.Content | ConvertFrom-Json
if ($readinessBody.app_env -eq "production" -and $readinessBody.status -ne "ready") {
  $blockers = ($readinessBody.blockers | ForEach-Object { $_.key }) -join ", "
  throw "Production readiness blocked: $blockers"
}
Write-Host "Readiness status: $($readinessBody.status)"

if ($WebUrl) {
  $webHome = Assert-HttpOk "Web home" $WebUrl
  Assert-HeaderValue $webHome "Web home" "X-Content-Type-Options" "nosniff"
  Assert-HeaderValue $webHome "Web home" "X-Frame-Options" "DENY"
  Assert-HeaderValue $webHome "Web home" "Referrer-Policy" "no-referrer"
  Assert-HeaderContains $webHome "Web home" "Content-Security-Policy" "default-src 'self'"
  Assert-HeaderContains $webHome "Web home" "Strict-Transport-Security" "includeSubDomains"
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
  $response = Invoke-WebRequestWithRetry -Uri "$ApiUrl/api/v1/auth/login" -Method POST -ContentType "application/json" -Body $payload
  if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) {
    throw "Tenant admin login failed with HTTP $($response.StatusCode)"
  }
  $body = $response.Content | ConvertFrom-Json
  if (-not $body.access_token) {
    throw "Tenant admin login did not return access_token"
  }
  Write-Host "Tenant admin login OK: $AdminEmail"

  Write-Host "==> Authenticated storage status"
  $headers = @{ Authorization = "Bearer $($body.access_token)" }
  $storageResponse = Invoke-WebRequestWithRetry -Uri "$ApiUrl/api/v1/storage/status" -Headers $headers
  if ($storageResponse.StatusCode -lt 200 -or $storageResponse.StatusCode -ge 300) {
    throw "Storage status failed with HTTP $($storageResponse.StatusCode)"
  }
  $storageBody = $storageResponse.Content | ConvertFrom-Json
  if ($storageBody.provider -ne "s3-compatible") {
    throw "Unexpected storage provider: $($storageBody.provider)"
  }
  Write-Host "Storage status OK: backend=$($storageBody.backend)"
} else {
  Write-Host "Tenant admin login skipped. Set LEXFLOW_SMOKE_TENANT_SLUG, LEXFLOW_SMOKE_ADMIN_EMAIL and LEXFLOW_SMOKE_ADMIN_PASSWORD to enable it."
}

Write-Host "Cloud smoke passed."
