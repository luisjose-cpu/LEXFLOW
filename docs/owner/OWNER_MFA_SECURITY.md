# Owner MFA Security

## Estado

Owner Console soporta MFA TOTP real para usuarios propietarios.

Endpoints:

- `GET /api/v1/owner/auth/mfa/status`
- `POST /api/v1/owner/auth/mfa/enroll`
- `POST /api/v1/owner/auth/mfa/verify`
- `POST /api/v1/owner/auth/mfa/disable`

Login owner acepta `mfa_code` en `POST /api/v1/owner/auth/login`. Cuando el owner tiene MFA activo, el codigo TOTP es obligatorio.

## Seguridad

- El secreto MFA se cifra con el boundary de cifrado existente.
- El secreto solo se retorna durante el enrolamiento.
- No se registra secreto, password ni codigo temporal en logs.
- Verificar o desactivar MFA incrementa `refresh_token_version`, revocando sesiones owner previas.
- Toda accion genera `owner_audit_logs` con `entity_type=owner_mfa`.
- Los endpoints MFA owner exigen bearer token owner; no aceptan fallback por headers.

## Frontend

Owner Console incluye un panel `Seguridad owner` para:

- consultar estado MFA
- iniciar enrolamiento
- confirmar codigo
- desactivar MFA con password owner y codigo

## Pendiente productivo

- Exigir MFA para todos los roles owner antes de abrir pilotos externos.
- Recovery codes para emergencia.
- Alertas por activacion/desactivacion MFA.
- IP allowlist opcional para owner_admin y owner_devops.
