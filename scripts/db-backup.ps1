param(
  [string]$DatabaseUrl = $env:DATABASE_URL,
  [string]$BackupDir = $env:LEXFLOW_BACKUP_DIR,
  [string]$Label = "manual"
)

$ErrorActionPreference = "Stop"

if (-not $DatabaseUrl) {
  throw "DATABASE_URL or -DatabaseUrl is required"
}

if (-not $BackupDir) {
  $BackupDir = "backups/postgres"
}

$pgDump = Get-Command pg_dump -ErrorAction SilentlyContinue
if (-not $pgDump) {
  throw "pg_dump is required. Install PostgreSQL client tools before running backups."
}

$safeLabel = ($Label -replace "[^a-zA-Z0-9._=-]", "-").Trim(".-")
if (-not $safeLabel) {
  $safeLabel = "manual"
}

$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$resolvedBackupDir = New-Item -ItemType Directory -Force -Path $BackupDir
$backupPath = Join-Path $resolvedBackupDir.FullName "lexflow-$safeLabel-$timestamp.dump"

Write-Host "==> Creating PostgreSQL custom-format backup"
& $pgDump.Source --dbname $DatabaseUrl --format custom --no-owner --no-acl --file $backupPath
if ($LASTEXITCODE -ne 0) {
  throw "pg_dump failed"
}

$item = Get-Item $backupPath
if ($item.Length -le 0) {
  throw "Backup file is empty"
}

Write-Host "Backup ready: $backupPath"
Write-Host "Backup bytes: $($item.Length)"
