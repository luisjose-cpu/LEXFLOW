# Security Alerts

## Estado

LEXFLOW registra alertas operativas para eventos criticos de seguridad, separadas del audit log.

Endpoints tenant:

- `GET /api/v1/settings/security-alerts`
- `POST /api/v1/settings/security-alerts/{id}/acknowledge`

Endpoints owner:

- `GET /api/v1/owner/security-alerts`
- `POST /api/v1/owner/security-alerts/{id}/acknowledge`

## Eventos cubiertos

Tenant:

- cambio de password autenticado
- recuperacion de password completada
- MFA activado
- MFA desactivado
- politica MFA tenant actualizada
- invitacion creada, reenviada o cancelada

Owner:

- login owner
- MFA owner activado
- MFA owner desactivado
- recovery code owner usado
- recovery codes owner regenerados

## Seguridad

- Las alertas no almacenan passwords, tokens, secretos MFA ni recovery codes.
- El acceso tenant queda limitado por RBAC y tenant isolation.
- El acceso owner exige permisos owner y bearer token cuando se marca una alerta.
- Reconocer una alerta registra `status=acknowledged`, usuario/owner responsable y timestamp.

## Pendiente productivo

- Envio por email/push para eventos `high` y `critical`.
- Politicas de retencion y export para auditoria externa.
- Agrupacion/dedupe para evitar ruido por login owner frecuente.
