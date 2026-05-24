# Feature Flags

## Flags iniciales

- `client_portal`
- `whatsapp`
- `ai`
- `ocr`
- `sinoe`
- `legal_intelligence`
- `automation_studio`
- `dashboard`
- `mobile_pwa`

## Reglas

- Cada flag pertenece a un tenant.
- Cambios de flags se auditan.
- Los endpoints funcionales deben verificar feature gates en backend.
- El frontend solo refleja disponibilidad; no es la barrera de seguridad.
- Planes y limites deben validar upgrades/downgrades.

## Uso comercial

Las flags permiten pilotos graduales, demos por vertical, bloqueo por deuda, upgrades controlados y pruebas enterprise.

## Planes owner

Owner Console administra el catalogo SaaS con:

- `POST /api/v1/owner/plans`
- `PATCH /api/v1/owner/plans/{code}`

Cada alta o cambio de plan genera `owner_audit_logs`. El catalogo propietario queda aislado en un tenant tecnico `lexflow-owner-catalog` y no expone datos sensibles de estudios.
