# Post-Deploy Runbook

## Objetivo

Validar despues de cada deploy que API, web, readiness, revision y evidencia operativa estan correctos.

## Pasos

1. Confirmar deploy completado en Render y Vercel.
2. Exportar URLs:

```powershell
$env:LEXFLOW_API_URL="https://lexflow-api.onrender.com"
$env:LEXFLOW_WEB_URL="https://lexflow-web-nine.vercel.app"
```

3. Verificar revision:

```powershell
npm run cloud:revision
```

Cuando Render ya exponga revision y se quiera bloquear mismatch:

```powershell
npm run cloud:revision -- -Strict
```

4. Ejecutar smoke:

```powershell
npm run cloud:smoke
```

5. Generar evidencia:

```powershell
npm run cloud:evidence
```

6. Revisar el JSON mas reciente en `reports/cloud/`.

## Criterios de salida

- `/health` responde 200.
- `/api/v1/status` responde 200.
- `/metrics` responde 200.
- `/readiness` tiene `status=ready`.
- `readiness.blockers=0`.
- `production_ready=true`.
- `public_production_ready=false` es aceptable para piloto controlado si las warnings estan documentadas.
- Para produccion publica: `public_production_ready=true` y `warnings=0`.

## Si falla

- Revision no disponible: redeploy latest `master` o configurar `RELEASE_REVISION`.
- Revision mismatch: revisar que Render/Vercel esten apuntando a branch `master` y que el deploy no haya fallado.
- Readiness blocked: abrir `/settings/production-gate` y resolver blockers listados.
- Provider modes mock: cerrar gaps de `docs/cloud/P25_PUBLIC_PRODUCTION_GAPS.md`.

## Evidencia

Los reportes bajo `reports/` no se versionan en git. Para auditoria externa, exportarlos al repositorio documental del proyecto o herramienta de compliance acordada.
