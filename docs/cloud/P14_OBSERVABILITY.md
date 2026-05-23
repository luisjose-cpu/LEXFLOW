# P14 Observability

## Signals

- Health: `/health` and `/api/v1/health`.
- Version/release: `/version` and `/api/v1/status`.
- Metrics: `/metrics`.
- Request correlation: `X-Request-Id`.
- Timing: `X-Response-Time-Ms`.
- Audit: `audit_logs`.

## Logs

Production logs must include request id, route, method, status, latency, tenant id when available, and sanitized error category. Logs must not include secrets, tokens, document contents, or AI prompt payloads.

## Alerts

- API 5xx rate.
- Auth failure spike.
- Rate limit spike.
- CAPTCHA checkpoint backlog.
- Automation failures.
- Billing webhook failures.
- Backup failure.

## RC1 Status

Basic metrics and headers exist. Full metrics backend, tracing, dashboards, and alert routing remain production tasks.
