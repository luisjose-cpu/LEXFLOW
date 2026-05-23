# P5 CAPTCHA And Authorized Source Policy

## Absolute Rule

LEXFLOW must not evade CAPTCHA, bypass access controls, break anti-bot protections, or use aggressive scraping against judicial sources.

## Required Behavior

When a judicial source requires CAPTCHA:

1. Stop automated checking for that source.
2. Set the source status to `paused_captcha`.
3. Create a paused judicial update with `captcha_required=true`.
4. Create a tenant-scoped CAPTCHA checkpoint.
5. Create evidence for the event.
6. Notify the tenant.
7. Write an audit log.
8. Wait for human resolution before continuing.

## Approval Boundary

Judicial updates that require unresolved human intervention cannot be approved by automation. They must be resolved through the CAPTCHA checkpoint flow first.

## Future Production Controls

- Source-specific legal review.
- Rate limits and backoff.
- Credential vaulting.
- Signed evidence artifacts.
- Monitoring and alerting for paused sources.
- Manual override permissions.
