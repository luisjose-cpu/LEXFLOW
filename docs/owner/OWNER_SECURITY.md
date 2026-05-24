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

## Pendiente productivo

Owner Console usa JWT owner dedicado con refresh token versionado, logout revocando tokens y bootstrap por variables de entorno. El fallback por headers owner queda permitido solo en `APP_ENV=local` o `APP_ENV=test`.

El frontend owner expone logout dedicado, llama `/owner/auth/logout` cuando existe JWT y limpia `lexflow.owner_access_token`, `lexflow.owner_refresh_token` y `lexflow.owner_user`.

Pendientes antes de produccion publica:

- MFA enforcement real.
- IP allowlist opcional.
- alertas por login owner.
- rotacion periodica de owner passwords.
- revision mensual de `owner_audit_logs`.
