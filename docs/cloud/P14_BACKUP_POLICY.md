# P14 Backup Policy

## Scope

- PostgreSQL database.
- S3-compatible object storage.
- Environment configuration.
- Audit logs and operational logs.

## Policy

- Database backup: daily full backup, hourly WAL/archive where supported.
- Object storage backup: daily bucket replication or versioned snapshot.
- Retention: 30 daily, 12 monthly for production.
- Encryption: at rest and in transit.
- Access: least privilege, break-glass audited.

## Scripts

Create a PostgreSQL custom-format backup:

```powershell
$env:DATABASE_URL="<render-postgres-url>"
npm run db:backup -- -Label staging
```

Validate backup catalog without restoring:

```powershell
npm run db:restore-drill -- -BackupPath backups/postgres/lexflow-staging-YYYYMMDDTHHMMSSZ.dump
```

Restore into an isolated drill database:

```powershell
$env:RESTORE_DATABASE_URL="<isolated-restore-db-url>"
npm run db:restore-drill -- -BackupPath backups/postgres/lexflow-staging-YYYYMMDDTHHMMSSZ.dump -Execute
```

The scripts do not print database URLs or credentials. Backup artifacts are ignored by git under `backups/`.

`db:backup` writes a non-secret manifest under `reports/backup/lexflow-backup-*.json` with backup filename, bytes, duration and security flags.

Apply local backup retention policy in dry-run mode:

```powershell
npm run db:backup-retention
```

Delete candidates only after review:

```powershell
npm run db:backup-retention -- -Apply
```

`db:backup-retention` keeps the newest 30 daily backups and newest 12 monthly backups by default. It writes non-secret evidence under `reports/backup/lexflow-backup-retention-*.json`; deletion is opt-in and refuses paths outside the configured backup directory.

`db:restore-drill` writes structured evidence under `reports/restore/lexflow-restore-drill-*.json`. The report includes backup filename, backup bytes, catalog sample, status, duration and security flags. It does not include database URLs, passwords, tokens or tenant data.

Validate latest restore evidence before public production:

```powershell
npm run db:restore-evidence
```

By default, this gate requires recent evidence with `status=restore_completed` and `executed_restore=true`. It also verifies that the restore evidence declares `database_urls_included=false`, `credentials_included=false` and `tenant_data_included=false`.

After the gate passes for an isolated restore drill, update the API environment with the UTC completion timestamp:

```env
RESTORE_DRILL_VERIFIED_AT=2026-05-24T00:00:00Z
RESTORE_DRILL_MAX_AGE_HOURS=720
```

`/readiness` uses those values to keep public production blocked by warning until the restore drill evidence is recent.

For a controlled pilot where only backup catalog inspection is being reviewed, the gate can be run explicitly in inspection mode:

```powershell
npm run db:restore-evidence -- -AllowInspectionOnly
```

## Restore

Before public production, run a restore drill:

1. Restore database into isolated environment.
2. Restore object storage sample set.
3. Verify tenant isolation and login.
4. Verify document links.
5. Verify audit log continuity.
6. Record RPO/RTO evidence.

## RC1 Status

Policy, scripts, local evidence generation and restore evidence gating are documented. Public production still requires a real restore drill against an isolated database, then `npm run db:restore-evidence`.
