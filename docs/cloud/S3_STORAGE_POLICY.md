# S3-Compatible Storage Policy

## Objetivo

Definir plantillas revisables para storage documental productivo S3/R2 sin aplicar cambios destructivos automaticamente.

## Archivos

- `infra/cloud/s3-lifecycle-policy.json`
- `infra/cloud/s3-cors-policy.json`

## Lifecycle

La plantilla propone:

- Scope: objetos bajo `tenants/`.
- Transicion a storage infrecuente despues de 90 dias.
- Versiones no actuales a storage infrecuente despues de 30 dias.
- Expiracion de versiones no actuales despues de 365 dias.
- Limpieza de multipart uploads incompletos despues de 7 dias.

## CORS

La plantilla permite solo:

- Origen web productivo esperado.
- `GET`, `PUT`, `HEAD`.
- Headers minimos para content type/checksum.
- Exposicion de `ETag` y version id.

Antes de aplicar, reemplazar `https://app.lexflow.example` por el dominio real.

## Seguridad

- No contiene access keys, secret keys ni bucket names reales.
- No ejecutar contra produccion sin aprobacion y respaldo vigente.
- Mantener versioning del bucket habilitado para documentos legales.
- No habilitar origen wildcard.

## Validacion

Despues de aplicar en el proveedor:

1. Ejecutar upload de documento piloto.
2. Verificar `ETag`/checksum.
3. Ejecutar download portal autorizado.
4. Validar bloqueo cross-tenant.
5. Registrar evidencia en `reports/cloud/` o bitacora operativa.
