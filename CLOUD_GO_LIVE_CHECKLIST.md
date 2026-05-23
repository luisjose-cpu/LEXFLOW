# CLOUD_GO_LIVE_CHECKLIST

## Objetivo

Dejar LEXFLOW desplegado en staging cloud con API, web, base de datos, Redis, migraciones, health checks y gate de produccion activo.

## Ruta recomendada

- API: Render Docker service usando `render.yaml`.
- Database: Render PostgreSQL administrado.
- Queue/cache: Render Redis.
- Web: Vercel usando `vercel.json`.
- Storage inicial: Render persistent disk con `STORAGE_BACKEND=local`.
- Storage productivo futuro: S3/R2 con backend dedicado y URLs firmadas.

## Antes de crear servicios

- Confirmar repositorio remoto GitHub.
- Confirmar rama de deploy.
- Confirmar acceso a Render.
- Confirmar acceso a Vercel.
- Confirmar dominio o subdominios:
  - `app.lexflow...`
  - `api.lexflow...`
- Confirmar responsable tecnico del deploy.

## Render

1. Crear Blueprint desde `render.yaml`.
2. Confirmar servicios:
   - `lexflow-api`
   - `lexflow-redis`
   - `lexflow-postgres`
3. Configurar variables manuales:
   - `ALLOWED_ORIGINS=https://app.tu-dominio`
   - `STORAGE_PUBLIC_BASE_URL=https://api.tu-dominio`
4. Confirmar que Render genere:
   - `JWT_SECRET`
   - `S3_SECRET_KEY`
5. Validar que el API inicia con Alembic antes de Uvicorn.
6. Probar:
   - `GET /health`
   - `GET /readiness`
   - `GET /api/v1/status`

## Vercel

1. Importar repo.
2. Framework: Next.js.
3. Build command: `npm --workspace apps/web run build`.
4. Output directory: `apps/web/.next`.
5. Configurar variables:
   - `NEXT_PUBLIC_API_URL=https://api.tu-dominio`
   - `NEXT_PUBLIC_APP_ENV=production`
6. Conectar dominio web.
7. Validar rutas criticas:
   - `/dashboard`
   - `/cases/demo-case-1`
   - `/settings/import`
   - `/settings/pilot`
   - `/settings/production-gate`

## Primer tenant productivo

- Crear tenant real.
- Crear usuario admin real.
- Desactivar seeds demo en produccion.
- Cargar datos piloto por CSV.
- Validar audit log de importacion.
- Validar aislamiento tenant.

## Gate obligatorio

Ejecutar antes de subir y antes de cada release:

```bash
npm run cloud:preflight
npm run lint
npm run test
npm run build
cd apps/api
python -m pytest -q
```

## No abrir a produccion publica hasta completar

- Storage S3/R2 real con URLs firmadas.
- Backups y restore probados.
- Monitoreo externo con alertas.
- Rate limits revisados por entorno.
- Pentest o revision security externa.
- Politica de retencion de documentos.
- Contrato de tratamiento de datos.
- Runbook de incidentes.
- Dominio, TLS, CORS y cookies finales.

## Estado P24

Listo para staging cloud. No listo para produccion publica sin los pendientes anteriores.
