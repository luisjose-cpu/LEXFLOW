# READY_FOR_P4.md

## Status

LEXFLOW P3 is ready for P4 planning after validation passes.

## P4 Recommended Scope

P4 should connect the persistent database to the application layer:

- SQLAlchemy repositories
- API endpoints backed by database sessions
- Persistent auth users and roles
- Persistent clients and cases
- Persistent audit log
- Expediente 360 API contract
- Judicial source status API
- Portal Cliente read model
- Dashboard queries

## P4 Entry Criteria

- Alembic initial migration exists.
- Full MVP schema exists.
- Demo seed passes tests.
- Tenant isolation is tested.
- CAPTCHA-required judicial source behavior is tested.
- Existing P2 auth/RBAC tests still pass.

## P4 Exit Criteria

- P2 in-memory services are replaced or wrapped by database-backed repositories.
- API reads and writes persist to PostgreSQL-compatible storage.
- Tenant isolation is enforced at repository/query level.
- Audit logs are append-only and persistent.
- Frontend can consume persistent cases, clients, hearings, tasks, documents, and dashboard metrics.

## Known P3 Limitation

P3 creates the schema, seed, migrations, and database-level tests. API endpoints still use the P2 in-memory services until P4 connects them to the database layer.
