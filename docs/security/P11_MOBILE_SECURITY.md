# P11 Mobile Security

## Access Rules

- Client mobile endpoints only expose client portal-safe data.
- Client users cannot access lawyer mobile endpoints.
- Lawyer mobile endpoints require internal roles: `tenant_admin`, `partner`, `lawyer`, or `assistant`.
- Lawyer endpoints are tenant scoped and require server-side authorization.

## Visibility Rules

Clients must never see:

- Other clients' cases.
- Internal notes.
- Legal strategy.
- Private documents.
- Unapproved judicial updates.
- Internal AI work products not approved for sharing.

## PWA Rules

- No credentials are stored in the service worker.
- Offline fallback is informational only.
- Cached assets must not include confidential case payloads.
- Push notifications remain future-ready and must not expose sensitive content without explicit policy.

## Audit Rules

Mobile critical actions must continue to use existing audit paths. P11 read endpoints are scoped for mobile consumption; future write actions must add explicit audit events.
