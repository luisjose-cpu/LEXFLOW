# AGENTS.md

## Mission

Build LEXFLOW as a governed legal operating system, not as a collection of isolated pages. Every contribution must respect the product chain:

`CLIENTE -> EXPEDIENTE -> DOCUMENTO -> COMUNICACION -> AUTOMATIZACION -> IA -> INTELIGENCIA -> DECISION`

## Master Flow

All project work follows this sequence:

1. **PLAN**: Define objective, scope, affected areas, acceptance criteria, risks, and rollback path.
2. **ANALIZAR**: Read existing documents and code before acting. Identify constraints, dependencies, and tenant impact.
3. **DISEÑAR**: Propose the smallest coherent design that fits architecture, security, UX, and QA rules.
4. **IMPLEMENTAR**: Execute only the approved or implied scope. Preserve existing code and avoid unrelated refactors.
5. **TEST**: Run applicable lint, unit, integration, build, and QA checks. Add tests for new behavior.
6. **DOCUMENTAR**: Update relevant docs, decisions, changelog, and operational notes.
7. **VALIDAR**: Confirm acceptance criteria, known risks, and readiness for the next phase.

## Stack Direction

- Web: Next.js, React, TypeScript, Tailwind, shadcn/ui, Framer Motion, Recharts, TanStack Query, Zustand.
- Mobile/PWA: responsive PWA first; React Native + Expo may come later.
- Backend: Python, FastAPI, PostgreSQL, SQLAlchemy, Pydantic, Redis, Celery.
- Storage: MinIO/S3 compatible.
- IA: OpenAI API, OCR, RAG, embeddings, extraction, classification, summaries.
- Infra: Docker, Docker Compose, Nginx, CI/CD, backups, logs, monitoring.

## Security Rules

- Never hardcode credentials, tokens, API keys, secrets, tenant IDs, or privileged user IDs.
- Every principal entity must be multi-tenant.
- Every critical action must create an audit log.
- Authorization must be explicit and server-enforced.
- Sensitive data must be minimized, encrypted where appropriate, and never exposed in logs.
- AI features must respect confidentiality, traceability, and user authorization.

## Cloud Rules

- Design cloud-ready from the start.
- Services must be stateless where possible.
- Storage must be S3-compatible.
- Background work must be queue-friendly.
- Backups, logs, metrics, and health checks are mandatory before production.

## Frontend Premium Rules

- UI base is light, modern, responsive, and mobile-first.
- Visual direction: Apple + Stripe + Linear + Notion.
- Base colors: white, soft gray, deep blue, technology light blue.
- No empty screens.
- No basic or rough frontend.
- Use real workflow surfaces, useful states, and polished responsive behavior.
- Avoid dark UI as the default product base.

## Testing Rules

- No module is complete without tests.
- Critical paths require unit and integration coverage.
- UI work requires responsive and visual QA.
- API work requires tenant isolation and authorization tests.
- Automation and AI features require deterministic test fixtures.

## Restrictions

- Do not delete existing code unless explicitly requested.
- Do not improvise architecture.
- Do not create isolated screens.
- Do not introduce functional modules without product scope, architecture, security, and QA alignment.
- Do not add production dependencies without clear reason.
- Do not bypass lint, tests, build, or QA.

## Mandatory Delivery

Every delivery must include:

- What changed
- What was intentionally not changed
- Tests or checks run
- Risks or limitations
- Next recommended step
