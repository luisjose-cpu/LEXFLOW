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
