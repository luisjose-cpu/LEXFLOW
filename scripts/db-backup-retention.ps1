param(
  [string]$BackupDir = $env:LEXFLOW_BACKUP_DIR,
  [string]$ReportDir = "reports/backup",
  [int]$DailyKeep = 30,
  [int]$MonthlyKeep = 12,
  [switch]$Apply
)

$ErrorActionPreference = "Stop"

if (-not $BackupDir) {
  $BackupDir = "backups/postgres"
}

if ($DailyKeep -lt 1) {
  throw "DailyKeep must be at least 1"
}

if ($MonthlyKeep -lt 0) {
  throw "MonthlyKeep must be zero or greater"
}

$backupRoot = Resolve-Path -Path $BackupDir -ErrorAction SilentlyContinue
if (-not $backupRoot) {
  Write-Host "Backup directory does not exist: $BackupDir"
  $backupRootPath = (New-Item -ItemType Directory -Force -Path $BackupDir).FullName
} else {
  $backupRootPath = $backupRoot.Path
}

$backupRootFull = [System.IO.Path]::GetFullPath($backupRootPath)
$files = Get-ChildItem -Path $backupRootFull -Filter "lexflow-*.dump" -File | Sort-Object LastWriteTimeUtc -Descending

$protected = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($file in ($files | Select-Object -First $DailyKeep)) {
  [void]$protected.Add($file.FullName)
}

if ($MonthlyKeep -gt 0) {
  $monthly = $files |
    Group-Object { $_.LastWriteTimeUtc.ToString("yyyy-MM") } |
    Sort-Object Name -Descending |
    Select-Object -First $MonthlyKeep
  foreach ($group in $monthly) {
    $monthlyFile = $group.Group | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
    if ($monthlyFile) {
      [void]$protected.Add($monthlyFile.FullName)
    }
  }
}

$candidates = @($files | Where-Object { -not $protected.Contains($_.FullName) })
$deleted = @()

if ($Apply) {
  foreach ($candidate in $candidates) {
    $candidateFull = [System.IO.Path]::GetFullPath($candidate.FullName)
    if (-not $candidateFull.StartsWith($backupRootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
      throw "Refusing to delete file outside backup directory: $candidateFull"
    }
    Remove-Item -LiteralPath $candidateFull -Force
    $deleted += $candidate.Name
  }
}

$targetDir = New-Item -ItemType Directory -Force -Path $ReportDir
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$reportPath = Join-Path $targetDir.FullName "lexflow-backup-retention-$timestamp.json"
$report = @{
  product = "LEXFLOW"
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  backup_dir = $backupRootFull
  applied = [bool]$Apply
  daily_keep = $DailyKeep
  monthly_keep = $MonthlyKeep
  total_backups = @($files).Count
  retained_backups = $protected.Count
  delete_candidates = @($candidates | ForEach-Object { $_.Name })
  deleted_backups = $deleted
  security = @{
    database_urls_included = $false
    credentials_included = $false
    tenant_data_included = $false
  }
}
$report | ConvertTo-Json -Depth 6 | Set-Content -Path $reportPath -Encoding UTF8

Write-Host "Backup retention evidence ready: $reportPath"
Write-Host "Delete candidates: $(@($candidates).Count)"
if ($Apply) {
  Write-Host "Deleted backups: $($deleted.Count)"
} else {
  Write-Host "Dry run only. Re-run with -Apply to delete candidates."
}
