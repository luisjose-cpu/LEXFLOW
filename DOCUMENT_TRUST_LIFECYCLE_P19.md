# DOCUMENT_TRUST_LIFECYCLE_P19

## Estado

P19 implementado: los documentos ahora tienen ciclo de confianza operacional.

## Flujo

1. Cliente registra documento.
2. Cliente sube bytes con URL firmada.
3. Storage calcula checksum y tamano.
4. Equipo legal verifica storage.
5. Escaneo mock marca documento como `clean` o `infected`.
6. Documento limpio pasa a `verified`.
7. Documento infectado o rechazado se oculta del portal.

## Veredicto

Funcional para piloto y preparado para reemplazar el escaneo mock por antivirus real.
