# Owner Security

## Principios

- Owner Console esta separado del tenant normal.
- Un usuario tenant nunca debe acceder a endpoints `/owner/*`.
- Owner puede administrar metadata SaaS, billing y soporte.
- Owner no puede ver datos sensibles de estudios sin autorizacion explicita, temporal y auditada.
- No se muestran passwords, tokens, secretos ni credenciales de tenants.

## Roles

- `owner_admin`: acceso total owner.
- `owner_support`: lectura owner, soporte e intervenciones limitadas.
- `owner_sales`: tenants y demos.
- `owner_finance`: planes y billing.
- `owner_devops`: salud tecnica e incidentes.
- `owner_readonly`: lectura.

## Intervenciones

Toda intervencion debe registrar:

- tenant afectado
- motivo
- scopes permitidos
- solicitante/aprobador
- expiracion
- cierre o expiracion automatica
- audit log

Owner Console permite cierre manual con `/api/v1/owner/interventions/{id}/close`. El cierre marca `status=closed`, llena `closed_at` y genera `tenant_intervention_closed`.

## Incidentes tecnicos

Solo `owner_admin` y `owner_devops` pueden crear o resolver incidentes con `/api/v1/owner/system/incidents`. Cada alta genera `system_incident_created`; cada resolucion genera `system_incident_resolved` con motivo, componente y timestamp.

## Pendiente productivo

Owner Console usa JWT owner dedicado con refresh token versionado, logout revocando tokens y bootstrap por variables de entorno. El fallback por headers owner queda permitido solo en `APP_ENV=local` o `APP_ENV=test`.

El frontend owner expone logout dedicado, llama `/owner/auth/logout` cuando existe JWT y limpia `lexflow.owner_access_token`, `lexflow.owner_refresh_token` y `lexflow.owner_user`.

Owner Console soporta MFA TOTP en `/owner/auth/mfa/status|enroll|verify|disable`. El login acepta `mfa_code` y lo exige cuando el propietario tiene MFA activo. Verificar o desactivar MFA revoca sesiones previas y registra `owner_audit_logs`.

Pendientes antes de produccion publica:

- MFA obligatorio para todos los roles owner antes de pilotos externos.
- IP allowlist opcional.
- alertas por login owner.
- rotacion periodica de owner passwords.
- revision mensual de `owner_audit_logs`.
