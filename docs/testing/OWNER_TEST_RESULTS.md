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

- owner JWT login/refresh/logout/me.
- initial owner bootstrap script.
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

- 101 passed.

## Frontend

Command:

```bash
npm --workspace apps/web run test -- components/__tests__/owner-console.test.tsx
```

Result:

- 12 passed.

Global web command:

```bash
npm --workspace apps/web run test
```

Result:

- 57 passed.

Build and cloud checks:

```bash
npm --workspace apps/web run lint
npm --workspace apps/web run build
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
- Owner dashboard conectado al Owner API cuando existe JWT owner.
- Owner logout remoto y limpieza de tokens locales owner.
- Owner tenant creation via Owner API.
- Owner tenant lifecycle actions via Owner API.
- Owner feature flag save via Owner API.
- Owner support ticket creation via Owner API.
- Owner support ticket resolution via Owner API.
- Owner commercial demo tenant creation via Owner API.
- Owner temporary intervention creation via Owner API.
