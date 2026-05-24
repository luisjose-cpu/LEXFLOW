# P12 Billing Security

## Permissions

- `billing:read`: view plan, subscription, usage, and feature gates.
- `billing:write`: subscribe mock, change plan, and process mock webhook.

Tenant admins and partners can read/write billing. Lawyers can read billing. Client users cannot access billing endpoints.

## Audit

Critical billing actions write `audit_logs`:

- `billing.subscribe_mock`
- `billing.change_plan`
- `billing.webhook_mock`

## Secrets

P12 does not store payment credentials and does not integrate a real provider. Future provider secrets must stay in environment variables or secret managers, never source code.

## Webhook Policy

The current webhook endpoint is mock-only. Production webhooks must verify signatures, enforce idempotency, redact payloads in logs, and reject cross-tenant mutations.

The mock webhook accepts an optional `idempotency_key` and suppresses duplicate events per tenant/event type while writing a duplicate audit entry. Real provider integrations must keep this behavior and add provider signature verification before processing.
