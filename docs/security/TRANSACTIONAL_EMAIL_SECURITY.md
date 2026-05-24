# Transactional Email Security

## Estado implementado

- Proveedor mock seguro por defecto: `EMAIL_PROVIDER=prepared`.
- Proveedor HTTP JSON preparado: `EMAIL_PROVIDER=http_json`.
- Flujos conectados:
  - recuperacion de password
  - invitaciones de usuarios
- Los links usan `LEXFLOW_WEB_URL` y agregan `?token=...` solo para entrega al destinatario.
- Los tokens siguen guardandose solo como hash en backend.
- Las pantallas `/login/reset/confirm` y `/login/invite` leen `?token=` para autocompletar el formulario.

## Variables

- `EMAIL_PROVIDER`
- `EMAIL_API_URL`
- `EMAIL_API_KEY`
- `EMAIL_FROM`
- `LEXFLOW_WEB_URL`

## Contrato HTTP JSON

LEXFLOW envia `POST` JSON al proveedor configurado:

```json
{
  "from": "no-reply@lexflow.example",
  "to": "usuario@estudio.com",
  "subject": "Invitacion a LEXFLOW",
  "template": "user_invitation",
  "data": {
    "full_name": "Usuario",
    "invitation_url": "https://app.lexflow.example/login/invite?token=..."
  }
}
```

La API key se envia como `Authorization: Bearer ...` y nunca se expone al frontend.

## Pendiente productivo

- Seleccionar proveedor real y configurar dominio remitente.
- Verificar SPF, DKIM y DMARC.
- Agregar cola/retry para envios fallidos.
- Registrar eventos de entrega sin guardar contenido sensible.
