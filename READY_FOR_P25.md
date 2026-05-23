# READY_FOR_P25

## Estado

LEXFLOW queda listo para iniciar P25: despliegue staging cloud y validacion operativa con cuentas reales de Render, Vercel y GitHub.

## Entregado en P24

- Render Blueprint para API, PostgreSQL, Redis y persistent disk.
- Configuracion Vercel para Next.js.
- CI cloud en GitHub Actions.
- Dockerfile API con migraciones Alembic al iniciar.
- Dockerfile web de produccion para alternativa container.
- Preflight cloud automatizado.
- Normalizacion de URLs PostgreSQL cloud.
- Checklist go-live cloud.
- Pruebas P24 para deploy pack.

## Validaciones

- `npm run cloud:preflight`
- `npm run lint`
- `npm run test`
- `npm run build`
- `python -m pytest -q`

## Riesgos abiertos

- Falta conectar cuentas reales de cloud.
- Falta configurar dominios y CORS finales.
- Falta storage S3/R2 real para produccion publica.
- Falta validar backup/restore en la nube.
- Falta monitoreo externo con alertas.

## Proximo paso

Crear staging cloud en Render y Vercel, configurar variables reales, validar health/readiness y cargar el primer tenant piloto.
