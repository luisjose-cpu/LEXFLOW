param(
  [string]$ApiUrl = $env:LEXFLOW_API_URL
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

$ApiUrl = Normalize-Url $ApiUrl
if (-not $ApiUrl) {
  throw "LEXFLOW_API_URL or -ApiUrl is required"
}

$readinessResponse = Invoke-WebRequest -Uri "$ApiUrl/readiness" -Method GET -UseBasicParsing -TimeoutSec 30
$readiness = $readinessResponse.Content | ConvertFrom-Json
$statusResponse = Invoke-WebRequest -Uri "$ApiUrl/api/v1/status" -Method GET -UseBasicParsing -TimeoutSec 30
$apiStatus = $statusResponse.Content | ConvertFrom-Json
$versionResponse = Invoke-WebRequest -Uri "$ApiUrl/version" -Method GET -UseBasicParsing -TimeoutSec 30
$version = $versionResponse.Content | ConvertFrom-Json

Write-Host "LEXFLOW public production gate"
Write-Host "API URL: $ApiUrl"
Write-Host "Version: $($version.version)"
Write-Host "Revision: $($version.revision)"
Write-Host "Production ready: $($readiness.production_ready)"
Write-Host "Public production ready: $($readiness.public_production_ready)"
Write-Host "External providers: ai=$($apiStatus.external_providers.ai) whatsapp=$($apiStatus.external_providers.whatsapp) billing=$($apiStatus.external_providers.billing) email=$($apiStatus.external_providers.email) storage=$($apiStatus.external_providers.storage) malware_scanner=$($apiStatus.external_providers.malware_scanner)"

$blockers = @($readiness.blockers)
$warnings = @($readiness.warnings)
Write-IssueList "Blockers:" $blockers
Write-IssueList "Warnings:" $warnings

if ($readiness.public_production_ready -ne $true) {
  throw "Public production gate failed. Resolve all readiness blockers and warnings before commercial public launch."
}

Write-Host "Public production gate passed."
