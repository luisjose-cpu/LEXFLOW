# TENANT_BOOTSTRAP_IMPORT_P20

## Estado

P20 implementado: bootstrap del tenant actual e importacion CSV para clientes, expedientes y manifiestos documentales.

## Flujo piloto

1. Crear o actualizar tenant piloto.
2. Importar clientes con `dry_run=true`.
3. Importar clientes con `dry_run=false`.
4. Importar expedientes asociados a clientes.
5. Importar manifiesto documental.
6. Subir bytes con flujo P18.
7. Verificar y escanear documentos con flujo P19.

## Veredicto

Listo para cargar datos piloto controlados desde CSV exportado de Excel.
