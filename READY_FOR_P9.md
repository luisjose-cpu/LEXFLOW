# READY_FOR_P9.md

## Status

LEXFLOW P8 is ready for P9 after validation passes.

## Completed In P8

- Practical legal AI service facade.
- OCR service and mock OCR provider.
- Document analysis service for summary, classification, and extraction.
- Case summary and search service.
- AI job service with human review.
- AI usage audit service.
- Future provider boundaries for cloud OCR and OpenAI LLM.
- AI RBAC permissions.
- AI endpoints for documents, cases, jobs, approval, and rejection.
- Prompt files for all requested P8 tasks.
- Practical AI frontend route.
- Backend and frontend tests.
- AI architecture, safety, product, and validation docs.

## P9 Recommended Scope

P9 should build billing SaaS foundations:

- Plans and subscriptions.
- Tenant billing state.
- Usage metering for users, storage, messages, and AI jobs.
- Invoice-ready records.
- Payment provider boundary.
- Admin billing views.

## P9 Entry Criteria

- `npm run p8:check` passes.
- AI outputs include the professional review disclaimer.
- AI endpoints are tenant scoped.
- AI jobs are auditable.
- Human review approve/reject works.

## P9 Exit Criteria

- Billing entities are tenant scoped.
- Subscription state affects access safely.
- Usage metrics are auditable.
- Billing docs and tests are complete.
