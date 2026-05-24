# Cloud Rollback Runbook

## Objetivo

Volver rapidamente a una version estable de LEXFLOW cuando un deploy degrade API, web, autenticacion, expedientes, documentos o integraciones criticas.

## Disparadores

- `/health`, `/readiness` o `cloud:smoke` fallan despues del deploy.
- `cloud:revision` reporta un commit inesperado.
- Errores 5xx sostenidos en Render o Vercel.
- Login, Expediente 360, portal cliente, storage o SINOE quedan inutilizables.
- Incidente owner marcado como `critical`.

## Antes de revertir

1. Registrar incidente en Owner Console: componente, severidad, hora, version actual y responsable.
2. Descargar logs relevantes de Render/Vercel sin incluir secretos.
3. Confirmar ultimo commit estable y evidencia previa en `reports/cloud/`.
4. Si hay migraciones destructivas o cambios de datos, pausar y evaluar restore aislado antes de tocar produccion.

## Rollback API en Render

1. Abrir `lexflow-api` en Render.
2. Ir a deploys.
3. Seleccionar el ultimo deploy estable.
4. Ejecutar rollback/redeploy de ese deploy.
5. Esperar health check OK.
6. Ejecutar:

```powershell
$env:LEXFLOW_API_URL="https://lexflow-api.onrender.com"
npm run cloud:revision
npm run cloud:smoke
```

## Rollback web en Vercel

1. Abrir proyecto `lexflow-web`.
2. Ir a Deployments.
3. Promover el ultimo deployment estable a production.
4. Ejecutar:

```powershell
$env:LEXFLOW_WEB_URL="https://lexflow-web-nine.vercel.app"
$env:LEXFLOW_API_URL="https://lexflow-api.onrender.com"
npm run cloud:smoke
```

## Base de datos

No restaurar base productiva como primer paso salvo corrupcion confirmada.

1. Si el fallo es por migracion, revisar si existe migracion correctiva no destructiva.
2. Ejecutar restore drill en base aislada:

```powershell
$env:RESTORE_DATABASE_URL="<isolated-restore-db-url>"
npm run db:restore-drill -- -BackupPath backups/postgres/lexflow-staging-YYYYMMDDTHHMMSSZ.dump -Execute
```

3. Solo restaurar produccion con autorizacion owner/admin y ventana comunicada.

## Cierre

1. Ejecutar `npm run cloud:evidence`.
2. Adjuntar evidencia al incidente.
3. Resolver incidente en Owner Console con causa, accion y prevencion.
4. Crear tarea de remediacion antes de reintentar deploy.

## Reglas de seguridad

- No pegar secretos en tickets, logs ni chat.
- No hacer reset destructivo de Git.
- No borrar datos de tenants para resolver deploy.
- Todo acceso soporte a datos sensibles requiere intervencion temporal auditada.
