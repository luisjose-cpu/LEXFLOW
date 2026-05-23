# READY_FOR_P6.md

## Status

LEXFLOW P5 is ready for P6 after validation passes.

## Completed In P5

- Judicial source registration endpoints.
- Authorized-source mock adapter contract.
- Judicial update check flow.
- Evidence records for judicial checks.
- CAPTCHA checkpoint flow with human intervention.
- Notifications for paused judicial sources.
- Approval and rejection endpoints.
- Tenant isolation and audit coverage.
- Expediente 360 judicial automation UI states.

## P6 Recommended Scope

P6 should build the Portal Cliente on top of the governed case data model:

- Client-user authentication and restricted permissions.
- Read-only client case dashboard.
- Documents visible to client.
- Notifications and next actions.
- Secure message thread.
- Mobile-first PWA experience.
- Audit logs for client access and document views.

## P6 Entry Criteria

- `npm run p5:check` passes.
- CAPTCHA policy is documented and tested.
- Judicial source actions create audit logs.
- Tenant isolation blocks cross-tenant source access.
- Expediente 360 renders judicial automation states.

## P6 Exit Criteria

- Client users can access only their authorized matters.
- Portal Cliente has mobile-first views for cases, documents, notifications, and messages.
- Client-visible data is explicitly scoped.
- Tests cover permissions, tenancy, audit, loading, empty, and error states.
