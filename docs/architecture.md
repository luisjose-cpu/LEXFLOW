# LEXFLOW Architecture

## Product Spine

LEXFLOW is not a set of isolated screens. The system is organized around one operational spine:

1. Client
2. Matter
3. Document
4. Communication
5. Automation
6. AI
7. Intelligence
8. Decision

Every module should either enrich this chain, automate part of it, or produce managerial visibility from it.

## Tenancy

All principal entities include `tenant_id`. API access must resolve the active tenant before data access. Cross-tenant queries are forbidden unless a future platform-admin boundary explicitly allows them.

Principal entities:

- Tenant
- User
- Client
- Matter
- Document
- Communication
- AutomationRun
- AiInsight
- BillingSubscription
- AuditLog

## Audit

Critical actions create an `AuditLog` row:

- Create, update, delete principal entity
- Upload, classify, or share document
- Send communication
- Trigger automation
- Run AI extraction, summary, or classification
- Billing and permission changes

## Backend Layers

- `api`: HTTP routes and request/response schemas
- `domain`: entity definitions and business rules
- `services`: orchestration, audit, integrations
- `db`: database session and persistence concerns
- `core`: configuration, security, tenancy context

## Frontend Layers

- `app`: route shells and screen composition
- `components`: reusable UI primitives and domain surfaces
- `lib`: clients, formatters, constants
- `styles`: Tailwind/global tokens

## Quality Gate

A module is not done until:

- It is tenant-aware
- Critical actions are audited
- Empty/loading/error states exist
- Tests cover core behavior
- Lint, tests, build, and QA pass
