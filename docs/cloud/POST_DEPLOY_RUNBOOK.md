# Post-Deploy Runbook

## Objetivo

Validar despues de cada deploy que API, web, readiness, revision y evidencia operativa estan correctos.

## Pasos

1. Confirmar deploy completado en Render y Vercel.
   - Render debe usar `autoDeployTrigger: checksPass`.
   - Si el deploy no arranca tras CI verde, ejecutar `Manual Deploy -> Deploy latest commit`.
2. Exportar URLs:

```powershell
$env:LEXFLOW_API_URL="https://lexflow-api.onrender.com"
$env:LEXFLOW_WEB_URL="https://lexflow-web-nine.vercel.app"
```

3. Verificar revision:

```powershell
npm run cloud:revision
```

Si Render acaba de iniciar deploy automatico, esperar hasta que sirva el commit esperado:

```powershell
npm run cloud:wait-revision
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

6. Para salida publica, ejecutar gate estricto:

```powershell
npm run cloud:public-ready
```

7. Revisar el JSON mas reciente en `reports/cloud/`.
8. Confirmar `revision.matches_expected=true` cuando Render/Vercel ya expongan revision.
9. Si `cloud:wait-revision` expira, usar `Manual Deploy -> Deploy latest commit` en Render y repetir desde el paso 3.
10. Si `cloud:public-ready` falla, revisar `reports/cloud/lexflow-public-ready-*.json` para las claves pendientes.

El workflow manual `Cloud CI` acepta `wait_for_revision=true` y `public_ready_gate=true` para ejecutar estos pasos desde GitHub Actions.

## Criterios de salida

- `/health` responde 200.
- `/api/v1/status` responde 200.
- `/metrics` responde 200.
- Headers de seguridad API/web presentes: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, HSTS.
- `/readiness` tiene `status=ready`.
- `readiness.blockers=0`.
- `production_ready=true`.
- `public_production_ready=false` es aceptable para piloto controlado si las warnings estan documentadas.
- Para produccion publica: `public_production_ready=true` y `warnings=0`.
- `cloud:public-ready` debe pasar antes de venta publica sin acompaniamiento.

## Si falla

- Revision no disponible: redeploy latest `master` o configurar `RELEASE_REVISION`.
- Revision mismatch: revisar que Render/Vercel esten apuntando a branch `master` y que el deploy no haya fallado.
- Readiness blocked: abrir `/settings/production-gate` y resolver blockers listados.
- Provider modes mock: cerrar gaps de `docs/cloud/P25_PUBLIC_PRODUCTION_GAPS.md`.
- Degradacion posterior a deploy: ejecutar [ROLLBACK_RUNBOOK.md](ROLLBACK_RUNBOOK.md).

## Evidencia

Los reportes bajo `reports/` no se versionan en git. Para auditoria externa, exportarlos al repositorio documental del proyecto o herramienta de compliance acordada.
