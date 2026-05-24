# P17 - Document Storage Foundation

## Objetivo

Avanzar de registro documental demo a contrato de storage productivo S3-compatible.

## Entregado

- `StorageService` S3-ready.
- Storage keys multitenant:

`tenants/{tenant_id}/cases/{case_id}/documents/{document_id}/{filename}`

- Contrato de upload firmado para portal cliente.
- Contrato de download firmado para portal cliente.
- Endpoint interno `GET /api/v1/storage/status`.
- Endpoint cliente `GET /api/v1/client-portal/documents/{document_id}/download`.
- Auditoria para generacion de links de descarga.
- Validaciones de filename, content type y max upload bytes configurado.
- Backend S3/R2 compatible con `boto3` cuando `STORAGE_BACKEND=s3`.
- Upload/download via API proxy sobre objetos S3 sin exponer credenciales al frontend.
- `head_object` para verificar existencia, bytes y checksum/ETag.

## Seguridad

- El cliente solo obtiene links para documentos visibles, de su cliente y de su expediente.
- Los documentos privados o de otro cliente devuelven 404.
- Las URLs firmadas expiran.
- El storage key siempre incluye tenant, case y document.
- No se exponen credenciales S3.

## Configuracion S3/R2

- `STORAGE_BACKEND=s3`
- `S3_ENDPOINT=https://<account>.r2.cloudflarestorage.com` o endpoint S3-compatible.
- `S3_ACCESS_KEY`
- `S3_SECRET_KEY`
- `S3_BUCKET`
- `STORAGE_PUBLIC_BASE_URL=https://<api-publica>/api/v1/storage/mock`

## Produccion pendiente

- Antivirus/antimalware para archivos cargados.
- Versionado y retencion por tenant.
- Politica de eliminacion segura.
- Presigned URLs nativas del proveedor para cargas pesadas, si el piloto supera el proxy API.
