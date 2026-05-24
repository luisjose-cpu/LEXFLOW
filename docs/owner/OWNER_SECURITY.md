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

La base actual usa headers owner para pruebas y staging. Produccion requiere autenticacion dedicada, MFA, rotacion de sesiones, alertas de acceso, IP allowlist opcional y revision de auditoria.
