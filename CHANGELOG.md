# CHANGELOG.md

## 2026-05-24 - Security Alert Email Deliveries

### Added

- `security_alert_deliveries` persistence with Alembic migration `20260524_0022`.
- Tenant delivery telemetry endpoints under `/api/v1/settings/security-alert-deliveries`.
- Owner delivery telemetry endpoints under `/api/v1/owner/security-alert-deliveries`.
- Automatic prepared/email-provider delivery for `high` and `critical` security alerts.
- Retry-ready delivery processing with attempt counters, due dates and failure state.
- One-off script `scripts/process_security_alert_deliveries.py` for Render jobs or cron-based processing.
- Settings and Owner Console panels now show security alert delivery telemetry and manual retry processing.

### Security

- Alert delivery recipients are encrypted at rest and exposed only as redacted hints.
- Delivery payloads never include passwords, MFA secrets, recovery codes, tokens or tenant secrets.
- Tenant deliveries target active `tenant_admin` and `partner` users; owner deliveries stay inside Owner Console scope.

## 2026-05-24 - Cloud Post-Deploy Smoke

### Added

- `scripts/cloud-smoke.ps1` to verify public API health, version, API status, web home and web login after deploy.
- Smoke validation reads `/readiness` and fails on production blockers.
- Smoke validation checks `/metrics` availability.
- Optional tenant admin login smoke using `LEXFLOW_SMOKE_TENANT_SLUG`, `LEXFLOW_SMOKE_ADMIN_EMAIL` and `LEXFLOW_SMOKE_ADMIN_PASSWORD`.
- Tenant login smoke now also validates authenticated `/api/v1/storage/status`.
- `npm run cloud:smoke` for repeatable post-deploy validation.
- GitHub Actions now runs on `main` and `master` and exposes a manual post-deploy smoke job.
- Settings Production Gate now loads live `/ops/production-gate` readiness checks when a tenant session exists.
- Render blueprint now includes cron `lexflow-security-alert-deliveries` for scheduled security alert delivery processing.

### Security

- Smoke test does not print passwords, bearer tokens or response payloads with secrets.

## 2026-05-24 - S3 Compatible Document Storage

### Added

- S3/R2-compatible document storage backend with lazy `boto3` client.
- `STORAGE_BACKEND=s3` support for upload, metadata verification and download through the existing signed API proxy contract.
- Storage tests with fake S3 client to validate bytes, checksum metadata and download without real credentials.
- Production readiness now warns when public production is still using `STORAGE_BACKEND=local` and checks S3 access key when S3 mode is enabled.

### Security

- S3 credentials stay server-side and are never returned to the frontend.
- Existing signed token, tenant storage key, content-type, size limit and audit controls remain enforced for S3 mode.

## 2026-05-24 - Backup And Restore Drill Scripts

### Added

- `scripts/db-backup.ps1` for PostgreSQL custom-format backups using `pg_dump`.
- `scripts/db-restore-drill.ps1` for safe backup catalog inspection and optional isolated restore with `-Execute`.
- `npm run db:backup` and `npm run db:restore-drill`.
- `backups/` ignored by git.

### Security

- Backup and restore scripts do not print database URLs, tokens or credentials.
- Restore execution requires explicit `-Execute` and `RESTORE_DATABASE_URL`.

## 2026-05-24 - Owner Live System Health

### Added

- Render blueprint now uses `autoDeployTrigger: checksPass` to avoid stale deploys while preserving CI gates.
- Added `cloud:wait-revision` to poll deployed `/version.revision` until Render serves the expected commit.
- Production readiness now rejects placeholder secret values such as `replace-with...` even when they are long enough.
- Added `cloud:public-ready` as a strict commercial launch gate for zero readiness blockers and warnings.
- Web now declares baseline production security headers in Next.js config.
- API security headers now include HSTS for production transport hardening.
- Cloud smoke, revision, and public-ready checks now retry transient HTTP failures during redeploy windows.
- Cloud smoke now verifies baseline API and web security headers.
- Cloud CI workflow now exposes manual `wait_for_revision` and `public_ready_gate` controls.
- Added a cloud rollback runbook for Render, Vercel, database restore drills, and owner incident closure.
- Production readiness now blocks non-HTTPS allowed origins and warns on non-HTTPS public web URLs.
- Cloud release evidence now records observed API and web security headers.
- Public production gate now writes non-sensitive evidence reports under `reports/cloud/`.
- API rate limiter now prunes stale in-memory buckets to reduce long-running service memory growth.
- Early API 403/429 middleware responses now include security headers and request IDs.
- Production Gate now lists the current cloud validation commands and HTTPS-only origin requirement.
- Added dry-run-by-default `db:backup-retention` for local PostgreSQL backup retention evidence and opt-in cleanup.
- Billing mock webhooks now support tenant-scoped idempotency keys and duplicate audit entries.
- Added `REQUIRE_OWNER_MFA` production readiness warning and owner login enforcement when enabled.
- Restore drill script now writes non-secret JSON evidence under `reports/restore/`.
- Database backup script now writes a non-secret JSON manifest under `reports/backup/`.
- Added S3/R2 lifecycle and CORS policy templates plus storage policy runbook.
- Readiness and provider mode telemetry now track `MALWARE_SCANNER_PROVIDER`.
- Added `cloud:revision` to compare deployed API revision with the expected git commit.
- Manual Cloud CI now runs deployed revision verification before generating release evidence.
- Added post-deploy runbook for revision, smoke and release evidence validation.
- Cloud release evidence now records expected/actual revision and match status.
- Public production gaps guide now calls out stale deploy detection for malware scanner readiness.
- Owner system health now includes live API request metrics, production readiness summary and storage backend metadata.
- Owner Console frontend now renders live health details from the API instead of generic placeholder health text.
- Added `cloud:evidence` to generate a local JSON release evidence report from cloud preflight, smoke, readiness and version checks.
- Added optional `REQUIRE_VERIFIED_DOCUMENT_DOWNLOADS` gate to block client portal downloads until storage verification and clean scan are complete.
- Release evidence now records readiness blocker/warning keys so production gaps are explicit without reading raw logs.
- Manual Cloud CI now runs release evidence generation and uploads the JSON as a GitHub Actions artifact.
- Readiness now exposes `public_production_ready`, which requires zero blockers and zero warnings.
- Production Gate UI now shows public production readiness separately from general deployment status.
- Production Gate API now includes dynamic readiness blockers/warnings in the public production requirements list.
- API status now exposes non-secret external provider modes for AI, WhatsApp, billing, email and storage.
- Cloud smoke verifies provider modes are present.
- Owner system health now includes external provider modes without exposing tokens or secrets.
- Cloud release evidence now stores non-secret external provider modes from `/api/v1/status`.
- Version, metrics and API status now expose deployment revision from cloud/git environment variables.
- Production Gate API/UI now surface deployment revision and non-secret external provider modes.
- Added P25 public production gaps guide with exact provider/storage variables and validation steps.

### Security

- Health checks expose operational metadata only, never tenant legal content, document bytes, tokens or provider secrets.
- Release evidence reports explicitly exclude passwords, tokens, secrets and tenant data, and `reports/` is ignored by git.
- Blocked unverified document downloads are audited without exposing document bytes or storage credentials.

## 2026-05-24 - Security Alerts

### Added

- `security_alerts` persistence with Alembic migration `20260524_0021`.
- Tenant security alert endpoints under `/api/v1/settings/security-alerts`.
- Owner security alert endpoints under `/api/v1/owner/security-alerts`.
- Automatic alerts for owner login, owner MFA/recovery events, tenant MFA/password events, security policy changes and invitations.
- Settings and Owner Console panels to review and acknowledge alerts.

### Security

- Alerts never store passwords, MFA secrets, tokens or recovery codes.
- Acknowledgement is tenant/owner scoped and records responsible user plus timestamp.

## 2026-05-24 - Owner MFA Recovery Codes

### Added

- `owner_mfa_recovery_codes` persistence with Alembic migration `20260524_0020`.
- One-time owner MFA recovery codes generated after MFA verification.
- Owner login accepts either TOTP or unused recovery code when MFA is active.
- `/api/v1/owner/auth/mfa/recovery-codes` for audited recovery code regeneration.
- Owner Console displays generated recovery codes once and shows remaining count.

### Security

- Recovery codes are stored only as SHA-256 hashes.
- Used recovery codes are marked with `used_at` and cannot be reused.
- Regeneration requires owner password and MFA/recovery verification.

## 2026-05-24 - Owner MFA Security

### Added

- Owner MFA TOTP persistence with Alembic migration `20260524_0019`.
- `/api/v1/owner/auth/mfa/status|enroll|verify|disable` endpoints.
- Owner login accepts `mfa_code` and enforces it when MFA is active.
- Owner Console security panel for MFA enrollment, verification and disable flow.
- Backend and frontend tests for owner MFA enforcement and UI flow.

### Security

- Owner MFA secrets are encrypted at rest and never logged.
- MFA verify/disable rotates owner sessions through `refresh_token_version`.
- Owner MFA actions generate `owner_audit_logs`.

## 2026-05-24 - Tenant MFA Security Policy

### Added

- `tenant_security_policies` persistence with Alembic migration `20260524_0018`.
- `/api/v1/settings/security-policy` read/update endpoints with tenant RBAC.
- Login enforcement for roles covered by tenant MFA policy.
- Settings policy panel for role-based MFA enforcement.
- Backend and frontend tests for policy update, self-lockout guard and UI save flow.

### Security

- Policy changes generate `tenant_security_policy` audit logs.
- A user cannot enforce MFA for their own role unless their account already has MFA enabled.
- Policy responses do not expose secrets, MFA codes, passwords or token material.

## 2026-05-24 - Transactional Email Provider Boundary

### Added

- Configurable transactional email provider boundary with `EMAIL_PROVIDER=prepared|http_json`.
- `email_delivery_logs` persistence with Alembic migration `20260524_0017`.
- `/api/v1/settings/email/deliveries` for tenant-scoped delivery telemetry.
- `EMAIL_API_URL`, `EMAIL_API_KEY`, `EMAIL_FROM`, and `LEXFLOW_WEB_URL` settings.
- Password reset and user invitation delivery now use the shared email provider boundary.
- Settings now shows recent redacted email deliveries.
- `/login/reset/confirm` and `/login/invite` auto-fill tokens from `?token=`.
- Production readiness warning for incomplete HTTP JSON email provider configuration.

### Security

- Email provider secrets remain server-side environment variables.
- Email links deliver plain tokens only to the recipient while backend persistence remains hash-only.
- Delivery telemetry redacts recipient email and never stores message body, token or URL.

## 2026-05-24 - Tenant User Invitations

### Added

- `user_invitations` persistence with Alembic migration `20260524_0016`.
- `/api/v1/users/invitations` create/list endpoints with tenant RBAC.
- `/api/v1/users/invitations/{invitation_id}/resend|cancel` with token rotation and cancellation.
- `/api/v1/auth/invitations/accept` for one-time invite acceptance and first password definition.
- Settings user invitation panel with resend/cancel actions and `/login/invite` acceptance page.
- Backend and frontend tests for invitation creation, permission blocking, token acceptance and session storage.

### Security

- Invitation tokens are stored only as SHA-256 hashes and are never returned in list responses.
- Resending invalidates previous invitation tokens.
- Invitation audit logs avoid passwords, hashes and plain token values.

## 2026-05-24 - Owner Tenant Onboarding

### Added

- Owner tenant creation can provision initial tenant admin, seats, modules, feature flags, plan limits and mock subscription.
- `/api/v1/owner/tenants/{tenant_id}/onboarding` endpoint with readiness steps and secure handoff guidance.
- Owner Console tenant creation form now includes admin email/name/password, seats and modules.
- Tenant onboarding creates tenant audit logs without recording temporary passwords.
- Backend and frontend tests for owner tenant onboarding.

### Security

- Initial admin passwords are hashed and never returned in API responses or audit metadata.
- Owner handoff explicitly requires external secure password delivery and first-login MFA/password rotation.

## 2026-05-24 - Tenant MFA TOTP

### Added

- Tenant user MFA TOTP service with standard `otpauth://` enrollment.
- `users.mfa_secret_encrypted` and `users.mfa_confirmed_at` persistence with Alembic migration `20260524_0015`.
- `/api/v1/auth/mfa/status`, `/api/v1/auth/mfa/enroll`, `/api/v1/auth/mfa/verify` and `/api/v1/auth/mfa/disable`.
- Login support for optional `mfa_code` and enforcement when MFA is enabled.
- Settings MFA controls for enrollment, confirmation and disable flows.
- Backend and frontend tests for MFA enrollment, login enforcement and session rotation.

### Security

- MFA secrets are encrypted at rest and never logged.
- MFA enable/disable actions rotate sessions and create audit logs.

## 2026-05-24 - Password Reset Workflow

### Added

- `password_reset_tokens` persistence with Alembic migration `20260524_0014`.
- `/api/v1/auth/password-reset/request` with generic account-safe response and hashed one-time tokens.
- `/api/v1/auth/password-reset/confirm` with token expiration, single-use enforcement and session revocation.
- Login password recovery pages for requesting and confirming reset tokens.
- Backend and frontend tests for reset request, token confirmation, reuse blocking and old-session revocation.

### Security

- Reset tokens are stored only as SHA-256 hashes and are never returned outside local/test environments.
- Password reset audit events avoid logging passwords, hashes or token values.

## 2026-05-24 - Production Auth Hardening

### Added

- Tenant user `refresh_token_version` persistence with Alembic migration `20260524_0013`.
- `/api/v1/auth/change-password` endpoint with current-password verification, token rotation and old-token revocation.
- Settings account security panel for password changes from the web app.
- Backend and frontend tests for password change, token revocation and rotated session storage.

### Security

- Password changes create audit logs without exposing password, hash or token values.
- Logout and password changes now sync tenant session revocation to persisted users.

## 2026-05-24 - Owner Console Foundation

### Added

- Owner JWT authentication endpoints for login, refresh, logout and me.
- Initial owner bootstrap script using `INITIAL_OWNER_*` environment variables.
- `/owner/login` page with owner token storage isolated from tenant sessions.
- Owner Console logout action that calls `/owner/auth/logout` and clears owner-only local tokens.
- Owner Console web API bridge that loads dashboard, tenants, usage, features, plans, tickets, system health, demos, interventions and audit logs from `/api/v1/owner/*` when an owner JWT exists.
- Owner Console plan management with audited create/update endpoints for SaaS plan catalog.
- Owner Console tenant limit management with audited read/update endpoints and tenant detail controls.
- Owner Console temporary intervention manual close action with owner audit trail.
- Owner Console system incidents can now be created and resolved from the system health UI with devops-only audited API writes.
- Owner Console commercial demos can now be reset with audited owner action.
- Owner Console creation flows for tenants, support tickets, commercial demo tenants and temporary interventions through audited backend endpoints.
- Owner Console support ticket resolution through audited backend endpoint.
- Owner Console tenant lifecycle actions for suspend, reactivate and change plan through audited backend endpoints.
- Owner Console feature flag save action through audited backend endpoint.
- Owner-only backend models for owner users, roles, audit logs, health scores, support tickets, feature flags, limits, usage, interventions, demos, system health and incidents.
- `/api/v1/owner/*` endpoints for dashboard, tenants, lifecycle, plans, billing, support, health, demos, interventions and audit logs.
- Owner RBAC boundary with owner roles separated from tenant users.
- Owner Console frontend under `/owner` with dashboard, tenant management, usage, billing, feature flags, plans, support, system health, demos, interventions and audit.
- Owner documentation for security, tenant management, support workflow, feature flags and health score.
- Backend and frontend tests for owner flows.

### Security

- Owner views show SaaS metadata and redact sensitive tenant content unless a temporary intervention exists.
- Tenant JWT users are blocked from owner endpoints.
- Critical owner actions create `owner_audit_logs`.
- Owner header fallback is limited to local/test environments; staging and production require owner JWT.
- Owner web surfaces keep demo fallback when the Owner API is unavailable and block mutating actions until an owner JWT exists.

## 2026-05-24 - Operational Core: Clients, Cases And Advanced Expediente 360

### Added

- Global operational search across dashboard, clients, cases and Expediente 360 surfaces.
- Cloud-ready search bridge that calls `/api/v1/dashboard/search` with JWT when a user session exists.
- Cloud-ready client and case lists that call `/api/v1/clients/search` and `/api/v1/cases/search` with JWT.
- Cloud-ready client detail that calls `/api/v1/clients/{client_id}/profile` with JWT.
- Cloud-ready case resource panels that call `/api/v1/cases/{case_id}/documents|hearings|communications|judicial|automation|intelligence` with JWT.
- Client module routes for list, create wizard, profile and edit views.
- Case module routes for list, create, edit, documents, hearings, communications, SINOE judicial updates, automation and intelligence.
- Advanced client and case UI components for metrics, risk, timelines, tags, documents, communications and resource panels.
- Backend operational endpoints for global search, client profile/timeline/documents/communications/metrics/risk and case documents/hearings/judicial/automation/intelligence.
- Tests for operational search, client/case module surfaces, tenant isolation and SINOE consumption.

### Changed

- App shell now exposes `SearchGlobalBar` as a persistent Legal OS search layer.
- Global search, operational lists, client detail and case resource panels keep demo fallback when the API is unavailable.
- Judicial update views consume the existing SINOE module instead of duplicating judicial automation logic.

## 2026-05-24 - SINOE Integration Foundation

### Added

- Settings route for SINOE integration with encrypted credential storage.
- SINOE-specific backend endpoints for credentials, connection test, case source linking, source checks and update history.
- `SinoeAutomationService`, `SinoeAdapter` interface and `SinoeAdapterMock`.
- SINOE CAPTCHA human-in-the-loop checkpoints, notifications, evidence and audit events.
- Expediente 360 SINOE source panel, update history, source form and CAPTCHA modal.
- SINOE backend and frontend tests plus integration/security/product/compliance docs.

### Security

- SINOE password is never returned by API responses and is not included in audit metadata.
- `client_user` is blocked from SINOE integration settings and checks.
- CAPTCHA bypass, anti-bot evasion and automated CAPTCHA solving remain forbidden.

## 2026-05-24 - Cloud Login

### Added

- Real web login flow connected to `NEXT_PUBLIC_API_URL`.
- Tenant slug field for multi-studio authentication.
- Client session storage for access token, refresh token, user, tenant id, and tenant slug.
- Login tests for successful cloud auth and invalid credentials.

### Changed

- `/login` is no longer a placeholder and now redirects authenticated users to `/dashboard`.

## 2026-05-22 - P24 Cloud Deploy Pack

### Added

- Render Blueprint for API, PostgreSQL, Redis, and persistent disk staging storage.
- Vercel config for the Next.js web app.
- GitHub Actions Cloud CI workflow.
- Cloud preflight script and `npm run cloud:preflight`.
- Production web Dockerfile and API Dockerfile migration startup.
- PostgreSQL URL normalization for cloud provider connection strings.
- P24 cloud deployment documentation.
- P24 tests for Render, Vercel, CI and cloud PostgreSQL contracts.
- Cloud go-live checklist and `READY_FOR_P25`.

### Changed

- Status/version/metrics now report `P24` and `CLOUD-DEPLOY-PACK`.

## 2026-05-22 - P21-P23 Ops Import, Pilot Center and Production Gate

### Added

- Import UI route `/settings/import` with CSV templates and recommended import flow.
- Pilot Ops Center route `/settings/pilot` and endpoint `/api/v1/ops/pilot/readiness`.
- Production Gate route `/settings/production-gate` and endpoint `/api/v1/ops/production-gate`.
- Production gate script `scripts/production-gate.ps1`.
- `npm run production:gate` and `npm run production:gate:fast`.
- P21, P22 and P23 tests and documentation.

### Changed

- Status/version/metrics now report `P23` and `OPS-IMPORT-PRODUCTION-GATE`.

## 2026-05-22 - P20 Tenant Bootstrap + CSV Import

### Added

- Operational bootstrap endpoint for the current tenant.
- CSV import endpoints for clients, cases, and document manifests.
- Dry-run previews for imports.
- Tenant-scoped storage keys for imported document manifests.
- Import audit events and P20 tests/documentation.

### Changed

- Status/version/metrics now report `P20` and `TENANT-BOOTSTRAP-IMPORT`.

## 2026-05-22 - P19 Document Trust Lifecycle

### Added

- Document lifecycle metadata for file size, SHA256 checksum, storage verification timestamp, malware scan status, and scan result.
- Internal endpoints for document storage status, verify-storage, mock scan, and reject.
- Audit events for document storage verification, malware scan completion, and rejection.
- UI demo metadata for real document trust states in Portal Cliente and Expediente 360.
- P19 migration, tests, and documentation.

### Changed

- Status/version/metrics now report `P19` and `DOCUMENT-TRUST-LIFECYCLE`.
- Client-visible infected/rejected documents are hidden from portal download flows.

## 2026-05-22 - P18 Storage Bytes Foundation

### Added

- Functional signed `PUT` upload endpoint for local storage bytes.
- Functional signed `GET` download endpoint for local storage bytes.
- HMAC token verification, expiry checks, content-type checks, max-size checks, SHA256 checksums, and local path containment.
- Audit events for `storage_object_uploaded` and `storage_object_downloaded`.
- P18 storage bytes tests and documentation.

### Changed

- Storage status now reports backend, mode, and local root when using local storage.

## 2026-05-22 - P17 Document Storage Foundation

### Added

- S3-compatible StorageService with tenant/case/document scoped storage keys.
- Signed upload contract for client portal document uploads.
- Signed download link contract for client portal visible documents.
- `/api/v1/storage/status` endpoint.
- `/api/v1/client-portal/documents/{document_id}/download` endpoint.
- P17 storage documentation and tests.

### Changed

- Client portal document upload responses now include an upload contract.
- Client portal document serialization now marks download availability.

## 2026-05-22 - P16 Production Foundation

### Added

- Production readiness guardrails for environment, PostgreSQL, JWT secret, CORS, S3 secret, demo seed, rate limit, OpenAI, WhatsApp, and billing.
- `/readiness` and `/api/v1/readiness` endpoints.
- Startup readiness blocker when `REQUIRE_PRODUCTION_READY=true`.
- `APP_ENV`, `RELEASE_PHASE`, `RELEASE_NAME`, `REQUIRE_PRODUCTION_READY`, and `SEED_DEMO_ON_STARTUP` settings.
- `.env.production.example` and `infra/docker/docker-compose.production.yml`.
- P16 production readiness tests and cloud documentation.

### Changed

- Demo seed no longer runs automatically when `APP_ENV=production`.
- Status/version/metrics now report `P16` and `PRODUCTION-FOUNDATION`.

## 2026-05-22 - P15 LEXFLOW OS Final

### Added

- Commercial pilot package with demo script, onboarding checklist, pilot scope agreement, success metrics, and production-pending guardrails.
- LexflowOSService with Legal Memory, RAG Legal, global search, Copiloto Juridico, specialized AI agents, Legal Graph, future Marketplace, Demo Mode, and release status.
- P15 API endpoints under `/api/v1/lexflow-os`.
- RAG response policy: cite sources or state that no evidence was found.
- Audit logging for RAG, global search, and Copiloto usage.
- `/lexflow-os` and `/demo` frontend routes with premium OS final surface and E2E demo sequence.
- Commercial landing links to LEXFLOW OS and Demo Mode.
- P15 backend and frontend tests.
- Final release, pilot readiness, production pending, release-ready/not-ready, architecture, security, product, and validation docs.

### Changed

- `/api/v1/status`, `/version`, and `/metrics` now report phase `P15` and release `FINAL-PILOT`.
- Main navigation now includes LEXFLOW OS and Demo.
- `README.md` now documents P15 commands, endpoints, routes, and final release status.

## 2026-05-22 - P14 Hardening + Release Candidate RC1

### Added

- Security headers middleware for nosniff, frame denial, referrer policy, permissions policy, and no-store cache control.
- Configurable CORS origins and unsafe-method Origin guard.
- Configurable in-memory rate limit middleware for local/API hardening validation.
- `/metrics` endpoint with basic request/error/latency counters for RC1 observability.
- Upload hardening for client portal documents: safe filename normalization, content type allowlist, blocked executable/script extensions, and filename length limit.
- P14 validation tests for security headers, metrics, Origin guard, and upload security.
- P14 master test matrix, security audit, threat model, performance, backup policy, observability, release candidate, risk, tech debt, production, pilot, and readiness documents.

### Changed

- `/api/v1/status` and `/version` now report phase `P14` and release `RC1`.
- `.env.example` now documents hardening controls for origins, rate limit, and uploads.
- `README.md` now documents RC1 hardening and P14 validation.

## 2026-05-22 - P13 Automation Studio

### Added

- Automation data model: `automation_workflows`, `automation_conditions`, `automation_actions`, `automation_runs`, and `automation_run_steps`.
- AutomationService with trigger catalog, workflow CRUD, activation, trigger dispatch, condition evaluation, action execution, run steps, feature gate enforcement, and audit logging.
- Trigger catalog for case, hearing, document, judicial, CAPTCHA, client message, task, AI, and legal news events.
- Action catalog for tasks, notifications, WhatsApp mock, email prepared, case events, document requests, status changes, assignments, alerts, AI summary mock, and legal news links.
- Automation endpoints for catalog, workflows, activation, run, trigger dispatch, and run history.
- RBAC permissions `automation:read`, `automation:write`, and `automation:run`.
- Billing feature gate `automation_studio`.
- `/automation` frontend builder with trigger, conditions, actions, test, activate, audit, and result surfaces.
- Backend and frontend tests for P13.
- P13 docs and READY_FOR_P14.

### Changed

- `/api/v1/status` and `/version` now report phase `P13`.
- Main navigation now includes Automation.

## 2026-05-22 - P12 Billing SaaS + planes

### Added

- Billing SaaS data model: `billing_plans`, `plan_features`, `tenant_subscriptions`, `tenant_usage`, `billing_events`, and `invoices`.
- START, PRO, AI, and ENTERPRISE plan catalog with feature gates and limits.
- BillingService with catalog seeding, current subscription, subscribe mock, change plan, usage, features, invoices, webhook mock, and audit logging.
- Billing endpoints for plans, current subscription, subscribe mock, change plan, usage, features, and webhook mock.
- RBAC permissions `billing:read` and `billing:write`.
- Demo seed data for plans, trial subscription, usage, and billing event.
- Frontend routes `/pricing`, `/onboarding`, `/settings/billing`, `/settings/usage`, and `/settings/features`.
- Components PricingCards, PlanFeatureTable, SubscriptionStatusCard, UsageMeter, UpgradePrompt, and OnboardingWizard.
- Backend and frontend tests for P12.
- P12 docs and READY_FOR_P13.

### Changed

- `/api/v1/status` and `/version` now report phase `P12`.
- `README.md` now documents P12 billing endpoints, routes, and validation command.

## 2026-05-22 - P11 PWA y experiencia movil

### Added

- MobileClientService and MobileLawyerService for role-specific mobile payloads.
- Mobile endpoints for client home, cases, documents, messages, notifications, and lawyer dashboard, cases, tasks, hearings, and notifications.
- Installable PWA metadata, service worker, offline fallback, and install prompt registration.
- `/m/client` and `/m/lawyer` mobile route families with bottom tabs and responsive PWA surfaces.
- Frontend mobile demo data and tests for client/lawyer routes, manifest metadata, service worker, and offline fallback.
- Backend tests for mobile endpoint permissions, tenant isolation, client scope, lawyer scope, and role separation.
- P11 product, architecture, security, validation docs, and READY_FOR_P12.

### Changed

- `/api/v1/status` and `/version` now report phase `P11`.
- `README.md` now documents P11 mobile/PWA endpoints and routes.

## 2026-05-22 - P10 Legal Command Center

### Added

- DashboardService, KPIService, RiskService, ProductivityService, CommandCenterService, LegalTrendAnalyticsService, JudicialMonitoringAnalyticsService, AIAnalyticsService, and CommunicationAnalyticsService.
- Dashboard endpoints for overview, KPIs, risks, productivity, judicial monitoring, communications, AI, legal intelligence, trends, and snapshot.
- Dashboard RBAC permission `dashboard:read`.
- `/dashboard` executive overview and `/dashboard/command-center` decision center.
- Frontend components for KPI grid, risk panel, cases overview, productivity chart, judicial monitoring, AI usage, communication, legal intelligence, and decision queue.
- Backend tests for KPIs, dashboard endpoints, permissions, tenant isolation, and snapshot.
- Frontend tests for command center dashboard and command mode.
- P10 docs and READY_FOR_P11.

### Changed

- `/api/v1/status` and `/version` now report phase `P10`.

## 2026-05-22 - P9 Centro de Inteligencia Juridica

### Added

- Legal intelligence schema extensions for source adapters, news metadata, AI summaries, favorites, case links, alerts, and tags.
- LegalNewsSourceService, LegalNewsService, LegalAlertService, LegalTagService, LegalTrendService, and LegalNewsAIService.
- Mock adapters for LP Derecho, Juris.pe, El Peruano, SPIJ, Poder Judicial, MPFN, and SINOE.
- Endpoints for source list/create/sync, news list/detail/summarize/favorite/link-case, alerts, tags, and trends.
- Intelligence RBAC permissions and audit events.
- `/legal-intelligence` frontend dashboard with news cards, filters, search, AI summary boxes, favorite/link buttons, alerts, sources, and trend chart.
- Expediente 360 `Inteligencia relacionada` panel.
- Backend tests for source sync, news, AI summary, favorites, case links, alerts, trends, audit, permissions, and tenant isolation.
- Frontend tests for legal intelligence dashboard and source adapters.
- P9 docs and READY_FOR_P10.

### Changed

- `/api/v1/status` and `/version` now report phase `P9`.

## 2026-05-22 - P8 IA Practica Legal

### Added

- Practical legal AI services for OCR, document summary, classification, extraction, case summary, search, jobs, and usage audit.
- Providers: MockOCRProvider, FutureCloudOCRProvider placeholder, MockLLMProvider, and OpenAILLMProvider placeholder.
- AI job result storage, reviewer, and review note migration.
- Endpoints for document OCR/summarize/classify/extract, case summary/search, job retrieval, approve, and reject.
- RBAC permissions for `ai:read`, `ai:write`, and `ai:review`.
- Mandatory AI disclaimer on every output: `Requiere revisión profesional.`
- Prompt files for summarize, classify, extraction, case summary, smart search, and draft assistant.
- Practical AI frontend route `/ai` with document pipeline, case intelligence, human review queue, and prompt inventory.
- Backend tests for OCR, summaries, classification, extraction, permissions, review, audit, and tenant isolation.
- Frontend tests for the practical AI panel and prompt contracts.
- P8 docs and READY_FOR_P9.

### Changed

- `/api/v1/status` and `/version` now report phase `P8`.

## 2026-05-22 - P7 Comunicacion + WhatsApp Business

### Added

- Multichannel communication tables: `communication_threads`, `communication_messages`, `message_templates`, and `notification_rules`.
- CommunicationService, NotificationService, WhatsAppService, MessageTemplateService, and CommunicationAuditService.
- Provider interface with WhatsAppMockProvider and WhatsAppBusinessProvider placeholder.
- Endpoints for case communications, template CRUD, notification send/test/list/mark-read.
- Required P7 templates: audiencia proxima, documento requerido, informe disponible, actualizacion expediente, and proximo paso.
- Demo notification rules for hearing, document, and report events.
- Client portal message bridge into internal communication threads.
- Communication center frontend route `/communication`.
- Frontend communication components, demo data, and tests.
- Backend tests for templates, WhatsApp mock, audit, notifications, portal bridge, lawyer view, and client blocking.
- P7 docs and READY_FOR_P8.

### Changed

- `/api/v1/status` and `/version` now report phase `P7`.
- Expediente 360 communications include channel metadata.

## 2026-05-22 - P6 Portal Cliente

### Added

- Client portal service with client-user role enforcement and `tenant_id + client_id` scoping.
- Portal endpoints for profile, cases, case detail, public timeline, visible documents, hearings, notifications, messages, document uploads, and reports.
- Visibility flags for `case_events` and `documents`.
- P6 migration for portal visibility columns.
- Client-safe seed data with a linked demo client user and portal notification.
- Portal frontend routes: `/portal/login`, `/portal`, `/portal/cases`, `/portal/cases/[id]`, `/portal/documents`, `/portal/notifications`, `/portal/messages`, and `/portal/profile`.
- Premium responsive portal components for client dashboard, case detail, documents, messages, notifications, profile, and login.
- Backend tests for client isolation, document visibility, public timeline, messages, uploads, notifications, reports, audit, and role blocking.
- Frontend tests for portal rendering and safe demo visibility.
- P6 docs and READY_FOR_P7.

### Changed

- `/api/v1/status` now reports phase `P6`.

## 2026-05-22 - P5 Actualizacion Judicial Automatizada

### Added

- Judicial automation services for source registration, update checks, CAPTCHA checkpoints, evidence, notifications, and approvals.
- Mock adapters for Poder Judicial, CEJ, SINOE, and MPFN with a strict no-CAPTCHA-evasion behavior.
- P5 database migration for `captcha_checkpoints` and `judicial_evidence`.
- Endpoints for case sources, source checks, source updates, CAPTCHA resolution, and judicial update approval/rejection.
- Frontend components: JudicialSourcesPanel, JudicialUpdateStatusCard, CaptchaCheckpointModal, JudicialUpdateTimelineItem, SourceConfigurationForm, and JudicialUpdatesList.
- Backend tests for judicial sources, updates, evidence, CAPTCHA flow, audit, and tenant isolation.
- Frontend tests for judicial source states and human-in-the-loop UI.
- P5 docs, validation notes, CAPTCHA policy, and READY_FOR_P6.

### Changed

- `/api/v1/status` now reports phase `P5`.
- Expediente 360 now includes the P5 judicial automation panels.

## 2026-05-22 - P4 Expediente 360 And QA

### Added

- Expediente 360 backend overview endpoint.
- Case event, task, document, and status mutation endpoints backed by SQLAlchemy models.
- Persistent audit records for Expediente 360 mutations.
- Backend tests for overview, tenant isolation, permissions, errors, audit, and real flow.
- Expediente 360 frontend route and requested `apps/web/src/app/cases/[id]/page.tsx` mirror.
- Components: CaseHeader, ClientSummaryCard, RiskBadge, StatusBadge, CaseTimeline, DocumentsPanel, HearingsPanel, TasksPanel, JudicialUpdatesPanel, CommunicationsPanel, AlertsPanel, AuditSummaryPanel, NextActionsPanel.
- Frontend unit tests for Expediente 360 panels.
- P4 docs, QA checklist, and READY_FOR_P5.

### Changed

- `/api/v1/status` now reports phase `P4`.

## 2026-05-22 - P3 Complete MVP Database And Judicial Sources

### Added

- SQLAlchemy database package with full MVP schema.
- Alembic configuration and initial P3 migration.
- Tables: tenants, users, roles, permissions, role_permissions, clients, cases, case_events, case_sources, judicial_updates, documents, hearings, tasks, notifications, audit_logs, whatsapp_messages, ai_jobs, legal_news_sources, legal_news.
- Tenant-scoped relationships and indexes for tenant, case, client, status, created_at, external case number, and last checked timestamps.
- Soft delete support where appropriate.
- Demo relational seed with tenant, admin, lawyer, assistant, client user, 3 cases, documents, hearings, tasks, sources, judicial updates, notifications, WhatsApp messages, AI jobs, and legal news.
- Judicial update helper with CAPTCHA policy: pause, notify, require human intervention, and audit.
- P3 database tests for schema, tenant isolation, case creation, events, sources, judicial updates, CAPTCHA flow, audit logs, soft delete, relationships, and demo seed.
- Database docs and READY_FOR_P4.

## 2026-05-22 - P2 Backend Core

### Added

- Backend core models for Tenant, User, Role, Client, Case, and AuditLog.
- JWT auth with access tokens, refresh tokens, logout revocation, bcrypt password hashing, expiration, and MFA-ready user fields.
- RBAC roles: super_admin, tenant_admin, partner, lawyer, assistant, client_user.
- Users CRUD, Roles list, Clients CRUD/search/tags, Cases CRUD/assign/change-status, and Audit list/filter endpoints.
- TenantService, AuthService, UserService, RoleService, ClientService, CaseService, and AuditService.
- Request ID, tenant resolver context, audit context, error handler, and timing middleware.
- Demo seed for tenant, admin, lawyer, client user, client, and case.
- P2 tests for auth, RBAC, tenant isolation, CRUD, permissions, and audit.
- P2 backend core documentation and READY_FOR_P3.

### Changed

- `/api/v1/status` now reports phase `P2`.

## 2026-05-22 - P1 Architecture Base

### Added

- Monorepo workspaces for web, mobile, admin, and shared packages.
- Shared packages: UI, design system, shared constants, and types.
- Premium web placeholders for login, dashboard, clients, cases, case detail, documents, hearings, portal, AI, legal intelligence, and settings.
- API status endpoints: `/health`, `/version`, `/api/v1/status`.
- Mobile/PWA scaffold with prepared screen placeholders.
- Admin scaffold for future platform operations.
- Domain module folders for legal core, expediente360, portal, communication, AI, intelligence, automation, billing, and analytics.
- AI folders for RAG, extraction, embeddings, and prompts.
- Infra skeleton for Docker, Nginx, monitoring, and cloud.
- P1 architecture, product, validation, and P2 readiness documents.

## 2026-05-22 - P0 Governance

### Added

- Project governance document set.
- Required folder structure for product, architecture, security, UX, cloud, testing, scripts, infrastructure, and tests.
- Risk register.
- Decision log.
- P0 checklist.
- P1 readiness document.

### Changed

- README now reflects P0 governance status and documents the project spine.

### Not Changed

- No new functional backend behavior.
- No new functional frontend behavior.
- No new database tables.
- No new Docker functionality.
