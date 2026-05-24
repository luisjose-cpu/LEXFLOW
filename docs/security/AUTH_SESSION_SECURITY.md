# Auth Session Security

## Estado implementado

- Login tenant con JWT access y refresh token.
- Refresh token versionado por usuario.
- Logout revoca tokens anteriores incrementando `refresh_token_version`.
- Cambio de password autenticado en `/api/v1/auth/change-password`.
- El cambio de password exige password actual, rota access/refresh token y revoca tokens previos.
- `users.refresh_token_version` queda persistido por migracion `20260524_0013`.
- La UI de Settings permite cambiar password y guarda la sesion rotada.

## Auditoria

El cambio de password registra `audit_logs` con:

- `entity_type=auth_password`
- `action=update`
- `actor_user_id`
- `tenant_id`
- `request_id`

No se registra password, hash, token ni secreto en logs.

## Pendiente productivo

- Recuperacion de password por email con token de un solo uso.
- MFA real para admin y owner.
- Alertas por cambio de password.
- Politica configurable de complejidad y expiracion.
- Pantalla de sesiones activas por usuario.
