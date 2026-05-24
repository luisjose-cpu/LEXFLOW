# P18 - Storage Bytes Foundation

## Objetivo

Hacer funcional el contrato de storage de P17: las URLs firmadas ahora permiten subir y descargar bytes en un backend local persistente para piloto.

## Entregado

- `PUT /api/v1/storage/mock/{document_id}?token=...`
- `GET /api/v1/storage/mock/{document_id}?token=...`
- Verificacion HMAC del token firmado.
- Expiracion de tokens.
- Validacion de `Content-Type`.
- Validacion de tamano maximo.
- Persistencia local en `STORAGE_LOCAL_ROOT`.
- Persistencia S3-compatible cuando `STORAGE_BACKEND=s3`.
- SHA256 por objeto.
- Auditoria:
  - `storage_object_uploaded`
  - `storage_object_downloaded`

## Configuracion

- `STORAGE_BACKEND=local`
- `STORAGE_LOCAL_ROOT=.lexflow-storage`
- `STORAGE_BACKEND=s3`
- `S3_ENDPOINT`
- `S3_ACCESS_KEY`
- `S3_SECRET_KEY`
- `S3_BUCKET`
- `MAX_UPLOAD_BYTES=26214400`
- `STORAGE_SIGNED_URL_MINUTES=15`

## Seguridad

- El token firmado contiene tenant, documento, storage key, accion y expiracion.
- El upload falla si el token no corresponde al documento.
- El download falla si el objeto no existe.
- El content type debe coincidir con el documento registrado.
- El path local se resuelve dentro de `STORAGE_LOCAL_ROOT`.
- En S3/R2, el frontend usa el mismo contrato firmado y la API hace proxy controlado al bucket.

## Pendiente productivo

- Integrar antivirus/antimalware.
- Agregar versionado y retencion.
- Agregar lifecycle policies por tenant.
- Evaluar presigned URLs nativas para archivos grandes.
