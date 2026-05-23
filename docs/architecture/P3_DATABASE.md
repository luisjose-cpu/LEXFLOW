# P3 Database

## Goal

Implement the complete MVP database prepared for:

- Expediente 360
- Authorized judicial updates
- Portal Cliente
- WhatsApp
- AI jobs
- Legal Intelligence Dashboard

## Tables

- `tenants`
- `users`
- `roles`
- `permissions`
- `role_permissions`
- `clients`
- `cases`
- `case_events`
- `case_sources`
- `judicial_updates`
- `documents`
- `hearings`
- `tasks`
- `notifications`
- `audit_logs`
- `whatsapp_messages`
- `ai_jobs`
- `legal_news_sources`
- `legal_news`

## Multi-Tenancy

All principal operational tables include `tenant_id`. `tenants` is the root table. `permissions` are global permission definitions; tenant-specific role assignment is expressed through `roles` and `role_permissions`.

## Soft Delete

Soft delete is implemented where records should remain legally traceable:

- `tenants`
- `roles`
- `users`
- `clients`
- `cases`
- `case_sources`
- `documents`
- `hearings`
- `tasks`
- `legal_news_sources`

Audit logs, events, notifications, judicial updates, WhatsApp messages, AI jobs, and legal news are append-style records and are not soft-deleted in P3.

## Indexes

Indexes are included for:

- `tenant_id`
- `case_id`
- `client_id`
- `status`
- `created_at`
- `external_case_number`
- `last_checked_at`

## Migrations

Alembic is configured in `apps/api/alembic.ini`.

Initial migration:

`apps/api/migrations/versions/20260522_0001_p3_initial_mvp_schema.py`

Run migrations from `apps/api`:

```bash
python -m alembic upgrade head
```

## Seed

`app.db.seed.seed_demo_database` creates:

- Demo tenant
- Admin
- Lawyer
- Assistant
- Client user
- 3 clients
- 3 cases
- Documents
- Hearings
- Tasks
- Case sources
- Simulated judicial updates
- CAPTCHA-required judicial update
- Notifications
- WhatsApp messages
- AI jobs
- Legal news source and news

## P4 Priority

P4 should connect API services to this persistent schema and retire or wrap the in-memory P2 services.
