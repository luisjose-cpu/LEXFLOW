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

`db:restore-drill` writes structured evidence under `reports/restore/lexflow-restore-drill-*.json`. The report includes backup filename, backup bytes, catalog sample, status, duration and security flags. It does not include database URLs, passwords, tokens or tenant data.

## Restore

Before public production, run a restore drill:

1. Restore database into isolated environment.
2. Restore object storage sample set.
3. Verify tenant isolation and login.
4. Verify document links.
5. Verify audit log continuity.
6. Record RPO/RTO evidence.

## RC1 Status

Policy, scripts and local evidence generation are documented. Public production still requires a real restore drill against an isolated database and evidence review.
