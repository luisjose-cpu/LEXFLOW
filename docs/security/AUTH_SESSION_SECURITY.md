# Auth Session Security

## Estado implementado

- Login tenant con JWT access y refresh token.
- Refresh token versionado por usuario.
- Logout revoca tokens anteriores incrementando `refresh_token_version`.
- Cambio de password autenticado en `/api/v1/auth/change-password`.
- El cambio de password exige password actual, rota access/refresh token y revoca tokens previos.
- Recuperacion de password con token de un solo uso en `/api/v1/auth/password-reset/request` y `/api/v1/auth/password-reset/confirm`.
- El token de recuperacion se guarda solo como hash SHA-256, expira segun `PASSWORD_RESET_TOKEN_MINUTES` y revoca sesiones anteriores al completar el cambio.
- `users.refresh_token_version` queda persistido por migracion `20260524_0013`.
- `password_reset_tokens` queda persistido por migracion `20260524_0014`.
- La UI de Settings permite cambiar password y guarda la sesion rotada.
- La UI de Login permite solicitar recuperacion y confirmar token sin exponer password ni secretos.

## Auditoria

El cambio de password registra `audit_logs` con:

- `entity_type=auth_password`
- `action=update`
- `actor_user_id`
- `tenant_id`
- `request_id`

No se registra password, hash, token ni secreto en logs.

La recuperacion de password registra `audit_logs` con:

- `entity_type=auth_password_reset`
- `action=request|confirm`
- `actor_user_id` cuando aplica
- `tenant_id`
- `request_id`

Las respuestas de solicitud son genericas para evitar enumeracion de cuentas.

## Pendiente productivo

- Proveedor real de email transaccional para entregar tokens de recuperacion.
- MFA real para admin y owner.
- Alertas por cambio de password.
- Politica configurable de complejidad y expiracion.
- Pantalla de sesiones activas por usuario.
