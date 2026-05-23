# P2 Auth And RBAC

## Authentication

P2 implements:

- Bcrypt password hashing
- JWT access tokens
- JWT refresh tokens
- Token expiration
- Logout token revocation by refresh token version
- MFA-ready user field

## Roles

Supported roles:

- `super_admin`
- `tenant_admin`
- `partner`
- `lawyer`
- `assistant`
- `client_user`

## Permission Model

Permissions are mapped by role in `RoleService`.

Examples:

- `users:read`
- `users:write`
- `roles:read`
- `clients:read`
- `clients:write`
- `cases:read`
- `cases:write`
- `cases:assign`
- `cases:change_status`
- `audit:read`

## Tenant Isolation

Tenant access is resolved from the authenticated token. If `X-Tenant-Id` is present, it must match the authenticated user tenant unless the role is `super_admin`.

## Audit

Audited actions include:

- Login
- Logout
- Refresh
- User create/update/delete
- Client create/update/delete
- Case create/update/delete
- Case assignment
- Case status change

## P3 Security Work

- Move secrets to managed config.
- Add persistent token/session storage if needed.
- Add MFA implementation.
- Add rate limiting.
- Add account lockout policy.
- Add production CORS configuration.
- Add security headers at the edge.
