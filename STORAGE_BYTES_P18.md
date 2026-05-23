# STORAGE_BYTES_P18

## Estado

P18 implementado: LEXFLOW ya puede subir y descargar bytes mediante URLs firmadas en backend local persistente.

## Flujo

1. Cliente registra documento en portal.
2. API devuelve contrato `PUT`.
3. Cliente sube bytes a `/api/v1/storage/mock/{document_id}` con token.
4. API guarda archivo en `STORAGE_LOCAL_ROOT`.
5. Cliente solicita link de descarga.
6. API devuelve contrato `GET`.
7. Cliente descarga bytes con token firmado.

## Veredicto

Funcional para piloto local/controlado. Produccion publica aun requiere S3 real, antivirus, checksum post-upload y politicas de retencion.
