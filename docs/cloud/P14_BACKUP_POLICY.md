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

## Restore

Before public production, run a restore drill:

1. Restore database into isolated environment.
2. Restore object storage sample set.
3. Verify tenant isolation and login.
4. Verify document links.
5. Verify audit log continuity.
6. Record RPO/RTO evidence.

## RC1 Status

Policy is documented. Restore drill evidence remains open for pilot/prod readiness.
