# P6 Client Portal Architecture

## Boundary

P6 adds a client-facing application boundary on top of the same tenant database. It does not reuse internal case endpoints because those endpoints can expose lawyer-only context.

## Service

`ClientPortalService` owns:

- Client-user role enforcement.
- Client profile resolution.
- Case access by `tenant_id + client_id`.
- Safe serializers for portal responses.
- Portal message and upload audit records.

## Data Visibility

- `case_events.is_client_visible` controls public timeline events.
- `documents.is_client_visible` controls document visibility.
- `documents.uploaded_by_client` identifies client-submitted files.
- Judicial updates are visible only after approval and only when they are not CAPTCHA-paused records.

## Future Membership Model

P6 links demo access through client contact email. Production should add a `client_portal_memberships` table with `tenant_id`, `client_id`, `user_id`, role, status, invitation state, and audit metadata.
