param(
  [string]$ApiUrl = $env:LEXFLOW_API_URL,
  [string]$ExpectedRevision = $env:LEXFLOW_EXPECTED_REVISION,
  [switch]$Strict
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
$ExpectedRevision = Resolve-ExpectedRevision $ExpectedRevision

if (-not $ApiUrl) {
  throw "LEXFLOW_API_URL or -ApiUrl is required"
}

if (-not $ExpectedRevision) {
  throw "LEXFLOW_EXPECTED_REVISION, -ExpectedRevision or local git HEAD is required"
}

$versionResponse = Invoke-WebRequestWithRetry -Uri "$ApiUrl/version"
$version = $versionResponse.Content | ConvertFrom-Json
$actualRevision = "$($version.revision)".Trim()

Write-Host "Expected revision: $ExpectedRevision"
Write-Host "Cloud revision: $actualRevision"

if (-not $actualRevision -or $actualRevision -eq "unknown") {
  $message = "Cloud API does not expose revision yet. Redeploy latest master or set RELEASE_REVISION/RENDER_GIT_COMMIT."
  if ($Strict) {
    throw $message
  }
  Write-Host $message
  exit 0
}

if (-not $ExpectedRevision.StartsWith($actualRevision) -and -not $actualRevision.StartsWith($ExpectedRevision)) {
  throw "Cloud revision mismatch. Expected $ExpectedRevision but API reports $actualRevision"
}

Write-Host "Cloud revision matches expected commit."
