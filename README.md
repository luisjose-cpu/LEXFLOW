# LEXFLOW

**LEXFLOW - The Legal Operating System** is a LegalTech SaaS project for law firms that need to replace Excel, Drive, folders, email, and WhatsApp with one governed operating system.

This repository is currently in **P15 - LEXFLOW OS Final**.

P16 production foundation has started. The product remains **pilot-ready**, not public-production-ready.

## P1 Purpose

P1 prepares the monorepo for web, mobile/PWA, API, cloud, testing, premium design, AI, and SaaS growth.

The current architecture creates:

- App structure for `web`, `mobile`, `api`, and `admin`
- Shared packages for UI, design system, shared constants, and types
- Domain module folders
- AI folders for RAG, extraction, embeddings, and prompts
- Infra skeleton for Docker, Nginx, monitoring, and cloud
- Premium web placeholders for core product surfaces
- API skeleton status endpoints
- Backend judicial automation with authorized-source adapters, CAPTCHA checkpoints, evidence, notifications, and approval flow
- Expediente 360 judicial source panels and human-in-the-loop CAPTCHA UI states
- Secure client portal for authorized cases, public timeline, visible documents, hearings, messages, notifications, reports, and uploads
- Multichannel communication center with portal, WhatsApp mock, email-ready payloads, templates, notification rules, and audit trail
- Practical legal AI with OCR, document summary, classification, structured extraction, case summary, search, human review, and usage audit
- Legal intelligence center with official/specialized source adapters, news, jurisprudence, regulations, AI summaries, favorites, alerts, tags, trends, and case links
- Executive Legal Command Center with KPIs, risk, productivity, judicial monitoring, AI usage, communications, legal trends, and decision snapshot
- Mobile-first PWA experience for clients and lawyers with install metadata, service worker, offline fallback, bottom tabs, and role-specific mobile routes
- Billing SaaS foundation with START, PRO, AI, ENTERPRISE plans, feature gates, usage, trial, mock subscription, invoices, onboarding, and billing settings
- Automation Studio with trigger-condition-action workflows, feature gate enforcement, auditable runs, run steps, mock actions, and no-code builder
- Release Candidate RC1 hardening with security headers, configurable CORS/Origin guard, rate limit, upload validation, metrics, QA matrix, threat model, backup policy, observability, open risks, tech debt, production and pilot checklists
- LEXFLOW OS Final with Legal Memory, RAG Legal, global search, Copiloto Juridico, specialized AI agents, Legal Graph, future Marketplace, Demo Mode, commercial landing, final documentation, and release readiness status

## Product Spine

`CLIENTE -> EXPEDIENTE -> DOCUMENTO -> COMUNICACION -> AUTOMATIZACION -> IA -> INTELIGENCIA -> DECISION`

Every future module must strengthen this chain. No isolated screens, orphan features, or ungoverned experiments are accepted.

## Repository Note

The repository contains an early scaffold created before the P0 governance pass. P1 preserves and extends it into a governed architecture base.

## Commands

```bash
npm install
npm run dev:web
npm run dev:api
npm run lint
npm run test
npm run build
npm run test:api
```

Full P1 validation:

```bash
npm run p1:check
```

Full P2 validation:

```bash
npm run p2:check
```

Full P3 validation:

```bash
npm run p3:check
```

Full P4 validation:

```bash
npm run p4:check
```

Full P5 validation:

```bash
npm run p5:check
```

Full P6 validation:

```bash
npm run p6:check
```

Full P7 validation:

```bash
npm run p7:check
```

Full P8 validation:

```bash
npm run p8:check
```

Full P9 validation:

```bash
npm run p9:check
```

Full P10 validation:

```bash
npm run p10:check
```

Full P11 validation:

```bash
npm run p11:check
```

Full P12 validation:

```bash
npm run p12:check
```

Full P13 validation:

```bash
npm run p13:check
```

Full P14 validation:

```bash
npm run p14:check
```

Full P15 validation:

```bash
npm run p15:check
```

Backend API runs at:

```bash
npm run dev:api
```

Core P2 endpoints are under `/api/v1`:

- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`
- `GET /roles`
- `GET|POST /users`
- `GET|POST /clients`
- `GET|POST /cases`
- `GET /audit`

P5 judicial automation endpoints are under `/api/v1`:

- `GET|POST /cases/{case_id}/sources`
- `POST /case-sources/{source_id}/check`
- `GET /case-sources/{source_id}/updates`
- `POST /captcha-checkpoints/{checkpoint_id}/resolve`
- `POST /judicial-updates/{update_id}/approve`
- `POST /judicial-updates/{update_id}/reject`

P6 client portal endpoints are under `/api/v1`:

- `GET /client-portal/me`
- `GET /client-portal/cases`
- `GET /client-portal/cases/{case_id}`
- `GET /client-portal/cases/{case_id}/timeline`
- `GET /client-portal/cases/{case_id}/documents`
- `GET /client-portal/cases/{case_id}/hearings`
- `GET /client-portal/notifications`
- `POST /client-portal/cases/{case_id}/messages`
- `POST /client-portal/cases/{case_id}/documents`
- `GET /client-portal/reports`

P7 communication endpoints are under `/api/v1`:

- `GET /cases/{case_id}/communications`
- `POST /cases/{case_id}/communications`
- `GET /message-templates`
- `POST /message-templates`
- `PATCH /message-templates/{template_id}`
- `DELETE /message-templates/{template_id}`
- `GET /notifications`
- `POST /notifications/send`
- `POST /notifications/test`
- `POST /notifications/{notification_id}/mark-read`

P8 practical legal AI endpoints are under `/api/v1`:

- `POST /ai/documents/{document_id}/ocr`
- `POST /ai/documents/{document_id}/summarize`
- `POST /ai/documents/{document_id}/classify`
- `POST /ai/documents/{document_id}/extract`
- `POST /ai/cases/{case_id}/summary`
- `POST /ai/cases/{case_id}/search`
- `GET /ai/jobs/{job_id}`
- `POST /ai/jobs/{job_id}/approve`
- `POST /ai/jobs/{job_id}/reject`

P9 legal intelligence endpoints are under `/api/v1`:

- `GET /legal-intelligence/sources`
- `POST /legal-intelligence/sources`
- `POST /legal-intelligence/sources/{source_id}/sync`
- `GET /legal-intelligence/news`
- `GET /legal-intelligence/news/{news_id}`
- `POST /legal-intelligence/news/{news_id}/summarize`
- `POST /legal-intelligence/news/{news_id}/favorite`
- `POST /legal-intelligence/news/{news_id}/link-case`
- `GET /legal-intelligence/alerts`
- `GET /legal-intelligence/tags`
- `GET /legal-intelligence/trends`

P10 Legal Command Center endpoints are under `/api/v1`:

- `GET /dashboard/overview`
- `GET /dashboard/kpis`
- `GET /dashboard/risks`
- `GET /dashboard/productivity`
- `GET /dashboard/judicial-monitoring`
- `GET /dashboard/communications`
- `GET /dashboard/ai`
- `GET /dashboard/legal-intelligence`
- `GET /dashboard/trends`
- `GET /dashboard/snapshot`

P11 mobile/PWA endpoints are under `/api/v1`:

- `GET /mobile/client/home`
- `GET /mobile/client/cases`
- `GET /mobile/client/cases/{case_id}`
- `GET /mobile/client/documents`
- `GET /mobile/client/messages`
- `GET /mobile/client/notifications`
- `GET /mobile/lawyer/home`
- `GET /mobile/lawyer/cases`
- `GET /mobile/lawyer/cases/{case_id}`
- `GET /mobile/lawyer/tasks`
- `GET /mobile/lawyer/hearings`
- `GET /mobile/lawyer/notifications`

P11 mobile routes:

- `/m/client`
- `/m/client/cases`
- `/m/client/cases/[id]`
- `/m/client/documents`
- `/m/client/messages`
- `/m/client/notifications`
- `/m/lawyer`
- `/m/lawyer/cases`
- `/m/lawyer/cases/[id]`
- `/m/lawyer/tasks`
- `/m/lawyer/hearings`
- `/m/lawyer/notifications`

P12 Billing SaaS endpoints are under `/api/v1`:

- `GET /billing/plans`
- `GET /billing/current`
- `POST /billing/subscribe-mock`
- `POST /billing/change-plan`
- `GET /billing/usage`
- `GET /billing/features`
- `POST /billing/webhook/mock`

P12 Billing SaaS routes:

- `/pricing`
- `/onboarding`
- `/settings/billing`
- `/settings/usage`
- `/settings/features`

P13 Automation Studio endpoints are under `/api/v1`:

- `GET /automation/catalog`
- `GET|POST /automation/workflows`
- `GET|PATCH|DELETE /automation/workflows/{workflow_id}`
- `POST /automation/workflows/{workflow_id}/activate`
- `POST /automation/workflows/{workflow_id}/run`
- `POST /automation/triggers/run`
- `GET /automation/runs`

P13 Automation Studio route:

- `/automation`

P14 hardening endpoints:

- `GET /metrics`
- `GET /health`
- `GET /version`

P15 LEXFLOW OS endpoints are under `/api/v1`:

- `GET /lexflow-os/memory`
- `POST /lexflow-os/rag/query`
- `POST /lexflow-os/search`
- `POST /lexflow-os/copilot`
- `GET /lexflow-os/agents`
- `GET /lexflow-os/graph`
- `GET /lexflow-os/marketplace`
- `GET /lexflow-os/demo`
- `GET /lexflow-os/release-status`

P15 LEXFLOW OS routes:

- `/`
- `/lexflow-os`
- `/demo`

P16 production foundation endpoints:

- `GET /readiness`
- `GET /api/v1/readiness`

P17 document storage endpoints:

- `GET /api/v1/storage/status`
- `GET /api/v1/client-portal/documents/{document_id}/download`

P18 storage bytes endpoints:

- `PUT /api/v1/storage/mock/{document_id}?token=...`
- `GET /api/v1/storage/mock/{document_id}?token=...`

P19 document trust lifecycle endpoints:

- `GET /api/v1/documents/{document_id}/storage`
- `POST /api/v1/documents/{document_id}/verify-storage`
- `POST /api/v1/documents/{document_id}/scan-mock`
- `POST /api/v1/documents/{document_id}/reject`

P20 tenant bootstrap and CSV import endpoints:

- `POST /api/v1/ops/bootstrap/current-tenant`
- `POST /api/v1/ops/import/clients`
- `POST /api/v1/ops/import/cases`
- `POST /api/v1/ops/import/documents`

P21-P23 operations endpoints and routes:

- `GET /api/v1/ops/import/templates`
- `GET /api/v1/ops/pilot/readiness`
- `GET /api/v1/ops/production-gate`
- `/settings/import`
- `/settings/pilot`
- `/settings/production-gate`
- `npm run production:gate`
- `npm run production:gate:fast`

P24 cloud deploy pack:

- `render.yaml`
- `vercel.json`
- `.github/workflows/cloud-ci.yml`
- `npm run cloud:preflight`
- [CLOUD_DEPLOY_PACK_P24.md](CLOUD_DEPLOY_PACK_P24.md)
- [docs/cloud/P24_CLOUD_DEPLOY_PACK.md](docs/cloud/P24_CLOUD_DEPLOY_PACK.md)

## Key Documents

- [AGENTS.md](AGENTS.md)
- [PROJECT_RULES.md](PROJECT_RULES.md)
- [PRODUCT_SCOPE.md](PRODUCT_SCOPE.md)
- [ROADMAP.md](ROADMAP.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [SECURITY.md](SECURITY.md)
- [QA_RULES.md](QA_RULES.md)
- [DECISIONS.md](DECISIONS.md)
- [RISKS.md](RISKS.md)
- [CHANGELOG.md](CHANGELOG.md)
- [CHECKLIST_P0.md](CHECKLIST_P0.md)
- [READY_FOR_P1.md](READY_FOR_P1.md)
- [READY_FOR_P2.md](READY_FOR_P2.md)
- [READY_FOR_P3.md](READY_FOR_P3.md)
- [READY_FOR_P4.md](READY_FOR_P4.md)
- [READY_FOR_P5.md](READY_FOR_P5.md)
- [READY_FOR_P6.md](READY_FOR_P6.md)
- [READY_FOR_P7.md](READY_FOR_P7.md)
- [READY_FOR_P8.md](READY_FOR_P8.md)
- [READY_FOR_P9.md](READY_FOR_P9.md)
- [READY_FOR_P10.md](READY_FOR_P10.md)
- [READY_FOR_P11.md](READY_FOR_P11.md)
- [READY_FOR_P12.md](READY_FOR_P12.md)
- [READY_FOR_P13.md](READY_FOR_P13.md)
- [READY_FOR_P14.md](READY_FOR_P14.md)
- [READY_FOR_P15.md](READY_FOR_P15.md)
- [READY_FOR_PILOT.md](READY_FOR_PILOT.md)
- [COMMERCIAL_PILOT_PACKAGE.md](COMMERCIAL_PILOT_PACKAGE.md)
- [FINAL_RELEASE.md](FINAL_RELEASE.md)
- [RELEASE_READY_NOT_READY.md](RELEASE_READY_NOT_READY.md)
- [PILOT_READY.md](PILOT_READY.md)
- [PRODUCTION_PENDING.md](PRODUCTION_PENDING.md)
- [RELEASE_CANDIDATE_RC1.md](RELEASE_CANDIDATE_RC1.md)
- [OPEN_RISKS.md](OPEN_RISKS.md)
- [TECH_DEBT.md](TECH_DEBT.md)
- [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)
- [PILOT_CHECKLIST.md](PILOT_CHECKLIST.md)
- [docs/architecture/P1_ARCHITECTURE_BASE.md](docs/architecture/P1_ARCHITECTURE_BASE.md)
- [docs/architecture/P2_BACKEND_CORE.md](docs/architecture/P2_BACKEND_CORE.md)
- [docs/architecture/P3_DATABASE.md](docs/architecture/P3_DATABASE.md)
- [docs/architecture/P6_CLIENT_PORTAL_ARCHITECTURE.md](docs/architecture/P6_CLIENT_PORTAL_ARCHITECTURE.md)
- [docs/architecture/P7_COMMUNICATION_ARCHITECTURE.md](docs/architecture/P7_COMMUNICATION_ARCHITECTURE.md)
- [docs/architecture/P8_AI_ARCHITECTURE.md](docs/architecture/P8_AI_ARCHITECTURE.md)
- [docs/architecture/P9_LEGAL_INTELLIGENCE_ARCHITECTURE.md](docs/architecture/P9_LEGAL_INTELLIGENCE_ARCHITECTURE.md)
- [docs/architecture/P10_COMMAND_CENTER_ARCHITECTURE.md](docs/architecture/P10_COMMAND_CENTER_ARCHITECTURE.md)
- [docs/architecture/P11_PWA_ARCHITECTURE.md](docs/architecture/P11_PWA_ARCHITECTURE.md)
- [docs/architecture/P12_BILLING_ARCHITECTURE.md](docs/architecture/P12_BILLING_ARCHITECTURE.md)
- [docs/architecture/P13_AUTOMATION_STUDIO_ARCHITECTURE.md](docs/architecture/P13_AUTOMATION_STUDIO_ARCHITECTURE.md)
- [docs/architecture/P15_LEXFLOW_OS_ARCHITECTURE.md](docs/architecture/P15_LEXFLOW_OS_ARCHITECTURE.md)
- [docs/testing/P14_PERFORMANCE.md](docs/testing/P14_PERFORMANCE.md)
- [docs/product/P4_EXPEDIENTE_360.md](docs/product/P4_EXPEDIENTE_360.md)
- [docs/product/P5_JUDICIAL_AUTOMATION.md](docs/product/P5_JUDICIAL_AUTOMATION.md)
- [docs/product/P6_CLIENT_PORTAL.md](docs/product/P6_CLIENT_PORTAL.md)
- [docs/product/P7_COMMUNICATION.md](docs/product/P7_COMMUNICATION.md)
- [docs/product/P8_PRACTICAL_LEGAL_AI.md](docs/product/P8_PRACTICAL_LEGAL_AI.md)
- [docs/product/P9_LEGAL_INTELLIGENCE.md](docs/product/P9_LEGAL_INTELLIGENCE.md)
- [docs/product/P10_LEGAL_COMMAND_CENTER.md](docs/product/P10_LEGAL_COMMAND_CENTER.md)
- [docs/product/P11_PWA_MOBILE_EXPERIENCE.md](docs/product/P11_PWA_MOBILE_EXPERIENCE.md)
- [docs/product/P12_BILLING_SAAS.md](docs/product/P12_BILLING_SAAS.md)
- [docs/product/P13_AUTOMATION_STUDIO.md](docs/product/P13_AUTOMATION_STUDIO.md)
- [docs/product/P15_LEXFLOW_OS_FINAL.md](docs/product/P15_LEXFLOW_OS_FINAL.md)
- [docs/product/PILOT_DEMO_SCRIPT.md](docs/product/PILOT_DEMO_SCRIPT.md)
- [docs/product/PILOT_ONBOARDING_CHECKLIST.md](docs/product/PILOT_ONBOARDING_CHECKLIST.md)
- [docs/product/PILOT_SCOPE_AGREEMENT.md](docs/product/PILOT_SCOPE_AGREEMENT.md)
- [docs/product/PILOT_SUCCESS_METRICS.md](docs/product/PILOT_SUCCESS_METRICS.md)
- [docs/security/P2_AUTH_RBAC.md](docs/security/P2_AUTH_RBAC.md)
- [docs/security/P3_JUDICIAL_SOURCES.md](docs/security/P3_JUDICIAL_SOURCES.md)
- [docs/security/P5_CAPTCHA_POLICY.md](docs/security/P5_CAPTCHA_POLICY.md)
- [docs/security/P6_CLIENT_PORTAL_SECURITY.md](docs/security/P6_CLIENT_PORTAL_SECURITY.md)
- [docs/security/P7_WHATSAPP_SECURITY.md](docs/security/P7_WHATSAPP_SECURITY.md)
- [docs/security/P8_AI_SAFETY.md](docs/security/P8_AI_SAFETY.md)
- [docs/security/P9_SOURCE_POLICY.md](docs/security/P9_SOURCE_POLICY.md)
- [docs/security/P11_MOBILE_SECURITY.md](docs/security/P11_MOBILE_SECURITY.md)
- [docs/security/P12_BILLING_SECURITY.md](docs/security/P12_BILLING_SECURITY.md)
- [docs/security/P13_AUTOMATION_SECURITY.md](docs/security/P13_AUTOMATION_SECURITY.md)
- [docs/security/P14_SECURITY_AUDIT.md](docs/security/P14_SECURITY_AUDIT.md)
- [docs/security/P14_THREAT_MODEL.md](docs/security/P14_THREAT_MODEL.md)
- [docs/security/P15_AI_RAG_SECURITY.md](docs/security/P15_AI_RAG_SECURITY.md)
- [docs/testing/P1_VALIDATION.md](docs/testing/P1_VALIDATION.md)
- [docs/testing/P2_VALIDATION.md](docs/testing/P2_VALIDATION.md)
- [docs/testing/P3_VALIDATION.md](docs/testing/P3_VALIDATION.md)
- [docs/testing/P4_QA_CHECKLIST.md](docs/testing/P4_QA_CHECKLIST.md)
- [docs/testing/P5_VALIDATION.md](docs/testing/P5_VALIDATION.md)
- [docs/testing/P6_VALIDATION.md](docs/testing/P6_VALIDATION.md)
- [docs/testing/P7_VALIDATION.md](docs/testing/P7_VALIDATION.md)
- [docs/testing/P8_VALIDATION.md](docs/testing/P8_VALIDATION.md)
- [docs/testing/P9_VALIDATION.md](docs/testing/P9_VALIDATION.md)
- [docs/testing/P10_VALIDATION.md](docs/testing/P10_VALIDATION.md)
- [docs/testing/P11_VALIDATION.md](docs/testing/P11_VALIDATION.md)
- [docs/testing/P12_VALIDATION.md](docs/testing/P12_VALIDATION.md)
- [docs/testing/P13_VALIDATION.md](docs/testing/P13_VALIDATION.md)
- [docs/testing/P14_MASTER_TEST_MATRIX.md](docs/testing/P14_MASTER_TEST_MATRIX.md)
- [docs/testing/P15_FINAL_VALIDATION.md](docs/testing/P15_FINAL_VALIDATION.md)
- [docs/cloud/P14_BACKUP_POLICY.md](docs/cloud/P14_BACKUP_POLICY.md)
- [docs/cloud/P14_OBSERVABILITY.md](docs/cloud/P14_OBSERVABILITY.md)

## Phase Status

P15 is complete when LEXFLOW OS Final, demo mode, RAG source policy, final docs, pilot readiness, production-pending list, tests, build, and visual QA evidence are complete. Release status is **RELEASE READY FOR PILOT / NOT READY FOR PUBLIC PRODUCTION**.
