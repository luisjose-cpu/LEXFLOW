param(
  [string]$ReportDir = "reports/restore",
  [int]$MaxAgeHours = 720,
  [switch]$AllowInspectionOnly
)

$ErrorActionPreference = "Stop"

function Fail-EvidenceGate {
  param([string]$Message)
  throw "Restore evidence gate failed: $Message"
}

if (-not (Test-Path $ReportDir)) {
  Fail-EvidenceGate "restore evidence directory not found: $ReportDir"
}

$latestReport = Get-ChildItem -Path $ReportDir -Filter "lexflow-restore-drill-*.json" -File |
  Sort-Object LastWriteTimeUtc -Descending |
  Select-Object -First 1

if (-not $latestReport) {
  Fail-EvidenceGate "no lexflow-restore-drill-*.json report found in $ReportDir"
}

$evidence = Get-Content -Path $latestReport.FullName -Raw | ConvertFrom-Json

if ($evidence.product -ne "LEXFLOW") {
  Fail-EvidenceGate "unexpected product marker"
}

if (-not $evidence.generated_at) {
  Fail-EvidenceGate "generated_at is required"
}

$generatedAt = ([datetime]::Parse($evidence.generated_at)).ToUniversalTime()
$ageHours = ((Get-Date).ToUniversalTime() - $generatedAt).TotalHours

if ($ageHours -gt $MaxAgeHours) {
  Fail-EvidenceGate "latest restore evidence is older than $MaxAgeHours hours"
}

if (-not $evidence.backup_file -or $evidence.backup_bytes -le 0) {
  Fail-EvidenceGate "backup filename and non-empty byte count are required"
}

if (-not $evidence.catalog_sample -or $evidence.catalog_sample.Count -le 0) {
  Fail-EvidenceGate "backup catalog sample is required"
}

$hasExecutedRestore = ($evidence.status -eq "restore_completed" -and $evidence.executed_restore -eq $true)
$hasInspectionOnly = ($evidence.status -eq "inspection_passed" -and $evidence.executed_restore -eq $false)

if (-not $hasExecutedRestore) {
  if (-not ($AllowInspectionOnly -and $hasInspectionOnly)) {
    Fail-EvidenceGate "status must be restore_completed with executed_restore=true"
  }
}

if (-not $evidence.security) {
  Fail-EvidenceGate "security evidence flags are required"
}

if ($evidence.security.database_urls_included -ne $false) {
  Fail-EvidenceGate "database_urls_included must be false"
}

if ($evidence.security.credentials_included -ne $false) {
  Fail-EvidenceGate "credentials_included must be false"
}

if ($evidence.security.tenant_data_included -ne $false) {
  Fail-EvidenceGate "tenant_data_included must be false"
}

$summary = @{
  product = "LEXFLOW"
  status = "restore_evidence_gate_passed"
  report = $latestReport.Name
  restore_status = $evidence.status
  executed_restore = $evidence.executed_restore
  generated_at = $evidence.generated_at
  max_age_hours = $MaxAgeHours
  allow_inspection_only = [bool]$AllowInspectionOnly
  secrets_included = $false
  credentials_included = $false
  tenant_data_included = $false
}

Write-Host "Restore evidence gate passed: $($latestReport.FullName)"
$summary | ConvertTo-Json -Depth 4
