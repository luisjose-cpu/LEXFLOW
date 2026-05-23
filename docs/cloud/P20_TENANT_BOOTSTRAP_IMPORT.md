# P20 - Tenant Bootstrap and CSV Import

## Objetivo

Permitir cargar datos reales o anonimizados de un estudio piloto sin hacerlo manualmente pantalla por pantalla.

## Endpoints

- `POST /api/v1/ops/bootstrap/current-tenant`
- `POST /api/v1/ops/import/clients`
- `POST /api/v1/ops/import/cases`
- `POST /api/v1/ops/import/documents`

## Seguridad

- Todos los endpoints usan RBAC interno.
- Todos los imports son tenant-scoped.
- `dry_run=true` permite previsualizar sin escribir.
- Las importaciones reales generan `audit_logs`.
- El cliente del portal no puede importar.
- Headers cross-tenant son bloqueados por `get_request_tenant`.

## CSV clientes

```csv
name,contact_email,risk_profile,tags
Acme Legal,legal@acme.test,high,corporate;pilot
Beta Corp,legal@beta.test,standard,contracts
```

## CSV expedientes

```csv
client_email,title,external_case_number,status,description
legal@acme.test,Cobro Acme,ACME-001,active,Expediente piloto
```

## CSV documentos

```csv
case_external_case_number,filename,content_type,classification,is_client_visible
ACME-001,demanda-acme.pdf,application/pdf,pleading,true
```

## Comportamiento documentos

Los documentos importados quedan en `pending_upload` y reciben `storage_key` tenant-scoped. Luego se suben bytes usando el flujo P18 y se verifican con P19.

## Produccion pendiente

- Importador desde archivo multipart.
- Mapeo visual de columnas.
- Validacion masiva antes de commit.
- Reporte descargable de errores.
- Import asincrono con Celery para cargas grandes.
