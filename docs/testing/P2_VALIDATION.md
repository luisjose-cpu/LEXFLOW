# P2 Validation

## Command

```bash
cd apps/api
python -m pytest
```

Full workspace gate:

```bash
npm run p2:check
```

`p2:check` currently delegates to the full workspace gate: lint, web tests, web build, and API tests.

## Covered

- Auth login, me, refresh, logout, revoked refresh token
- Bad password rejection
- RBAC denial for lawyer user administration
- Client CRUD, search, tags
- Case CRUD, assignment, status change
- Tenant isolation for cross-tenant header
- Audit list and filters
- Existing P1/P0 health and tenant audit tests

## Current Result

`9 passed`

## P3 Test Expansion

- Database integration tests
- Migration tests
- Repository tests
- Auth edge cases
- Permission matrix tests
- Rate limit tests
- API contract tests for frontend integration
