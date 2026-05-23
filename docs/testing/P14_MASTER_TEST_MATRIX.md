# P14 Master Test Matrix

## Scope

RC1 validates the whole LEXFLOW chain:

`CLIENTE -> EXPEDIENTE -> DOCUMENTO -> COMUNICACION -> AUTOMATIZACION -> IA -> INTELIGENCIA -> DECISION`

## Automated Gates

Run:

```bash
npm run p14:check
```

This executes frontend lint, frontend tests, production build, and API tests.

## Matrix

| Area | Coverage | Evidence |
| --- | --- | --- |
| JWT | login, refresh, logout, revoked refresh version | API auth tests |
| RBAC | role permissions by endpoint family | API P2-P13 tests |
| Tenant isolation | users, clients, cases, portal, AI, billing, automation | API tests |
| Audit | critical auth, portal, judicial, AI, billing, automation events | API tests |
| CORS/CSRF | configured origins and unsafe Origin guard | P14 hardening tests |
| Rate limiting | configurable per-minute API guard | middleware + docs |
| Uploads | content-type allowlist, filename normalization, blocked extensions | P14 upload tests |
| SQL injection | ORM filters and structured query parameters | code review + API tests |
| XSS | React escaping, no raw HTML rendering in app surfaces | code review |
| SSRF | live adapters are mock-only; no arbitrary fetch execution | security docs |
| Backups/restore | PostgreSQL/S3 policy defined, restore drill required | backup policy |
| Health/metrics | `/health`, `/version`, `/metrics` | P14 tests |
| Performance | target budget documented for critical routes | performance doc |

## Runner Stability

P14 pins Vitest to single-worker file execution for RC validation stability on local/desktop environments. This avoids false RC failures from worker RPC timeouts while preserving the same assertions.
