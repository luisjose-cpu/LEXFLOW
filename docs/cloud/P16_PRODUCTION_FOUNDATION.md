# P16 - Production Foundation

## Objetivo

Iniciar el paso de `pilot-ready` a `production-ready` con controles de entorno, secretos, seeds, readiness y compose productivo.

## Cambios de base

- `APP_ENV` separa local, pilot/staging y production.
- `SEED_DEMO_ON_STARTUP=false` es obligatorio en production.
- `REQUIRE_PRODUCTION_READY=true` bloquea el arranque si hay blockers.
- `/readiness` y `/api/v1/readiness` reportan estado productivo.
- `production_ready` significa que no hay blockers de arranque.
- `public_production_ready` exige cero blockers y cero warnings para salida comercial publica.
- `.env.production.example` define variables esperadas sin credenciales reales.
- `infra/docker/docker-compose.production.yml` define un perfil base para web, API, PostgreSQL, Redis y MinIO.

## Checks bloqueantes

- PostgreSQL obligatorio.
- JWT secret fuerte.
- CORS sin wildcard.
- CORS sin localhost.
- CORS solo HTTPS.
- S3 secret fuerte.
- Demo seed deshabilitado.

## Warnings

- Rate limit productivo recomendado.
- `LEXFLOW_WEB_URL` publico HTTPS.
- OpenAI key requerido antes de IA real.
- WhatsApp token requerido antes de WhatsApp real.
- Billing secret requerido antes de suscripcion real.

## Siguiente bloque

P17 recomendado:

1. Storage real de documentos con S3/MinIO client.
2. Migraciones y bootstrap de tenant production.
3. CI/CD con gates de lint, tests, build y readiness.
4. Observabilidad real con logs estructurados y alertas.
