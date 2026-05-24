# Owner Console Test Results

Date: 2026-05-24

## Backend

Command:

```bash
python -m pytest tests/test_owner_console.py -q
```

Result:

- 4 passed.

Coverage:

- owner_admin accede.
- tenant normal bloqueado.
- owner_support limitado.
- crear tenant.
- suspender tenant.
- reactivar tenant.
- cambiar plan.
- activar feature.
- crear y resolver ticket.
- crear y expirar intervencion.
- health score calculado.
- audit log creado.

Global API command:

```bash
python -m pytest -q
```

Result:

- 99 passed.

## Frontend

Command:

```bash
npm run test -- --run components/__tests__/owner-console.test.tsx
```

Result:

- 5 passed.

Global web command:

```bash
npm run test
```

Result:

- 50 passed.

Build and cloud checks:

```bash
npm run lint
npm run build
npm run cloud:preflight
```

Result:

- Passed.

Coverage:

- OwnerDashboard.
- TenantsList.
- TenantDetail.
- TenantUsage.
- TenantFeatures.
- PlansManager.
- SupportTickets.
- SystemHealth.
- DemoTenants.
- InterventionRequests.
- OwnerAuditLogs.
