# Owner Console

## Objetivo

Owner Console es el panel propietario de LEXFLOW. Sirve para administrar el SaaS completo: tenants, planes, billing, soporte, consumo, feature flags, demos, auditoria y salud del sistema.

No es una pantalla para estudios juridicos clientes. Vive separado del tenant operativo y no debe abrir informacion sensible de expedientes, documentos, comunicaciones o estrategia legal.

## Superficies

- `/owner`: dashboard propietario.
- `/owner/login`: login propietario con JWT owner separado de la sesion tenant.
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

- `POST /owner/auth/login`
- `POST /owner/auth/refresh`
- `POST /owner/auth/logout`
- `GET /owner/auth/me`
- `GET /owner/dashboard`
- `GET|POST /owner/tenants`
- `GET /owner/tenants/{id}`
- `POST /owner/tenants/{id}/suspend`
- `POST /owner/tenants/{id}/reactivate`
- `POST /owner/tenants/{id}/change-plan`
- `GET|POST /owner/tenants/{id}/features`
- `GET /owner/tenants/{id}/usage`
- `GET /owner/tenants/{id}/health-score`
- `GET|POST /owner/plans`
- `PATCH /owner/plans/{code}`
- `GET /owner/billing`
- `GET|POST /owner/support/tickets`
- `POST /owner/support/tickets/{id}/resolve`
- `GET /owner/system/health`
- `GET /owner/system/incidents`
- `GET|POST /owner/demos`
- `GET|POST /owner/interventions`
- `GET /owner/audit-logs`

## Estado

READY para piloto controlado con autenticacion owner JWT. El frontend owner consume `/api/v1/owner/*` cuando existe `lexflow.owner_access_token`, permite crear tenants, planes, tickets, demos e intervenciones, ejecuta acciones auditadas para suspender/reactivar tenants, cambiar plan, actualizar estado de planes y guardar feature flags, y cae a demo seguro si la API no esta disponible. El fallback por headers queda limitado a `APP_ENV=local|test`.

## Bootstrap owner

Crear el primer propietario con:

```bash
cd apps/api
python scripts/create_initial_owner.py
```

Variables requeridas:

- `INITIAL_OWNER_EMAIL`
- `INITIAL_OWNER_NAME`
- `INITIAL_OWNER_PASSWORD`
- `INITIAL_OWNER_ROLE`

La password se guarda hasheada y nunca se imprime.
