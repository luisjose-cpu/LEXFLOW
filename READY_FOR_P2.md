# READY_FOR_P2.md

## Status

LEXFLOW P1 is ready for P2 when validation passes.

## P2 Recommended Scope

P2 should focus on **Expediente 360** as the first end-to-end legal workflow:

- Tenant context
- Auth boundary
- Client model
- Matter model
- Document metadata
- Audit log persistence
- Matter list
- Matter detail
- Responsive workflow UI
- API tests for tenant isolation and audit

## P2 Entry Criteria

- P1 monorepo structure exists.
- Web placeholders exist and build.
- API P1 status endpoints pass tests.
- Shared packages are importable.
- Infra and AI skeletons are documented.
- Risks remain tracked.

## P2 Exit Criteria

- One tenant-scoped legal workflow works end to end.
- Critical actions are audited.
- Tests cover tenant isolation.
- UI has loading, empty, error, and permission states.
- Documentation and changelog are updated.
