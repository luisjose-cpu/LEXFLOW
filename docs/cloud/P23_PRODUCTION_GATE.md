# P23 - Production Gate

## Objetivo

Crear una compuerta repetible antes de produccion publica.

## Backend

- `GET /api/v1/ops/production-gate`

## Frontend

- `/settings/production-gate`

## Script

- `npm run production:gate`
- `npm run production:gate:fast`

## Gate completo

Ejecuta:

- `npm run lint`
- `npm run test`
- `npm run build`
- `npm run test:api`

## Fast gate

Valida que existan:

- `.env.production.example`
- `infra/docker/docker-compose.production.yml`
- Variables productivas obligatorias.

## Pendiente

- Integrar con GitHub Actions.
- Publicar artefactos de test.
- Bloquear deploy si readiness falla.
