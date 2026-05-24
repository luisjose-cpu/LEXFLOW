param(
  [Parameter(Mandatory = $true)]
  [string]$BackupPath,
  [string]$RestoreDatabaseUrl = $env:RESTORE_DATABASE_URL,
  [switch]$Execute
)

$ErrorActionPreference = "Stop"

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
& $pgRestore.Source --list $BackupPath | Select-Object -First 20
if ($LASTEXITCODE -ne 0) {
  throw "pg_restore --list failed"
}

if (-not $Execute) {
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

Write-Host "Restore drill completed against isolated database."
