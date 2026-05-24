# Transactional Email Security

## Estado implementado

- Proveedor mock seguro por defecto: `EMAIL_PROVIDER=prepared`.
- Proveedor HTTP JSON preparado: `EMAIL_PROVIDER=http_json`.
- Flujos conectados:
  - recuperacion de password
  - invitaciones de usuarios
- Los links usan `LEXFLOW_WEB_URL` y agregan `?token=...` solo para entrega al destinatario.
- Los tokens siguen guardandose solo como hash en backend.
- Cada intento de entrega se registra en `email_delivery_logs` sin contenido, sin token y sin email completo.
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

## Telemetria Redactada

`GET /api/v1/settings/email/deliveries` devuelve entregas recientes por tenant:

- template
- provider
- status
- recipient_hint
- created_at

No devuelve `recipient_hash`, token, URL de invitacion/reset ni cuerpo del mensaje.

## Pendiente productivo

- Seleccionar proveedor real y configurar dominio remitente.
- Verificar SPF, DKIM y DMARC.
- Agregar cola/retry para envios fallidos.
- Panel avanzado de filtros/reintento para entregas fallidas.
