param(
  [string]$ApiUrl = $env:LEXFLOW_API_URL,
  [string]$WebUrl = $env:LEXFLOW_WEB_URL,
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

function Invoke-ReleaseStep {
  param(
    [string]$Name,
    [string[]]$Command
  )
  Write-Host "==> $Name"
  $startedAt = (Get-Date).ToUniversalTime()
  $exe = $Command[0]
  $arguments = @()
  if ($Command.Length -gt 1) {
    $arguments = $Command[1..($Command.Length - 1)]
  }
  $output = & $exe @arguments 2>&1
  foreach ($line in $output) {
    Write-Host $line
  }
  if ($LASTEXITCODE -ne 0) {
    throw "$Name failed with exit code $LASTEXITCODE"
  }
  $finishedAt = (Get-Date).ToUniversalTime()
  return @{
    name = $Name
    status = "passed"
    started_at = $startedAt.ToString("o")
    finished_at = $finishedAt.ToString("o")
    duration_seconds = [Math]::Round(($finishedAt - $startedAt).TotalSeconds, 2)
  }
}

$ApiUrl = Normalize-Url $ApiUrl
$WebUrl = Normalize-Url $WebUrl

if (-not $ApiUrl) {
  throw "LEXFLOW_API_URL or -ApiUrl is required"
}

$steps = @()
$steps += Invoke-ReleaseStep "cloud-preflight" @("powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts/cloud-preflight.ps1")

$smokeCommand = @("powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts/cloud-smoke.ps1", "-ApiUrl", $ApiUrl)
if ($WebUrl) {
  $smokeCommand += @("-WebUrl", $WebUrl)
}
$steps += Invoke-ReleaseStep "cloud-smoke" $smokeCommand

$readinessResponse = Invoke-WebRequest -Uri "$ApiUrl/readiness" -Method GET -UseBasicParsing -TimeoutSec 30
$readiness = $readinessResponse.Content | ConvertFrom-Json
$statusResponse = Invoke-WebRequest -Uri "$ApiUrl/api/v1/status" -Method GET -UseBasicParsing -TimeoutSec 30
$apiStatus = $statusResponse.Content | ConvertFrom-Json
$versionResponse = Invoke-WebRequest -Uri "$ApiUrl/version" -Method GET -UseBasicParsing -TimeoutSec 30
$version = $versionResponse.Content | ConvertFrom-Json
$blockerCount = @($readiness.blockers).Count
$warningCount = @($readiness.warnings).Count
$publicProductionReady = $readiness.public_production_ready
if ($null -eq $publicProductionReady) {
  $publicProductionReady = [bool]($readiness.status -eq "ready" -and $blockerCount -eq 0 -and $warningCount -eq 0)
}

$report = @{
  product = "LEXFLOW"
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  api_url = $ApiUrl
  web_url = $WebUrl
  version = $version
  external_providers = $apiStatus.external_providers
  readiness = @{
    status = $readiness.status
    app_env = $readiness.app_env
    production_ready = $readiness.production_ready
    public_production_ready = $publicProductionReady
    blockers = $blockerCount
    warnings = $warningCount
    blocker_keys = @($readiness.blockers | ForEach-Object { $_.key })
    warning_keys = @($readiness.warnings | ForEach-Object { $_.key })
  }
  steps = $steps
  security = @{
    secrets_included = $false
    credentials_included = $false
    tenant_data_included = $false
  }
}

$resolvedReportDir = Resolve-Path -Path "." | Select-Object -ExpandProperty Path
$targetDir = Join-Path $resolvedReportDir $ReportDir
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$reportPath = Join-Path $targetDir "lexflow-cloud-release-$timestamp.json"
$report | ConvertTo-Json -Depth 8 | Set-Content -Path $reportPath -Encoding UTF8

Write-Host "Release evidence ready: $reportPath"
