# P3 Validation

## Command

```bash
npm run p3:check
```

API-only:

```bash
cd apps/api
python -m pytest
```

## Covered

- Full MVP schema exists.
- Required indexes exist.
- Demo seed creates MVP graph.
- Tenant isolation queries are scoped.
- Case creation relationships work.
- Case events work.
- Case sources work.
- Judicial updates work.
- CAPTCHA-required flow pauses, notifies, requires human intervention, and audits.
- Audit logs are created.
- Soft delete keeps records while hiding active queries.
- Relationship tables are tenant-scoped.
- Existing P2 auth/RBAC tests still pass.

## Current Result

`17 passed`
