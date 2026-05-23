# P14 Threat Model

## Assets

- Tenant legal data.
- Client portal data.
- Documents and storage keys.
- Authentication tokens.
- Audit logs.
- Billing and automation configuration.
- AI job payloads and results.

## Primary Threats

- Cross-tenant data access.
- Broken RBAC.
- Token theft or replay.
- Malicious document upload.
- XSS in rendered legal content.
- SQL injection in search/filter endpoints.
- SSRF through future adapters.
- CAPTCHA/anti-bot bypass attempts.
- Unauthorized automation execution.
- Billing webhook spoofing in future provider integrations.

## Current Mitigations

- Tenant scoped queries.
- Role permission dependencies.
- JWT token type and refresh-version revocation.
- Upload allowlist and filename normalization.
- React escaped rendering.
- SQLAlchemy structured queries.
- Mock-only external adapters.
- Human-in-the-loop CAPTCHA policy.
- Automation feature gate and audit logs.
- Mock billing provider only.

## Residual Risk

RC1 is fit for controlled pilot with trusted tenants. Public production requires managed secrets, external scanning, signed provider webhooks, WAF, object malware scanning, and restore drill evidence.
