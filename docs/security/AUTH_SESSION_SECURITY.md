# Auth Session Security

## Estado implementado

- Login tenant con JWT access y refresh token.
- Refresh token versionado por usuario.
- Logout revoca tokens anteriores incrementando `refresh_token_version`.
- Cambio de password autenticado en `/api/v1/auth/change-password`.
- El cambio de password exige password actual, rota access/refresh token y revoca tokens previos.
- Recuperacion de password con token de un solo uso en `/api/v1/auth/password-reset/request` y `/api/v1/auth/password-reset/confirm`.
- El token de recuperacion se guarda solo como hash SHA-256, expira segun `PASSWORD_RESET_TOKEN_MINUTES` y revoca sesiones anteriores al completar el cambio.
- MFA TOTP en `/api/v1/auth/mfa/status|enroll|verify|disable`.
- El secreto MFA se guarda cifrado, se confirma con codigo temporal y se exige en login cuando `mfa_enabled=true`.
- Politica MFA por tenant en `/api/v1/settings/security-policy` para exigir MFA a roles sensibles.
- El login bloquea cuentas de roles cubiertos por politica si aun no tienen MFA activo.
- Invitaciones de usuarios en `/api/v1/users/invitations` y `/api/v1/auth/invitations/accept`.
- Las invitaciones permiten que cada usuario defina su propia password y almacenan solo hash del token.
- Reenvio de invitaciones rota token y cancelacion bloquea aceptacion pendiente.
- `users.refresh_token_version` queda persistido por migracion `20260524_0013`.
- `password_reset_tokens` queda persistido por migracion `20260524_0014`.
- Los campos `users.mfa_secret_encrypted` y `users.mfa_confirmed_at` quedan persistidos por migracion `20260524_0015`.
- `user_invitations` queda persistido por migracion `20260524_0016`.
- La UI de Settings permite cambiar password y guarda la sesion rotada.
- La UI de Settings permite activar y desactivar MFA TOTP con rotacion de sesion.
- La UI de Login permite solicitar recuperacion y confirmar token sin exponer password ni secretos.
- Los links de email para recuperacion e invitacion usan `LEXFLOW_WEB_URL` y autocompletan `?token=` en frontend.
- Las entregas de email registran telemetria redactada por tenant en `email_delivery_logs`.
- `tenant_security_policies` queda persistido por migracion `20260524_0018`.
- `REQUIRE_OWNER_MFA=true` exige MFA owner antes de permitir login propietario sin segundo factor.
- `CREDENTIAL_ENCRYPTION_KEY` dedicado queda validado por readiness para proteger secretos MFA y credenciales de integraciones sin depender del `JWT_SECRET`.
- `FAILED_LOGIN_LIMIT` y `FAILED_LOGIN_WINDOW_MINUTES` aplican bloqueo temporal en memoria por cuenta/tenant y por owner ante intentos fallidos repetidos.

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

MFA registra `audit_logs` con:

- `entity_type=auth_mfa`
- `action=update`
- motivos `mfa_enrollment_started`, `mfa_enabled` y `mfa_disabled`

No se registra el secreto MFA ni codigos temporales.

Invitaciones registra `audit_logs` con:

- `entity_type=user_invitation`
- `action=create|update`
- correo, rol y estado operativo

No se registra password, hash ni token plano.

Politica MFA tenant registra `audit_logs` con:

- `entity_type=tenant_security_policy`
- `action=update`
- roles cubiertos y flags operativos

No se registra secreto MFA, codigo temporal ni password.

## Pendiente productivo

- Proveedor real de email transaccional para entregar tokens de recuperacion.
- Proveedor real de email transaccional para entregar invitaciones.
- Cola/retry de email y eventos de entrega.
- Grace-period real por usuario para MFA obligatorio.
- Flujo de bootstrap seguro para activar `REQUIRE_OWNER_MFA=true` despues de enrolar al primer owner admin.
- Persistir/centralizar counters de intentos fallidos en Redis para multiples replicas.
- Alertas por cambio de password.
- Politica configurable de complejidad y expiracion.
- Pantalla de sesiones activas por usuario.
