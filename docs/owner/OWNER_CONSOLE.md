# Owner Console

## Objetivo

Owner Console es el panel propietario de LEXFLOW. Sirve para administrar el SaaS completo: tenants, planes, billing, soporte, consumo, feature flags, demos, auditoria y salud del sistema.

No es una pantalla para estudios juridicos clientes. Vive separado del tenant operativo y no debe abrir informacion sensible de expedientes, documentos, comunicaciones o estrategia legal.

## Superficies

- `/owner`: dashboard propietario.
- `/owner/tenants`: lista y gestion de tenants.
- `/owner/tenants/{id}`: detalle administrativo del tenant.
- `/owner/tenants/{id}/usage`: consumo y limites.
- `/owner/tenants/{id}/billing`: estado comercial y cobranza.
- `/owner/tenants/{id}/features`: feature flags por tenant.
- `/owner/plans`: planes y licencias.
- `/owner/support`: tickets y SLA.
- `/owner/system`: salud tecnica.
- `/owner/demos`: tenants demo comerciales.
- `/owner/interventions`: accesos temporales autorizados.
- `/owner/audit`: bitacora owner.

## Backend

Endpoints implementados bajo `/api/v1/owner/*`:

- `GET /owner/dashboard`
- `GET|POST /owner/tenants`
- `GET /owner/tenants/{id}`
- `POST /owner/tenants/{id}/suspend`
- `POST /owner/tenants/{id}/reactivate`
- `POST /owner/tenants/{id}/change-plan`
- `GET|POST /owner/tenants/{id}/features`
- `GET /owner/tenants/{id}/usage`
- `GET /owner/tenants/{id}/health-score`
- `GET /owner/plans`
- `GET /owner/billing`
- `GET|POST /owner/support/tickets`
- `POST /owner/support/tickets/{id}/resolve`
- `GET /owner/system/health`
- `GET /owner/system/incidents`
- `GET|POST /owner/demos`
- `GET|POST /owner/interventions`
- `GET /owner/audit-logs`

## Estado

READY para piloto controlado con autenticacion owner mock por headers internos. Antes de produccion publica, reemplazar por login owner real con JWT, MFA, session control y allowlist administrativa.
