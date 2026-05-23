# DOCUMENT_STORAGE_P17

## Estado

P17 Document Storage Foundation implementado.

## Endpoints

- `GET /api/v1/storage/status`
- `GET /api/v1/client-portal/documents/{document_id}/download`
- `POST /api/v1/client-portal/cases/{case_id}/documents`

## Contrato

Los uploads del portal devuelven un bloque `upload` con:

- `url`
- `method`
- `headers`
- `max_bytes`
- `expires_at`

Las descargas devuelven:

- `url`
- `method`
- `expires_at`
- `storage_key`

## Veredicto

Listo para piloto con contrato S3-compatible. Produccion requiere conectar SDK/proveedor real y controles antivirus/checksum.
