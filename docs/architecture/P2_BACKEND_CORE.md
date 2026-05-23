# P2 Backend Core

## Goal

Create the core backend foundation for LEXFLOW:

- Multi-tenant domain model
- JWT authentication
- Refresh token flow
- RBAC
- Users
- Roles
- Clients
- Cases
- Audit log
- Middleware foundation

## Models

- `Tenant`
- `User`
- `Role`
- `Client`
- `LegalCase`
- `AuditLog`

Legacy P1 prototype models remain preserved where they existed.

## Services

- `TenantService`
- `AuthService`
- `UserService`
- `RoleService`
- `ClientService`
- `CaseService`
- `AuditService`

P2 uses in-memory services as a contract-first backend core. Durable persistence and migrations should be introduced in the next backend hardening phase.

## Endpoints

Base path: `/api/v1`

Auth:

- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`

RBAC:

- `GET /roles`

Users:

- `GET /users`
- `POST /users`
- `GET /users/{user_id}`
- `PATCH /users/{user_id}`
- `DELETE /users/{user_id}`

Clients:

- `GET /clients?search=&tag=`
- `POST /clients`
- `GET /clients/{client_id}`
- `PATCH /clients/{client_id}`
- `DELETE /clients/{client_id}`

Cases:

- `GET /cases?status=`
- `POST /cases`
- `GET /cases/{case_id}`
- `PATCH /cases/{case_id}`
- `POST /cases/{case_id}/assign`
- `POST /cases/{case_id}/change-status`
- `DELETE /cases/{case_id}`

Audit:

- `GET /audit?action=&entity_type=&actor_user_id=`

## Middleware

- Request ID
- Tenant resolver context
- Audit context injector
- Error handler
- Timing response header

## Seed

P2 seeds:

- Demo tenant
- Demo tenant admin
- Demo lawyer
- Demo client user
- Demo client
- Demo case

## P3 Architecture Priority

Move this contract into persistent database models, migrations, repository boundaries, and production-grade auth configuration.
