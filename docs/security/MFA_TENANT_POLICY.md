# Tenant MFA Policy

## Estado

LEXFLOW permite configurar una politica MFA por tenant desde Settings.

Endpoints:

- `GET /api/v1/settings/security-policy`
- `PATCH /api/v1/settings/security-policy`

Campos:

- `enforce_mfa`
- `mfa_required_roles`
- `grace_period_hours`
- `allow_client_user_mfa_bypass`

## Seguridad

- Solo roles con `users:read` pueden ver la politica.
- Solo roles con `users:write` pueden modificarla.
- La politica siempre se resuelve dentro del tenant autenticado.
- Todo cambio genera `audit_log` con `entity_type=tenant_security_policy`.
- No se almacenan secretos ni codigos MFA en la politica.
- El login bloquea roles cubiertos cuando `enforce_mfa=true` y la cuenta aun no tiene MFA activo.
- Para evitar bloqueo administrativo, un usuario no puede activar MFA obligatorio para su propio rol si todavia no tiene MFA activo.

## Uso recomendado

1. Activar MFA en al menos una cuenta `tenant_admin`.
2. Habilitar politica primero para `partner` y `lawyer`.
3. Confirmar adopcion.
4. Activar `tenant_admin`.
5. Mantener `client_user` con bypass salvo que el estudio tenga un flujo de soporte preparado.

## Pendiente productivo

- Pantalla de adopcion MFA por usuario.
- Grace-period real por usuario con fecha limite de enrolamiento.
- Alertas previas al bloqueo.
- Politica equivalente para Owner Console.
