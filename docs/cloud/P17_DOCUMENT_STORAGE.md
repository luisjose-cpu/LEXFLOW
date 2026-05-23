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

## Seguridad

- El cliente solo obtiene links para documentos visibles, de su cliente y de su expediente.
- Los documentos privados o de otro cliente devuelven 404.
- Las URLs firmadas expiran.
- El storage key siempre incluye tenant, case y document.
- No se exponen credenciales S3.

## Produccion pendiente

- Implementar cliente S3 real con boto3/aioboto3 o SDK compatible.
- Validar checksum y tamano real post-upload.
- Antivirus/antimalware para archivos cargados.
- Versionado y retencion por tenant.
- Politica de eliminacion segura.
- Descarga real por proxy o presigned URL nativa del proveedor.
