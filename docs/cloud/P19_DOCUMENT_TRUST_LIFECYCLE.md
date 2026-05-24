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
  - `POST /api/v1/documents/{document_id}/scan`
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
- `REQUIRE_VERIFIED_DOCUMENT_DOWNLOADS=true` bloquea descargas del portal hasta que el documento tenga storage verificado, estado `verified` y escaneo `clean`.
- `MALWARE_SCANNER_PROVIDER` debe dejar de ser `mock` antes de produccion publica.
- `MALWARE_SCANNER_PROVIDER=clamav` usa protocolo ClamAV INSTREAM contra `CLAMAV_HOST:CLAMAV_PORT`.
- Toda accion interna queda auditada.

## Produccion pendiente

- Configurar proveedor antivirus real y documentar su SLA operativo.
- Politica de cuarentena.
- Retencion y borrado fisico del objeto rechazado.
- Escaneo asincrono con Celery.
- Integrar el gate de descarga verificada con politicas configurables por tenant.
