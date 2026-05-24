param(
  [Parameter(Mandatory = $true)]
  [string]$BackupPath,
  [string]$RestoreDatabaseUrl = $env:RESTORE_DATABASE_URL,
  [string]$ReportDir = "reports/restore",
  [switch]$Execute
)

$ErrorActionPreference = "Stop"
$startedAt = (Get-Date).ToUniversalTime()

if (-not (Test-Path $BackupPath)) {
  throw "Backup file not found: $BackupPath"
}

$pgRestore = Get-Command pg_restore -ErrorAction SilentlyContinue
if (-not $pgRestore) {
  throw "pg_restore is required. Install PostgreSQL client tools before running restore drills."
}

$item = Get-Item $BackupPath
if ($item.Length -le 0) {
  throw "Backup file is empty: $BackupPath"
}

Write-Host "==> Inspecting backup catalog"
$catalogSample = & $pgRestore.Source --list $BackupPath | Select-Object -First 20
$catalogSample
if ($LASTEXITCODE -ne 0) {
  throw "pg_restore --list failed"
}

function Write-RestoreEvidence {
  param(
    [string]$Status,
    [bool]$Executed,
    [string[]]$CatalogSample,
    [string]$ErrorMessage = ""
  )
  $finishedAt = (Get-Date).ToUniversalTime()
  $targetDir = New-Item -ItemType Directory -Force -Path $ReportDir
  $timestamp = $finishedAt.ToString("yyyyMMddTHHmmssZ")
  $reportPath = Join-Path $targetDir.FullName "lexflow-restore-drill-$timestamp.json"
  $report = @{
    product = "LEXFLOW"
    generated_at = $finishedAt.ToString("o")
    status = $Status
    executed_restore = $Executed
    backup_file = $item.Name
    backup_bytes = $item.Length
    catalog_sample = $CatalogSample
    started_at = $startedAt.ToString("o")
    finished_at = $finishedAt.ToString("o")
    duration_seconds = [Math]::Round(($finishedAt - $startedAt).TotalSeconds, 2)
    security = @{
      database_urls_included = $false
      credentials_included = $false
      tenant_data_included = $false
    }
    error = $ErrorMessage
  }
  $report | ConvertTo-Json -Depth 6 | Set-Content -Path $reportPath -Encoding UTF8
  Write-Host "Restore evidence ready: $reportPath"
}

if (-not $Execute) {
  Write-RestoreEvidence -Status "inspection_passed" -Executed $false -CatalogSample $catalogSample
  Write-Host "Restore drill inspection passed. Re-run with -Execute and RESTORE_DATABASE_URL to restore into an isolated database."
  exit 0
}

if (-not $RestoreDatabaseUrl) {
  throw "RESTORE_DATABASE_URL or -RestoreDatabaseUrl is required when -Execute is used"
}

Write-Host "==> Restoring into isolated database"
& $pgRestore.Source --dbname $RestoreDatabaseUrl --clean --if-exists --no-owner --no-acl $BackupPath
if ($LASTEXITCODE -ne 0) {
  throw "pg_restore execution failed"
}

Write-RestoreEvidence -Status "restore_completed" -Executed $true -CatalogSample $catalogSample
Write-Host "Restore drill completed against isolated database."
