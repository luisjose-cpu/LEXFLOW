# P19 - Document Trust Lifecycle

## Objetivo

Agregar ciclo de confianza documental sobre los bytes reales de P18: verificacion de storage, checksum, escaneo mock, aprobacion implicita por documento limpio y rechazo controlado.

## Entregado

- Nuevas columnas en `documents`:
  - `file_size_bytes`
  - `checksum_sha256`
  - `storage_verified_at`
  - `malware_scan_status`
  - `malware_scan_result`
- Endpoints internos:
  - `GET /api/v1/documents/{document_id}/storage`
  - `POST /api/v1/documents/{document_id}/verify-storage`
  - `POST /api/v1/documents/{document_id}/scan-mock`
  - `POST /api/v1/documents/{document_id}/reject`
- Auditoria:
  - `document_storage_verified`
  - `document_malware_scan_completed`
  - `document_rejected`
- UI demo muestra tamano, checksum corto, storage verificado y estado de escaneo.

## Estados recomendados

- `pending_review`: archivo recibido y pendiente de revision.
- `verified`: archivo con storage verificado y escaneo limpio.
- `rejected`: archivo oculto al cliente y bloqueado por rechazo o infeccion.
- `private`: archivo interno no visible para cliente.

## Seguridad

- Cliente no puede invocar lifecycle interno.
- Documento infectado se oculta del portal.
- Documento rechazado se oculta del portal.
- Toda accion interna queda auditada.

## Produccion pendiente

- Integracion antivirus real.
- Politica de cuarentena.
- Retencion y borrado fisico del objeto rechazado.
- Escaneo asincrono con Celery.
- Bloqueo de descarga hasta `verified` si el estudio lo requiere.
