# SINOE Credential Security

## Rules

- Never store SINOE username or password in plaintext.
- Never return password from API responses.
- Never log credentials or include them in audit metadata.
- Only tenant admins and partners can configure or run SINOE integration actions.
- `client_user` is blocked from SINOE settings and source checks.
- Tenant isolation is enforced through the bearer token and optional `X-Tenant-Id` guard.

## Encryption

Credentials are stored in `integration_credentials`:

- `tenant_id`
- `provider = SINOE`
- `username_encrypted`
- `password_encrypted`
- `status`
- `last_checked_at`
- `created_by`

`CredentialCipher` uses Fernet encryption. The encryption key should be provided through:

```bash
CREDENTIAL_ENCRYPTION_KEY=...
```

If the variable is absent in local/demo mode, the service derives a Fernet-compatible key from `JWT_SECRET`. Production should use a dedicated credential encryption key and rotate it under a controlled migration plan.

## API Response Contract

Allowed response fields:

- `provider`
- `configured`
- `status`
- `last_checked_at`
- `username_hint`

Forbidden response fields:

- `password`
- `password_encrypted`
- `username_encrypted`
- raw SINOE credentials

## Audit

Audit events are written for:

- create credentials
- update credentials
- delete credentials
- test connection
- link SINOE case source
- check SINOE source
- create CAPTCHA checkpoint
- resolve CAPTCHA checkpoint

Audit metadata must stay credential-free.
