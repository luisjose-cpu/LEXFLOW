# READY_FOR_P3.md

## Status

LEXFLOW P2 Backend Core is ready for P3 planning after validation passes.

## P3 Recommended Scope

P3 should focus on turning the backend core into a persistent Expediente 360 foundation:

- SQLAlchemy models
- Alembic migrations
- PostgreSQL persistence
- Repository layer
- Auth configuration hardening
- Tenant-aware database queries
- Persistent audit log
- Frontend integration with auth and cases
- Loading, empty, error, and permission states in web

## P3 Entry Criteria

- P2 tests pass.
- Auth endpoints work.
- RBAC blocks unauthorized actions.
- Tenant isolation is tested.
- Client and case CRUD contracts exist.
- Audit filtering exists.
- Demo seed exists.

## P3 Exit Criteria

- Data survives process restart.
- Tenant isolation is enforced at query layer.
- Audit log is append-only in persistent storage.
- Frontend can log in and call protected endpoints.
- At least one Expediente 360 workflow works end to end.
- CI runs backend and web gates.

## Known P2 Limitation

P2 uses in-memory services. This is intentional for backend contract formation. P3 must replace in-memory storage with durable persistence before production-like usage.
