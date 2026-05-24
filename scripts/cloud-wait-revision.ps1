param(
  [string]$ApiUrl = $env:LEXFLOW_API_URL,
  [string]$ExpectedRevision = $env:LEXFLOW_EXPECTED_REVISION,
  [int]$TimeoutSeconds = 900,
  [int]$IntervalSeconds = 15
)

$ErrorActionPreference = "Stop"

function Normalize-Url {
  param([string]$Url)
  if (-not $Url) {
    return ""
  }
  return $Url.Trim().TrimEnd("/")
}

function Resolve-ExpectedRevision {
  param([string]$Revision)
  if ($Revision) {
    return $Revision.Trim()
  }
  $git = Get-Command git -ErrorAction SilentlyContinue
  if (-not $git) {
    return ""
  }
  $head = & $git.Source rev-parse HEAD
  if ($LASTEXITCODE -ne 0) {
    return ""
  }
  return $head.Trim()
}

function Test-RevisionMatch {
  param(
    [string]$Expected,
    [string]$Actual
  )
  if (-not $Expected -or -not $Actual -or $Actual -eq "unknown") {
    return $false
  }
  return $Expected.StartsWith($Actual) -or $Actual.StartsWith($Expected)
}

if ($TimeoutSeconds -lt 30) {
  throw "TimeoutSeconds must be at least 30"
}

if ($IntervalSeconds -lt 5) {
  throw "IntervalSeconds must be at least 5"
}

$ApiUrl = Normalize-Url $ApiUrl
$ExpectedRevision = Resolve-ExpectedRevision $ExpectedRevision

if (-not $ApiUrl) {
  throw "LEXFLOW_API_URL or -ApiUrl is required"
}

if (-not $ExpectedRevision) {
  throw "LEXFLOW_EXPECTED_REVISION, -ExpectedRevision or local git HEAD is required"
}

$startedAt = Get-Date
$deadline = $startedAt.AddSeconds($TimeoutSeconds)
$attempt = 0
$lastRevision = ""

Write-Host "Waiting for cloud revision."
Write-Host "Expected revision: $ExpectedRevision"
Write-Host "API URL: $ApiUrl"
Write-Host "Timeout seconds: $TimeoutSeconds"

while ((Get-Date) -lt $deadline) {
  $attempt += 1
  try {
    $versionResponse = Invoke-WebRequest -Uri "$ApiUrl/version" -Method GET -UseBasicParsing -TimeoutSec 30
    $version = $versionResponse.Content | ConvertFrom-Json
    $lastRevision = "$($version.revision)".Trim()
    Write-Host "Attempt ${attempt}: cloud revision '$lastRevision'"

    if (Test-RevisionMatch -Expected $ExpectedRevision -Actual $lastRevision) {
      $elapsedSeconds = [Math]::Round(((Get-Date) - $startedAt).TotalSeconds, 2)
      Write-Host "Cloud revision matches expected commit after $elapsedSeconds seconds."
      exit 0
    }
  } catch {
    Write-Host "Attempt ${attempt}: revision check failed: $($_.Exception.Message)"
  }

  Start-Sleep -Seconds $IntervalSeconds
}

throw "Cloud revision did not match expected commit within $TimeoutSeconds seconds. Expected $ExpectedRevision, last cloud revision '$lastRevision'."
