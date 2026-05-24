# P24 - Cloud Deploy Pack

## Decision

Ruta recomendada para staging:

- API FastAPI: Render Docker service.
- PostgreSQL: Render managed PostgreSQL.
- Redis: Render Redis.
- Web Next.js: Vercel.
- Storage piloto: Render persistent disk usando `STORAGE_BACKEND=local`.
- Storage produccion publica: S3/R2 compatible usando `STORAGE_BACKEND=s3`.

## Entregado

- `render.yaml`.
- `vercel.json`.
- `.github/workflows/cloud-ci.yml`.
- API Dockerfile con Alembic antes de Uvicorn.
- Web Dockerfile productivo para alternativa container.
- `scripts/cloud-preflight.ps1`.
- `scripts/cloud-smoke.ps1`.
- `scripts/cloud-release-evidence.ps1`.
- `npm run cloud:preflight`.
- `npm run cloud:smoke`.
- `npm run cloud:evidence`.
- Normalizacion de `postgres://` y `postgresql://` a `postgresql+psycopg://`.
- Backend S3/R2 real para documentos via API proxy firmado.
- Readiness warning `storage_backend_public_ready` cuando produccion sigue usando `STORAGE_BACKEND=local`.
- Render cron `lexflow-security-alert-deliveries` para procesar entregas criticas cada 15 minutos.
- Scripts `db:backup` y `db:restore-drill` para backup PostgreSQL y restore drill aislado.

## Render

1. Crear Blueprint desde `render.yaml`.
2. Revisar `lexflow-api`.
3. Confirmar `lexflow-postgres`, `lexflow-redis` y cron `lexflow-security-alert-deliveries`.
4. Configurar manualmente:
   - `ALLOWED_ORIGINS`
   - `STORAGE_PUBLIC_BASE_URL`
   - dominios
5. Confirmar que `REQUIRE_PRODUCTION_READY=true`.
6. Confirmar que `SEED_DEMO_ON_STARTUP=false`.

## Vercel

1. Importar repo.
2. Framework: Next.js.
3. Build command: `npm --workspace apps/web run build`.
4. Output: `apps/web/.next`.
5. Variables:
   - `NEXT_PUBLIC_API_URL=https://api.tu-dominio`
   - `NEXT_PUBLIC_APP_ENV=production`

## Preflight local

```bash
npm run cloud:preflight
```

## Smoke post-deploy

```powershell
$env:LEXFLOW_API_URL="https://lexflow-api.onrender.com"
$env:LEXFLOW_WEB_URL="https://lexflow-web-nine.vercel.app"
npm run cloud:smoke
```

Con login tenant:

```powershell
$env:LEXFLOW_SMOKE_TENANT_SLUG="piloto"
$env:LEXFLOW_SMOKE_ADMIN_EMAIL="admin@estudio.com"
$env:LEXFLOW_SMOKE_ADMIN_PASSWORD="<password-seguro>"
npm run cloud:smoke
```

El smoke valida `/health`, `/version`, `/metrics`, `/api/v1/status`, `/readiness`, home web, login web y login tenant opcional sin imprimir secretos. Si hay login tenant, tambien valida `/api/v1/storage/status` autenticado. Si `APP_ENV=production`, falla cuando readiness reporta blockers.

## Evidencia release piloto

```powershell
$env:LEXFLOW_API_URL="https://lexflow-api.onrender.com"
$env:LEXFLOW_WEB_URL="https://lexflow-web-nine.vercel.app"
npm run cloud:evidence
```

El comando ejecuta `cloud:preflight`, luego `cloud:smoke`, consulta `/readiness` y `/version`, y genera un JSON local en `reports/cloud/lexflow-cloud-release-*.json`. El reporte incluye conteo y claves de blockers/warnings de readiness para seguimiento operativo. No incluye passwords, tokens, secretos ni datos de tenants; `reports/` queda fuera de git.

## Validacion ejecutada

- `npm run cloud:preflight`: OK.
- `npm run lint`: OK.
- `npm run test`: OK, 13 files / 32 tests.
- `npm run build`: OK, 44 rutas.
- `python -m pytest -q`: OK, 85 tests.

## CI

GitHub Actions ejecuta:

- lint
- web tests
- web build
- API tests
- production gate fast
- post-deploy release evidence manual con `workflow_dispatch` e inputs `api_url` / `web_url`
- artifact `lexflow-cloud-release-evidence` con el JSON generado por `cloud:evidence`

El workflow corre en `main` y `master`. Para habilitar login tenant en el smoke manual, configurar secrets:

- `LEXFLOW_SMOKE_TENANT_SLUG`
- `LEXFLOW_SMOKE_ADMIN_EMAIL`
- `LEXFLOW_SMOKE_ADMIN_PASSWORD`

## Pendiente antes de produccion publica

- Dominios reales y CORS final.
- Secrets reales en Render/Vercel.
- Cambiar de `STORAGE_BACKEND=local` a `STORAGE_BACKEND=s3` para produccion publica.
- Primer tenant/admin productivo.
- Ejecutar restore drill real y guardar evidencia RPO/RTO.
- Observabilidad externa y alertas.
- Pentest.
