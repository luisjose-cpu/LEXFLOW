# P24 - Cloud Deploy Pack

## Decision

Ruta recomendada para staging:

- API FastAPI: Render Docker service.
- PostgreSQL: Render managed PostgreSQL.
- Redis: Render Redis.
- Web Next.js: Vercel.
- Storage piloto: Render persistent disk usando `STORAGE_BACKEND=local`.
- Storage produccion publica futura: S3/R2 con backend dedicado.

## Entregado

- `render.yaml`.
- `vercel.json`.
- `.github/workflows/cloud-ci.yml`.
- API Dockerfile con Alembic antes de Uvicorn.
- Web Dockerfile productivo para alternativa container.
- `scripts/cloud-preflight.ps1`.
- `scripts/cloud-smoke.ps1`.
- `npm run cloud:preflight`.
- `npm run cloud:smoke`.
- Normalizacion de `postgres://` y `postgresql://` a `postgresql+psycopg://`.

## Render

1. Crear Blueprint desde `render.yaml`.
2. Revisar `lexflow-api`.
3. Confirmar `lexflow-postgres` y `lexflow-redis`.
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

El smoke valida `/health`, `/version`, `/api/v1/status`, home web, login web y login tenant opcional sin imprimir secretos.

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
- post-deploy smoke manual con `workflow_dispatch` e inputs `api_url` / `web_url`

El workflow corre en `main` y `master`. Para habilitar login tenant en el smoke manual, configurar secrets:

- `LEXFLOW_SMOKE_TENANT_SLUG`
- `LEXFLOW_SMOKE_ADMIN_EMAIL`
- `LEXFLOW_SMOKE_ADMIN_PASSWORD`

## Pendiente antes de produccion publica

- Backend S3/R2 real.
- Dominios reales y CORS final.
- Secrets reales en Render/Vercel.
- Primer tenant/admin productivo.
- Backups/restore probados.
- Observabilidad externa y alertas.
- Pentest.
