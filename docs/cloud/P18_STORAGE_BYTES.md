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
- SHA256 por objeto.
- Auditoria:
  - `storage_object_uploaded`
  - `storage_object_downloaded`

## Configuracion

- `STORAGE_BACKEND=local`
- `STORAGE_LOCAL_ROOT=.lexflow-storage`
- `MAX_UPLOAD_BYTES=26214400`
- `STORAGE_SIGNED_URL_MINUTES=15`

## Seguridad

- El token firmado contiene tenant, documento, storage key, accion y expiracion.
- El upload falla si el token no corresponde al documento.
- El download falla si el objeto no existe.
- El content type debe coincidir con el documento registrado.
- El path local se resuelve dentro de `STORAGE_LOCAL_ROOT`.

## Pendiente para S3 real

- Reemplazar backend `local` por presigned URLs nativas del proveedor.
- Confirmar checksum post-upload.
- Integrar antivirus/antimalware.
- Agregar versionado y retencion.
- Agregar lifecycle policies por tenant.
