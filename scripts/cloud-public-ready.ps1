param(
  [string]$ApiUrl = $env:LEXFLOW_API_URL,
  [string]$ReportDir = "reports/cloud"
)

$ErrorActionPreference = "Stop"

function Normalize-Url {
  param([string]$Url)
  if (-not $Url) {
    return ""
  }
  return $Url.Trim().TrimEnd("/")
}

function Write-IssueList {
  param(
    [string]$Title,
    [object[]]$Items
  )
  if (@($Items).Count -eq 0) {
    return
  }
  Write-Host $Title
  foreach ($item in $Items) {
    Write-Host "- $($item.key): $($item.message)"
  }
}

function Invoke-WebRequestWithRetry {
  param([string]$Uri)
  for ($attempt = 1; $attempt -le 3; $attempt += 1) {
    try {
      return Invoke-WebRequest -Uri $Uri -Method GET -UseBasicParsing -TimeoutSec 30
    } catch {
      if ($attempt -eq 3) {
        throw
      }
      Write-Host "Transient request failure for $Uri. Retrying attempt $($attempt + 1)/3..."
      Start-Sleep -Seconds (5 * $attempt)
    }
  }
}

$ApiUrl = Normalize-Url $ApiUrl
if (-not $ApiUrl) {
  throw "LEXFLOW_API_URL or -ApiUrl is required"
}

$readinessResponse = Invoke-WebRequestWithRetry -Uri "$ApiUrl/readiness"
$readiness = $readinessResponse.Content | ConvertFrom-Json
$statusResponse = Invoke-WebRequestWithRetry -Uri "$ApiUrl/api/v1/status"
$apiStatus = $statusResponse.Content | ConvertFrom-Json
$versionResponse = Invoke-WebRequestWithRetry -Uri "$ApiUrl/version"
$version = $versionResponse.Content | ConvertFrom-Json
$blockers = @($readiness.blockers)
$warnings = @($readiness.warnings)
$passed = $readiness.public_production_ready -eq $true

Write-Host "LEXFLOW public production gate"
Write-Host "API URL: $ApiUrl"
Write-Host "Version: $($version.version)"
Write-Host "Revision: $($version.revision)"
Write-Host "Production ready: $($readiness.production_ready)"
Write-Host "Public production ready: $($readiness.public_production_ready)"
Write-Host "External providers: ai=$($apiStatus.external_providers.ai) whatsapp=$($apiStatus.external_providers.whatsapp) billing=$($apiStatus.external_providers.billing) email=$($apiStatus.external_providers.email) storage=$($apiStatus.external_providers.storage) malware_scanner=$($apiStatus.external_providers.malware_scanner)"

Write-IssueList "Blockers:" $blockers
Write-IssueList "Warnings:" $warnings

$targetDir = Join-Path (Resolve-Path -Path "." | Select-Object -ExpandProperty Path) $ReportDir
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$reportPath = Join-Path $targetDir "lexflow-public-ready-$timestamp.json"
$report = @{
  product = "LEXFLOW"
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  api_url = $ApiUrl
  passed = $passed
  revision = "$($version.revision)"
  production_ready = $readiness.production_ready
  public_production_ready = $readiness.public_production_ready
  blocker_keys = @($blockers | ForEach-Object { $_.key })
  warning_keys = @($warnings | ForEach-Object { $_.key })
  external_providers = $apiStatus.external_providers
  security = @{
    secrets_included = $false
    credentials_included = $false
    tenant_data_included = $false
  }
}
$report | ConvertTo-Json -Depth 8 | Set-Content -Path $reportPath -Encoding UTF8
Write-Host "Public readiness evidence ready: $reportPath"

if (-not $passed) {
  throw "Public production gate failed. Resolve all readiness blockers and warnings before commercial public launch."
}

Write-Host "Public production gate passed."
