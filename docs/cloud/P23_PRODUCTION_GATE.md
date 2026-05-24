# P23 - Production Gate

## Objetivo

Crear una compuerta repetible antes de produccion publica.

## Backend

- `GET /api/v1/ops/production-gate`

## Frontend

- `/settings/production-gate`
- Muestra `Public prod` para distinguir deploy piloto sin blockers de produccion publica sin warnings.
- `required_before_public_production` combina requisitos base con blockers/warnings vivos de readiness.

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

## Estado CI

- GitHub Actions ejecuta lint, tests, build, API tests y production gate fast.
- Workflow manual post-deploy genera artifact `lexflow-cloud-release-evidence`.
- Cloud smoke bloquea readiness con blockers; `public_production_ready=false` mantiene visibles los warnings pendientes.
