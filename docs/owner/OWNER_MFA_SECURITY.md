# Owner MFA Security

## Estado

Owner Console soporta MFA TOTP real para usuarios propietarios.

Endpoints:

- `GET /api/v1/owner/auth/mfa/status`
- `POST /api/v1/owner/auth/mfa/enroll`
- `POST /api/v1/owner/auth/mfa/verify`
- `POST /api/v1/owner/auth/mfa/disable`
- `POST /api/v1/owner/auth/mfa/recovery-codes`

Login owner acepta `mfa_code` en `POST /api/v1/owner/auth/login`. Cuando el owner tiene MFA activo, el codigo TOTP es obligatorio.

Al confirmar MFA se generan 10 codigos de recuperacion de un solo uso. El backend guarda solo hashes SHA-256 y retorna los codigos planos una vez para que el owner los guarde en un gestor seguro. Un codigo usado queda marcado con `used_at` y no puede reutilizarse.

## Seguridad

- El secreto MFA se cifra con el boundary de cifrado existente.
- El secreto solo se retorna durante el enrolamiento.
- No se registra secreto, password ni codigo temporal en logs.
- Verificar o desactivar MFA incrementa `refresh_token_version`, revocando sesiones owner previas.
- Toda accion genera `owner_audit_logs` con `entity_type=owner_mfa`.
- Los endpoints MFA owner exigen bearer token owner; no aceptan fallback por headers.
- La regeneracion de recovery codes exige password owner y codigo MFA/recovery valido.

## Frontend

Owner Console incluye un panel `Seguridad owner` para:

- consultar estado MFA
- iniciar enrolamiento
- confirmar codigo
- desactivar MFA con password owner y codigo
- regenerar codigos de recuperacion

## Pendiente productivo

- Exigir MFA para todos los roles owner antes de abrir pilotos externos.
- Alertas por activacion/desactivacion MFA.
- IP allowlist opcional para owner_admin y owner_devops.
