# Security Alerts

## Estado

LEXFLOW registra alertas operativas para eventos criticos de seguridad, separadas del audit log.

Endpoints tenant:

- `GET /api/v1/settings/security-alerts`
- `POST /api/v1/settings/security-alerts/{id}/acknowledge`
- `GET /api/v1/settings/security-alert-deliveries`
- `POST /api/v1/settings/security-alert-deliveries/process`

Endpoints owner:

- `GET /api/v1/owner/security-alerts`
- `POST /api/v1/owner/security-alerts/{id}/acknowledge`
- `GET /api/v1/owner/security-alert-deliveries`
- `POST /api/v1/owner/security-alert-deliveries/process`

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
- Las entregas email guardan destinatario cifrado y solo exponen hash/hint.
- Solo alertas `high` y `critical` generan entrega email automatica.
- El provider usa el boundary transaccional existente `EMAIL_PROVIDER=prepared|http_json`.
- Los reintentos quedan limitados por `max_attempts` y `next_attempt_at`.
- El acceso tenant queda limitado por RBAC y tenant isolation.
- El acceso owner exige permisos owner y bearer token cuando se marca una alerta.
- Reconocer una alerta registra `status=acknowledged`, usuario/owner responsable y timestamp.

## Operacion

Procesar entregas pendientes desde un One-Off Job o cron externo:

```bash
python scripts/process_security_alert_deliveries.py --limit 100
python scripts/process_security_alert_deliveries.py --scope owner --limit 50
python scripts/process_security_alert_deliveries.py --scope tenant --tenant-id <tenant_id> --limit 50
```

El comando no imprime destinatarios reales ni payloads sensibles.

En Render, el blueprint declara `lexflow-security-alert-deliveries` como cron cada 15 minutos para procesar pendientes automaticamente.

## Pendiente productivo

- Worker Celery dedicado para alto volumen y metricas avanzadas de reintentos.
- Push para eventos `critical`.
- Politicas de retencion y export para auditoria externa.
- Agrupacion/dedupe para evitar ruido por login owner frecuente.
