# P5 Judicial Automation Architecture

## Module Shape

P5 extends the P3/P4 backend with service-layer orchestration around judicial sources:

- Source lifecycle: create, list, activate, pause for CAPTCHA.
- Adapter execution: one adapter contract with source-specific mock implementations.
- Update lifecycle: pending approval, approved, rejected, paused.
- Evidence lifecycle: store raw adapter metadata for future traceability.
- Notification lifecycle: create tenant-scoped operational notices.
- Audit lifecycle: every critical source, CAPTCHA, and approval action is logged.

## Database Additions

- `captcha_checkpoints`
- `judicial_evidence`

Existing P3 tables remain the system of record for `case_sources`, `judicial_updates`, `notifications`, and `audit_logs`.

## Tenant Model

Every P5 operation is resolved through the authenticated user tenant. Case source creation checks case ownership by tenant, source checks enforce tenant ownership, and approval/rejection operations are blocked across tenants.

## Adapter Contract

Adapters return a normalized result with:

- `status`
- `title`
- `summary`
- `captcha_required`
- `raw_payload`

This keeps future real connectors replaceable without changing Expediente 360 or approval workflow contracts.
