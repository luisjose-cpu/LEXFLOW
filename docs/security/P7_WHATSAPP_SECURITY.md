# P7 WhatsApp And Communication Security

## Rules

- No WhatsApp Business credentials are hardcoded.
- WhatsAppBusinessProvider is a placeholder only.
- WhatsAppMockProvider is the only active P7 provider.
- Every communication action is tenant scoped.
- Internal communication endpoints require internal communication permissions.
- Client users can create messages only through client portal endpoints.

## Production Requirements

Before real WhatsApp Business usage:

- Store credentials in a vault or managed secret service.
- Verify webhook signatures.
- Add rate limits and retry/backoff policy.
- Persist delivery callbacks.
- Add template approval state for official WhatsApp templates.
- Audit inbound and outbound payload metadata without storing unnecessary secrets.
