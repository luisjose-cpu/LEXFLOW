# P1 Architecture Base

## Goal

Prepare the LEXFLOW monorepo for web, mobile/PWA, API, cloud, shared packages, testing, premium design, and SaaS growth.

## Created Structure

- `apps/web`
- `apps/mobile`
- `apps/api`
- `apps/admin`
- `packages/ui`
- `packages/design-system`
- `packages/shared`
- `packages/types`
- `modules/*`
- `infra/docker`
- `infra/nginx`
- `infra/monitoring`
- `infra/cloud`
- `ai/rag`
- `ai/extraction`
- `ai/embeddings`
- `ai/prompts`
- `docs`
- `tests`
- `scripts`

## Web Surface

P1 provides premium placeholders for:

- Login
- Dashboard
- Clients
- Cases
- Case detail
- Documents
- Hearings
- Portal
- AI
- Legal Intelligence
- Settings

## API Surface

P1 exposes:

- `GET /health`
- `GET /version`
- `GET /api/v1/status`

Existing prototype endpoints are preserved.

## Shared Packages

- `@lexflow/ui`: Button, Card, Badge, Input, Modal, EmptyState, PageHeader, MetricCard.
- `@lexflow/design-system`: colors, spacing, typography, radius, shadows, breakpoints.
- `@lexflow/shared`: product spine, navigation, P1 metrics.
- `@lexflow/types`: shared SaaS and legal domain types.

## Guardrail

P1 is architecture base only. Real business workflows, persistence, auth, billing, automation, and AI execution are deferred.
