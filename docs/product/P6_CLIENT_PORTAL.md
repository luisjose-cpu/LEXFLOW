# P6 Portal Cliente

## Goal

Create a secure client portal for authorized cases, status, visible timeline, approved documents, hearings, messages, notifications, reports, and client document submissions.

## Product Rule

Client users never see other clients, internal notes, legal strategy, private documents, or judicial updates that have not been approved for visibility.

## Backend Endpoints

- `GET /api/v1/client-portal/me`
- `GET /api/v1/client-portal/cases`
- `GET /api/v1/client-portal/cases/{case_id}`
- `GET /api/v1/client-portal/cases/{case_id}/timeline`
- `GET /api/v1/client-portal/cases/{case_id}/documents`
- `GET /api/v1/client-portal/cases/{case_id}/hearings`
- `GET /api/v1/client-portal/notifications`
- `POST /api/v1/client-portal/cases/{case_id}/messages`
- `POST /api/v1/client-portal/cases/{case_id}/documents`
- `GET /api/v1/client-portal/reports`

## Frontend Routes

- `/portal/login`
- `/portal`
- `/portal/cases`
- `/portal/cases/[id]`
- `/portal/documents`
- `/portal/notifications`
- `/portal/messages`
- `/portal/profile`

## Visibility Model

- Client access is resolved from authenticated `client_user` plus the linked client contact email.
- Cases are filtered by `tenant_id` and `client_id`.
- Timeline includes only `case_events.is_client_visible=true` and approved judicial updates.
- Documents include only `documents.is_client_visible=true` and never `status=private`.
- Messages and uploads are scoped to the client case and audited.
